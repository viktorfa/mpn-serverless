from datetime import datetime
import logging
from typing import Sequence
from sqlalchemy.orm import Session
from sqlalchemy import update
from storage.postgres.denormalized_products import update_denormalized_products
from storage.postgres.offer_pricing import update_offer_pricing
from storage.postgres.offers import (
    get_offer_price_object_from_processed_offer,
    upsert_brands_postgres,
    upsert_dealers_postgres,
    upsert_offer_prices_batch,
    upsert_offers_postgres,
    upsert_vendors_postgres,
)
from storage.postgres.products import handle_gtins_for_offers
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
    product_ids = handle_gtins_for_offers(offers, context)
    timer.stop("Insert gtins")

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
