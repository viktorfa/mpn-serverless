from datetime import datetime
import logging
from typing import Any, Dict, Iterable, List, Optional, Sequence
from uuid import UUID
from pydantic import BaseModel, ValidationError
from pymongo import UpdateOne
from slugify import slugify
from sqlalchemy.orm import Session
import json
import argparse

from amp_types.amp_product import ProcessedMpnOffer
from config.mongo import get_collection
from storage.postgres.common import get_pg_engine
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
from storage.postgres.offers import (
    upsert_brands_postgres,
    upsert_dealers_postgres,
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
from util.logging import configure_lambda_logging
from util.mappings import get_offer_context_from_site_collection
from util.timer import Timer


# For old offers without scrapeBatchId
DEFAULT_SCRAPE_BATCH_ID = "6ut_Kt.jk4NvVE.ycCN1xDy5ihGv_OWX"
OFFER_LIMIT = 1024 * 2
BATCH_SIZE = 1024
configure_lambda_logging()


example_mongo_offer = {
    "_id": {"$oid": "62b8312a800bc7ba7fb2b8f0"},
    "uri": "easygrocery_au:product:STK000217",
    "ahref": None,
    "brand": "FIG",
    "categories": [],
    "dealer": "easygrocery_au",
    "description": "Carrot, Walnut & Pumpkin Seed Loaf Large Product Details Shelf Life 7 Days Nutritional Information",
    "gtins": {},
    "href": "https://ipantry.com.au/products/carrot-walnut-pumpkin-seed-loaf-large?variant=33797359403147",
    "imageUrl": "https://ipantry.com.au/Carrot, Walnut & Pumpkin Seed Loaf Large-Indulgence-FIG-iPantry-australia",
    "isPartner": False,
    "items": {"max": 1, "min": 1},
    "market": "au",
    "mpnIngredients": None,
    "mpnNutrition": {},
    "mpnProperties": {},
    "mpnStock": "InStock",
    "pricing": {"price": 27, "currency": "AUD", "prePrice": None, "priceUnit": "pcs"},
    "provenance": "ipantry_au_spider",
    "provenanceId": "STK000217",
    "quantity": {"size": {}, "pieces": {}},
    "siteCollection": "augroceryoffers",
    "sku": "STK000217",
    "title": "Carrot, Walnut & Pumpkin Seed Loaf Large",
    "validFrom": {"$date": "2024-10-07T05:41:16.000Z"},
    "validThrough": {"$date": "2024-10-17T09:41:16.000Z"},
    "value": {"size": {}, "pieces": {}},
    "scrapeBatchId": "yDGuJSDrqUh2QjHz6WW73ZKa.8ugD6xA",
    "isRecent": True,
    "brandKey": "fig",
    "dealerKey": "easygrocery_au",
    "difference": 0,
    "difference30DaysMean": 0,
    "difference30DaysMeanPercentage": 0,
    "difference365DaysMean": 0,
    "difference365DaysMeanPercentage": 0,
    "difference7DaysMean": 0,
    "difference7DaysMeanPercentage": 0,
    "difference90DaysMean": 0,
    "difference90DaysMeanPercentage": 0,
    "differencePercentage": 0,
    "price30DaysMean": 27,
    "price365DaysMean": 27,
    "price7DaysMean": 0,
    "price90DaysMean": 27,
}
example_mongo_offer2 = {
    "_id": {"$oid": "66f8bba333ef80b473ddd26a"},
    "uri": "kolonial:product:65866",
    "ahref": None,
    "brand": "Aunt Mabels",
    "brandKey": "aunt_mabels",
    "categories": ["Iskrem, kaker og kjeks"],
    "dealer": "kolonial",
    "dealerKey": "kolonial",
    "gtins": {},
    "href": "https://oda.com/no/products/65866-aunt-mabels-muffin-melkesjokolade/",
    "imageUrl": "https://bilder.kolonial.no/local_products/9775730c-3bc8-4d35-8c70-870b61fd5c48.jpg?auto=format&fit=max&w=300&s=86298dea496489dc71462ed768c521f8",
    "isPartner": False,
    "isRecent": True,
    "items": {"max": 1, "min": 1},
    "market": "no",
    "mpnCategoriesV": 1,
    "mpnIngredients": {
        "ingredients": {
            "sugar": {
                "text": "melkesjokolade 4,8% (sukker",
                "key": "sugar",
                "shortDescription": "",
                "name": "Sukker",
            },
            "vegetableOil": {
                "text": "vegetabilsk olje (raps)",
                "key": "vegetableOil",
                "shortDescription": "",
                "name": "Vegetabilsk olje",
            },
            "egg": {
                "text": "EGGEHVITEPULVER",
                "key": "egg",
                "shortDescription": "",
                "name": "Egg",
            },
            "aqua": {
                "text": "vann",
                "key": "aqua",
                "shortDescription": "",
                "name": "Vann",
            },
            "cocoaButter": {
                "text": "kakaosmør",
                "key": "cocoaButter",
                "shortDescription": "",
                "name": "Kakaosmør",
            },
            "cocoaMass": {
                "text": "kakaomasse",
                "key": "cocoaMass",
                "shortDescription": "",
                "name": "Kakaomasse",
            },
            "emulgator": {
                "text": "emulgator (mono- og diglyserider av fettsyrer)",
                "key": "emulgator",
                "shortDescription": "",
                "name": "Emulgator",
            },
            "e322": {
                "text": "emulgator (SOYALECITIN)",
                "key": "e322",
                "shortDescription": "",
                "name": "Lecitin",
            },
            "aroma": {
                "text": "aroma",
                "key": "aroma",
                "shortDescription": "Varen er tilsatt aroma",
                "name": "Aroma",
            },
            "glycerol": {
                "text": "fuktighetsbevarende (glyserol",
                "key": "glycerol",
                "shortDescription": "",
                "name": "Glyserol",
            },
            "starch": {
                "text": "modifisert maisstivelse",
                "key": "starch",
                "shortDescription": "",
                "name": "Stivelse",
            },
            "e450": {
                "text": "hevemiddel (dinatriumdifosfat",
                "key": "e450",
                "shortDescription": "",
                "name": "Dinatriumdifosfat",
            },
            "e500": {
                "text": "natriumhydrogenkarbonat)",
                "key": "e500",
                "shortDescription": "",
                "name": "Natriumhydrogenkarbonat",
            },
            "glycerides": {
                "text": "emulgator (mono- og diglyserider av fettsyrer)",
                "key": "glycerides",
                "shortDescription": "",
                "name": "Glyserider",
            },
            "eggWhitePowder": {
                "text": "EGGEHVITEPULVER",
                "key": "eggWhitePowder",
                "shortDescription": "",
                "name": "Eggehvitepulver",
            },
            "potassiumSorbate": {
                "text": "konserveringsmiddel (kaliumsorbat)",
                "key": "potassiumSorbate",
                "shortDescription": "",
                "name": "Kaliumsorbat",
            },
            "stabilizer": {
                "text": "stabilisator (xantangum).",
                "key": "stabilizer",
                "shortDescription": "",
                "name": "Stabilisator",
            },
        },
        "processedScore": 0,
    },
    "mpnIngredientsV": 3,
    "mpnNutrition": {
        "fats": {"key": "fats", "value": 20, "unit": "."},
        "carbohydrates": {"key": "carbohydrates", "value": 45, "unit": "."},
        "proteins": {"key": "proteins", "value": 5, "unit": "."},
        "satFats": {"key": "satFats", "value": 2, "unit": "."},
        "salt": {"key": "salt", "value": 1, "unit": "g"},
        "fibers": {"key": "fibers", "value": 1, "unit": "."},
        "sugars": {"key": "sugars", "value": 24, "unit": "."},
        "energy": {"key": "energy", "value": 394, "unit": "kcal"},
        "energyKcal": {"value": 394, "key": "energyKcal"},
    },
    "mpnNutritionV": 2,
    "mpnProperties": {},
    "mpnPropertiesV": 1,
    "mpnQuantityV": 2,
    "mpnStock": "InStock",
    "mpnStockV": 1,
    "namespace": "kolonial",
    "pricing": {"price": 9.97, "currency": "NOK", "prePrice": None, "priceUnit": "pcs"},
    "provenance": "kolonial_spider",
    "provenanceId": "65866",
    "quantity": {
        "size": {
            "unit": {
                "symbol": "g",
                "type": "quantity",
                "si": {"symbol": "kg", "factor": 0.001},
            },
            "amount": {"min": 95, "max": 95},
            "standard": {"min": 0.095, "max": 0.095},
        },
        "pieces": {},
    },
    "scrapeBatchId": "KfAP2LaPFFsmU_i64rLIXi_5ovxXLKRE",
    "siteCollection": "groceryoffers",
    "sku": "65866",
    "subtitle": "95 g",
    "title": "Aunt Mabels Muffin Melkesjokolade",
    "validFrom": {"$date": "2024-09-29T02:29:53.000Z"},
    "validThrough": {"$date": "2024-10-09T06:29:53.000Z"},
    "value": {
        "size": {
            "unit": {
                "symbol": "kg",
                "type": "quantity_value",
                "si": {"symbol": "kg", "factor": 1},
            },
            "amount": {"min": 104.95, "max": 104.95},
            "standard": {"min": 104.95, "max": 104.95},
        },
        "pieces": {},
    },
    "vendor": "Baxt AS",
    "vendorKey": "baxt_as",
    "mpnCategories": [],
    "difference": 0,
    "difference30DaysMean": 0,
    "difference30DaysMeanPercentage": 0,
    "difference365DaysMean": 0,
    "difference365DaysMeanPercentage": 0,
    "difference7DaysMean": 0,
    "difference7DaysMeanPercentage": 0,
    "difference90DaysMean": 0,
    "difference90DaysMeanPercentage": 0,
    "differencePercentage": 0,
    "differencePrevYear90DaysMean": 0,
    "differencePrevYear90DaysPercentage": 0,
    "price30DaysMean": 0,
    "price365DaysMean": 0,
    "price7DaysMean": 0,
    "price90DaysMean": 0,
    "pricePrevYear90DaysMean": 0,
    "migrated_at": {"$date": "2024-10-08T19:23:59.790Z"},
}


class MongoOffer(BaseModel):
    uri: str
    ahref: Optional[str]
    dealer: str
    brand: Optional[str]
    vendor: Optional[str]
    categories: List[str]
    subtitle: Optional[str]
    description: Optional[str]
    shortDescription: Optional[str]
    gtins: Dict[str, str]
    href: str
    imageUrl: Optional[str]
    isPartner: Optional[bool]
    items: Dict[str, int]
    market: str
    mpnIngredients: Optional[Dict[str, Any]]
    mpnNutrition: Dict[str, Any]
    mpnProperties: Dict[str, Any]
    mpnStock: Optional[str]
    pricing: Dict[str, Any]
    provenance: str
    provenanceId: str
    quantity: Dict[str, Any]
    siteCollection: str
    title: str
    validFrom: datetime
    validThrough: datetime
    value: Dict[str, Any]
    scrapeBatchId: str
    isRecent: Optional[bool]
    difference: Optional[float]
    difference30DaysMean: Optional[float]
    difference30DaysMeanPercentage: Optional[float]
    difference365DaysMean: Optional[float]
    difference365DaysMeanPercentage: Optional[float]
    difference7DaysMean: Optional[float]
    difference7DaysMeanPercentage: Optional[float]
    difference90DaysMean: Optional[float]
    difference90DaysMeanPercentage: Optional[float]
    differencePercentage: Optional[float]
    price30DaysMean: Optional[float]
    price365DaysMean: Optional[float]
    price7DaysMean: Optional[float]
    price90DaysMean: Optional[float]


class OfferForMigration(ProcessedMpnOffer):
    mongo_id: str


def sanitize_data(offer: OfferForMigration) -> OfferForMigration:
    for key, value in offer.items():
        if isinstance(value, str):
            offer[key] = value.replace("\0", "")  # Remove NUL characters
    return offer


def migrate_data(limit: int, batch_size: int):
    logging.info(
        f"Starting migration of mongo offers with limit {limit} and batch size {batch_size}"
    )

    timer = Timer()
    timer.start("Migrate data")
    timer.start("Get collection")

    collection = get_collection("mpnoffers")

    # Use a cursor to iterate through the MongoDB collection
    cursor: Iterable[dict] = (
        collection.find(
            {"migrated_at": {"$exists": False}},
            {
                "_id": 1,
                "uri": 1,
                "ahref": 1,
                "brand": 1,
                "vendor": 1,
                "dealer": 1,
                "subtitle": 1,
                "categories": 1,
                "description": 1,
                "shortDescription": 1,
                "gtins": 1,
                "href": 1,
                "imageUrl": 1,
                "isPartner": 1,
                "items": 1,
                "market": 1,
                "mpnIngredients": 1,
                "mpnNutrition": 1,
                "mpnProperties": 1,
                "mpnStock": 1,
                "pricing": 1,
                "provenance": 1,
                "quantity": 1,
                "siteCollection": 1,
                "title": 1,
                "validFrom": 1,
                "validThrough": 1,
                "value": 1,
                "scrapeBatchId": 1,
            },
        )
        .limit(limit)
        .batch_size(batch_size)
    )
    timer.stop("Get collection")

    offer_counter = 0
    offers_for_context: Dict[str, List[OfferForMigration]] = {}

    migrated_offer_ids: List[str] = []

    timer.start("Save mongo batch")
    for _offer in cursor:
        if offer_counter >= limit:
            break
        if _offer.get("provenance") == "custom":
            logging.info("Skipping custom offer")
            migrated_offer_ids.append(_offer["_id"])
            continue
        offer_counter += 1
        offer_market = _offer.get("market")
        site_collection = "".join(filter(str.isalnum, _offer["siteCollection"].lower()))
        offer_context = get_offer_context_from_site_collection(site_collection)
        if not offer_market:
            offer_market = offer_context.split("-")[-1]
        offer_provenance_id = _offer["uri"].split(":")[-1]

        value = _offer.get("value", {}) or {}
        if type(value) is str:
            value = {}
        items = _offer.get("items", {}) or {}
        if type(items) is str:
            items = {}
        for k, v in items.items():
            if type(v) is not int:
                items = {}
                break
        quantity = _offer.get("quantity", {}) or {}
        if type(quantity) is str:
            quantity = {}

        try:
            offer = MongoOffer(
                uri=_offer["uri"],
                ahref=_offer.get("ahref"),
                dealer=_offer["dealer"],
                brand=_offer.get("brand"),
                vendor=_offer.get("vendor"),
                categories=_offer.get("categories", []) or [],
                subtitle=_offer.get("subtitle"),
                description=_offer.get("description"),
                shortDescription=_offer.get("shortDescription"),
                gtins=_offer.get("gtins", {}) or {},
                href=_offer["href"],
                imageUrl=_offer.get("imageUrl"),
                isPartner=_offer.get("isPartner"),
                items=items,
                market=offer_market,
                mpnIngredients=_offer.get("mpnIngredients") or {},
                mpnNutrition=_offer.get("mpnNutrition", {}) or {},
                mpnProperties=_offer.get("mpnProperties", {}) or {},
                mpnStock=_offer.get("mpnStock"),
                pricing=_offer["pricing"],
                provenance=_offer["provenance"],
                provenanceId=offer_provenance_id,
                quantity=quantity,
                siteCollection=site_collection,
                title=_offer["title"],
                validFrom=_offer["validFrom"],
                validThrough=_offer["validThrough"],
                value=value,
                scrapeBatchId=_offer.get("scrapeBatchId", DEFAULT_SCRAPE_BATCH_ID),
                isRecent=_offer.get("isRecent"),
                difference=_offer.get("difference"),
                difference30DaysMean=_offer.get("difference30DaysMean"),
                difference30DaysMeanPercentage=_offer.get(
                    "difference30DaysMeanPercentage"
                ),
                difference365DaysMean=_offer.get("difference365DaysMean"),
                difference365DaysMeanPercentage=_offer.get(
                    "difference365DaysMeanPercentage"
                ),
                difference7DaysMean=_offer.get("difference7DaysMean"),
                difference7DaysMeanPercentage=_offer.get(
                    "difference7DaysMeanPercentage"
                ),
                difference90DaysMean=_offer.get("difference90DaysMean"),
                difference90DaysMeanPercentage=_offer.get(
                    "difference90DaysMeanPercentage"
                ),
                differencePercentage=_offer.get("differencePercentage"),
                price30DaysMean=_offer.get("price30DaysMean"),
                price365DaysMean=_offer.get("price365DaysMean"),
                price7DaysMean=_offer.get("price7DaysMean"),
                price90DaysMean=_offer.get("price90DaysMean"),
            )
        except ValidationError as e:
            logging.error(f"Error validating offer {_offer['_id']}: {e}")
            logging.error(json.dumps(offer, indent=2, default=str))
            raise
        except KeyError as e:
            logging.error(f"Error getting key {_offer['_id']}: {e}")
            logging.error(json.dumps(offer, indent=2, default=str))
            raise

        # Convert the MongoDB offer to a ProcessedMpnOffer object
        vendor_key = slugify(offer.vendor, separator="_") if offer.vendor else None
        brand_key = slugify(offer.brand, separator="_") if offer.brand else None
        raw_ingredients: List[str] = []
        try:
            for k, v in offer.mpnIngredients.get("ingredients", {}).items():
                raw_ingredients.append(v["text"] + " " + k)
        except Exception:
            pass

        try:
            if type(offer.pricing["currency"]) is str:
                if len(offer.pricing["currency"]) != 3:
                    offer.pricing["currency"] = None
        except KeyError:
            pass

        try:
            if type(offer.pricing["price"]) is str:
                offer.pricing["price"] = float(offer.pricing["price"].replace(",", "."))
        except KeyError:
            pass
        except ValueError:
            logging.warning(
                f"Could not convert price to float: {offer.pricing.get('price')}"
            )
            offer.pricing["price"] = None

        try:
            if type(offer.pricing["prePrice"]) is str:
                offer.pricing["prePrice"] = float(
                    offer.pricing["prePrice"].replace(",", ".")
                )
        except KeyError:
            pass
        except ValueError:
            logging.warning(
                f"Could not convert prePrice to float: {offer.pricing.get('prePrice')}"
            )
            offer.pricing["prePrice"] = None

        processed_offer = OfferForMigration(
            title=offer.title,
            pricing=offer.pricing,
            dealer=offer.dealer,
            brand=offer.brand,
            brandKey=brand_key,
            vendor=offer.vendor,
            vendorKey=vendor_key,
            subtitle=offer.subtitle,
            shortDescription=offer.shortDescription,
            description=offer.description,
            imageUrl=offer.imageUrl,
            pieces=offer.quantity.get("pieces", {}),
            value=offer.value,
            quantity=offer.quantity,
            items=offer.items,
            validFrom=offer.validFrom,
            validThrough=offer.validThrough,
            href=offer.href,
            provenance=offer.provenance,
            uri=offer.uri,
            provenanceId=offer.provenanceId,
            availability=offer.mpnStock,
            additionalProperties={},
            mpnNutrition=offer.mpnNutrition,
            mpnProperties=offer.mpnProperties,
            rawIngredients=raw_ingredients,
            categories=offer.categories,
            gtins=offer.gtins,
            market=offer.market,
            isPartner=offer.isPartner,
            siteCollection=offer.siteCollection,
            scrapeBatchId=offer.scrapeBatchId,
            namespace=offer.uri.split(":")[0],
            context=get_offer_context_from_site_collection(offer.siteCollection),
            mongo_id=_offer["_id"],
        )
        processed_offer = sanitize_data(processed_offer)

        if offer_context not in offers_for_context:
            offers_for_context[offer_context] = []
        offers_for_context[offer_context].append(processed_offer)

        if offer_counter % batch_size == 0:
            for c, offers in offers_for_context.items():
                if len(offers) > 1:
                    for offer in offers:
                        if offer["context"] != c:
                            raise ValueError(
                                f"Offer context {offer['context']} does not match site collection {c}"
                            )
                    try:
                        handle_store_offer_batch(offers, c)
                    except Exception:
                        logging.error(offers)
                        raise
                    offers_for_context[c] = []
                    now = datetime.now()
                    collection.bulk_write(
                        [
                            UpdateOne(
                                {"_id": _offer["mongo_id"]},
                                {"$set": {"migrated_at": now}},
                            )
                            for _offer in offers
                        ]
                    )
            timer.stop("Save mongo batch")
            timer.start("Save mongo batch")
        migrated_offer_ids.append(_offer["_id"])

    for c, offers in offers_for_context.items():
        if len(offers) > 0:
            for offer in offers:
                if offer["context"] != c:
                    raise ValueError(
                        f"Offer context {offer['context']} does not match site collection {c}"
                    )
            try:
                handle_store_offer_batch(offers, c)
            except Exception:
                logging.error(offers)
                raise
            offers_for_context[c] = []
            now = datetime.now()
            collection.bulk_write(
                [
                    UpdateOne(
                        {"_id": _offer["mongo_id"]},
                        {"$set": {"migrated_at": now}},
                    )
                    for _offer in offers
                ]
            )

    print(f"Migrated {offer_counter} offers")
    timer.stop("Migrate data")


def handle_store_offer_batch(offers: Sequence[OfferForMigration], context: str):
    timer = Timer()
    timer.start("Save batch")
    logging.info(f"Processing {len(offers)} offers for context {context}")

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
    if False:
        update_denormalized_products(product_ids)
    timer.stop("Update denormalized products")

    timer.start("Update offer pricing")

    timer.stop("Update offer pricing")

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
