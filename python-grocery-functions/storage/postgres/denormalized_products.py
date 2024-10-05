from typing import List
from sqlalchemy.orm import Session
from sqlalchemy import select, func, and_, or_
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


def update_denormalized_products(affected_product_ids: List[str]):
    # Set up your engine and session

    with Session(get_pg_engine()) as session:
        try:
            # Query to aggregate data for affected products
            aggregated_data = (
                session.query(
                    # Select columns
                    ProductsTable.id.label("product_id"),
                    ProductMarketInfoTable.market,
                    ProductMarketInfoTable.title,
                    ProductMarketInfoTable.subtitle,
                    ProductMarketInfoTable.description,
                    ProductMarketInfoTable.short_description,
                    ProductMarketInfoTable.brand_key,
                    ProductMarketInfoTable.vendor_key,
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
                    ProductMarketInfoTable.context,
                    ProductMarketInfoTable.category_key,
                    func.array_agg(func.distinct(OffersTable.dealer_key)).label(
                        "dealer_keys"
                    ),
                )
                .select_from(ProductsTable)
                # Join ProductMarketInfoTable
                .join(
                    ProductMarketInfoTable,
                    ProductsTable.id == ProductMarketInfoTable.product_id,
                )
                # Outer join GtinsTable
                .outerjoin(GtinsTable, GtinsTable.product_id == ProductsTable.id)
                # Outer join OfferHasGtinTable
                .outerjoin(OfferHasGtinTable, OfferHasGtinTable.gtin == GtinsTable.gtin)
                # Outer join OffersTable via OfferHasGtinTable
                .outerjoin(
                    OffersTable,
                    and_(
                        OffersTable.product_id == ProductsTable.id,
                        OffersTable.market == ProductMarketInfoTable.market,
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
                    ProductMarketInfoTable.market,
                    ProductMarketInfoTable.title,
                    ProductMarketInfoTable.subtitle,
                    ProductMarketInfoTable.description,
                    ProductMarketInfoTable.short_description,
                    ProductMarketInfoTable.brand_key,
                    ProductMarketInfoTable.vendor_key,
                    ProductsTable.nutrition,
                    ProductsTable.quantity_unit,
                    ProductsTable.quantity_amount,
                    ProductMarketInfoTable.context,
                    ProductMarketInfoTable.category_key,
                )
                .having(func.count(OffersTable.uri) > 0)
                .all()
            )

            for data in aggregated_data:
                print("data.ingredients", data.ingredients)
                insert_stmt = pg_insert(DenormalizedProductsTable).values(
                    product_id=data.product_id,
                    market=data.market,
                    image_url=data.image_url,
                    title=data.title,
                    subtitle=data.subtitle,
                    description=data.description,
                    short_description=data.short_description,
                    brand_key=data.brand_key,
                    vendor_key=data.vendor_key,
                    gtins=data.gtins,
                    ingredients=data.ingredients,
                    nutrition=data.nutrition,
                    quantity_unit=data.quantity_unit,
                    quantity_amount=data.quantity_amount,
                    offers=data.offers,
                    price_min=data.price_min,
                    price_max=data.price_max,
                    value_min=data.value_min,
                    value_max=data.value_max,
                    valid_through=data.valid_through,
                    context=data.context,
                    category_key=data.category_key,
                    dealer_keys=data.dealer_keys,
                    # created_at and updated_at will be set automatically
                )

                update_stmt = insert_stmt.on_conflict_do_update(
                    index_elements=["product_id", "market"],
                    set_={
                        "image_url": insert_stmt.excluded.image_url,
                        "title": insert_stmt.excluded.title,
                        "subtitle": insert_stmt.excluded.subtitle,
                        "description": insert_stmt.excluded.description,
                        "short_description": insert_stmt.excluded.short_description,
                        "brand_key": insert_stmt.excluded.brand_key,
                        "vendor_key": insert_stmt.excluded.vendor_key,
                        "gtins": insert_stmt.excluded.gtins,
                        "ingredients": insert_stmt.excluded.ingredients,
                        "nutrition": insert_stmt.excluded.nutrition,
                        "quantity_unit": insert_stmt.excluded.quantity_unit,
                        "quantity_amount": insert_stmt.excluded.quantity_amount,
                        "offers": insert_stmt.excluded.offers,
                        "price_min": insert_stmt.excluded.price_min,
                        "price_max": insert_stmt.excluded.price_max,
                        "value_min": insert_stmt.excluded.value_min,
                        "value_max": insert_stmt.excluded.value_max,
                        "valid_through": insert_stmt.excluded.valid_through,
                        "context": insert_stmt.excluded.context,
                        "category_key": insert_stmt.excluded.category_key,
                        "dealer_keys": insert_stmt.excluded.dealer_keys,
                        # 'updated_at' will be updated by the trigger
                    },
                )

                session.execute(update_stmt)

            session.commit()
        except Exception as e:
            session.rollback()
            raise e


def delete_denormalized_products_without_valid_offers():
    # Delete denormalized_products where valid_through <= NOW()
    with Session(get_pg_engine()) as session:
        try:
            session.query(DenormalizedProductsTable).filter(
                DenormalizedProductsTable.valid_through <= func.now()
            ).delete(synchronize_session=False)
            session.commit()
        except Exception as e:
            session.rollback()
            raise e
