import logging
from typing import List, Sequence, Set, Optional, Dict, Tuple
from sqlalchemy.orm import Session
from uuid_extensions import uuid7str
import pydash
from sqlalchemy import case

from parsing.ingredients_extraction import get_extracted_ingredients_postgres
from parsing.nutrition_extraction import extract_nutritional_data_new
from storage.postgres.common import get_pg_engine
from storage.postgres.pydantic_models import (
    DbMarketInfo,
    DbProductInfo,
    MarketInfo,
    NutritionType,
    PreparedData,
    ProductInfo,
)
from amp_types.amp_product import ProcessedMpnOffer
from storage.postgres.postgres_tables import (
    OfferHasGtinTable,
    OffersTable,
    ProductHasIngredientTable,
    ProductMarketInfoTable,
    GtinsTable,
    ProductsTable,
)
from storage.postgres.utils import UnionFind
from util.utils import log_traceback


def get_offer_from_gtin(
    gtin_offer_object_map: Dict[str, ProcessedMpnOffer], gtin: str
) -> ProcessedMpnOffer:
    return gtin_offer_object_map[gtin]


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


def merge_product_info(existing: ProductInfo, new: ProductInfo) -> ProductInfo:
    return ProductInfo(
        quantity_unit=existing.quantity_unit or new.quantity_unit,
        quantity_amount=existing.quantity_amount or new.quantity_amount,
        quantity_standard_amount=existing.quantity_standard_amount
        or new.quantity_standard_amount,
        nutrition=NutritionType(
            **{
                **(existing.nutrition.model_dump() if existing.nutrition else {}),
                **(new.nutrition.model_dump() if new.nutrition else {}),
            }
        ),
        merged_to=None,
    )


def find_existing_gtins(
    session: Session, offer_gtins: Set[str]
) -> Tuple[Dict[str, str], Set[str], Set[str]]:
    existing_gtin_rows = (
        session.query(GtinsTable).filter(GtinsTable.gtin.in_(offer_gtins)).all()
    )

    print(f"Found {len(existing_gtin_rows)} existing GTINs.")

    gtin_to_product_map: Dict[str, str] = {
        row.gtin: str(row.product_id)
        for row in existing_gtin_rows
        if bool(row.product_id)
    }
    existing_gtins: Set[str] = set(gtin_to_product_map.keys())
    new_gtins: Set[str] = offer_gtins - existing_gtins

    return gtin_to_product_map, existing_gtins, new_gtins


def build_root_to_gtins(uf: UnionFind, offer_gtins: Set[str]) -> Dict[str, Set[str]]:
    root_to_gtins: Dict[str, Set[str]] = {}
    for gtin in offer_gtins:
        root: str = uf.find(gtin)
        if root not in root_to_gtins:
            root_to_gtins[root] = set()
        root_to_gtins[root].add(gtin)
    return root_to_gtins


