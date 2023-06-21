import json
import aws_config
import logging
import pydash
from typing import Iterable, TypedDict
from datetime import datetime
import time
from pymongo import UpdateOne
from storage.db import get_collection, yield_rows
from amp_types.amp_product import MpnOffer
from util.logging import configure_lambda_logging
from bson import ObjectId
from scraper_feed.helpers import is_valid_ean, is_valid_nobb


configure_lambda_logging()


class SnsMessage(TypedDict):
    collection_name: str
    scrape_time: str
    provenance: str


def handle_offer_relations_sns(event, context):
    aws_config.lambda_context = context
    logging.info(json.dumps(event))
    sns_message: SnsMessage = json.loads(event["Records"][0]["Sns"]["Message"])
    provenance = sns_message["provenance"]
    market = sns_message["market"]
    scrape_batch_id = sns_message.get("scrapeBatchId")

    if scrape_batch_id:
        return handle_offer_relations_with_scrape_batch(scrape_batch_id, market)
    elif provenance:
        return handle_offer_relations_with_provenance(provenance, market)


def handle_offer_relations_trigger(event, context):
    aws_config.lambda_context = context
    logging.info(json.dumps(event))
    provenance = event["provenance"]
    scrape_batch_id = event.get("scrapeBatchId")
    market = event["market"]

    if scrape_batch_id:
        return handle_offer_relations_with_scrape_batch(scrape_batch_id, market)
    elif provenance:
        return handle_offer_relations_with_provenance(provenance, market)


def handle_offer_relations_with_provenance(provenance: str, market: str):
    logging.warn("Handling offer relations with provenance")
    offer_filter = {
        "provenance": provenance,
        "isRecent": True,
        "validThrough": {"$gt": datetime.now()},
    }
    return handle_offer_relations(offer_filter, market)


def handle_offer_relations_with_scrape_batch(scrape_batch_id: str, market: str):
    offer_filter = {
        "scrapeBatchId": scrape_batch_id,
    }

    return handle_offer_relations(offer_filter, market)


def handle_offer_relations(offer_filter, market):
    timer_start = time.perf_counter_ns()
    CHUNK_SIZE = 1000
    uris = []

    offers_collection = get_collection("mpnoffers")
    offers_cursor = offers_collection.find(
        offer_filter,
        {
            "uri": 1,
            "gtins": 1,
            "title": 1,
            "description": 1,
            "shortDescription": 1,
            "subtitle": 1,
            "imageUrl": 1,
            "mpnCategories": 1,
            "mpnNutrition": 1,
            "mpnProperties": 1,
            "mpnIngredients": 1,
            "quantity": 1,
            "brand": 1,
            "brandKey": 1,
        },
        batch_size=CHUNK_SIZE,
    )
    chunks = yield_rows(offers_cursor, CHUNK_SIZE)
    result = []
    logging.info(f"Finish setup {int((time.perf_counter_ns() - timer_start) / 1e6)} ms")
    timer_start = time.perf_counter_ns()
    for chunk in chunks:
        chunk_list = list(chunk)
        for x in chunk_list:
            uris.append(x["uri"])
        insert_result = handle_offer_relations_chunk(chunk_list, market=market)
        result.append(insert_result)
    logging.info(
        f"Finish match offers {int((time.perf_counter_ns() - timer_start) / 1e6)} ms"
    )
    timer_start = time.perf_counter_ns()
    rel_collection = get_collection("offerbirelations")
    update_view_response = rel_collection.aggregate(
        [
            {
                "$match": {
                    "offerSet": {"$in": uris},
                    "relationType": "identical",
                    "isMerged": {"$ne": True},
                }
            },
            # {"$limit": 1000},
            {
                "$lookup": {
                    "from": "mpnoffers",
                    "localField": "offerSet",
                    "foreignField": "uri",
                    "as": "offers",
                    "let": {"size": "$quantity.size.standard.max"},
                    "pipeline": [
                        {"$match": {"isRecent": True, "market": market}},
                        {
                            "$project": {
                                "uri": 1,
                                "pricing": 1,
                                "siteCollection": 1,
                                "market": 1,
                                "href": 1,
                                "ahref": 1,
                                "vendorKey": 1,
                                "dealerKey": 1,
                                "validThrough": 1,
                                "isRecent": 1,
                                "mpnStock": 1,
                                "pageviews": 1,
                                "isPartner": 1,
                            }
                        },
                        {
                            "$set": {
                                "value": {
                                    "$cond": [
                                        {"$gt": ["$$size", 0]},
                                        {
                                            "$divide": [
                                                "$pricing.price",
                                                "$$size",
                                            ],
                                        },
                                        None,
                                    ],
                                }
                            },
                        },
                    ],
                }
            },
            {
                "$set": {
                    "priceMin": {"$min": "$offers.pricing.price"},
                    "priceMax": {"$max": "$offers.pricing.price"},
                    "valueMin": {"$min": "$offers.value"},
                    "valueMax": {"$max": "$offers.value"},
                    "pageviews": {"$sum": "$offers.pageviews"},
                    "title": f"$m:{market}.title",
                    "subtitle": f"$m:{market}.subtitle",
                    "shortDescription": f"$m:{market}.shortDescription",
                    "description": f"$m:{market}.description",
                    "mpnCategories": f"$m:{market}.mpnCategories",
                }
            },
            {"$unset": [f"m:{market}"]},
            {
                "$merge": {
                    "into": f"relations_with_offers_{market}",
                    "on": "_id",
                    "whenMatched": "replace",
                    "whenNotMatched": "insert",
                }
            },
        ]
    )
    logging.info(
        f"Finish update view {int((time.perf_counter_ns() - timer_start) / 1e6)} ms"
    )
    timer_start = time.perf_counter_ns()
    # market_rel_collection = get_collection(f"relations_with_offers_{market}")

    return json.dumps(update_view_response, default=str)


