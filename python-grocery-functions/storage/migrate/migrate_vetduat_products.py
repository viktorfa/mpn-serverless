import argparse
import logging
from collections.abc import Iterable
from datetime import datetime
from typing import TypedDict
from uuid import UUID

import pydash
from config.mongo import get_collection
from pymongo import UpdateOne
from slugify import slugify
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session
from uuid_extensions import uuid7

from parsing.ingredients_extraction import (
    get_extracted_ingredients_postgres,
    get_raw_ingredients_from_strings,
)
from parsing.quantity_extraction import parse_quantity, standardize_quantity
from scraper_feed.helpers import is_valid_ean
from storage.postgres.common import get_pg_engine
from storage.postgres.postgres_tables import (
    BrandsTable,
    GtinsTable,
    IngredientsTable,
    ProductHasIngredientTable,
    ProductMarketInfoTable,
    ProductsTable,
)
from storage.postgres.pydantic_models import (
    DbMarketInfo,
    DbProductInfo,
    MpnBrand,
    MpnGtin,
    NutritionType,
    ProductHasIngredient,
)

logging.basicConfig(level=logging.DEBUG)


class VetDuAtNutrition(TypedDict):
    amount: float
    key: str
    size: float


class VetDuAtProduct(TypedDict):
    _id: str
    allergenerInneholder: list[str]
    allergenerInneholderIkke: list[str]
    allergenerKanInneholde: list[str]
    allergierklaring: str | None
    carbohydrates: VetDuAtNutrition | None
    deklarasjonListe: list[str] | None
    energyKcal: VetDuAtNutrition | None
    energyKj: VetDuAtNutrition | None
    epdNr: str
    erForbrukerpakning: bool
    erOkologisk: bool | None
    erSnus: bool
    erStorhusholdningsprodukt: bool
    erTobakk: bool
    fats: VetDuAtNutrition | None
    fellesProduktnavn: str
    fibers: VetDuAtNutrition | None
    firmaNavn: str
    gtin: str
    harBilde: bool | None
    holdbarhetsdagerTotalt: int | None
    informasjonstekst: str | None
    ingredienser: str | None
    isBasispakning: bool
    isNewProduct: bool
    kategoriNavn: str
    maksimumstemperaturCelcius: float | None
    markedsnavn: str
    mengde: float
    mengdetypeenhet: str
    merkeordninger: list[str]
    merkeOrdninger: list[str]
    minimumstemperaturCelsius: float | None
    pakningID: str
    parsedIngredients: str
    polyfats: VetDuAtNutrition | None
    polyols: VetDuAtNutrition | None
    produksjonsland: str | None
    produktID: str
    proteins: VetDuAtNutrition | None
    salt: VetDuAtNutrition | None
    satFats: VetDuAtNutrition | None
    starch: VetDuAtNutrition | None
    sugars: VetDuAtNutrition | None
    varegruppenavn: str
    varemerke: str | None


LIMIT = 512
BATCH_SIZE = 128


def get_quantity(product: VetDuAtProduct):
    quantity_string = f"{product['mengde']}{product['mengdetypeenhet']}"
    quantity = parse_quantity([quantity_string])["quantity"]
    standard_quantity = standardize_quantity({"quantity": quantity})["quantity"]

    if pydash.get(standard_quantity, ["size", "standard", "min"]):
        return standard_quantity
    else:
        return None


def get_product_data(product: VetDuAtProduct, product_id: UUID) -> DbProductInfo:
    nutrition = NutritionType(
        fats=product["fats"]["amount"] if "fats" in product else None,
        carbohydrates=product["carbohydrates"]["amount"]
        if "carbohydrates" in product
        else None,
        proteins=product["proteins"]["amount"] if "proteins" in product else None,
        satFats=product["satFats"]["amount"] if "satFats" in product else None,
        monoFats=None,
        polyFats=product["polyfats"]["amount"] if "polyfats" in product else None,
        salt=product["salt"]["amount"] if "salt" in product else None,
        polyols=product["polyols"]["amount"] if "polyols" in product else None,
        fibers=product["fibers"]["amount"] if "fibers" in product else None,
        starch=product["starch"]["amount"] if "starch" in product else None,
        sugars=product["sugars"]["amount"] if "sugars" in product else None,
        kcals=product["energyKcal"]["amount"] if "energyKcal" in product else None,
    )

    quantity = get_quantity(product)

    return DbProductInfo(
        id=product_id,
        quantity_unit=quantity["size"]["unit"]["symbol"] if quantity else None,
        quantity_amount=quantity["size"]["amount"]["min"] if quantity else None,
        quantity_standard_amount=quantity["size"]["standard"]["min"]
        if quantity
        else None,
        nutrition=nutrition,
        merged_to=product_id,
    )


