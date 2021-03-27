import json
from bson import json_util
import logging
from pymongo import UpdateOne, InsertOne
from util.utils import log_traceback

import boto3
from typing import Iterable, TypedDict, List
from pymongo.results import InsertManyResult
from datetime import datetime

from offer_feed.process_offers import MpnOfferWithProduct, OfferConfig, process_offers

from storage.db import (
    get_collection,
    get_insert_product_has_offer,
    get_offers_with_product,
    get_offers_same_gtin_offers,
)

import sentry_sdk
from sentry_sdk.integrations.aws_lambda import AwsLambdaIntegration

sentry_sdk.init(
    integrations=[AwsLambdaIntegration()],
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()
logging.getLogger("botocore").setLevel(logging.WARNING)
logging.getLogger("boto3").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logger.setLevel(logging.DEBUG)
s3 = boto3.client("s3")


class SnsMessage(TypedDict):
    collection_name: str
    scrape_time: str
    provenance: str


def handle_offers(
    offers_list: Iterable[Iterable[dict]],
):
    """
    Adds offers with the same gtins to be identical."""
    operations = []
    now = datetime.now()
    for offers in offers_list:
        all_uris = list(set(x["uri"] for x in offers))

        upsert_operation1 = UpdateOne(
            {
                "relationType": "identical",
                "offerSet": {"$in": all_uris},
            },
            {
                "$setOnInsert": {
                    "createdAt": now,
                    "updatedAt": now,
                    "relationType": "identical",
                    "offerSet": all_uris,
                },
            },
            upsert=True,
        )
        operations.append(upsert_operation1)
        upsert_operation2 = UpdateOne(
            {
                "relationType": "identical",
                "offerSet": {"$in": all_uris},
            },
            {
                "$set": {"updatedAt": now},
                "$addToSet": {
                    "offerSet": {"$each": all_uris},
                },
            },
            upsert=False,
        )
        operations.append(upsert_operation2)

    print(f"{len(operations)} operations to add identical offers")

    collection = get_collection("offerbirelations")

    bulk_write_result = collection.bulk_write(operations, ordered=True)

    return {"message": json_util.dumps(bulk_write_result.bulk_api_result)}


def get_offers_list_for_gtins(provenance: str) -> List[List[dict]]:
    now = datetime.now()
    collection = get_collection("mpnoffers")
    scraped_offers = collection.find(
        {
            "provenance": provenance,
            "validThrough": {"$gt": now},
            "gtins": {"$exists": True, "$ne": {}},
        },
        {"uri": 1, "provenance": 1, "gtins": 1, "dealer": 1},
    )
    all_offers = collection.find(
        {"validThrough": {"$gt": now}, "gtins": {"$exists": True, "$ne": {}}},
        {"uri": 1, "provenance": 1, "gtins": 1, "dealer": 1},
    )
    gtin_offer_map = {}
    for offer in all_offers:
        for gtin_key, gtin_value in offer.get("gtins", {}).items():
            gtin = f"{gtin_key}_{gtin_value}"
            if gtin in gtin_offer_map.keys():
                gtin_offer_map[gtin].append(offer)
            else:
                gtin_offer_map[gtin] = [offer]

    offers_list = []

    for offer in scraped_offers:
        for gtin_key, gtin_value in offer.get("gtins", {}).items():
            gtin = f"{gtin_key}_{gtin_value}"
            # Remove self from identical offers
            identical_offers = list(
                (x for x in gtin_offer_map.get(gtin, []) if x["uri"] != offer["uri"])
            )
            if len(identical_offers) > 0:
                offers_list.append([offer, *identical_offers])

    print(f"gtins found: {len(gtin_offer_map.keys())}")
    return offers_list


def offer_feed_sns(event, context):
    logging.info("event")
    logging.info(event)
    sns_message: SnsMessage = json.loads(event["Records"][0]["Sns"]["Message"])
    provenance = sns_message["provenance"]
    try:
        offers_list = get_offers_list_for_gtins(provenance)
        if len(offers_list) > 0:
            return handle_offers(offers_list)
        else:
            return {"message": f"No offers with gtins for {provenance}"}
    except Exception as e:
        logging.error(e)
        log_traceback(e)
    return {"message": "no cannot"}


def offer_feed_trigger(event, context):
    provenance = event["provenance"]
    try:
        offers_list = get_offers_list_for_gtins(provenance)
        if len(offers_list) > 0:
            return handle_offers(offers_list)
        else:
            return {"message": f"No offers with gtins for {provenance}"}
    except Exception as e:
        logging.error(e)
        log_traceback(e)
    return {"message": "no cannot"}
