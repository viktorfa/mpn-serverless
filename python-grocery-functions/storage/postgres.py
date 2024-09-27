from datetime import datetime
import logging
from typing import Any, List, Sequence, Set, Optional, Dict, Tuple, TypedDict
import re
from string import capwords
from uuid_extensions import uuid7str


import pydash
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy import create_engine, select, update, case
from sqlalchemy.engine import Result

from amp_types.amp_product import HandleConfig, ProcessedMpnOffer
from storage.postgres_tables import (
    brands_table,
    dealers_table,
    gtins_table,
    offer_has_gtin_table,
    offers_table,
    offer_prices_table,
    vendors_table,
    products_table,
    product_market_info_table,
    scrape_batches_table,
)
from scraper_feed.filters import (
    mpn_categories_version,
    mpn_ingredients_version,
    mpn_nutrition_version,
    mpn_properties_version,
    mpn_stock_version,
    mpn_quantity_version,
)
from util.timer import Timer
from config.vars import POSTGRES_URL

# Define database URL
DATABASE_URL = POSTGRES_URL

# Create an engine and metadata
engine = create_engine(DATABASE_URL)


def execute_statement(stmt):
    with engine.connect() as connection:
        transaction = connection.begin()
        try:
            result = connection.execute(stmt)
            transaction.commit()
            return result
        except Exception as e:
            transaction.rollback()
            print(f"An error occurred: {e}")
            raise e


def insert_scrape_batch(config: HandleConfig):
    stmt = (
        insert(scrape_batches_table)
        .values(
            dict(
                scrape_time=config["scrape_time"],
                status="PROCESSING",
                scrape_batch_id=config["scrapeBatchId"],
                # config_id=config["id"],
                categories_v=mpn_categories_version,
                ingredients_v=mpn_ingredients_version,
                nutrition_v=mpn_nutrition_version,
                properties_v=mpn_properties_version,
                stock_v=mpn_stock_version,
                quantity_v=mpn_quantity_version,
            )
        )
        .returning(scrape_batches_table.c.id)
    )
    return execute_statement(stmt)


def update_scrape_batch_status(scrape_batch_id: str, status: str):
    stmt = (
        update(scrape_batches_table)
        .where(scrape_batches_table.c.scrape_batch_id == scrape_batch_id)
        .values(status=status)
    )
    return execute_statement(stmt)


def processed_offer_to_pg_offer(offer: ProcessedMpnOffer):
    uri = f"{offer['namespace']}:{offer['provenanceId']}"

    return {
        "uri": uri,
        "dealer_key": offer.get("dealer"),
        "href": offer["href"],
        "image": offer.get("imageUrl"),
        "mpn_stock": offer.get("mpn"),
        "price": offer["pricing"].get("price"),
        "currency": offer["pricing"].get("currency"),
        "pre_price": offer["pricing"].get("prePrice"),
        "price_unit": offer["pricing"].get("priceUnit"),
        "provenance": offer["provenance"],
        "provenance_id": offer["provenanceId"],
        "quantity_unit": pydash.get(offer, ["quantity", "size", "unit", "symbol"]),
        "quantity_amount": pydash.get(offer, ["quantity", "size", "amount", "max"]),
        "quantity_standard_amount": pydash.get(
            offer, ["quantity", "size", "standard", "max"]
        ),
        "site_collection": offer["siteCollection"],
        "subtitle": offer.get("subtitle"),
        "title": offer["title"],
        "valid_from": offer["validFrom"],
        "valid_through": offer["validThrough"],
        "value_unit": pydash.get(offer, ["value", "size", "unit", "symbol"]),
        "value_amount": pydash.get(offer, ["value", "size", "amount", "max"]),
        "value_standard_amount": pydash.get(
            offer, ["value", "size", "standard", "max"]
        ),
        "brand": offer.get("brand"),
        "description": offer.get("description"),
        "item_condition": offer.get("itemCondition"),
        "mpn": offer.get("mpn"),
        "upc": offer.get("gtin"),
        "ahref": offer.get("ahref"),
        "is_partner": offer.get("isPartner"),
        "market": offer["market"],
        "is_promotion_restricted": offer.get("isPromoted"),
        "scrape_batch_id": offer["scrapeBatchId"],
        "brand_key": offer.get("brandKey"),
        "vendor_key": offer.get("vendorKey"),
    }


