import argparse
import logging
from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from storage.postgres.common import get_pg_engine
from storage.postgres.denormalized_products import update_denormalized_products
from storage.postgres.postgres_tables import (
    DenormalizedProductsTable,
    OffersTable,
    ProductsTable,
)
from util.logging import configure_lambda_logging
from util.timer import Timer

# For old offers without scrapeBatchId
OFFER_LIMIT = 1024 * 2
BATCH_SIZE = 1024
configure_lambda_logging()


def migrate_data(limit: int, batch_size: int):
    logging.info(
        f"Starting populating denormalized products offers with limit {limit} and batch size {batch_size}"
    )

    timer = Timer()
    timer.start("Migrate data")

    with Session(get_pg_engine()) as session:
        try:
            subquery = select(DenormalizedProductsTable.product_id).subquery()

            cursor = (
                session.query(OffersTable)
                .join(ProductsTable, OffersTable.product_id == ProductsTable.id)
                .filter(OffersTable.valid_through > datetime.now())
                .filter(
                    ~OffersTable.product_id.in_(select(subquery))
                )  # Exclude product_ids found in denormalized_products
                .options(joinedload(OffersTable.product))
                .yield_per(batch_size)
            )

            product_count = 0
            product_ids: list[UUID] = []

            for row in cursor:
                product_count += 1
                if product_count >= limit:
                    break
                product_ids.append(UUID(str(row.product_id)))

                if product_count % batch_size == 0:
                    update_denormalized_products(product_ids)
                    product_ids = []
                    logging.info(f"Processed {product_count} products")
            if product_ids:
                update_denormalized_products(product_ids)
                logging.info(f"Processed {product_count} products")
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    timer.stop("Migrate data")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Populate denormalized_products.")
    parser.add_argument(
        "--limit", type=int, default=OFFER_LIMIT, help="Limit of offers to migrate"
    )
    parser.add_argument(
        "--batch_size", type=int, default=BATCH_SIZE, help="Batch size for migration"
    )

    args = parser.parse_args()

    migrate_data(limit=args.limit, batch_size=args.batch_size)