def handle_offer_relations_chunk(offers: Iterable[MpnOffer], market):
    relations_collection = get_collection("offerbirelations")
    gtins = []
    uris = []
    now = datetime.now()
    rel_fields = [
        "quantity",
        "brand",
        "brandKey",
        "mpnNutrition",
        "mpnIngredients",
        "mpnProperties",
        "imageUrl",
    ]
    rel_market_fields = [
        "title",
        "subtitle",
        "shortDescription",
        "description",
        "mpnCategories",
    ]
    for offer in offers:
        uris.append(offer["uri"])
        for key, value in offer.get("gtins", {}).items():
            if key in ("gtin13", "ean") and is_valid_ean(str(value)):
                gtins.append(f"ean:{value}")
            elif key == "nobb" and is_valid_nobb(str(value)):
                gtins.append(f"{key}:{value}")

    relations_projection = {
        "offerSet": 1,
        "gtins": 1,
        "title": 1,
        "subtitle": 1,
        "shortDescription": 1,
        "description": 1,
        "imageUrl": 1,
        "brand": 1,
        "brandKey": 1,
        "mpnIngredients": 1,
        "mpnProperties": 1,
        "mpnNutrition": 1,
        "quantity": 1,
        ":manual": 1,
        f"m:{market}": 1,
    }
    existing_uri_relations = relations_collection.find(
        {
            "relationType": "identical",
            "isMerged": {"$ne": True},
            "offerSet": {"$in": uris},
        },
        relations_projection,
    )
    existing_gtins_relations = relations_collection.find(
        {
            "relationType": "identical",
            "isMerged": {"$ne": True},
            "gtins": {"$in": gtins},
            "gtins.0": {"$exists": True},
        },
        relations_projection,
    )

    relations_map = {}
    for rel in existing_uri_relations:
        for uri in rel["offerSet"]:
            rels = relations_map.get(uri)
            if rels:
                rels.append(rel)
            else:
                relations_map[uri] = [rel]
        for gtin in rel.get("gtins", []):
            rels = relations_map.get(gtin)
            if rels:
                rels.append(rel)
            else:
                relations_map[gtin] = [rel]
    for rel in existing_gtins_relations:
        for uri in rel["offerSet"]:
            rels = relations_map.get(uri)
            if rels:
                rels.append(rel)
            else:
                relations_map[uri] = [rel]
        for gtin in rel.get("gtins", []):
            rels = relations_map.get(gtin)
            if rels:
                rels.append(rel)
            else:
                relations_map[gtin] = [rel]

    merge_operations = []
    operations = []

    for offer in offers:
        mongo_safe_uri = offer["uri"].replace(".", "\uff0E")
        rels = [*relations_map.get(offer["uri"], [])]
        offer_gtins = []
        for key, value in offer.get("gtins", {}).items():
            if key in ("gtin13", "ean") and is_valid_ean(str(value)):
                offer_gtins.append(f"ean:{value}")
            elif key == "nobb" and is_valid_nobb(str(value)):
                offer_gtins.append(f"{key}:{value}")
        for gtin in offer_gtins:
            gtin_rels = relations_map.get(gtin)
            if gtin_rels:
                if rels:
                    rels.extend(gtin_rels)
                else:
                    rels = [*gtin_rels]

        if rels:
            # Choose the one with most offers in the set, and if equal, the one without the offer itself in the set
            rel_to_use = sorted(
                rels,
                key=lambda x: (len(x["offerSet"]), offer["uri"] not in x["offerSet"]),
                reverse=True,
            )[0]
            other_rels = list([x for x in rels if x["_id"] != rel_to_use["_id"]])

            rel_info = get_relation_info(offer, rels, market=market)

            other_uris = []

            for rel in other_rels:
                other_uris.extend(rel["offerSet"])

            operations.append(
                UpdateOne(
                    {"_id": ObjectId(rel_to_use["_id"])},
                    {
                        "$addToSet": {
                            "gtins": {"$each": offer_gtins},
                            "offerSet": {"$each": [*other_uris, offer["uri"]]},
                        },
                        "$set": {
                            "updatedAt": now,
                            f"m:{market}": pydash.pick(
                                rel_info["rel"],
                                rel_market_fields,
                            ),
                            # f"p:{provenance}": rel_info["offer"],
                            **pydash.pick(
                                rel_info["rel"],
                                rel_fields,
                            ),
                        },
                    },
                )
            )
            for rel in other_rels:
                merge_operations.append(
                    UpdateOne(
                        {"_id": rel["_id"]},
                        {
                            "$set": {
                                "mergedTo": ObjectId(rel_to_use["_id"]),
                                "isMerged": True,
                                "updatedAt": now,
                                f"offerSetMeta.{mongo_safe_uri}.auto": {
                                    "method": "auto",
                                    "reason": "merged",
                                    "updatedAt": now,
                                },
                            },
                        },
                    )
                )
        else:
            rel_info = get_relation_info(offer, [], market=market)
            operations.append(
                UpdateOne(
                    {"relationType": "identical", "offerSet": offer["uri"]},
                    {
                        "$setOnInsert": {
                            "relationType": "identical",
                            "createdAt": now,
                            "updatedAt": now,
                            "offerSet": [offer["uri"]],
                            f"offerSetMeta.{mongo_safe_uri}.auto": {
                                "method": "auto",
                                "reason": "initial",
                                "updatedAt": now,
                            },
                            "gtins": offer_gtins,
                            f"m:{market}": pydash.pick(
                                rel_info["rel"],
                                rel_market_fields,
                            ),
                            # f"p:{provenance}": rel_info["offer"],
                            **pydash.pick(
                                rel_info["rel"],
                                rel_fields,
                            ),
                        },
                    },
                    upsert=True,
                )
            )

    try:
        if len(merge_operations) > 0:
            relations_collection.bulk_write(merge_operations, ordered=False)

        if len(operations) > 0:
            return pydash.pick(
                relations_collection.bulk_write(
                    operations, ordered=False
                ).bulk_api_result,
                ["nInserted", "nUpserted", "nMatched", "nModified", "nRemoved"],
            )
    except Exception as e:
        logging.error(e)
    return None