def get_market_info(product: VetDuAtProduct, product_id: UUID) -> DbMarketInfo:
    return DbMarketInfo(
        product_id=product_id,
        market="no",
        title=product["markedsnavn"],
        description=product.get("informasjonstekst"),
        subtitle=None,
        short_description=None,
        brand_key=slugify(product["varemerke"], separator="_")
        if product["varemerke"]
        else None,
        vendor_key=None,
        context="amp-no",
        category_key=None,
        category_keys=None,
    )


def migrate_data(limit: int, batch_size: int):
    logging.info(
        f"Starting migration of vetduat products with limit {limit} and batch size {batch_size}"
    )
    vetduat_collection = get_collection("vetduat_items")

    # mpnoffers_collection = get_collection("mpnoffers")
    # vetduat_response = vetduat_collection.update_many(
    #    {"detailFetchedAt": {"$exists": True}, "migrated_pg_at": {"$exists": True}},
    #    {"$unset": {"migrated_pg_at": ""}},
    # )
    # offers_response = mpnoffers_collection.update_many(
    #    {"migrated_at": {"$exists": True}},
    #    {"$unset": {"migrated_at": ""}},
    # )
    # print(
    #    f"Removed migrated_pg_at from {vetduat_response.modified_count} vetduat items"
    # )
    # print(f"Removed migrated_at from {offers_response.modified_count} mpnoffers")
    # return

    vetduat_products: Iterable[VetDuAtProduct] = (
        vetduat_collection.find(
            {"detailFetchedAt": {"$exists": True}, "migrated_pg_at": {"$exists": False}}
        )
        .limit(limit)
        .batch_size(batch_size)
    )

    product_batch: list[VetDuAtProduct] = []
    migrated_mongo_ids: set[str] = set()

    product_counter = 0

    with Session(get_pg_engine()) as session:
        try:
            ingredients = session.query(IngredientsTable).all()

            for product in vetduat_products:
                if product_counter >= limit:
                    break
                migrated_mongo_ids.add(product["_id"])
                if not is_valid_ean(product["gtin"]):
                    logging.warning(
                        f"Invalid ean {product['gtin']} {product['fellesProduktnavn']}"
                    )
                    continue
                product_counter += 1
                product_batch.append(product)
                if product_counter % batch_size == 0:
                    print(f"Processed {product_counter} products")
                    if len(product_batch) > 0:
                        now = datetime.now()
                        insert_batch(session, product_batch, ingredients)
                        session.commit()
                        vetduat_collection.bulk_write(
                            [
                                UpdateOne(
                                    {"_id": _id},
                                    {"$set": {"migrated_pg_at": now}},
                                )
                                for _id in migrated_mongo_ids
                            ]
                        )
                        migrated_mongo_ids.clear()
                        product_batch = []

            if len(product_batch) > 0:
                now = datetime.now()
                insert_batch(session, product_batch, ingredients)
                session.commit()
                vetduat_collection.bulk_write(
                    [
                        UpdateOne(
                            {"_id": _id},
                            {"$set": {"migrated_pg_at": now}},
                        )
                        for _id in migrated_mongo_ids
                    ]
                )
                migrated_mongo_ids.clear()
            elif len(migrated_mongo_ids) > 0:
                now = datetime.now()
                vetduat_collection.bulk_write(
                    [
                        UpdateOne(
                            {"_id": _id},
                            {"$set": {"migrated_pg_at": now}},
                        )
                        for _id in migrated_mongo_ids
                    ]
                )
                migrated_mongo_ids.clear()

        except Exception:
            session.rollback()
            raise

    logging.info(f"Processed {product_counter} products.")


