from amp_types.amp_product import MpnOffer
from offer_feed.categories import handle_offers_for_categories

import json
import pydash
import logging
import os
from pymongo import UpdateOne
from util.logging import configure_lambda_logging
from util.utils import log_traceback

import aws_config
import boto3
from typing import Iterable, TypedDict
from datetime import datetime


from storage.db import get_collection

import sentry_sdk
from sentry_sdk.integrations.aws_lambda import AwsLambdaIntegration


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


def handle_gtins_for_offers(offers: Iterable[MpnOffer]):
    operations = []
    result = []
    now = datetime.now()
    try:
        relations_collection = get_collection("offerbirelations")

        count = 0

        for offer in offers:
            count += 1
            if count % 50000 == 0:
                logging.info(f"On offer number {count}")
                logging.info(f"Running {len(operations)} operations")
                try:
                    mongo_result = relations_collection.bulk_write(
                        operations,
                        ordered=False,
                    )
                    operations = []
                    result.append(
                        dict(
                            deleted_count=mongo_result.deleted_count,
                            inserted_count=mongo_result.inserted_count,
                            matched_count=mongo_result.matched_count,
                            modified_count=mongo_result.modified_count,
                            upserted_count=mongo_result.upserted_count,
                        )
                    )
                except Exception as e:
                    logging.error(e)
                    log_traceback(e)
                    result.append({"message": str(e)})

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
            mongo_result = relations_collection.bulk_write(
                operations,
                ordered=False,
            )
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
            result.append({"message": "No offers with gtins"})
    except Exception as e:
        logging.error(e)
        log_traceback(e)
        result.append({"message": str(e)})

    return result


def handle_offer_feed_for_gtins_with_provenance(provenance: str):
    now = datetime.now()
    offers_collection = get_collection("mpnoffers")
    offers = offers_collection.find(
        {"provenance": provenance, "validThrough": {"$gt": now}, "isRecent": True},
        {"uri": 1, "gtins": 1},
    )

    offers = (
        offer
        for offer in offers
        if pydash.get(offer, "gtins.nobb")
        or pydash.get(offer, "gtins.gtin12")
        or pydash.get(offer, "gtins.gtin13")
    )

    return handle_gtins_for_offers(offers)


def handle_offer_feed_for_gtins_with_scrape_batch(scrape_batch_id: str):
    now = datetime.now()
    offers_collection = get_collection("mpnoffers")
    offers = offers_collection.find(
        {"scrapeBatchId": scrape_batch_id},
        {"uri": 1, "gtins": 1},
    )

    offers = (
        offer
        for offer in offers
        if pydash.get(offer, "gtins.nobb")
        or pydash.get(offer, "gtins.gtin12")
        or pydash.get(offer, "gtins.gtin13")
    )

    return handle_gtins_for_offers(offers)


def offer_feed_sns_for_gtins(event, context):
    logging.info("event")
    logging.info(event)
    aws_config.lambda_context = context
    sns_message: SnsMessage = json.loads(event["Records"][0]["Sns"]["Message"])
    provenance = sns_message.get("provenance")
    scrape_batch_id = sns_message.get("scrapeBatchId")

    if scrape_batch_id:
        return handle_offer_feed_for_gtins_with_scrape_batch(scrape_batch_id)
    elif provenance:
        return handle_offer_feed_for_gtins_with_provenance(provenance)
    else:
        logging.error(f"Need scrapeBatchId or provenance")
        return


def offer_feed_trigger_for_gtins(event, context):
    logging.info("event")
    logging.info(event)
    aws_config.lambda_context = context
    provenance = event.get("provenance")
    scrape_batch_id = event.get("scrapeBatchId")

    if scrape_batch_id:
        return handle_offer_feed_for_gtins_with_scrape_batch(scrape_batch_id)
    elif provenance:
        return handle_offer_feed_for_gtins_with_provenance(provenance)
    else:
        logging.error(f"Need scrapeBatchId or provenance")
        return


def handle_offer_feed_for_meta(provenance: str):
    logging.info("Not handling meta fields")
    if provenance != "NEVER":
        return {"message": "Not handling meta fields"}

    offer_meta_collection = get_collection("offermeta")
    offer_collection = get_collection("mpnoffers")

    now = datetime.now()

    offers = offer_collection.find(
        {"provenance": provenance, "validThrough": {"$gt": now}, "isRecent": True},
        {"uri": 1},
    )

    offer_metas = offer_meta_collection.find(
        {"uri": {"$in": list(x["uri"] for x in offers)}}
    )

    operations = []

    for offer_meta in offer_metas:
        update_set = {}
        for key, meta_field in offer_meta.get("auto", {}).items():
            update_set[key] = meta_field["value"]
        for key, meta_field in offer_meta.get("manual", {}).items():
            update_set[key] = meta_field["value"]
        if len(update_set.keys()) > 0:
            operations.append(
                UpdateOne({"uri": offer_meta["uri"]}, {"$set": update_set})
            )

    if len(operations) == 0:
        return {"message": "No offer metas"}
    else:
        return offer_collection.bulk_write(operations).bulk_api_result


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
