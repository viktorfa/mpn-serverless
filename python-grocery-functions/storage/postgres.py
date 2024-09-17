from datetime import datetime
import logging
from typing import List, Mapping, Sequence, Set
import re
from string import capwords
from uuid import uuid4

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy import create_engine, select, update

from amp_types.amp_product import ProcessedMpnOffer
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
)

# Define database URL
DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/local"

# Create an engine and metadata
engine = create_engine(DATABASE_URL)


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
        "quantity_unit": offer["quantity"].get("unit"),
        "quantity_amount": offer["quantity"].get("amount"),
        "quantity_standard_amount": offer["quantity"].get("standardAmount"),
        "site_collection": offer["siteCollection"],
        "subtitle": offer.get("subtitle"),
        "title": offer["title"],
        "valid_from": offer["validFrom"],
        "valid_through": offer["validThrough"],
        "value_unit": offer["value"].get("unit"),
        "value_amount": offer["value"].get("amount"),
        "value_standard_amount": offer["value"].get("standardAmount"),
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
    def __init__(self):
        self.parent = {}

    def find(self, x):
        # Path compression
        if x not in self.parent:
            self.parent[x] = x
        while x != self.parent[x]:
            self.parent[x] = self.parent[self.parent[x]]
            x = self.parent[x]
        return x

    def union(self, x, y):
        xroot = self.find(x)
        yroot = self.find(y)
        if xroot != yroot:
            self.parent[yroot] = xroot


def handle_store_offer_batch(
    offers: Sequence[ProcessedMpnOffer], scrape_time: datetime
):
    # Upsert offers to the database
    logging.info(f"Upserting {len(offers)} offers")
    upsert_offers_postgres(offers)

    # Extract offer prices from the offers
    offer_prices = [
        get_offer_price_object_from_processed_offer(offer, scrape_time)
        for offer in offers
        if offer["pricing"].get("price") is not None
    ]

    # Upsert offer prices to the database
    logging.info(f"Upserting {len(offer_prices)} offer prices")
    upsert_offer_prices_batch(offer_prices)

    # Extract and upsert brands, vendors, and dealers
    logging.info("Upserting brands, vendors, and dealers")
    upsert_brands_postgres(offers)
    upsert_vendors_postgres(offers)
    upsert_dealers_postgres(offers)

    handle_gtins_for_offers(offers)


