import logging
from typing import List
from uuid import UUID
from sqlalchemy.orm import Session, aliased
from sqlalchemy import bindparam, delete, func, and_, select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from datetime import datetime, timezone
from dateutil.parser import isoparse


from storage.postgres.common import get_pg_engine
from storage.postgres.postgres_tables import (
    ProductsTable,
    ProductMarketInfoTable,
    IngredientsTable,
    GtinsTable,
    ProductHasIngredientTable,
    OffersTable,
    DealersTable,
    OfferHasGtinTable,
    DenormalizedProductsTable,
)
from util.logging import configure_lambda_logging


def update_denormalized_products(affected_product_ids: List[UUID]):
    with Session(get_pg_engine()) as session:
        try:
            # Alias for ProductMarketInfoTable
            pm_info = aliased(ProductMarketInfoTable)

            # Main query to aggregate data for affected products
            aggregated_data = (
                session.query(
                    # Existing selected columns
                    ProductsTable.id.label("product_id"),
                    pm_info.market,
                    pm_info.title,
                    pm_info.subtitle,
                    pm_info.description,
                    pm_info.short_description,
                    pm_info.brand_key,
                    pm_info.vendor_key,
                    func.array_agg(func.distinct(GtinsTable.gtin)).label("gtins"),
                    # Aggregate ingredients
                    func.jsonb_agg(
                        func.jsonb_build_object(
                            "ingredient_id",
                            IngredientsTable.id,
                            "name",
                            IngredientsTable.title,
                            "shortDescription",
                            IngredientsTable.short_description,
                            "key",
                            IngredientsTable.id,
                        )
                    )
                    .filter(IngredientsTable.id.isnot(None))
                    .label("ingredients"),
                    ProductsTable.nutrition,
                    ProductsTable.quantity_unit,
                    ProductsTable.quantity_amount,
                    # Aggregate offers into JSONB array
                    func.array_agg(
                        func.distinct(
                            func.jsonb_build_object(
                                "uri",
                                OffersTable.uri,
                                "href",
                                OffersTable.href,
                                "ahref",
                                OffersTable.ahref,
                                "dealer_key",
                                OffersTable.dealer_key,
                                "valid_through",
                                OffersTable.valid_through,
                                "price",
                                OffersTable.price,
                                "pre_price",
                                OffersTable.pre_price,
                                "price_unit",
                                OffersTable.price_unit,
                                "currency",
                                OffersTable.currency,
                                "dealerObject",
                                func.jsonb_build_object(
                                    "key",
                                    DealersTable.key,
                                    "market",
                                    DealersTable.market,
                                    "title",
                                    DealersTable.title,
                                ),
                            )
                        )
                    ).label("offers"),
                    func.min(OffersTable.price).label("price_min"),
                    func.max(OffersTable.price).label("price_max"),
                    func.min(OffersTable.value_standard_amount).label("value_min"),
                    func.max(OffersTable.value_standard_amount).label("value_max"),
                    func.max(OffersTable.valid_through).label("valid_through"),
                    func.max(OffersTable.image).label("image_url"),
                    pm_info.context,
                    pm_info.category_key,
                    # Include category hierarchy using the database function
                    func.get_category_hierarchy(
                        pm_info.category_key, pm_info.context
                    ).label("category_keys"),
                    func.array_agg(func.distinct(OffersTable.dealer_key)).label(
                        "dealer_keys"
                    ),
                )
                .select_from(ProductsTable)
                # Join ProductMarketInfoTable
                .join(
                    pm_info,
                    ProductsTable.id == pm_info.product_id,
                )
                # Rest of your joins...
                # Outer join GtinsTable
                .outerjoin(GtinsTable, GtinsTable.product_id == ProductsTable.id)
                # Outer join OfferHasGtinTable
                .outerjoin(OfferHasGtinTable, OfferHasGtinTable.gtin == GtinsTable.gtin)
                # Outer join OffersTable
                .outerjoin(
                    OffersTable,
                    and_(
                        OffersTable.product_id == ProductsTable.id,
                        OffersTable.market == pm_info.market,
                        OffersTable.valid_through > func.now(),
                    ),
                )
                # Outer join DealersTable
                .outerjoin(DealersTable, DealersTable.key == OffersTable.dealer_key)
                # Outer join ProductHasIngredientTable
                .outerjoin(
                    ProductHasIngredientTable,
                    ProductHasIngredientTable.product_id == ProductsTable.id,
                )
                # Outer join IngredientsTable
                .outerjoin(
                    IngredientsTable,
                    IngredientsTable.id == ProductHasIngredientTable.ingredient_id,
                )
                # Filter by affected product IDs
                .filter(ProductsTable.id.in_(affected_product_ids))
                # Group by necessary columns
                .group_by(
                    ProductsTable.id,
                    pm_info.market,
                    pm_info.title,
                    pm_info.subtitle,
                    pm_info.description,
                    pm_info.short_description,
                    pm_info.brand_key,
                    pm_info.vendor_key,
                    ProductsTable.nutrition,
                    ProductsTable.quantity_unit,
                    ProductsTable.quantity_amount,
                    pm_info.context,
                    pm_info.category_key,
                )
                .having(func.count(OffersTable.uri) > 0)
                .all()
            )

            # Collect all insert data into a list
            insert_data_list = []
            for data in aggregated_data:
                insert_data = {
                    "product_id": data.product_id,
                    "market": data.market,
                    "image_url": data.image_url,
                    "title": data.title,
                    "subtitle": data.subtitle,
                    "description": data.description,
                    "short_description": data.short_description,
                    "brand_key": data.brand_key,
                    "vendor_key": data.vendor_key,
                    "gtins": data.gtins,
                    "ingredients": data.ingredients,
                    "nutrition": data.nutrition,
                    "quantity_unit": data.quantity_unit,
                    "quantity_amount": data.quantity_amount,
                    "offers": data.offers,
                    "price_min": data.price_min,
                    "price_max": data.price_max,
                    "value_min": data.value_min,
                    "value_max": data.value_max,
                    "valid_through": data.valid_through,
                    "context": data.context,
                    "category_key": data.category_key,
                    "category_keys": data.category_keys,
                    "dealer_keys": data.dealer_keys,
                }
                insert_data_list.append(insert_data)

            # Perform bulk insert with on_conflict_do_update
            if insert_data_list:
                insert_stmt = pg_insert(DenormalizedProductsTable).values(
                    insert_data_list
                )
                update_columns = {
                    # Exclude primary keys from update
                    key: getattr(insert_stmt.excluded, key)
                    for key in insert_data_list[0].keys()
                    if key not in ["product_id", "market"]
                }

                on_conflict_stmt = insert_stmt.on_conflict_do_update(
                    index_elements=["product_id", "market"], set_=update_columns
                )

                session.execute(on_conflict_stmt)
                session.commit()

                logging.info(f"Upserted {len(insert_data_list)} denormalized products")
            else:
                logging.info("No denormalized products to upsert")
        except Exception as e:
            session.rollback()
            raise e


