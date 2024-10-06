from typing import List, Set, Dict, Tuple, TypedDict
from uuid import UUID
from sqlalchemy.orm import Session
from uuid_extensions import uuid7
from sqlalchemy import bindparam

from parsing.ingredients_extraction import get_extracted_ingredients_postgres
from storage.postgres.pydantic_models import DbProductInfo, NutritionType, ProductInfo
from amp_types.amp_product import ProcessedMpnOffer
from storage.postgres.postgres_tables import (
    OffersTable,
    ProductHasIngredientTable,
    ProductsTable,
)
from storage.postgres.utils import get_offer_from_gtin


class OfferProductUpdate(TypedDict):
    uri: str
    product_id: UUID


def update_offers_with_product_id(
    session: Session,
    offer_to_gtins: Dict[str, List[str]],
    gtin_to_product_map: Dict[str, UUID],
) -> None:
    if offer_to_gtins:
        offer_product_updates: List[OfferProductUpdate] = []
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
            update_values = [
                {"b_uri": item["uri"], "b_product_id": item["product_id"]}
                for item in offer_product_updates
            ]

            stmt = (
                OffersTable.__table__.update()
                .where(OffersTable.uri == bindparam("b_uri"))
                .values(product_id=bindparam("b_product_id"))
            )

            # Execute the bulk update
            session.execute(stmt, update_values)

            print(f"Updated {len(offer_product_updates)} offers with product_id.")


def update_products(
    session: Session,
    products_to_update: Dict[UUID, DbProductInfo],
    root_to_gtins: Dict[str, Set[str]],
    gtin_to_product_map: Dict[str, ProductInfo],
    existing_gtins: Set[str],
    gtin_to_product_id_map: Dict[str, UUID],
) -> None:
    from sqlalchemy.dialects.postgresql import insert as pg_insert

    existing_products = (
        session.query(ProductsTable)
        .filter(ProductsTable.id.in_(products_to_update))
        .all()
    )
    product_updates: Dict[UUID, ProductInfo] = {}
    for gtin, component_gtins in root_to_gtins.items():
        if gtin not in existing_gtins:
            continue
        merged_product_info = ProductInfo(
            quantity_unit=None,
            quantity_amount=None,
            quantity_standard_amount=None,
            nutrition=NutritionType(),
            merged_to=None,
        )
        for component_gtin in component_gtins:
            product_id = gtin_to_product_id_map[component_gtin]
            new_product_info = gtin_to_product_map[gtin]
            existing_product_info_row = next(
                (p for p in existing_products if UUID(str(p.id)) == product_id),
                None,
            )
            if existing_product_info_row is None:
                raise Exception(
                    f"Product with ID {product_id} not found in existing products."
                )
            existing_product_info = ProductInfo(
                quantity_unit=str(existing_product_info_row.quantity_unit),
                quantity_amount=float(existing_product_info_row.quantity_amount)
                if existing_product_info_row.quantity_amount
                else None,
                quantity_standard_amount=float(
                    existing_product_info_row.quantity_standard_amount
                )
                if existing_product_info_row.quantity_standard_amount
                else None,
                nutrition=NutritionType(**existing_product_info_row.nutrition),
                merged_to=UUID(str(existing_product_info_row.merged_to))
                if existing_product_info_row.merged_to
                else None,
            )
            merged_product_info = merge_product_info(
                existing_product_info, new_product_info
            )

        if len(component_gtins) > 1:
            product_to_merge_to = min(
                [gtin_to_product_id_map[gtin] for gtin in component_gtins]
            )
            merged_product_info.merged_to = product_to_merge_to
            for component_gtin in component_gtins:
                product_id = gtin_to_product_id_map[component_gtin]
                product_updates[product_id] = ProductInfo(
                    **merged_product_info.model_dump()
                )
        else:
            if merged_product_info == existing_product_info:
                continue
            else:
                product_updates[product_id] = merged_product_info

    if product_updates:
        update_stmt = pg_insert(ProductsTable.__table__).values(
            [dict(id=k, **v.model_dump()) for k, v in product_updates.items()]
        )
        update_stmt_on_conflict = update_stmt.on_conflict_do_update(
            index_elements=["id"],
            set_={
                "quantity_unit": update_stmt.excluded.quantity_unit,
                "quantity_amount": update_stmt.excluded.quantity_amount,
                "quantity_standard_amount": update_stmt.excluded.quantity_standard_amount,
                "nutrition": update_stmt.excluded.nutrition,
                "merged_to": update_stmt.excluded.merged_to,
            },
        )

        session.execute(update_stmt_on_conflict)
        print(f"Updated {len(product_updates)} products.")


def insert_products(session: Session, new_products: List[DbProductInfo]) -> None:
    from sqlalchemy.dialects.postgresql import insert as pg_insert

    products_entries = [product.model_dump() for product in new_products]

    for pe in products_entries:
        pe["nutrition"] = {k: v for k, v in pe["nutrition"].items() if v is not None}

    if products_entries:
        insert_stmt = pg_insert(ProductsTable.__table__).values(products_entries)
        session.execute(insert_stmt)
        print(f"Inserted {len(products_entries)} new products.")


def determine_product_ids(
    root_to_gtins: Dict[str, Set[str]],
    gtin_to_product_map: Dict[str, UUID],
    gtin_product_map: Dict[str, ProductInfo],
) -> Tuple[
    Dict[str, UUID],
    List[DbProductInfo],
    Dict[UUID, DbProductInfo],
]:
    component_product_id: Dict[str, UUID] = {}  # Map from root to product_id
    new_products: List[DbProductInfo] = []
    products_to_update: Dict[UUID, DbProductInfo] = {}

    for root, component_gtins in root_to_gtins.items():
        # Collect product_ids associated with GTINs in the component
        product_ids_in_component: Set[UUID] = set()
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
            new_product_id: UUID = uuid7()
            product_data.merged_to = new_product_id
            product_data = DbProductInfo(id=new_product_id, **product_data.model_dump())
            new_products.append(product_data)
            component_product_id[root] = new_product_id
            for gtin in component_gtins:
                gtin_to_product_map[gtin] = new_product_id
            gtin_to_product_map[root] = new_product_id

        else:
            # Existing product_ids found
            for product_id in product_ids_in_component:
                gtin_to_product_map[root] = product_id
                for gtin in component_gtins:
                    gtin_to_product_map[gtin] = product_id
                products_to_update[product_id] = DbProductInfo(
                    id=product_id, **product_data.model_dump()
                )

    return component_product_id, new_products, products_to_update


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
        merged_to=existing.merged_to or new.merged_to,
    )


def upsert_product_has_ingredient(
    session: Session,
    gtin_product_map: Dict[str, ProductInfo],
    gtin_offer_object_map: Dict[str, ProcessedMpnOffer],
    gtin_to_product_map: Dict[str, UUID],
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