def get_offer_price_object_from_processed_offer(
    offer: ProcessedMpnOffer, scrape_time: datetime
):
    uri = f"{offer['namespace']}:{offer['provenanceId']}"
    return {
        "uri": uri,
        "price": offer["pricing"]["price"],
        "recorded_at": scrape_time,
    }


# Union-Find data structure for grouping GTINs
class UnionFind:
    def __init__(self) -> None:
        self.parent: Dict[str, str] = {}

    def find(self, x: str) -> str:
        # Path compression
        if x not in self.parent:
            self.parent[x] = x
        while x != self.parent[x]:
            self.parent[x] = self.parent[self.parent[x]]
            x = self.parent[x]
        return x

    def union(self, x: str, y: str) -> None:
        xroot: str = self.find(x)
        yroot: str = self.find(y)
        if xroot != yroot:
            self.parent[yroot] = xroot


def handle_store_offer_batch(
    offers: Sequence[ProcessedMpnOffer], scrape_time: datetime
):
    timer = Timer()
    timer.start("Save batch")
    timer.start("Upsert offers")
    # Upsert offers to the database
    logging.info(f"Upserting {len(offers)} offers")
    upsert_offers_postgres(offers)
    timer.stop("Upsert offers")

    timer.start("Insert prices")

    # Extract offer prices from the offers
    offer_prices = [
        get_offer_price_object_from_processed_offer(offer, scrape_time)
        for offer in offers
        if offer["pricing"].get("price") is not None
    ]

    # Upsert offer prices to the database
    logging.info(f"Upserting {len(offer_prices)} offer prices")
    upsert_offer_prices_batch(offer_prices)
    timer.stop("Insert prices")

    # Extract and upsert brands, vendors, and dealers
    logging.info("Upserting brands, vendors, and dealers")
    timer.start("Upsert misc")
    upsert_brands_postgres(offers)
    upsert_vendors_postgres(offers)
    upsert_dealers_postgres(offers)
    timer.stop("Upsert misc")

    timer.start("Insert gtins")
    handle_gtins_for_offers(offers)
    timer.stop("Insert gtins")
    timer.stop("Save batch")


class ProductInfo(TypedDict):
    quantity_unit: Optional[str]
    quantity_amount: Optional[float]
    quantity_standard_amount: Optional[float]


class MarketInfo(TypedDict):
    market: str
    title: str
    description: Optional[str]
    subtitle: Optional[str]
    short_description: Optional[str]
    brand_key: Optional[str]
    vendor_key: Optional[str]


class DbMarketInfo(MarketInfo):
    product_id: str


class PreparedData(TypedDict):
    offer_gtins: Set[str]
    offer_has_gtin_list: List[Dict[str, str]]
    gtin_offer_map: Dict[str, Set[str]]
    gtin_market_info_map: Dict[str, MarketInfo]
    gtin_product_map: Dict[str, ProductInfo]
    offer_to_gtins: Dict[str, List[str]]


def prepare_offer_data(
    offers: Sequence[ProcessedMpnOffer],
) -> Tuple[PreparedData, UnionFind]:
    offer_gtins: Set[str] = set()
    offer_has_gtin_list: List[Dict[str, str]] = []
    gtin_offer_map: Dict[str, Set[str]] = {}
    gtin_market_info_map: Dict[str, MarketInfo] = {}
    gtin_product_map: Dict[str, ProductInfo] = {}
    offer_to_gtins: Dict[str, List[str]] = {}
    uf = UnionFind()

    for offer in offers:
        uri_string: str = f"{offer['namespace']}:{offer['provenanceId']}"
        gtin_list: List[str] = []
        internal_gtin_string = f"_mpn:{uri_string}"
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
        market_info: MarketInfo = {
            "market": offer["market"],
            "title": offer["title"],
            "description": offer.get("description"),
            "subtitle": offer.get("subtitle"),
            "short_description": offer.get("short_description"),
            "brand_key": offer.get("brandKey"),
            "vendor_key": offer.get("vendorKey"),
        }
        product_info: ProductInfo = {
            "quantity_unit": pydash.get(offer, ["quantity", "size", "unit", "symbol"]),
            "quantity_amount": pydash.get(offer, ["quantity", "size", "amount", "max"]),
            "quantity_standard_amount": pydash.get(
                offer, ["quantity", "size", "standard", "max"]
            ),
        }

        for gtin in gtin_list:
            if gtin not in gtin_market_info_map:
                gtin_market_info_map[gtin] = market_info
            if gtin not in gtin_product_map:
                gtin_product_map[gtin] = product_info

    prepared_data = PreparedData(
        offer_gtins=offer_gtins,
        offer_has_gtin_list=offer_has_gtin_list,
        gtin_offer_map=gtin_offer_map,
        gtin_market_info_map=gtin_market_info_map,
        gtin_product_map=gtin_product_map,
        offer_to_gtins=offer_to_gtins,
    )

    return prepared_data, uf