def determine_product_ids(
    root_to_gtins: Dict[str, Set[str]],
    gtin_to_product_map: Dict[str, str],
    gtin_product_map: Dict[str, ProductInfo],
) -> Tuple[
    Dict[str, str],
    List[DbProductInfo],
    Dict[str, DbProductInfo],
    List[Dict[str, str]],
]:
    component_product_id: Dict[str, str] = {}  # Map from root to product_id
    new_products: List[DbProductInfo] = []
    products_to_update: Dict[str, DbProductInfo] = {}
    gtins_to_update: List[Dict[str, str]] = []

    for root, component_gtins in root_to_gtins.items():
        # Collect product_ids associated with GTINs in the component
        product_ids_in_component: Set[str] = set()
        for gtin in component_gtins:
            if gtin in gtin_to_product_map:
                product_ids_in_component.add(gtin_to_product_map[gtin])

        # Collect product data from GTINs in the component
        product_data = ProductInfo(
            quantity_unit=None,
            quantity_amount=None,
            quantity_standard_amount=None,
            nutrition=NutritionType(),
            merged_to=None,
        )

        for gtin in component_gtins:
            gtin_product_info = gtin_product_map.get(gtin)
            if gtin_product_info:
                for key in [
                    "quantity_unit",
                    "quantity_amount",
                    "quantity_standard_amount",
                    "nutrition",
                ]:
                    new_value = getattr(gtin_product_info, key)
                    old_value = getattr(product_data, key)
                    if key == "nutrition":
                        new_n_filled_keys = sum(
                            1 for k in new_value.model_dump().values() if k
                        )
                        old_n_filled_keys = sum(
                            1 for k in old_value.model_dump().values() if k
                        )
                        if new_n_filled_keys > old_n_filled_keys:
                            setattr(product_data, key, new_value)

                    elif new_value and not old_value:
                        setattr(product_data, key, new_value)

        if not product_ids_in_component:
            # No existing product_id, create new product
            new_product_id: str = uuid7str()
            product_data = DbProductInfo(id=new_product_id, **product_data.model_dump())
            new_products.append(product_data)
            component_product_id[root] = new_product_id
        else:
            # Existing product_ids found
            selected_product_id = get_product_to_merge_to(
                product_ids=list(product_ids_in_component),
                root_to_gtins=root_to_gtins,
                gtin_to_product_map=gtin_to_product_map,
                gtin_product_map=gtin_product_map,
            )
            component_product_id[root] = selected_product_id

            other_product_ids: Set[str] = product_ids_in_component - {
                selected_product_id
            }

            for product_id in other_product_ids:
                product_data = DbProductInfo(
                    id=product_id,
                    merged_to=selected_product_id,
                    quantity_amount=None,
                    quantity_standard_amount=None,
                    nutrition=None,
                    quantity_unit=None,
                )
                products_to_update[product_id] = product_data

            # Prepare product data for update
            product_data = DbProductInfo(
                id=selected_product_id, **product_data.model_dump()
            )
            products_to_update[selected_product_id] = product_data

            if len(product_ids_in_component) > 1:
                # Need to merge products

                print(
                    f"Merging products {other_product_ids} into {selected_product_id}"
                )
                # Update GTINs to use the selected product_id
                for gtin in component_gtins:
                    existing_product_id: Optional[str] = gtin_to_product_map.get(gtin)
                    if (
                        existing_product_id
                        and existing_product_id != selected_product_id
                    ):
                        gtins_to_update.append(
                            {
                                "gtin": gtin,
                                "product_id": selected_product_id,
                            }
                        )
                        gtin_to_product_map[gtin] = selected_product_id

        # Update gtin_to_product_map for all GTINs in component
        for gtin in component_gtins:
            gtin_to_product_map[gtin] = component_product_id[root]

    return component_product_id, new_products, products_to_update, gtins_to_update


def get_product_to_merge_to(
    product_ids: Sequence[str],
    root_to_gtins: Dict[str, Set[str]],
    gtin_to_product_map: Dict[str, str],
    gtin_product_map: Dict[str, ProductInfo],
) -> str:
    # Get the product with the lowest ID
    result = min(product_ids)
    return result


def upsert_products(
    session: Session,
    new_products: List[DbProductInfo],
    products_to_update: Dict[str, DbProductInfo],
) -> None:
    from sqlalchemy.dialects.postgresql import insert as pg_insert
    from sqlalchemy import case

    products_entries = [product.model_dump() for product in new_products] + [
        product.model_dump() for product in products_to_update.values()
    ]

    for pe in products_entries:
        pe["nutrition"] = {k: v for k, v in pe["nutrition"].items() if v is not None}

    if products_entries:
        products_stmt = pg_insert(ProductsTable.__table__).values(products_entries)
        # Define the update columns with conditional expressions
        update_columns = {
            "quantity_unit": case(
                (
                    ProductsTable.quantity_unit == None,
                    products_stmt.excluded.quantity_unit,
                ),
                else_=ProductsTable.quantity_unit,
            ),
            "quantity_amount": case(
                (
                    ProductsTable.quantity_amount == None,
                    products_stmt.excluded.quantity_amount,
                ),
                else_=ProductsTable.quantity_amount,
            ),
            "quantity_standard_amount": case(
                (
                    ProductsTable.quantity_standard_amount == None,
                    products_stmt.excluded.quantity_standard_amount,
                ),
                else_=ProductsTable.quantity_standard_amount,
            ),
            "nutrition": case(
                (
                    ProductsTable.nutrition == None,
                    products_stmt.excluded.nutrition,
                ),
                else_=ProductsTable.nutrition,
            ),
        }
        upsert_stmt = products_stmt.on_conflict_do_update(
            index_elements=["id"], set_=update_columns
        )
        session.execute(upsert_stmt)
        print(f"Upserted {len(products_entries)} products.")


def insert_new_gtins(
    session: Session, new_gtins: Set[str], gtin_to_product_map: Dict[str, str]
) -> None:
    from sqlalchemy.dialects.postgresql import insert as pg_insert

    if new_gtins:
        gtins_to_insert = [
            {
                "gtin": gtin,
                "product_id": gtin_to_product_map[gtin],
            }
            for gtin in new_gtins
        ]
        gtin_insert_stmt = (
            pg_insert(GtinsTable.__table__)
            .values(gtins_to_insert)
            .on_conflict_do_nothing(index_elements=["gtin"])
        )
        session.execute(gtin_insert_stmt)
        print(f"Inserted {len(gtins_to_insert)} new GTINs.")


