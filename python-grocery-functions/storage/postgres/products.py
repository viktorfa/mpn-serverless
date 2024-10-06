from typing import List, Sequence, Set, Dict, Tuple
from uuid import UUID
from sqlalchemy.orm import Session
import pydash

from parsing.nutrition_extraction import extract_nutritional_data_new
from storage.postgres.common import get_pg_engine
from storage.postgres.gtins import (
    find_existing_gtins,
    insert_new_gtins,
    upsert_offer_has_gtin,
)
from storage.postgres.market_infos import (
    collect_product_market_info_entries,
    upsert_product_market_info,
)
from storage.postgres.products_handling import (
    determine_product_ids,
    insert_products,
    merge_product_info,
    update_offers_with_product_id,
    update_products,
    upsert_product_has_ingredient,
)
from storage.postgres.pydantic_models import MarketInfo, PreparedData, ProductInfo
from amp_types.amp_product import ProcessedMpnOffer
from storage.postgres.utils import UnionFind
from util.utils import log_traceback


def prepare_offer_data(
    offers: Sequence[ProcessedMpnOffer],
) -> Tuple[PreparedData, UnionFind]:
    offer_gtins: Set[str] = set()
    offer_has_gtin_list: List[Dict[str, str]] = []
    gtin_offer_map: Dict[str, Set[str]] = {}
    gtin_market_info_map: Dict[str, MarketInfo] = {}
    gtin_product_map: Dict[str, ProductInfo] = {}
    offer_to_gtins: Dict[str, List[str]] = {}
    gtin_offer_object_map: Dict[str, ProcessedMpnOffer] = {}
    uf = UnionFind()

    for offer in offers:
        uri_string: str = f"{offer['namespace']}:{offer['provenanceId']}"
        gtin_list: List[str] = []
        internal_gtin_string = f"_mpn:{uri_string}"
        gtin_offer_object_map[internal_gtin_string] = offer
        gtin_list.append(internal_gtin_string)
        offer_gtins.add(internal_gtin_string)
        gtin_offer_map.setdefault(internal_gtin_string, set()).add(uri_string)
        offer_has_gtin_list.append(
            {
                "offer_uri": uri_string,
                "gtin": internal_gtin_string,
                "match_type": "copy",
            }
        )

        for key, value in offer.get("gtins", {}).items():
            gtin_string: str = f"{key}:{value}"
            gtin_offer_object_map[gtin_string] = offer
            offer_gtins.add(gtin_string)
            gtin_offer_map.setdefault(gtin_string, set()).add(uri_string)
            gtin_list.append(gtin_string)

            offer_has_gtin_list.append(
                {
                    "offer_uri": uri_string,
                    "gtin": gtin_string,
                    "match_type": "auto",
                }
            )

        offer_to_gtins[uri_string] = gtin_list

        if len(gtin_list) > 1:
            # Union all GTINs in the offer
            first_gtin: str = gtin_list[0]
            for gtin in gtin_list[1:]:
                uf.union(first_gtin, gtin)

        # Collect market info for each GTIN
        market_info = MarketInfo(
            market=offer["market"],
            title=offer["title"],
            description=offer.get("description"),
            subtitle=offer.get("subtitle"),
            short_description=offer.get("short_description"),
            brand_key=offer.get("brandKey"),
            vendor_key=offer.get("vendorKey"),
            context=offer["context"],
            category_key=None,
        )

        product_info = ProductInfo(
            quantity_unit=pydash.get(offer, ["quantity", "size", "unit", "symbol"]),
            quantity_amount=pydash.get(offer, ["quantity", "size", "amount", "max"]),
            quantity_standard_amount=pydash.get(
                offer, ["quantity", "size", "standard", "max"]
            ),
            nutrition=extract_nutritional_data_new(offer.get("mpnNutrition", {})),
            merged_to=None,
        )

        for gtin in gtin_list:
            if gtin not in gtin_market_info_map:
                gtin_market_info_map[gtin] = market_info
            existing_product_info = gtin_product_map.get(gtin)
            if existing_product_info:
                gtin_product_map[gtin] = merge_product_info(
                    existing_product_info, product_info
                )
            else:
                gtin_product_map[gtin] = product_info

    prepared_data = PreparedData(
        offer_gtins=offer_gtins,
        offer_has_gtin_list=offer_has_gtin_list,
        gtin_offer_map=gtin_offer_map,
        gtin_market_info_map=gtin_market_info_map,
        gtin_product_map=gtin_product_map,
        offer_to_gtins=offer_to_gtins,
        gtin_offer_object_map=gtin_offer_object_map,
    )

    return prepared_data, uf


def build_root_to_gtins(uf: UnionFind, offer_gtins: Set[str]) -> Dict[str, Set[str]]:
    """
    Builds a dictionary mapping each root GTIN to a set of GTINs that share the same root.

    Args:
        uf (UnionFind): An instance of the UnionFind data structure used to find the root of each GTIN.
        offer_gtins (Set[str]): A set of GTINs (Global Trade Item Numbers) to be processed.

    Returns:
        Dict[str, Set[str]]: A dictionary where each key is a root GTIN and each value is a set of GTINs that share the same root.
    """
    root_to_gtins: Dict[str, Set[str]] = {}
    for gtin in offer_gtins:
        root: str = uf.find(gtin)
        if root not in root_to_gtins:
            root_to_gtins[root] = set()
        root_to_gtins[root].add(gtin)
    return root_to_gtins


def handle_gtins_for_offers(
    offers: Sequence[ProcessedMpnOffer], context: str
) -> List[UUID] | None:
    prepared_data, uf = prepare_offer_data(offers)

    with Session(get_pg_engine()) as session:
        try:
            gtin_to_product_map, existing_gtins, new_gtins = find_existing_gtins(
                session, prepared_data.offer_gtins
            )
            root_to_gtins = build_root_to_gtins(uf, prepared_data.offer_gtins)
            component_product_id, new_products, products_to_update = (
                determine_product_ids(
                    root_to_gtins,
                    gtin_to_product_map,
                    prepared_data.gtin_product_map,
                )
            )
            insert_products(session, new_products)

            insert_new_gtins(session, new_gtins, gtin_to_product_map)

            update_products(
                session,
                products_to_update,
                root_to_gtins,
                prepared_data.gtin_product_map,
                existing_gtins,
                gtin_to_product_map,
            )

            upsert_offer_has_gtin(session, prepared_data.offer_has_gtin_list)
            product_market_info_entries = collect_product_market_info_entries(
                session,
                context,
                root_to_gtins,
                gtin_to_product_map,
                prepared_data.gtin_market_info_map,
                prepared_data.gtin_offer_object_map,
            )

            upsert_product_has_ingredient(
                session=session,
                gtin_product_map=prepared_data.gtin_product_map,
                gtin_offer_object_map=prepared_data.gtin_offer_object_map,
                gtin_to_product_map=gtin_to_product_map,
            )
            upsert_product_market_info(
                session, list(product_market_info_entries.values())
            )
            update_offers_with_product_id(
                session, prepared_data.offer_to_gtins, gtin_to_product_map
            )

            session.commit()
            print("gtin_to_product_map.values()", gtin_to_product_map.values())
            return list(gtin_to_product_map.values())
        except Exception as e:
            print(f"An error occurred: {e}")
            log_traceback(e)
            session.rollback()