def find_existing_gtins(
    connection, offer_gtins: Set[str]
) -> Tuple[Dict[str, str], Set[str], Set[str]]:
    stmt = select(gtins_table.c.gtin, gtins_table.c.product_id).where(
        gtins_table.c.gtin.in_(offer_gtins)
    )
    result: Result = connection.execute(stmt)
    existing_gtin_rows = result.mappings().all()

    print(f"Found {len(existing_gtin_rows)} existing GTINs.")

    gtin_to_product_map: Dict[str, str] = {
        row["gtin"]: str(row["product_id"])
        for row in existing_gtin_rows
        if row["product_id"]
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
    List[Dict[str, Any]],
    Dict[str, Dict[str, Any]],
    List[Dict[str, str]],
]:
    component_product_id: Dict[str, str] = {}  # Map from root to product_id
    new_products: List[Dict[str, Any]] = []
    products_to_update: Dict[str, Dict[str, Any]] = {}
    gtins_to_update: List[Dict[str, str]] = []

    for root, component_gtins in root_to_gtins.items():
        # Collect product_ids associated with GTINs in the component
        product_ids_in_component: Set[str] = set()
        for gtin in component_gtins:
            if gtin in gtin_to_product_map:
                product_ids_in_component.add(gtin_to_product_map[gtin])

        # Collect product data from GTINs in the component
        product_data: Dict[str, Any] = {
            "quantity_unit": None,
            "quantity_amount": None,
            "quantity_standard_amount": None,
        }

        for gtin in component_gtins:
            gtin_product_info = gtin_product_map.get(gtin)
            if gtin_product_info:
                for key in [
                    "quantity_unit",
                    "quantity_amount",
                    "quantity_standard_amount",
                ]:
                    value = gtin_product_info.get(key)
                    if value is not None and product_data[key] is None:
                        product_data[key] = value

        if not product_ids_in_component:
            # No existing product_id, create new product
            new_product_id: str = uuid7str()
            product_data["id"] = new_product_id
            new_products.append(product_data)
            component_product_id[root] = new_product_id
        else:
            # Existing product_ids found
            selected_product_id: str = min(product_ids_in_component)
            component_product_id[root] = selected_product_id

            # Prepare product data for update
            product_data["id"] = selected_product_id
            products_to_update[selected_product_id] = product_data

            if len(product_ids_in_component) > 1:
                # Need to merge products
                other_product_ids: Set[str] = product_ids_in_component - {
                    selected_product_id
                }
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


def upsert_products(
    connection,
    new_products: List[Dict[str, Any]],
    products_to_update: Dict[str, Dict[str, Any]],
) -> None:
    from sqlalchemy.dialects.postgresql import insert as pg_insert

    products_entries: List[Dict[str, Any]] = new_products + list(
        products_to_update.values()
    )
    if products_entries:
        products_stmt = pg_insert(products_table).values(products_entries)
        # Define the update columns with conditional expressions
        update_columns = {
            "quantity_unit": case(
                *[
                    (
                        products_table.c.quantity_unit == None,
                        products_stmt.excluded.quantity_unit,
                    )
                ],
                else_=products_table.c.quantity_unit,
            ),
            "quantity_amount": case(
                *[
                    (
                        products_table.c.quantity_amount == None,
                        products_stmt.excluded.quantity_amount,
                    )
                ],
                else_=products_table.c.quantity_amount,
            ),
            "quantity_standard_amount": case(
                *[
                    (
                        products_table.c.quantity_standard_amount == None,
                        products_stmt.excluded.quantity_standard_amount,
                    )
                ],
                else_=products_table.c.quantity_standard_amount,
            ),
        }
        upsert_stmt = products_stmt.on_conflict_do_update(
            index_elements=["id"], set_=update_columns
        )
        connection.execute(upsert_stmt)
        print(f"Upserted {len(products_entries)} products.")


