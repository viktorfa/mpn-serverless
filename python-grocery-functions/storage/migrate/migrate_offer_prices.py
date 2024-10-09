from datetime import datetime
import logging
from typing import Sequence, List
from pydantic import BaseModel, ValidationError
from sqlalchemy.orm import Session
import argparse
from sqlalchemy.dialects.postgresql import insert as pg_insert

from config.mongo import get_collection
from storage.postgres.common import get_pg_engine
from storage.postgres.postgres_tables import OfferPricesTable, OffersTable
from util.logging import configure_lambda_logging
from util.timer import Timer


# For old offers without scrapeBatchId
OFFER_LIMIT = 1024 * 2
BATCH_SIZE = 1024
configure_lambda_logging()


class HistoryItem(BaseModel):
    price: float
    date: str  # yyyy-mm-dd


class MongoPricingHistory(BaseModel):
    history: List[HistoryItem]
    uri: str
    _id: str


def migrate_data(limit: int, batch_size: int):
    logging.info(
        f"Starting migration of mongo offers with limit {limit} and batch size {batch_size}"
    )

    timer = Timer()
    timer.start("Migrate data")
    timer.start("Get collection")

    with Session(get_pg_engine()) as session:
        try:
            offset = 0
            while True:
                if offset >= limit:
                    break
                cursor = (
                    session.query(OffersTable.uri)
                    .outerjoin(
                        OfferPricesTable, OffersTable.uri == OfferPricesTable.uri
                    )
                    .filter(
                        OfferPricesTable.uri == None
                    )  # No corresponding offer_prices entry exists
                    .offset(offset)
                    .limit(batch_size)
                    .all()
                )

                if not cursor:
                    break  # No more data

                offer_uris = [str(row.uri) for row in cursor]
                handle_store_offer_prices_batch(session, offer_uris)
                logging.info(f"Processed {len(offer_uris)} offers")

                session.commit()
                offset += batch_size

        except Exception:
            session.rollback()
            raise
        finally:
            session.close()


def handle_store_offer_prices_batch(session: Session, offer_uris: Sequence[str]):
    timer = Timer()
    timer.start("Save batch")
    logging.info(f"Processing {len(offer_uris)} offers")

    collection = get_collection("offerpricinghistories")

    legacy_uris: List[str] = []
    for uri in offer_uris:
        namespace, sku = uri.split(":")
        legacy_uris.append(f"{namespace}:product:{sku}")

    # Get the pricing history for the offers
    cursor = collection.find({"uri": {"$in": legacy_uris}})

    offer_prices_batch = []
    for doc in cursor:
        try:
            pricing_history = MongoPricingHistory(**doc)
        except ValidationError as e:
            logging.error(f"Error parsing pricing history: {e}")
            continue

        for history_item in pricing_history.history:
            namespace, _, sku = pricing_history.uri.split(":")
            new_uri = f"{namespace}:{sku}"
            offer_price = {
                "uri": new_uri,
                "price": history_item.price,
                "recorded_at": datetime.strptime(history_item.date, "%Y-%m-%d"),
            }
            offer_prices_batch.append(offer_price)

    if not offer_prices_batch:
        logging.info("No offer prices found")
        return

    timer.start("Insert prices")
    stmt = (
        pg_insert(OfferPricesTable.__table__)
        .values(offer_prices_batch)
        .on_conflict_do_nothing(index_elements=["uri", "recorded_at"])
    )
    session.execute(stmt)

    logging.info(f"Upserted {len(offer_prices_batch)} offer prices")
    timer.stop("Insert prices")

    timer.stop("Save batch")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Migrate offers from MongoDB to PostgreSQL."
    )
    parser.add_argument(
        "--limit", type=int, default=OFFER_LIMIT, help="Limit of offers to migrate"
    )
    parser.add_argument(
        "--batch_size", type=int, default=BATCH_SIZE, help="Batch size for migration"
    )

    args = parser.parse_args()

    migrate_data(limit=args.limit, batch_size=args.batch_size)