def update_denormalized_products_for_valid_offers(event, context):
    configure_lambda_logging()
    batch_size = 1000
    max_products = 100_000

    with Session(get_pg_engine()) as session:
        try:
            logging.info("Starting batch processing to remove expired offers...")
            last_product_id = None
            total_processed = 0
            total_deleted = 0
            total_updated = 0

            now = datetime.now(timezone.utc)

            while True:
                logging.info(
                    f"Processing batch of {batch_size} starting from product_id: {last_product_id}"
                )
                # Build the query with pagination
                stmt = select(
                    DenormalizedProductsTable.product_id,
                    DenormalizedProductsTable.market,
                    DenormalizedProductsTable.offers,
                    DenormalizedProductsTable.valid_through,
                ).order_by(DenormalizedProductsTable.product_id)
                if last_product_id is not None:
                    stmt = stmt.where(
                        DenormalizedProductsTable.product_id > last_product_id
                    )
                products_batch = session.execute(stmt.limit(batch_size)).all()

                if not products_batch or total_processed >= max_products:
                    # No more rows to process or reached max_products
                    break

                ids_to_delete: List[dict] = []
                updates: List[dict] = []

                for dp in products_batch:
                    total_processed += 1
                    if total_processed > max_products:
                        # Reached the max_products limit
                        break

                    offers = dp.offers or []
                    valid_offers = []
                    new_valid_through = None
                    # Process offers to filter out expired ones
                    for offer in offers:
                        valid_through_str = offer.get("valid_through")
                        try:
                            valid_through = isoparse(valid_through_str)
                        except (ValueError, TypeError):
                            raise
                        if valid_through > now:
                            valid_offers.append(offer)
                            if (
                                not new_valid_through
                                or valid_through > new_valid_through
                            ):
                                new_valid_through = valid_through

                    if not valid_offers:
                        # No valid offers left, mark for deletion
                        ids_to_delete.append(
                            dict(product_id=dp.product_id, market=dp.market)
                        )
                        total_deleted += 1
                    elif len(valid_offers) != len(offers):
                        # Update the product with new offers and valid_through
                        updates.append(
                            {
                                "product_id": dp.product_id,
                                "market": dp.market,
                                "offers": valid_offers,
                                "valid_through": new_valid_through,
                            }
                        )
                        total_updated += 1
                    last_product_id = dp.product_id

                # Perform the updates and deletions
                if ids_to_delete:
                    stmt = delete(DenormalizedProductsTable).where(
                        (
                            DenormalizedProductsTable.product_id
                            == bindparam("product_id")
                        )
                        & (DenormalizedProductsTable.market == bindparam("market"))
                    )
                    # Use connection.execute() at the Core level
                    session.connection().execute(stmt, ids_to_delete)
                    logging.info(f"Deleted {len(ids_to_delete)} products")
                    ids_to_delete = []

                if updates:
                    session.execute(update(DenormalizedProductsTable), updates)

                    logging.info(f"Updated {len(updates)} products")
                    updates = []

                session.commit()
                logging.info(
                    f"Processed batch. Total processed: {total_processed}, total deleted: {total_deleted}, total updated: {total_updated}"
                )

                if total_processed >= max_products:
                    logging.info(f"Reached the max_products limit of {max_products}.")
                    break

            logging.info(
                f"Finished processing. Total processed: {total_processed}, total deleted: {total_deleted}"
            )

        except Exception as e:
            session.rollback()
            logging.error(f"An error occurred: {e}")
            raise


if __name__ == "__main__":
    update_denormalized_products_for_valid_offers(None, None)