def insert_new_gtins(
    connection, new_gtins: Set[str], gtin_to_product_map: Dict[str, str]
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
            pg_insert(gtins_table)
            .values(gtins_to_insert)
            .on_conflict_do_nothing(index_elements=["gtin"])
        )
        connection.execute(gtin_insert_stmt)
        print(f"Inserted {len(gtins_to_insert)} new GTINs.")


def update_gtins(connection, gtins_to_update: List[Dict[str, str]]) -> None:
    if gtins_to_update:
        # Prepare data for bulk update
        gtin_update_mapping = {
            item["gtin"]: item["product_id"] for item in gtins_to_update
        }
        gtins_to_update_list = list(gtin_update_mapping.keys())

        # Build a CASE statement for bulk update
        case_stmt = case(
            *[
                (gtins_table.c.gtin == gtin, gtin_update_mapping[gtin])
                for gtin in gtins_to_update_list
            ],
            else_=gtins_table.c.product_id,
        )

        update_stmt = (
            gtins_table.update()
            .where(gtins_table.c.gtin.in_(gtins_to_update_list))
            .values(product_id=case_stmt)
        )
        connection.execute(update_stmt)
        print(f"Updated {len(gtins_to_update)} GTINs to new product IDs.")


def collect_product_market_info_entries(
    root_to_gtins: Dict[str, Set[str]],
    component_product_id: Dict[str, str],
    gtin_market_info_map: Dict[str, MarketInfo],
) -> List[DbMarketInfo]:
    product_market_info_entries: List[DbMarketInfo] = []
    for root, component_gtins in root_to_gtins.items():
        product_id: str = component_product_id[root]
        # Get market info from one of the GTINs in the component
        for gtin in component_gtins:
            market_info_entry: Optional[MarketInfo] = gtin_market_info_map.get(gtin)
            if market_info_entry:
                entry: DbMarketInfo = {
                    "product_id": product_id,
                    "market": market_info_entry["market"],
                    "title": market_info_entry["title"],
                    "description": market_info_entry.get("description"),
                    "subtitle": market_info_entry.get("subtitle"),
                    "short_description": market_info_entry.get("short_description"),
                    "brand_key": market_info_entry.get("brand_key"),
                    "vendor_key": market_info_entry.get("vendor_key"),
                }
                product_market_info_entries.append(entry)
                break  # Use the first available market info
    return product_market_info_entries


def upsert_offer_has_gtin(
    connection, offer_has_gtin_list: List[Dict[str, str]]
) -> None:
    from sqlalchemy.dialects.postgresql import insert as pg_insert

    if offer_has_gtin_list:
        offer_has_gtin_stmt = (
            pg_insert(offer_has_gtin_table)
            .values(offer_has_gtin_list)
            .on_conflict_do_nothing(index_elements=["offer_uri", "gtin"])
        )
        connection.execute(offer_has_gtin_stmt)
        print(f"Upserted {len(offer_has_gtin_list)} offer_has_gtin entries.")


def update_offers_with_product_id(
    connection,
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
                    (offers_table.c.uri == uri, offer_update_mapping[uri])
                    for uri in offer_uris
                ],
                else_=offers_table.c.product_id,
            )

            update_stmt = (
                offers_table.update()
                .where(offers_table.c.uri.in_(offer_uris))
                .values(product_id=case_stmt)
            )
            connection.execute(update_stmt)
            print(f"Updated {len(offer_product_updates)} offers with product_id.")


def upsert_product_market_info(
    connection, product_market_info_entries: List[DbMarketInfo]
) -> None:
    from sqlalchemy.dialects.postgresql import insert as pg_insert

    if product_market_info_entries:
        # Remove duplicates based on (product_id, market)
        unique_entries_dict: Dict[Tuple[str, str], DbMarketInfo] = {
            (e["product_id"], e["market"]): e for e in product_market_info_entries
        }
        unique_entries: List[DbMarketInfo] = list(unique_entries_dict.values())
        product_market_info_stmt = pg_insert(product_market_info_table).values(
            unique_entries
        )
        update_columns = {
            "title": product_market_info_stmt.excluded.title,
            "description": product_market_info_stmt.excluded.description,
            "subtitle": product_market_info_stmt.excluded.subtitle,
            "short_description": product_market_info_stmt.excluded.short_description,
            "brand_key": product_market_info_stmt.excluded.brand_key,
            "vendor_key": product_market_info_stmt.excluded.vendor_key,
        }
        upsert_stmt = product_market_info_stmt.on_conflict_do_update(
            index_elements=["product_id", "market"], set_=update_columns
        )
        connection.execute(upsert_stmt)
        print(f"Upserted {len(unique_entries)} product market info entries.")