def update_gtins(session: Session, gtins_to_update: List[Dict[str, str]]) -> None:
    if gtins_to_update:
        # Prepare data for bulk update
        gtin_update_mapping: Dict[str, str] = {
            item["gtin"]: item["product_id"] for item in gtins_to_update
        }
        gtins_to_update_list = list(gtin_update_mapping.keys())

        # Build a CASE statement for bulk update
        case_stmt = case(
            *[
                (GtinsTable.gtin == gtin, gtin_update_mapping[gtin])
                for gtin in gtins_to_update_list
            ],
            else_=GtinsTable.product_id,
        )

        update_stmt = (
            GtinsTable.__table__.update()
            .where(GtinsTable.gtin.in_(gtins_to_update_list))
            .values(product_id=case_stmt)
        )
        session.execute(update_stmt)
        print(f"Updated {len(gtins_to_update)} GTINs to new product IDs.")


def collect_product_market_info_entries(
    root_to_gtins: Dict[str, Set[str]],
    component_product_id: Dict[str, str],
    gtin_market_info_map: Dict[str, MarketInfo],
) -> Dict[str, DbMarketInfo]:
    product_market_info_entries: Dict[str, DbMarketInfo] = {}
    for root, component_gtins in root_to_gtins.items():
        product_id: str = component_product_id[root]
        # Get market info from one of the GTINs in the component
        for gtin in component_gtins:
            market_info_entry: Optional[MarketInfo] = gtin_market_info_map.get(gtin)
            if market_info_entry:
                entry = DbMarketInfo(
                    product_id=product_id,
                    **market_info_entry.model_dump(),
                )

                product_market_info_entries[gtin] = entry
                break  # Use the first available market info
    return product_market_info_entries


def upsert_offer_has_gtin(
    session: Session, offer_has_gtin_list: List[Dict[str, str]]
) -> None:
    from sqlalchemy.dialects.postgresql import insert as pg_insert

    if offer_has_gtin_list:
        offer_has_gtin_stmt = (
            pg_insert(OfferHasGtinTable.__table__)
            .values(offer_has_gtin_list)
            .on_conflict_do_nothing(index_elements=["offer_uri", "gtin"])
        )
        session.execute(offer_has_gtin_stmt)
        print(f"Upserted {len(offer_has_gtin_list)} offer_has_gtin entries.")


def update_offers_with_product_id(
    session: Session,
    offer_to_gtins: Dict[str, List[str]],
    gtin_to_product_map: Dict[str, str],
) -> None:
    if offer_to_gtins:
        offer_product_updates: List[Dict[str, str]] = []
        for offer_uri, gtin_list in offer_to_gtins.items():
            # Get the product_id from any GTIN in the gtin_list
            product_id = None
            for gtin in gtin_list:
                product_id = gtin_to_product_map.get(gtin)
                if product_id:
                    break
            if product_id:
                offer_product_updates.append(
                    {
                        "uri": offer_uri,
                        "product_id": product_id,
                    }
                )
            else:
                print(f"No product_id found for offer {offer_uri}")

        if offer_product_updates:
            # Prepare data for bulk update
            offer_update_mapping = {
                item["uri"]: item["product_id"] for item in offer_product_updates
            }
            offer_uris = list(offer_update_mapping.keys())

            # Build a CASE statement for bulk update
            case_stmt = case(
                *[
                    (OffersTable.uri == uri, offer_update_mapping[uri])
                    for uri in offer_uris
                ],
                else_=OffersTable.product_id,
            )

            update_stmt = (
                OffersTable.__table__.update()
                .where(OffersTable.uri.in_(offer_uris))
                .values(product_id=case_stmt)
            )
            session.execute(update_stmt)
            print(f"Updated {len(offer_product_updates)} offers with product_id.")


def upsert_product_market_info(
    session: Session, product_market_info_entries: List[DbMarketInfo]
) -> None:
    from sqlalchemy.dialects.postgresql import insert as pg_insert

    if product_market_info_entries:
        # Remove duplicates based on (product_id, market)
        unique_entries_dict: Dict[Tuple[str, str], DbMarketInfo] = {
            (e.product_id, e.market): e for e in product_market_info_entries
        }
        unique_entries: List[DbMarketInfo] = list(unique_entries_dict.values())
        entries_to_insert = [entry.model_dump() for entry in unique_entries]
        product_market_info_stmt = pg_insert(ProductMarketInfoTable.__table__).values(
            entries_to_insert
        )
        update_columns = {
            "title": product_market_info_stmt.excluded.title,
            "description": product_market_info_stmt.excluded.description,
            "subtitle": product_market_info_stmt.excluded.subtitle,
            "short_description": product_market_info_stmt.excluded.short_description,
            "brand_key": product_market_info_stmt.excluded.brand_key,
            "vendor_key": product_market_info_stmt.excluded.vendor_key,
            "context": product_market_info_stmt.excluded.context,
            "category_key": product_market_info_stmt.excluded.category_key,
        }
        upsert_stmt = product_market_info_stmt.on_conflict_do_update(
            index_elements=["product_id", "market"], set_=update_columns
        )
        session.execute(upsert_stmt)

        print(f"Upserted {len(unique_entries)} product market info entries.")


