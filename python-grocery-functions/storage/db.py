from amp_types.amp_product import MpnOffer
from typing import Iterable, List
from datetime import datetime
from bson.objectid import ObjectId
from pymongo import UpdateOne, InsertOne
from copy import deepcopy
import itertools
import logging
from util.utils import log_traceback

from config.mongo import get_collection
from util.helpers import get_product_uri
from util.enums import select_methods, provenances
from storage.helpers import (
    add_meta_fields_to_scraper_offers,
)
from util.errors import NoHandleConfigError

OVERWRITE_EDIT_LIMIT_DAYS = 365


def chunked_iterable(iterable: Iterable, size):
    it = iter(iterable)
    while True:
        chunk = tuple(itertools.islice(it, size))
        if not chunk:
            break
        yield chunk


def get_update_one(offer, id_field: str = "uri"):
    _offer = deepcopy(offer)
    quantity = offer.get("quantity")
    value = offer.get("value")
    if "quantity" in _offer.keys():
        del _offer["quantity"]
    if "value" in _offer.keys():
        del _offer["value"]
    return UpdateOne(
        {id_field: offer[id_field]},
        {"$set": _offer, "$setOnInsert": {"quantity": quantity, "value": value}},
        upsert=True,
    )


def bulk_upsert(iterable: Iterable, collection_name: str, id_field: str = "uri"):
    print(f"Start saving to Mongo collection: {collection_name}")
    collection = get_collection(collection_name)
    requests = list(map(get_update_one, iterable))
    print("{} items to write".format(len(requests)))
    result = collection.bulk_write(requests)
    return result


def save_promoted_offers(df, collection_name: str):
    collection = get_collection(collection_name)
    requests = list(
        [
            UpdateOne(
                dict(uri=get_product_uri(provenances.SHOPGUN, row.id)),
                {"$set": dict(is_promoted=True, select_method=select_methods.AUTO)},
            )
            for _, row in df.iterrows()
        ]
    )
    return collection.bulk_write(requests)


def save_scraped_products(offers: List[MpnOffer]):
    offer_updates = (add_meta_fields_to_scraper_offers(x) for x in offers)
    result = []
    for chunk in chunked_iterable(offer_updates, 1000):
        try:
            # Can get a write error here, probably due to high write load on Mongo
            result.append(bulk_upsert(chunk, "mpnoffers"))
        except Exception as e:
            logging.error(e)
            log_traceback(e)
    return result


def get_handle_configs(provenance: str):
    print(f"Getting handle config for {provenance}")
    collection = get_collection("handleconfigs")
    result = list(
        x
        for x in collection.find(
            {"provenance": provenance, "status": {"$ne": "disabled"}}
        )
    )
    if len(result) > 0:
        return result
    else:
        raise NoHandleConfigError(
            f"No handleconfig found for provenance: {provenance}."
        )


def get_single_handle_config(provenance: str):
    collection = get_collection("handleconfigs")
    result = collection.find_one(
        {
            "provenance": provenance,
        }
    )
    if result:
        return result
    else:
        raise NoHandleConfigError(
            f"No handleconfig found for provenance: {provenance}."
        )


