from datetime import datetime
import logging
from typing import Dict, Sequence
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import update
from storage.postgres.denormalized_products import update_denormalized_products
from storage.postgres.gtins import (
    find_existing_gtins,
    insert_new_gtins,
    upsert_offer_has_gtin,
)
from storage.postgres.market_infos import (
    collect_product_market_info_entries,
    upsert_product_market_info,
)
from storage.postgres.offer_pricing import update_offer_pricing
from storage.postgres.offers import (
    get_offer_price_object_from_processed_offer,
    upsert_brands_postgres,
    upsert_dealers_postgres,
    upsert_offer_prices_batch,
    upsert_offers_postgres,
    upsert_vendors_postgres,
)
from storage.postgres.products import build_root_to_gtins, prepare_offer_data
from storage.postgres.products_handling import (
    determine_product_ids,
    insert_products,
    update_products,
    upsert_product_has_ingredient,
)
from util.timer import Timer

from storage.postgres.common import execute_statement, get_pg_engine
from amp_types.amp_product import HandleConfig, ProcessedMpnOffer
from storage.postgres.postgres_tables import HandleConfigsTable, HandleRunBatchesTable
from scraper_feed.filters import (
    mpn_categories_version,
    mpn_ingredients_version,
    mpn_nutrition_version,
    mpn_properties_version,
    mpn_stock_version,
    mpn_quantity_version,
)


pg_engine = get_pg_engine()


def get_handle_configs(provenance: str):
    # Perform the ORM query
    with Session(pg_engine) as session:
        try:
            stmt = session.query(HandleConfigsTable).filter(
                HandleConfigsTable.provenance == provenance
            )
            # Return the result as a list of HandleConfigsTable objects
            return stmt.all()
        except Exception as e:
            print(f"An error occurred: {e}")
            raise e


def insert_handle_run_batch(config: HandleConfig):
    from sqlalchemy.dialects.postgresql import insert as pg_insert

    with Session(pg_engine) as session:
        try:
            stmt = (
                pg_insert(HandleRunBatchesTable.__table__)
                .values(
                    dict(
                        scrape_time=config["scrape_time"],
                        status="PROCESSING",
                        scrape_batch_id=config["scrapeBatchId"],
                        handle_config_id=config["id"],
                        categories_v=mpn_categories_version,
                        ingredients_v=mpn_ingredients_version,
                        nutrition_v=mpn_nutrition_version,
                        properties_v=mpn_properties_version,
                        stock_v=mpn_stock_version,
                        quantity_v=mpn_quantity_version,
                    )
                )
                .returning(HandleRunBatchesTable.id)
            )

            result = session.execute(stmt)
            session.commit()
            batch_id = result.scalar()
            if not batch_id:
                raise Exception("Failed to insert handle run batch")
            return str(batch_id)
        except Exception as e:
            print(f"An error occurred: {e}")
            raise


def update_handle_run_batch_status(id: str, status: str):
    stmt = (
        update(HandleRunBatchesTable)
        .where(HandleRunBatchesTable.id == id)
        .values(status=status)
    )

    return execute_statement(stmt)


def handle_store_offer_batch(
    offers: Sequence[ProcessedMpnOffer], scrape_time: datetime, context: str
):
    timer = Timer()
    timer.start("Save batch")

    # Extract and upsert brands, vendors, and dealers
    logging.info("Upserting brands, vendors, and dealers")
    timer.start("Upsert misc")
    upsert_brands_postgres(offers)
    upsert_vendors_postgres(offers)
    upsert_dealers_postgres(offers)
    timer.stop("Upsert misc")

    prepared_data, uf = prepare_offer_data(offers)
    with Session(get_pg_engine()) as session:
        try:
            timer.start("Insert gtins")
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

            # After determining gtin_to_product_map and offer_to_gtins
            offer_to_product_id: Dict[str, UUID] = {}
            for offer_uri, gtins in prepared_data.offer_to_gtins.items():
                for gtin in gtins:
                    product_id = gtin_to_product_map.get(gtin)
                    if product_id:
                        offer_to_product_id[offer_uri] = product_id
                        break  # Stop after finding the first valid product_id

            timer.start("Upsert offers")
            # Upsert offers to the database
            logging.info(f"Upserting {len(offers)} offers")
            upsert_offers_postgres(session, offers, offer_to_product_id)
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
            if len(offer_prices) > 0:
                upsert_offer_prices_batch(session, offer_prices)
            timer.stop("Insert prices")

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

            product_ids = list(gtin_to_product_map.values())

            session.commit()
            timer.stop("Insert gtins")

        except Exception as e:
            print(f"An error occurred: {e}")
            session.rollback()
            raise

    if not product_ids:
        print("No product ids found")
        return

    timer.start("Update denormalized products")
    update_denormalized_products(product_ids)
    timer.stop("Update denormalized products")

    timer.start("Update offer pricing")
    update_offer_pricing(
        affected_offer_uris=[
            f"{offer['namespace']}:{offer['provenanceId']}" for offer in offers
        ]
    )
    timer.stop("Update offer pricing")

    timer.stop("Save batch")
