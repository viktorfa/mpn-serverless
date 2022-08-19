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
    return UpdateOne(
        {id_field: offer[id_field]},
        {"$set": offer},
        upsert=True,
    )


def bulk_upsert(iterable: Iterable, collection_name: str, id_field: str = "uri"):
    print(f"Start saving to Mongo collection: {collection_name}")
    collection = get_collection(collection_name)
    requests = list(map(get_update_one, iterable))
    print("{} items to write".format(len(requests)))
    result = collection.bulk_write(requests)
    return result


def save_scraped_offers(offers: List[MpnOffer]):
    result = []
    for chunk in chunked_iterable(offers, 1000):
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


def store_handle_run(handle_run_config):
    collection = get_collection("handleruns")
    return collection.insert_one(handle_run_config)


def save_book_offers(offers):
    return bulk_upsert(offers, "bookoffers")
