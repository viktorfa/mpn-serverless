from datetime import datetime
from pprint import pprint
from time import time
import json

import pydash

from util.helpers import get_sns_message
from ml import get_model, get_most_similar_offers_of_df, get_most_similar_offers
from config.mongo import get_collection
from storage.db import save_similar_offers
from storage.s3 import save_model_to_s3, load_model_from_s3

N_HIGHEST = 32
OFFER_LIMIT = 2 ** 18
CHUNK_SIZE = 2 ** 10


def create_models(event, context):
    try:
        event_message = get_sns_message(event)
    except TypeError:
        event_message = event
    collection_name = event_message["collection_name"]
    offer_limit = event_message.get("offerLimit", OFFER_LIMIT)
    n_highest = event_message.get("nHighest", N_HIGHEST)

    collection = get_collection(collection_name)
    now = datetime.now()
    start_time = time()
    print(f"Fetching up to {OFFER_LIMIT} offers from db.")
    offers = collection.find({"validThrough": {"$gt": now}}, limit=offer_limit,)
    offers_list = list(offers)
    print(f"Time spent: {time() - start_time} s.")
    model = get_model(offers_list)
    result = save_model_to_s3(model, collection_name)
    return {"result": result}


def add_similar_offers(event, context):
    try:
        event_message = get_sns_message(event)
    except TypeError:
        event_message = event
    collection_name = event_message["collection_name"]
    offer_limit = event_message.get("offerLimit", OFFER_LIMIT)
    n_highest = event_message.get("nHighest", N_HIGHEST)
    provenance = event_message.get("provenance")

    collection = get_collection(collection_name)
    offer_limit = event.get("offerLimit", OFFER_LIMIT)
    n_highest = event.get("nHighest", N_HIGHEST)
    model = load_model_from_s3(collection_name)
    now = datetime.now()
    mongo_filter = {"validThrough": {"$gt": now}}
    if provenance:
        mongo_filter["provenance"] = provenance
    offers = collection.find(mongo_filter, limit=offer_limit,)
    offers_list = list(offers)
    result = list(
        add_similar_offers_to_batch(batch, model, collection_name, n_highest)
        for batch in pydash.chunk(offers_list, CHUNK_SIZE)
    )
    return {"event": event, "result": result}


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