def handle_gtins_for_offers(offers: Sequence[ProcessedMpnOffer]) -> None:
    prepared_data, uf = prepare_offer_data(offers)

    with engine.connect() as connection:
        transaction = connection.begin()
        try:
            gtin_to_product_map, existing_gtins, new_gtins = find_existing_gtins(
                connection, prepared_data["offer_gtins"]
            )
            print(
                'prepared_data["gtin_product_map"]', prepared_data["gtin_product_map"]
            )
            root_to_gtins = build_root_to_gtins(uf, prepared_data["offer_gtins"])
            component_product_id, new_products, products_to_update, gtins_to_update = (
                determine_product_ids(
                    root_to_gtins,
                    gtin_to_product_map,
                    prepared_data["gtin_product_map"],
                )
            )
            print("new_products", new_products)
            print("products_to_update", products_to_update)
            upsert_products(connection, new_products, products_to_update)
            insert_new_gtins(connection, new_gtins, gtin_to_product_map)
            update_gtins(connection, gtins_to_update)
            upsert_offer_has_gtin(connection, prepared_data["offer_has_gtin_list"])
            product_market_info_entries = collect_product_market_info_entries(
                root_to_gtins,
                component_product_id,
                prepared_data["gtin_market_info_map"],
            )
            upsert_product_market_info(connection, product_market_info_entries)
            update_offers_with_product_id(
                connection, prepared_data["offer_to_gtins"], gtin_to_product_map
            )

            transaction.commit()
        except Exception as e:
            print(f"An error occurred: {e}")
            transaction.rollback()


def upsert_brands_postgres(offers: Sequence[ProcessedMpnOffer]):
    brand_entries = []
    brand_keys = set()

    for offer in offers:
        brand_title = offer.get("brand")
        brand_key = offer.get("brandKey")
        market = offer["market"]

        if brand_key and brand_key not in brand_keys:
            brand_keys.add(brand_key)
            brand_entries.append(
                {"key": brand_key, "title": brand_title, "market": market}
            )

    if len(brand_entries) == 0:
        return 0

    with engine.connect() as connection:
        # Define the insert statement with conflict handling
        stmt = (
            insert(brands_table)
            .values(brand_entries)
            .on_conflict_do_nothing(index_elements=["key", "market"])
        )
        transaction = connection.begin()  # Start a transaction
        try:
            connection.execute(stmt)
            transaction.commit()  # Explicitly commit the transaction
            print(f"Upserted {len(brand_entries)} brands")
        except Exception as e:
            transaction.rollback()
            print(f"An error occurred: {e}")

        return len(brand_entries)


def upsert_vendors_postgres(offers: Sequence[ProcessedMpnOffer]):
    vendor_entries = []
    vendor_keys = set()

    for offer in offers:
        vendor_title = offer.get("vendor")
        vendor_key = offer.get("vendorKey")
        market = offer["market"]

        if vendor_key and vendor_key not in vendor_keys:
            vendor_keys.add(vendor_key)
            vendor_entries.append(
                {"key": vendor_key, "title": vendor_title, "market": market}
            )

    if len(vendor_entries) == 0:
        return 0

    with engine.connect() as connection:
        # Define the insert statement with conflict handling
        stmt = (
            insert(vendors_table)
            .values(vendor_entries)
            .on_conflict_do_nothing(index_elements=["key", "market"])
        )
        transaction = connection.begin()  # Start a transaction
        try:
            connection.execute(stmt)
            transaction.commit()  # Explicitly commit the transaction
            print(f"Upserted {len(vendor_entries)} vendors")
        except Exception as e:
            transaction.rollback()
            print(f"An error occurred: {e}")

        return len(vendor_entries)


def get_dealer_title(dealer: str) -> str:
    # Remove "www."
    dealer = re.sub(r"www\.", "", dealer)

    # Remove country code suffixes preceded by an underscore
    dealer = re.sub(r"_(no|se|de|dk|fi|us|uk|sg|th|nl|fr|es|it|pl|au)$", "", dealer)

    # Replace underscores with spaces
    dealer = dealer.replace("_", " ")

    # Capitalize each word
    return capwords(dealer)