def get_offers_with_product(
    provenance: str,
    collection_name: str,
    target_collection_name: str,
    relation_collection_name: str,
    limit: int = 0,
) -> Iterable[dict]:
    collection = get_collection(collection_name)
    pipeline = [
        # {"$match": {"provenance": provenance,}},
        {
            "$match": {
                "gtins": {"$ne": None},
            }
        },
        {
            "$addFields": {
                "gtin_list": {"$objectToArray": "$gtins"},
            },
        },
        {
            "$lookup": {
                "from": target_collection_name,
                # "localField": "gtin_list",
                # "foreignField": "gtins",
                "let": {"source_gtin_list": "$gtin_list"},
                "pipeline": [
                    {
                        "$addFields": {
                            "gtin_list": {"$objectToArray": "$gtins"},
                        },
                    },
                    {
                        "$addFields": {
                            "same_gtins": {
                                "$setIntersection": [
                                    "$$source_gtin_list",
                                    "$gtin_list",
                                ]
                            },
                        },
                    },
                    {
                        "$match": {"$expr": {"$gt": ["$same_gtins", []]}},
                    },
                    {
                        "$project": {
                            "_id": 1,
                            "provenance": 1,
                            "same_gtins": 1,
                        }
                    },
                ],
                "as": "gtin_products",
            },
        },
        {
            "$lookup": {
                "from": relation_collection_name,
                "let": {"source_id": "$_id"},
                "pipeline": [
                    {"$match": {"$expr": {"$eq": ["$$source_id", "$offer"]}}},
                    {"$project": {"_id": 1, "product": 1}},
                ],
                # "localField": "_id",
                # "foreignField": "offer",
                "as": "product_relations",
            }
        },
    ]
    if limit > 0:
        pipeline.append({"$limit": limit})
    return collection.aggregate(pipeline)


def get_offers_same_gtin_offers(
    provenance: str,
    collection_name: str,
    limit: int = 0,
) -> Iterable[dict]:
    collection = get_collection(collection_name)
    now = datetime.now()
    pipeline = [
        {
            "$match": {
                "validThrough": {"$gt": now},
                "provenance": provenance,
                "gtins": {"$ne": {}, "$exists": True},
            }
        },
        {"$project": {"gtins": 1, "provenance": 1, "uri": 1}},
        {
            "$addFields": {
                "gtin_list": {"$objectToArray": "$gtins"},
                "source_id": "$_id",
            },
        },
        {
            "$lookup": {
                "from": "mpnoffers",
                "let": {"source_gtin_list": "$gtin_list", "source_id": "$source_id"},
                "pipeline": [
                    {
                        "$match": {
                            "gtins": {"$ne": {}, "$exists": True},
                            "$expr": {"$ne": ["$$source_id", "$_id"]},
                        },
                    },
                    {
                        "$addFields": {
                            "gtin_list": {"$objectToArray": "$gtins"},
                        },
                    },
                    {
                        "$addFields": {
                            "same_gtins": {
                                "$setIntersection": [
                                    "$$source_gtin_list",
                                    "$gtin_list",
                                ]
                            },
                        },
                    },
                    {
                        "$match": {
                            "same_gtins": {"$exists": True},
                            "$expr": {"$gt": ["$same_gtins", []]},
                        },
                    },
                    {
                        "$project": {
                            "_id": 1,
                            "provenance": 1,
                            "same_gtins": 1,
                            "uri": 1,
                        }
                    },
                ],
                "as": "gtin_products",
            },
        },
        {"$match": {"gtin_products": {"$not": {"$size": 0}}}},
    ]
    if limit > 0:
        pipeline.append({"$limit": limit})
    return collection.aggregate(pipeline)


def get_update_product_with_offer(offer, product_relation) -> UpdateOne:
    return UpdateOne(
        {"_id": product_relation["product"]},
        {"$set": {"updatedAt": datetime.now()}},
    )


def get_insert_product_has_offer(
    offer_id: ObjectId, product_id: ObjectId, reason: str
) -> InsertOne:
    now = datetime.now()
    return InsertOne(
        {
            "offer": offer_id,
            "product": product_id,
            "updatedAt": now,
            "createdAt": now,
            "type": "auto",
            "reason": reason,
        }
    )


def get_new_product_from_offer(offer) -> dict:
    result = {**offer}
    del result["_id"]
    del result["product_relations"]
    del result["gtin_products"]
    return result


def get_insert_product_with_offer(offer) -> List[InsertOne]:
    return InsertOne({**get_new_product_from_offer(offer), "offers": [offer["_id"]]})


def store_handle_run(handle_run_config):
    collection = get_collection("handleruns")
    return collection.insert_one(handle_run_config)


def save_book_offers(offers):
    return bulk_upsert(offers, "bookoffers")