def insert_batch(
    session: Session,
    product_batch: list[VetDuAtProduct],
    ingredients: list[IngredientsTable],
):
    epd_gtins = []
    ean_gtins = []
    for product in product_batch:
        if is_valid_ean(product["gtin"]):
            gtin_key = f"ean:{product['gtin']}"
            ean_gtins.append(gtin_key)
        else:
            raise ValueError(
                f"Invalid ean {product['gtin']} {product['fellesProduktnavn']}"
            )
        epd_gtin = f"epd:{product['epdNr']}"
        epd_gtins.append(epd_gtin)
    existing_gtins = session.query(GtinsTable).filter(
        GtinsTable.gtin.in_([*epd_gtins, *ean_gtins])
    )
    existing_products_map: dict[str, UUID] = {}
    for row in existing_gtins:
        existing_products_map[str(row.gtin)] = UUID(str(row.product_id))

    brands_to_upsert: list[MpnBrand] = []
    products_to_upsert: list[DbProductInfo] = []
    market_infos_to_upsert: list[DbMarketInfo] = []
    gtins_to_upsert: list[MpnGtin] = []
    product_has_ingredient_to_upsert: list[ProductHasIngredient] = []

    for product in product_batch:
        ean_gtin = f"ean:{product['gtin']}"
        epd_gtin = f"epd:{product['epdNr']}"
        existing_product_id: UUID | None = existing_products_map.get(
            epd_gtin
        ) or existing_products_map.get(gtin_key)

        product_id: UUID = existing_product_id or uuid7()

        product_info = get_product_data(product, product_id)
        market_info = get_market_info(product, product_id)
        gtins = [
            MpnGtin(gtin=ean_gtin, product_id=product_id),
            MpnGtin(gtin=epd_gtin, product_id=product_id),
        ]
        try:
            brands_to_upsert.append(
                MpnBrand(
                    key=slugify(product["varemerke"], separator="_"),
                    title=product["varemerke"],
                    market="no",
                )
            )
        except KeyError:
            pass
        except TypeError:
            pass

        products_to_upsert.append(product_info)
        market_infos_to_upsert.append(market_info)
        gtins_to_upsert.extend(gtins)

        offer_ingredients = product.get("parsedIngredients")
        raw_ingredients = get_raw_ingredients_from_strings([offer_ingredients])
        if offer_ingredients:
            matched_ingredients = get_extracted_ingredients_postgres(
                raw_ingredients, ingredients
            )

            if matched_ingredients:
                for ingredient in matched_ingredients:
                    product_has_ingredient_to_upsert.append(
                        ProductHasIngredient(
                            product_id=product_id,
                            ingredient_id=UUID(str(ingredient.id)),
                        )
                    )

    if len(brands_to_upsert) > 0:
        brands_update_stmt = pg_insert(BrandsTable.__table__).values(
            [x.model_dump() for x in brands_to_upsert]
        )
        brands_update_stmt = brands_update_stmt.on_conflict_do_nothing(
            index_elements=["key", "market"]
        )
        session.execute(brands_update_stmt)

    products_update_stmt = pg_insert(ProductsTable.__table__).values(
        [
            {**x.model_dump(), "nutrition": x.nutrition.model_dump(exclude_none=True)}
            for x in products_to_upsert
        ]
    )

    products_update_stmt = products_update_stmt.on_conflict_do_update(
        index_elements=["id"],
        set_={
            "quantity_unit": products_update_stmt.excluded.quantity_unit,
            "quantity_amount": products_update_stmt.excluded.quantity_amount,
            "quantity_standard_amount": products_update_stmt.excluded.quantity_standard_amount,
            "nutrition": products_update_stmt.excluded.nutrition,
            "merged_to": products_update_stmt.excluded.merged_to,
        },
    )
    session.execute(products_update_stmt)
    market_info_update_stmt = pg_insert(ProductMarketInfoTable.__table__).values(
        [x.model_dump() for x in market_infos_to_upsert]
    )
    market_info_update_stmt = market_info_update_stmt.on_conflict_do_update(
        index_elements=["product_id", "market"],
        set_={
            "title": market_info_update_stmt.excluded.title,
            "description": market_info_update_stmt.excluded.description,
            "brand_key": market_info_update_stmt.excluded.brand_key,
            "context": market_info_update_stmt.excluded.context,
        },
    )
    session.execute(market_info_update_stmt)
    gtins_update_stmt = pg_insert(GtinsTable.__table__).values(
        [x.model_dump() for x in gtins_to_upsert]
    )
    gtins_update_stmt = gtins_update_stmt.on_conflict_do_nothing(
        index_elements=["gtin"]
    )
    session.execute(gtins_update_stmt)

    if product_has_ingredient_to_upsert:
        product_has_ingredient_update_stmt = pg_insert(
            ProductHasIngredientTable.__table__
        ).values([x.model_dump() for x in product_has_ingredient_to_upsert])
        product_has_ingredient_update_stmt = (
            product_has_ingredient_update_stmt.on_conflict_do_nothing(
                index_elements=["product_id", "ingredient_id"]
            )
        )
        session.execute(product_has_ingredient_update_stmt)

    logging.info(f"Upserted {len(products_to_upsert)} products")
    logging.info(f"Upserted {len(market_infos_to_upsert)} market infos")
    logging.info(f"Upserted {len(gtins_to_upsert)} gtins")
    logging.info(
        f"Upserted {len(product_has_ingredient_to_upsert)} product_has_ingredient"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Migrate vetduat products from MongoDB to PostgreSQL."
    )
    parser.add_argument(
        "--limit", type=int, default=LIMIT, help="Limit of offers to migrate"
    )
    parser.add_argument(
        "--batch_size", type=int, default=BATCH_SIZE, help="Batch size for migration"
    )

    args = parser.parse_args()

    migrate_data(limit=args.limit, batch_size=args.batch_size)
