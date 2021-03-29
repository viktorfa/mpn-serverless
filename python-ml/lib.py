import math
from datetime import datetime
from time import time
from typing import Iterable

from bson import json_util
from pymongo import UpdateOne
from pprint import pprint
import pydash

from ml import get_model, get_most_similar_offers
from config.mongo import get_collection
from storage.db import save_similar_offers
from storage.s3 import save_model_to_s3, load_model_from_s3
from util.helpers import  get_real_quantity

CHUNK_SIZE = 2 ** 10
MONGO_PROJECTION = {
    "validThrough": 1,
    "dealer": 1,
    "title": 1,
    "subtitle": 1,
    "shortDescription": 1,
    "categories": 1,
    "uri": 1,
    "quantity": 1,
    "pricing": 1,
}


def get_offers_by_uris(uris):
    collection = get_collection("mpnoffers")
    return collection.find({"uri": {"$in": uris}}, MONGO_PROJECTION)


def create_models(collection_name, offer_limit):
    collection = get_collection("mpnoffers")
    now = datetime.now()
    start_time = time()
    print(f"Fetching up to {OFFER_LIMIT} offers from db.")
    offers = collection.aggregate(
        [
            {"$match": {"validThrough": {"$gt": now}, "siteCollection": collection_name}},
            {"$project": MONGO_PROJECTION},
            {"$limit": 2 ** 17},
        ],
        allowDiskUse=True,
    )
    offers_list = list(offers)
    print(f"Time spent: {time() - start_time} s.")
    print(f"Got {len(offers_list)} after filter")
    model = get_model(offers_list)
    result = save_model_to_s3(model, collection_name)

    return result


def add_similar_offers(collection_name, offer_limit, n_highest, provenance=None):
    collection = get_collection("mpnoffers")
    model = load_model_from_s3(collection_name)
    now = datetime.now()
    mongo_filter = {"validThrough": {"$gt": now}, "siteCollection": collection_name}
    if provenance:
        mongo_filter["provenance"] = provenance
    offers = collection.find(
        mongo_filter, projection=MONGO_PROJECTION, limit=offer_limit,
    )
    offers_list = list(offers)
    result = list(
        add_similar_offers_to_batch(batch, model, collection_name, n_highest)
        for batch in pydash.chunk(offers_list, CHUNK_SIZE)
    )
    return result

def add_identical_offers(collection_name, offer_limit, n_highest, provenance=None):
    collection = get_collection("mpnoffers")
    model = load_model_from_s3(collection_name)
    now = datetime.now()
    mongo_filter = {"validThrough": {"$gt": now}, "siteCollection": collection_name}
    if provenance:
        mongo_filter["provenance"] = provenance
    offers = collection.find(
        mongo_filter, projection=MONGO_PROJECTION, limit=offer_limit,
    )
    offers_list = list(offers)
    result = list(
        add_identical_offers_to_batch(batch, model, collection_name, n_highest)
        for batch in pydash.chunk(offers_list, CHUNK_SIZE)
    )
    return result


def add_similar_offers_to_batch(
    offers: list, model: dict, collection_name: str, n_highest: int = 32
):
    index_to_uri_map = model["index_to_uri_map"]

    result = get_most_similar_offers(
        offers, model["fitted_pipeline"], model["tf_idf_matrix"], n_highest,
    )
    print("Mapping similar offers.")
    start_time = time()
    for i, ranking in enumerate(result):
        offer_uri = index_to_uri_map[i]
        ranking_with_uris = list(
            {**x, "uri": index_to_uri_map[x["idx"]]} for x in ranking
        )
        result[i] = ranking_with_uris

    updates = []
    for i, ranking in enumerate(result):
        offer = offers[i]
        most_similar_offers = list(
            {"uri": index_to_uri_map[similar["idx"]], "score": similar["score"]}
            for similar in ranking
        )
        updates.append(dict(uri=offer["uri"], similarOffers=most_similar_offers))
    print(f"Time spent: {time() - start_time} s.")
    print("Updating offers.")
    start_time = time()
    result = save_similar_offers(updates, collection_name)
    print(f"Time spent: {time() - start_time} s.")

    # Use this code if you don't use the http event with the LAMBDA-PROXY
    # integration
    return result.bulk_api_result