def handle_gtins_for_offers(offers: Sequence[ProcessedMpnOffer]):
    with engine.connect() as connection:
        offer_gtins: Set[str] = set()
        offer_has_gtin_list: List[dict] = []
        gtin_offer_map: Mapping[str, str] = {}

        uf = UnionFind()  # Initialize UnionFind

        # Prepare GTIN and offer maps
        for offer in offers:
            uri_string = f"{offer['namespace']}:{offer['provenanceId']}"
            gtin_list: List[str] = []

            for key, value in offer.get("gtins", {}).items():
                gtin_string = f"{key}:{value}"
                offer_gtins.add(gtin_string)
                gtin_offer_map[gtin_string] = uri_string
                gtin_list.append(gtin_string)

                offer_has_gtin_list.append(
                    {
                        "offer_uri": uri_string,
                        "gtin": gtin_string,
                        "match_type": "auto",
                    }
                )

            if len(gtin_list) > 1:
                # Union all GTINs in the offer
                first_gtin = gtin_list[0]
                for gtin in gtin_list[1:]:
                    uf.union(first_gtin, gtin)

        if len(offer_gtins) > 0:
            with engine.connect() as connection:
                transaction = connection.begin()
                try:
                    # 1. Find Existing GTINs
                    stmt = select(gtins_table.c.gtin, gtins_table.c.product_id).where(
                        gtins_table.c.gtin.in_(offer_gtins)
                    )
                    result = connection.execute(stmt)
                    existing_gtin_rows = result.mappings().all()

                    # Log found existing GTINs
                    print(f"Found {len(existing_gtin_rows)} existing GTINs.")

                    # Create a map of GTIN to product_id for existing GTINs
                    gtin_to_product_map: Mapping[str, str] = {
                        row["gtin"]: row["product_id"]
                        for row in existing_gtin_rows
                        if row["product_id"]
                    }

                    existing_gtins = set(gtin_to_product_map.keys())
                    new_gtins = offer_gtins - existing_gtins

                    # Build root_to_gtins mapping
                    root_to_gtins: Mapping[str, Set[str]] = {}
                    for gtin in offer_gtins:
                        root = uf.find(gtin)
                        if root not in root_to_gtins:
                            root_to_gtins[root] = set()
                        root_to_gtins[root].add(gtin)

                    # Now, for each component (root), determine the product_id to use
                    component_product_id: Mapping[
                        str, str
                    ] = {}  # Map from root to product_id
                    new_products = []
                    gtins_to_update = []  # List of GTINs needing product_id updates

                    for root, component_gtins in root_to_gtins.items():
                        # Collect product_ids associated with GTINs in the component
                        product_ids_in_component: Set[str] = set()
                        for gtin in component_gtins:
                            if gtin in gtin_to_product_map:
                                product_ids_in_component.add(gtin_to_product_map[gtin])

                        if len(product_ids_in_component) == 0:
                            # No existing product_id, create new product
                            new_product_id = str(uuid4())
                            new_products.append({"id": new_product_id})
                            component_product_id[root] = new_product_id
                        else:
                            # Existing product_ids found
                            selected_product_id = min(
                                product_ids_in_component
                            )  # Choose one product_id
                            component_product_id[root] = selected_product_id

                            if len(product_ids_in_component) > 1:
                                # Need to merge products
                                other_product_ids = product_ids_in_component - {
                                    selected_product_id
                                }
                                print(
                                    f"Merging products {other_product_ids} into {selected_product_id}"
                                )
                                # Update GTINs to use the selected product_id
                                for gtin in component_gtins:
                                    existing_product_id = gtin_to_product_map.get(gtin)
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

                    # 3. Insert New Products
                    if new_products:
                        products_stmt = insert(products_table).values(new_products)
                        connection.execute(products_stmt)
                        print(f"Inserted {len(new_products)} new products.")

                    # 4. Insert New GTINs
                    gtins_to_insert = []
                    for gtin in new_gtins:
                        gtins_to_insert.append(
                            {
                                "gtin": gtin,
                                "product_id": gtin_to_product_map[gtin],
                            }
                        )
                    if gtins_to_insert:
                        gtin_insert_stmt = (
                            insert(gtins_table)
                            .values(gtins_to_insert)
                            .on_conflict_do_nothing(index_elements=["gtin"])
                        )
                        connection.execute(gtin_insert_stmt)
                        print(f"Inserted {len(gtins_to_insert)} new GTINs.")

                    # 5. Update Existing GTINs' product_id if necessary
                    if gtins_to_update:
                        for gtin_entry in gtins_to_update:
                            update_stmt = (
                                update(gtins_table)
                                .where(gtins_table.c.gtin == gtin_entry["gtin"])
                                .values(product_id=gtin_entry["product_id"])
                            )
                            connection.execute(update_stmt)
                        print(
                            f"Updated {len(gtins_to_update)} GTINs to new product IDs."
                        )

                    # 6. Insert into offer_has_gtin_table
                    if offer_has_gtin_list:
                        offer_has_gtin_stmt = (
                            insert(offer_has_gtin_table)
                            .values(offer_has_gtin_list)
                            .on_conflict_do_nothing(
                                index_elements=["offer_uri", "gtin"]
                            )
                        )
                        connection.execute(offer_has_gtin_stmt)
                        print(
                            f"Upserted {len(offer_has_gtin_list)} offer_has_gtin entries."
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