def upsert_dealers_postgres(offers: Sequence[ProcessedMpnOffer]):
    dealer_entries = []
    dealer_keys = set()

    for offer in offers:
        dealer_key = offer["dealer"]
        dealer_title = get_dealer_title(dealer_key)

        market = offer["market"]
        is_partner = offer.get("isPartner")

        if dealer_key and dealer_key not in dealer_keys:
            dealer_keys.add(dealer_key)
            dealer_entries.append(
                {
                    "key": dealer_key,
                    "title": dealer_title,
                    "market": market,
                    "is_partner": is_partner,
                }
            )

    with engine.connect() as connection:
        # Define the insert statement with conflict handling

        stmt = insert(dealers_table).values(dealer_entries)

        on_conflict_stmt = stmt.on_conflict_do_update(
            index_elements=["key", "market"],
            set_={"is_partner": stmt.excluded.is_partner},
        )

        transaction = connection.begin()  # Start a transaction
        try:
            connection.execute(on_conflict_stmt)
            transaction.commit()  # Explicitly commit the transaction
            print(f"Upserted {len(dealer_entries)} dealers")
        except Exception as e:
            transaction.rollback()
            print(f"An error occurred: {e}")

        return len(dealer_entries)


def upsert_offers_postgres(offers: Sequence[ProcessedMpnOffer]):
    with engine.connect() as connection:
        # Define the upsert (insert on conflict) statement
        stmt = insert(offers_table).values(
            list(map(processed_offer_to_pg_offer, offers))
        )

        # Define the `ON CONFLICT` clause
        on_conflict_stmt = stmt.on_conflict_do_update(
            index_elements=[
                "uri",
            ],  # Columns to check for conflict
            set_={
                "dealer_key": stmt.excluded.dealer_key,
                "href": stmt.excluded.href,
                "image": stmt.excluded.image,
                "mpn_stock": stmt.excluded.mpn_stock,
                "price": stmt.excluded.price,
                "currency": stmt.excluded.currency,
                "pre_price": stmt.excluded.pre_price,
                "price_unit": stmt.excluded.price_unit,
                "quantity_unit": stmt.excluded.quantity_unit,
                "quantity_amount": stmt.excluded.quantity_amount,
                "quantity_standard_amount": stmt.excluded.quantity_standard_amount,
                "site_collection": stmt.excluded.site_collection,
                "subtitle": stmt.excluded.subtitle,
                "title": stmt.excluded.title,
                "valid_from": stmt.excluded.valid_from,
                "valid_through": stmt.excluded.valid_through,
                "value_unit": stmt.excluded.value_unit,
                "value_amount": stmt.excluded.value_amount,
                "value_standard_amount": stmt.excluded.value_standard_amount,
                "brand": stmt.excluded.brand,
                "description": stmt.excluded.description,
                "item_condition": stmt.excluded.item_condition,
                "mpn": stmt.excluded.mpn,
                "upc": stmt.excluded.upc,
                "ahref": stmt.excluded.ahref,
                "is_partner": stmt.excluded.is_partner,
                "market": stmt.excluded.market,
                "is_promotion_restricted": stmt.excluded.is_promotion_restricted,
                "scrape_batch_id": stmt.excluded.scrape_batch_id,
                "brand_key": stmt.excluded.brand_key,
                "vendor_key": stmt.excluded.vendor_key,
            },
        )

        transaction = connection.begin()  # Start a transaction
        try:
            result = connection.execute(on_conflict_stmt)
            transaction.commit()  # Explicitly commit the transaction
            print("result", result)
            print(f"Upserted {result.rowcount} offers")
        except Exception as e:
            transaction.rollback()  # Roll back in case of an error
            print(f"An error occurred: {e}")

        return len(offers)


def upsert_offer_prices_batch(offer_prices_batch):
    # Create the upsert (insert on conflict) statement
    stmt = (
        insert(offer_prices_table)
        .values(offer_prices_batch)
        .on_conflict_do_nothing(index_elements=["uri", "recorded_at"])
    )

    with engine.connect() as connection:
        transaction = connection.begin()
        try:
            connection.execute(stmt)
            transaction.commit()
        except Exception as e:
            transaction.rollback()
            print(f"Error occurred during upsert: {e}")