def add_identical_offers_to_batch(
    offers: list, model: dict, collection_name: str, n_highest: int = 32
):
    index_to_uri_map = model["index_to_uri_map"]

    result = get_most_similar_offers(
        offers, model["fitted_pipeline"], model["tf_idf_matrix"], n_highest+1,
    )
    print("Mapping similar offers.")
    start_time = time()
    for i, ranking in enumerate(result):
        offer_uri = index_to_uri_map[i]
        ranking_with_uris = list(
            {**x, "uri": index_to_uri_map[x["idx"]]} for x in ranking
        )
        result[i] = ranking_with_uris

    updates = []
    for i, ranking in enumerate(result):
        offer = offers[i]
        offer_namespace = offer["uri"].split(":")[0]
        most_similar_offers_hits = list(
            {"uri": index_to_uri_map[similar["idx"]], "score": similar["score"]}
            for similar in ranking if index_to_uri_map[similar["idx"]].split(":")[0] != offer_namespace and similar["score"] > 0.7
        )
        print(f"{offer['title']} {offer['uri']}")
        pprint(most_similar_offers_hits)

        if len(most_similar_offers_hits) == 0:
            continue


        most_similar_offers = get_offers_by_uris(list(x["uri"] for x in most_similar_offers_hits))
        most_similar_offers = list({**x, "score": next(y for y in most_similar_offers_hits if y["uri"] == x["uri"])["score"]} for x in most_similar_offers)
        offer_quantity = get_real_quantity(offer)
        if not offer_quantity:
            continue
        most_similar_offers_result = []
        for similar_offer in most_similar_offers:
            similar_quantity = get_real_quantity(similar_offer)
            print(f"offer_quantity: {offer_quantity}, similar_quantity: {similar_quantity}")
            # Filter offers with too big price difference, as it's probably a quantity parsing error.
            try:
                offer_price = offer["pricing"]["price"]
                similar_offer_price = similar_offer["pricing"]["price"]
                price_difference = abs(offer_price - similar_offer_price)
                price_ratio = price_difference / max(offer_price, similar_offer_price)
                print(f"price_ratio: {price_ratio}")
                if price_ratio > 0.6:
                    continue
            except Exception:
                print("Could not calculate price difference")
                continue
            if offer_quantity and offer_quantity == similar_quantity:
                most_similar_offers_result.append(similar_offer)

        if len(most_similar_offers_result) == 0:
            print("No offers with same quantity")
            continue
        print(f"{len(most_similar_offers_result)} offers with same quantity")

        print(pydash.pick(offer, ["title", "subtitle", "brand", "uri", "shortDescription"]))
        pprint(list(pydash.pick(x, ["title", "subtitle", "brand", "uri", "shortDescription", "score"]) for x in most_similar_offers_result))

        most_similar_offers_result = sorted(most_similar_offers_result, key=lambda x: x["score"], reverse=True)
        most_similar_offers_result = pydash.uniq_by(most_similar_offers_result, lambda x: x["uri"])
        # Only add one offer, as false positives are common
        most_similar_offer  = most_similar_offers_result[0]

        print("Using:")
        pprint(pydash.pick(most_similar_offer, ["title", "subtitle", "brand", "uri", "shortDescription", "score"]))

        
        #updates.append(dict(uri=offer["uri"], similarOffers=list(pydash.pick(x, ["uri", "score"]) for x in most_similar_offers_result)))
        if len(most_similar_offers) > 0:
            updates.append([offer["uri"], most_similar_offer["uri"]])
    print(f"Time spent: {time() - start_time} s.")

    if len(updates) > 0:
        print("Updating offers.")
        start_time = time()
        result = add_identical_offer_relations(updates)
        print(f"Time spent: {time() - start_time} s.")

        return json_util.dumps(result.bulk_api_result)
    else:
        return {"message": "No identical offers found"}



def add_identical_offer_relations(uris_lists: Iterable[Iterable[str]]):
    """
    Adds offers with the same gtins to be identical."""
    operations = []
    now = datetime.now()
    for uris in uris_lists:
        upsert_operation1 = UpdateOne(
            {
                "relationType": "identical",
                "offerSet": {"$in": uris},
            },
            {
                "$setOnInsert": {
                    "createdAt": now,
                    "updatedAt": now,
                    "relationType": "identical",
                    "offerSet": uris,
                    "selectMethod": "auto"
                },
            },
            upsert=True,
        )
        operations.append(upsert_operation1)
        upsert_operation2 = UpdateOne(
            {
                "relationType": "identical",
                "offerSet": {"$in": uris},
            },
            {
                "$set": {"updatedAt": now},
                "$addToSet": {
                    "offerSet": {"$each": uris},
                },
            },
            upsert=False,
        )
        operations.append(upsert_operation2)

    print(f"{len(operations)} operations to add identical offers")

    collection = get_collection("offerbirelations")

    bulk_write_result = collection.bulk_write(operations, ordered=True)

    return bulk_write_result