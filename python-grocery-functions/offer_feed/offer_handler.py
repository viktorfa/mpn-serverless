from bleach import ALLOWED_TAGS
from offer_feed.categories import handle_offers_for_categories
from parsing.quantity_extraction import get_value_from_quantity, standardize_quantity

import json
import pydash
from bson import json_util
import logging
import os
from pymongo import UpdateOne
from util.logging import configure_lambda_logging
from util.utils import log_traceback

import aws_config
import boto3
from typing import Iterable, Mapping, TypedDict, List
from datetime import datetime
from pprint import pprint


from storage.db import get_collection

import sentry_sdk
from sentry_sdk.integrations.aws_lambda import AwsLambdaIntegration
from offer_feed.gtins import get_lists_of_offers_with_same_gtins


if not os.getenv("IS_LOCAL"):
    sentry_sdk.init(
        integrations=[AwsLambdaIntegration()],
    )


configure_lambda_logging()

s3 = boto3.client("s3")


class SnsMessage(TypedDict):
    collection_name: str
    scrape_time: str
    provenance: str


def offer_feed_sns_for_categories(event, context):
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
    return result


def offer_feed_trigger_for_categories(event, context):
    logging.info("event")
    logging.info(event)
    aws_config.lambda_context = context
    provenance = event["provenance"]
    result = []

    try:
        result.append(handle_offers_for_categories(event))
    except Exception as e:
        logging.error(e)
        log_traceback(e)
        result.append({"message": str(e)})
    return result


def handle_offer_feed_for_gtins(provenance: str):
    result = []
    try:
        now = datetime.now()
        offers_collection = get_collection("mpnoffers")
        offers = offers_collection.find(
            {
                "$and": [
                    {"provenance": provenance},
                    {"validThrough": {"$gt": now}},
                    {
                        "$or": [
                            {"gtins.ean": {"$ne": None}},
                            {"gtins.gtin13": {"$ne": None}},
                            {"gtins.gtin12": {"$ne": None}},
                            {"gtins.nobb": {"$ne": None}},
                        ]
                    },
                ],
            },
            {"uri": 1, "gtins": 1},
        )
        operations = []

        count = 0

        for offer in offers:
            count += 1
            if count % 100000 == 0:
                logging.debug(f"On offer number {count}")
            gtins = []
            uri = offer["uri"]
            mongo_safe_uri = uri.replace(".", "\uff0E")
            for key, value in offer.get("gtins", {}).items():
                if key in ("gtin13", "ean"):
                    gtins.append(f"ean:{value}")
                elif key == "gtin12":
                    gtins.append(f"{key}:{value}")
                elif key == "nobb":
                    gtins.append(f"{key}:{value}")

            if len(gtins) == 0:
                continue
            operations.append(
                # Only when createing new entry
                UpdateOne(
                    {"gtins": {"$in": gtins}, "relationType": "identical"},
                    {
                        "$setOnInsert": {
                            "relationType": "identical",
                            "createdAt": now,
                            "updatedAt": now,
                            f"offerSetMeta.{mongo_safe_uri}.auto": {
                                "method": "auto",
                                "reason": "initial_with_gtins",
                                "updatedAt": now,
                            },
                            "gtins": gtins,
                            "offerSet": [uri],
                        },
                    },
                    upsert=True,
                )
            )

            # When adding existing because found gtins
            operations.append(
                UpdateOne(
                    {
                        "gtins": {"$in": gtins},
                        "offerSet": {"$ne": uri},
                        "relationType": "identical",
                    },
                    {
                        "$set": {
                            "updatedAt": now,
                            f"offerSetMeta.{mongo_safe_uri}.auto": {
                                "method": "auto",
                                "reason": "matching_gtins",
                                "updatedAt": now,
                            },
                        },
                        "$addToSet": {
                            "gtins": {"$each": gtins},
                            "offerSet": uri,
                        },
                    },
                    upsert=False,
                )
            )

            # To add additional gtins
            operations.append(
                UpdateOne(
                    {"offerSet": uri, "relationType": "identical"},
                    {"$addToSet": {"gtins": {"$each": gtins}}},
                )
            )
        logging.info(f"Running {len(operations)} operations")
        if len(operations) > 0:
            relations_collection = get_collection("offerbirelations")
            mongo_result = relations_collection.bulk_write(operations)
            result.append(
                dict(
                    deleted_count=mongo_result.deleted_count,
                    inserted_count=mongo_result.inserted_count,
                    matched_count=mongo_result.matched_count,
                    modified_count=mongo_result.modified_count,
                    upserted_count=mongo_result.upserted_count,
                )
            )

        else:
            result.append({"message": f"No offers with gtins for {provenance}"})
    except Exception as e:
        logging.error(e)
        log_traceback(e)
        result.append({"message": str(e)})

    return result


def offer_feed_sns_for_gtins(event, context):
    logging.info("event")
    logging.info(event)
    aws_config.lambda_context = context
    sns_message: SnsMessage = json.loads(event["Records"][0]["Sns"]["Message"])
    provenance = sns_message["provenance"]

    return handle_offer_feed_for_gtins(provenance)


def offer_feed_trigger_for_gtins(event, context):
    logging.info("event")
    logging.info(event)
    aws_config.lambda_context = context
    provenance = event["provenance"]

    return handle_offer_feed_for_gtins(provenance)


def handle_offer_feed_for_meta(provenance: str):
    logging.info("Not handling meta fields")
    return {"message": "Not handling meta fields"}


def offer_feed_meta_sns(event, context):
    logging.info("event")
    logging.info(event)
    aws_config.lambda_context = context
    sns_message: SnsMessage = json.loads(event["Records"][0]["Sns"]["Message"])
    provenance = sns_message["provenance"]
    return handle_offer_feed_for_meta(provenance)


def offer_feed_meta_trigger(event, context):
    logging.info("event")
    logging.info(event)
    aws_config.lambda_context = context
    provenance = event["provenance"]
    return handle_offer_feed_for_meta(provenance)