def get_relation_info(offer, relations, market):
    offer_result = {
        "title": offer["title"],
        "subtitle": offer.get("subtitle"),
        "shortDescription": offer.get("shortDescription"),
        "description": offer.get("description"),
        "mpnCategories": offer.get("mpnCategories", []),
        "mpnNutrition": offer.get("mpnNutrition", {}),
        "mpnIngredients": offer.get("mpnIngredients", {}),
        "mpnProperties": offer.get("mpnProperties", {}),
        "imageUrl": offer.get("imageUrl"),
        "quantity": offer["quantity"],
        "brand": offer.get("brand"),
        "brandKey": offer.get("brandKey"),
    }
    rel_result = {
        "title": offer["title"],
        "subtitle": offer.get("subtitle"),
        "shortDescription": offer.get("shortDescription"),
        "description": offer.get("description"),
        "mpnCategories": offer.get("mpnCategories", []),
        "mpnNutrition": offer.get("mpnNutrition", {}),
        "mpnIngredients": offer.get("mpnIngredients", {}),
        "mpnProperties": offer.get("mpnProperties", {}),
        "imageUrl": offer.get("imageUrl"),
        "quantity": offer["quantity"],
        "brand": offer.get("brand"),
        "brandKey": offer.get("brandKey"),
    }

    standard_quantities = []

    for rel in relations:
        rel_title = get_from_rel(rel, "title", market)
        if rel_title:
            rel_result["title"] = rel_title
        rel_subtitle = get_from_rel(rel, "subtitle", market)
        if rel_subtitle:
            rel_result["subtitle"] = rel_subtitle
        rel_shortDescription = get_from_rel(rel, "shortDescription", market)
        if rel_shortDescription:
            rel_result["shortDescription"] = rel_shortDescription
        rel_description = get_from_rel(rel, "description", market)
        if rel_description:
            rel_result["description"] = rel_description
        rel_brand = get_from_rel(rel, "brand")
        if rel_brand:
            rel_result["brand"] = rel_brand
        rel_brandKey = get_from_rel(rel, "brandKey")
        if rel_brandKey:
            rel_result["brandKey"] = rel_brandKey
        rel_imageUrl = get_from_rel(rel, "imageUrl")
        if rel_imageUrl:
            rel_result["imageUrl"] = rel_imageUrl
        rel_mpnNutrition = get_from_rel(rel, "mpnNutrition")
        if rel_mpnNutrition and len(list(rel_mpnNutrition.keys())) >= len(
            list(rel_result.get("mpnNutrition", {}).keys())
        ):
            rel_result["mpnNutrition"] = rel_mpnNutrition
        rel_mpnProperties = get_from_rel(rel, "mpnProperties")
        if rel_mpnProperties and len(list(rel_mpnProperties.keys())) >= len(
            list(rel_result.get("mpnProperties", {}).keys())
        ):
            rel_result["mpnProperties"] = rel_mpnProperties
        rel_mpnIngredients = get_from_rel(rel, "mpnIngredients")
        if rel_mpnIngredients and len(
            list(rel_mpnIngredients.get("ingredients", {}).keys())
        ) >= len(
            list(
                (rel_result.get("mpnIngredients", {}) or {})
                .get("ingredients", {})
                .keys()
            )
        ):
            rel_result["mpnIngredients"] = rel_mpnIngredients
        rel_mpnCategories = get_from_rel(rel, "mpnCategories", market)
        if rel_mpnCategories and len(rel_mpnCategories) >= len(
            rel_result.get("mpnCategories", []) or []
        ):
            rel_result["mpnCategories"] = rel_mpnCategories
        rel_quantity = get_from_rel(rel, "quantity")
        rel_standard_quantity = pydash.get(rel_quantity, "size.standard.max")
        if rel_standard_quantity:
            rel_result["quantity"] = rel_quantity

    return {"offer": offer_result, "rel": rel_result}


def is_null_or_empty(value):
    return value == {} or value == [] or not value


def get_from_rel(rel: dict, key: str, market: str = None):
    result = None
    if market:
        result = pydash.get(rel, [f"m:{market}", ":manual", key])
        if is_null_or_empty(result):
            result = pydash.get(rel, [f"m:{market}", key])
    else:
        result = pydash.get(rel, [":manual", key])
        if is_null_or_empty(result):
            result = pydash.get(rel, key)
    if is_null_or_empty(result):
        return None
    else:
        return result