def handle_gtins_for_offers(
    offers: Sequence[ProcessedMpnOffer], context: str
) -> List[str] | None:
    prepared_data, uf = prepare_offer_data(offers)

    with Session(get_pg_engine()) as session:
        try:
            gtin_to_product_map, existing_gtins, new_gtins = find_existing_gtins(
                session, prepared_data.offer_gtins
            )
            root_to_gtins = build_root_to_gtins(uf, prepared_data.offer_gtins)
            component_product_id, new_products, products_to_update, gtins_to_update = (
                determine_product_ids(
                    root_to_gtins,
                    gtin_to_product_map,
                    prepared_data.gtin_product_map,
                )
            )
            upsert_products(session, new_products, products_to_update)
            insert_new_gtins(session, new_gtins, gtin_to_product_map)
            update_gtins(session, gtins_to_update)
            upsert_offer_has_gtin(session, prepared_data.offer_has_gtin_list)
            product_market_info_entries = collect_product_market_info_entries(
                root_to_gtins,
                component_product_id,
                prepared_data.gtin_market_info_map,
            )
            populate_market_info_with_categories(
                session=session,
                context=context,
                product_market_info_entries=product_market_info_entries,
                gtin_offer_object_map=prepared_data.gtin_offer_object_map,
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
            return list(component_product_id.values())
        except Exception as e:
            print(f"An error occurred: {e}")
            log_traceback(e)
            session.rollback()


def populate_market_info_with_categories(
    session: Session,
    context: str,
    product_market_info_entries: Dict[str, DbMarketInfo],
    gtin_offer_object_map: Dict[str, ProcessedMpnOffer],
) -> None:
    from storage.postgres.postgres_tables import CategoryMappingsTable

    category_mappings = (
        session.query(CategoryMappingsTable)
        .filter(CategoryMappingsTable.context == context)
        .all()
    )

    if not category_mappings:
        return

    for gtin, market_info in product_market_info_entries.items():
        offer = get_offer_from_gtin(gtin_offer_object_map, gtin)
        offer_cats = offer.get("categories")
        if not offer_cats:
            continue

        matched_categories: List[CategoryMappingsTable] = []
        for cat in offer_cats:
            for mapping in category_mappings:
                if cat in mapping.source:
                    matched_categories.append(mapping)
                    break
        if not matched_categories:
            continue
        highest_level_matched_category = matched_categories[0]

        market_info.category_key = str(highest_level_matched_category.target)
        logging.debug(f"Found category {market_info.category_key} for GTIN {gtin}")

    return


def upsert_product_has_ingredient(
    session: Session,
    gtin_product_map: Dict[str, ProductInfo],
    gtin_offer_object_map: Dict[str, ProcessedMpnOffer],
    gtin_to_product_map: Dict[str, str],
) -> None:
    from storage.postgres.postgres_tables import IngredientsTable
    from sqlalchemy.dialects.postgresql import insert as pg_insert

    to_upsert: List[Dict] = []

    ingredients: List[IngredientsTable] = None

    for gtin, product_info in gtin_product_map.items():
        offer = get_offer_from_gtin(gtin_offer_object_map, gtin)
        offer_ingredients: List[str] = offer.get("rawIngredients")
        if not offer_ingredients:
            continue

        # Wait with db query until offer actually has data
        if ingredients is None:
            ingredients = session.query(IngredientsTable).all()
            if not ingredients:
                return

        matched_ingredients = get_extracted_ingredients_postgres(
            offer_ingredients, ingredients
        )

        if not matched_ingredients:
            continue

        product_id = gtin_to_product_map[gtin]
        processed_score = 0
        for ingredient in matched_ingredients:
            processed_score += int(ingredient.processed_value) or 0

            to_upsert.append(
                dict(
                    product_id=product_id,
                    ingredient_id=ingredient.id,
                )
            )

    if not to_upsert:
        return

    stmt = (
        pg_insert(ProductHasIngredientTable.__table__)
        .values(to_upsert)
        .on_conflict_do_nothing(index_elements=["product_id", "ingredient_id"])
    )
    session.execute(stmt)
    print(f"Upserted {len(to_upsert)} product_has_ingredient entries.")
