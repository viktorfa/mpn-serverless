import logging
from typing import List
from uuid import UUID
from sqlalchemy.orm import Session, aliased
from sqlalchemy import func, and_
from sqlalchemy.dialects.postgresql import insert as pg_insert

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


def delete_denormalized_products_without_valid_offers():
    # Delete denormalized_products where valid_through <= NOW()
    # TODO also delete offers that are not valid anymore and delete if no offers
    with Session(get_pg_engine()) as session:
        try:
            session.query(DenormalizedProductsTable).filter(
                DenormalizedProductsTable.valid_through <= func.now()
            ).delete(synchronize_session=False)
            session.commit()
        except Exception as e:
            session.rollback()
            raise e
