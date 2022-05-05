from offer_feed.categories import handle_offers_for_categories
from parsing.quantity_extraction import get_value_from_quantity, standardize_quantity

import json
import pydash
from bson import json_util
import logging
import os
from pymongo import UpdateOne
from util.utils import log_traceback

import aws_config
import boto3
from typing import Iterable, TypedDict, List
from datetime import datetime


from storage.db import get_collection

import sentry_sdk
from sentry_sdk.integrations.aws_lambda import AwsLambdaIntegration


if not os.getenv("IS_LOCAL"):
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


def handle_offers_for_meta(
    offers: Iterable[dict],
):
    """
    Updates offers according to meta fields."""
    operations = []

    for offer in offers:
        manual_quantity = pydash.get(offer, ["meta", "quantity", "manual", "value"])
        auto_quantity = pydash.get(offer, ["meta", "quantity", "auto", "value"])
        if manual_quantity and manual_quantity["size"]["amount"]["min"]:
            value = get_value_from_quantity(offer, manual_quantity["size"])
            new_offer = {"quantity": manual_quantity, "value": {"size": value}}
            new_offer = standardize_quantity(new_offer)
            operations.append(
                UpdateOne(
                    {"uri": offer["uri"]},
                    {
                        "$set": {
                            "quantity": new_offer["quantity"],
                            "value.size": new_offer["value"]["size"],
                        }
                    },
                )
            )
        elif auto_quantity and auto_quantity["size"]["amount"]["min"]:
            value = get_value_from_quantity(offer, auto_quantity["size"])
            new_offer = {"quantity": auto_quantity, "value": {"size": value}}
            new_offer = standardize_quantity(new_offer)
            operations.append(
                UpdateOne(
                    {"uri": offer["uri"]},
                    {
                        "$set": {
                            "quantity": new_offer["quantity"],
                            "value.size": new_offer["value"]["size"],
                        }
                    },
                )
            )

    collection = get_collection("mpnoffers")

    logging.info(f"Updating quantity of {len(operations)} offers")

    bulk_write_result = collection.bulk_write(operations)

    return {"message": json_util.dumps(bulk_write_result.bulk_api_result)}


def handle_offers(
    offers_list: Iterable[Iterable[dict]],
):
    """
    Adds offers with the same gtins to be identical."""
    logging.info("handle_offers")
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

    logging.info(f"{len(operations)} operations to add identical offers")

    collection = get_collection("offerbirelations")

    bulk_write_result = collection.bulk_write(operations, ordered=True)

    return {"message": json_util.dumps(bulk_write_result.bulk_api_result)}


def get_scraped_offers(provenance: str) -> List[dict]:
    now = datetime.now()
    collection = get_collection("mpnoffers")
    scraped_offers = collection.find(
        {
            "provenance": provenance,
            "validThrough": {"$gt": now},
            "$or": [
                {"meta.quantity.auto.value.size.amount": {"$exists": True}},
                {"meta.quantity.manual.value.size.amount": {"$exists": True}},
            ],
        },
        {"uri": 1, "meta": 1, "quantity": 1, "pricing": 1},
    )
    return list(scraped_offers)


def get_offers_list_for_gtins(provenance: str) -> List[List[dict]]:
    logging.info(f"get_offers_list_for_gtins for provenance {provenance}")
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
    aws_config.lambda_context = context
    sns_message: SnsMessage = json.loads(event["Records"][0]["Sns"]["Message"])
    provenance = sns_message["provenance"]
    result = []

    try:
        result.append(handle_offers_for_categories(sns_message))
    except Exception as e:
        logging.error(e)
        log_traceback(e)
        result.append({"message": str(e)})

    try:
        offers_list = get_offers_list_for_gtins(provenance)
        if len(offers_list) > 0:
            result.append(handle_offers(offers_list))
        else:
            result.append({"message": f"No offers with gtins for {provenance}"})
    except Exception as e:
        logging.error(e)
        log_traceback(e)
        result.append({"message": str(e)})

    return result


def offer_feed_trigger(event, context):
    aws_config.lambda_context = context
    provenance = event["provenance"]
    result = []

    try:
        result.append(handle_offers_for_categories(event))
    except Exception as e:
        logging.error(e)
        log_traceback(e)
        result.append({"message": str(e)})

    try:
        offers_list = get_offers_list_for_gtins(provenance)
        if len(offers_list) > 0:
            result.append(handle_offers(offers_list))
        else:
            result.append({"message": f"No offers with gtins for {provenance}"})
    except Exception as e:
        logging.error(e)
        log_traceback(e)
        result.append({"message": str(e)})

    return result


def offer_feed_meta_sns(event, context):
    logging.info("event")
    logging.info(event)
    aws_config.lambda_context = context
    sns_message: SnsMessage = json.loads(event["Records"][0]["Sns"]["Message"])
    provenance = sns_message["provenance"]
    try:
        offers_list = get_scraped_offers(provenance)
        if len(offers_list) > 0:
            return handle_offers_for_meta(offers_list)
        else:
            return {"message": f"No offers for {provenance}"}
    except Exception as e:
        logging.error(e)
        log_traceback(e)
        return {"message": str(e)}


def offer_feed_meta_trigger(event, context):
    logging.info("event")
    logging.info(event)
    aws_config.lambda_context = context
    provenance = event["provenance"]
    try:
        offers_list = get_scraped_offers(provenance)
        if len(offers_list) > 0:
            return handle_offers_for_meta(offers_list)
        else:
            return {"message": f"No offers for {provenance}"}
    except Exception as e:
        logging.error(e)
        log_traceback(e)
        return {"message": str(e)}
