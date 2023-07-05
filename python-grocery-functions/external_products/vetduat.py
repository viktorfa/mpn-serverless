from typing import Iterable, Optional, TypedDict
from pymongo import UpdateOne
from datetime import datetime
from slugify import slugify
import json
import logging
import pydash
from amp_types.amp_product import IngredientType
from config.mongo import get_collection
from parsing.ingredients_extraction import (
    get_ingredients_data,
    sort_db_ingredient_key,
)
from parsing.nutrition_extraction import macro_names
from parsing.quantity_extraction import parse_quantity, standardize_quantity
from scraper_feed.helpers import is_valid_ean
from util.helpers import is_null_or_empty
from scraper_feed.filters import (
    mpn_nutrition_version,
    mpn_ingredients_version,
    mpn_quantity_version,
)

logging.basicConfig(level=logging.DEBUG)


class VetDuAtNutrition(TypedDict):
    amount: float
    key: str
    size: float


class VetDuAtProduct(TypedDict):
    allergenerInneholder: list[str]
    allergenerInneholderIkke: list[str]
    allergenerKanInneholde: list[str]
    allergierklaring: Optional[str]
    carbohydrates: Optional[VetDuAtNutrition]
    deklarasjonListe: Optional[list[str]]
    energyKcal: Optional[VetDuAtNutrition]
    energyKj: Optional[VetDuAtNutrition]
    epdNr: str
    erForbrukerpakning: bool
    erOkologisk: Optional[bool]
    erSnus: bool
    erStorhusholdningsprodukt: bool
    erTobakk: bool
    fats: Optional[VetDuAtNutrition]
    fellesProduktnavn: str
    fibers: Optional[VetDuAtNutrition]
    firmaNavn: str
    gtin: str
    harBilde: Optional[bool]
    holdbarhetsdagerTotalt: Optional[int]
    informasjonstekst: Optional[str]
    ingredienser: Optional[str]
    isBasispakning: bool
    isNewProduct: bool
    kategoriNavn: str
    maksimumstemperaturCelcius: Optional[float]
    markedsnavn: str
    mengde: float
    mengdetypeenhet: str
    merkeordninger: list[str]
    merkeOrdninger: list[str]
    minimumstemperaturCelsius: Optional[float]
    pakningID: str
    parsedIngredients: str
    polyfats: Optional[VetDuAtNutrition]
    polyols: Optional[VetDuAtNutrition]
    produksjonsland: Optional[str]
    produktID: str
    proteins: Optional[VetDuAtNutrition]
    salt: Optional[VetDuAtNutrition]
    satFats: Optional[VetDuAtNutrition]
    starch: Optional[VetDuAtNutrition]
    sugars: Optional[VetDuAtNutrition]
    varegruppenavn: str
    varemerke: Optional[str]


config = {"extractIngredientsFields": ["ingredienser"]}


def get_quantity(product: VetDuAtProduct):
    quantity_string = f"{product['mengde']}{product['mengdetypeenhet']}"
    quantity = parse_quantity([quantity_string])["quantity"]
    standard_quantity = standardize_quantity({"quantity": quantity})["quantity"]

    if pydash.get(standard_quantity, ["size", "standard", "min"]):
        return standard_quantity
    else:
        return None


def add_vetduat_products():
    vetduat_collection = get_collection("vetduat_items")
    vetduat_products: Iterable[VetDuAtProduct] = vetduat_collection.find(
        {"detailFetchedAt": {"$exists": True}}
    ).limit(100000)

    ingredients_data = {}
    ingredients_collection = get_collection("ingredients")
    db_ingredients: Iterable[IngredientType] = ingredients_collection.find({})
    for x in sorted(db_ingredients, key=sort_db_ingredient_key):
        ingredients_data[x["key"]] = x

    updates = []

    now = datetime.now()

    for product in vetduat_products:
        if is_valid_ean(product["gtin"]):
            gtin_key = f"ean:{product['gtin']}"
        else:
            print(f"WARN invalid ean {product['gtin']} {product['fellesProduktnavn']}")
            continue
        result = {}
        mpn_ingredients = get_ingredients_data(
            product,
            config,
            ingredients_data,
        )
        if not is_null_or_empty(mpn_ingredients):
            result["mpnIngredients"] = mpn_ingredients

        mpn_nutrition = {}

        for key, value in product.items():
            if key in macro_names:
                mpn_nutrition[key] = {"key": key, "value": value["amount"]}
        if not is_null_or_empty(mpn_nutrition):
            result["nutrition"] = mpn_nutrition

        result["quantity"] = get_quantity(product)
        result["epd_no"] = product["epdNr"]

        result["gtins"] = [gtin_key]
        is_promotion_restricted = product["erTobakk"] or product["erSnus"]
        result["isPromotionRestricted"] = is_promotion_restricted
        result["brand"] = product["varemerke"] if product["varemerke"] else None
        result["brandKey"] = (
            slugify(product["varemerke"], separator="_")
            if product["varemerke"]
            else None
        )
        # result["countryOfOrigin"] = product["produksjonsland"]

        result["title"] = product["fellesProduktnavn"]
        result["subtitle"] = product["informasjonstekst"]

        # print(json.dumps(result, indent=2))

        update_set = {
            "updatedAt": now,
            "vetduatAddedAt": now,
            "brand": result["brand"],
            "brandKey": result["brandKey"],
            "epd_no": result["epd_no"],
            "isPromotionRestricted": result["isPromotionRestricted"],
            "mpnIngredientsV": mpn_ingredients_version,
            "mpnNutritionV": mpn_nutrition_version,
            "mpnQuantityV": mpn_quantity_version,
        }

        if "mpnIngredients" in result.keys():
            update_set["mpnIngredients"] = result["mpnIngredients"]
        if "mpnNutrition" in result.keys():
            update_set["mpnNutrition"] = result["mpnNutrition"]
        if "quantity" in result.keys():
            update_set["quantity"] = result["quantity"]

        product_uri = f"vetduat:product:{product['produktID']}"

        updates.append(
            UpdateOne(
                {
                    "gtins": gtin_key,
                    "isMerged": {"$ne": True},
                    "relationType": "identical",
                    "gtins.0": {"$exists": 1},
                },
                {
                    "$setOnInsert": {
                        "isMerged": False,
                        "createdAt": now,
                        "provenance": "vetduat",
                        "gtins": [gtin_key],
                        "relationType": "identical",
                        "m:no": {
                            "title": result["title"],
                            "subtitle": result["subtitle"],
                        },
                    },
                    "$set": {
                        **update_set,
                    },
                    "$addToSet": {"offerSet": product_uri},
                },
                upsert=True,
            )
        )
        # print(gtin_key)

    # print(updates)

    birelations_collection = get_collection("offerbirelations")
    update_response = birelations_collection.bulk_write(updates)

    print(update_response)


__name__ == "__main__" and add_vetduat_products()
