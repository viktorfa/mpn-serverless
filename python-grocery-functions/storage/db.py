from typing import Iterable
from datetime import datetime
from datetime import timedelta

from pymongo import UpdateOne

from config.mongo import get_collection
from util.helpers import get_product_uri
from util.enums import select_methods, provenances
from storage.helpers import meta_fields_result_to_dict, remove_protected_fields

OVERWRITE_EDIT_LIMIT_DAYS = 365


def get_update_one(product, id_field: str = "uri"):
    return UpdateOne({id_field: product[id_field]}, {"$set": product}, upsert=True)


def bulk_upsert(iterable: Iterable, collection_name: str, id_field: str = "uri"):
    print("Start saving to Mongo collection: {}".format(collection_name))
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


def save_scraped_products(products: Iterable, offers_collection_name: str):
    last_update_limit = datetime.utcnow() - timedelta(OVERWRITE_EDIT_LIMIT_DAYS)
    meta_fields_collection = get_collection(f"{offers_collection_name}meta")
    meta_fields = meta_fields_collection.find(
        dict(updatedAt={"$gt": last_update_limit})
    )
    uri_field_dict = meta_fields_result_to_dict(meta_fields)
    return bulk_upsert(
        remove_protected_fields(products, uri_field_dict), offers_collection_name, "uri"
    )
