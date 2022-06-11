from datetime import timedelta
import json
from json.decoder import JSONDecodeError
import logging
import os
from typing import Dict, List, Mapping

from pymongo.errors import BulkWriteError
from pymongo.results import InsertManyResult
from pymongo import InsertOne, UpdateOne
from config.mongo import get_collection
from scraper_feed.handle_config import fetch_single_handle_config
from scraper_feed.pricing_history import get_price_difference_update_set
from util.utils import log_traceback
import boto3
import botostubs

import aws_config
from util.helpers import get_product_uri
from amp_types.amp_product import (
    EventHandleConfig,
    HandleConfig,
    PriceHistoryForOffer,
    PriceHistoryRecord,
)
from storage.s3 import get_s3_object, get_s3_object_versions

import sentry_sdk
from sentry_sdk.integrations.aws_lambda import AwsLambdaIntegration

if not os.getenv("IS_LOCAL"):
    sentry_sdk.init(
        integrations=[AwsLambdaIntegration()],
    )

logger = logging.getLogger()
logging.getLogger("botocore").setLevel(logging.WARNING)
logging.getLogger("boto3").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
if os.getenv("IS_LOCAL"):
    logging.basicConfig(level=logging.DEBUG)
    logger.setLevel(logging.DEBUG)
else:
    logging.basicConfig(level=logging.INFO)
    logger.setLevel(logging.INFO)


def trigger_scraper_feed_with_config(event: EventHandleConfig, context):
    logging.info("event")
    logging.info(event)
    aws_config.lambda_context = context

    if "amazon" in event["namespace"]:
        return
    if "shopgun" in event["namespace"]:
        return
    if "computersalg" in event["namespace"]:
        return
    if "cdon" in event["namespace"]:
        return

    try:
        bucket = os.environ["SCRAPER_FEED_BUCKET"]
        key = event["feed_key"]
        s3_object = get_s3_object(bucket, key)
        scrape_time = s3_object["LastModified"]
        file_content = s3_object["Body"].read().decode()
    except Exception as e:
        logging.error(e)
        log_traceback(e)
        return {"message": f"Could not read s3 file", "error": str(e)}
    if not file_content:
        logging.warn("No items in scraper feed")
        return {"message": "No items in scraped feed"}
    try:
        # Limit the number of offers to avoid too much database load
        offers = json.loads(file_content)[:20000]
        if os.getenv("STAGE") == "dev":
            offers = offers[:512]

        result = handle_feed_with_config_for_pricing_series(
            offers, {**event, "scrape_time": scrape_time}
        )

        return {
            "message": "Go Serverless v1.0! Your function executed successfully!",
            "event": event,
            "result": json.dumps(result, default=str),
        }
    except Exception as e:
        logging.error(e)
        log_traceback(e)
        return {"message": str(e)}


def trigger_scraper_feed_pricing_with_history(event, context):
    logging.info("event")
    logging.info(event)
    aws_config.lambda_context = context

    result = []

    try:
        key = event["feed_key"]
        provenance = key.split("/")[0]
        lambda_client = boto3.client("lambda")  # type: botostubs.Lambda
        config = fetch_single_handle_config(provenance)

        if not config:
            logging.error(f"No handle config for {provenance}")
            return {"messsage": f"No handle config for {provenance}"}

        try:
            bucket = os.environ["SCRAPER_FEED_BUCKET"]
            versions = get_s3_object_versions(bucket, key)
            for version in versions:
                logging.debug(f"version: {version}")
                version_data = version.get()
                logging.debug(json.dumps(version_data, default=str))
                scrape_time = version_data.get("LastModified")
                file_content = version_data["Body"].read().decode()
                try:
                    result.append(
                        handle_feed_with_config_for_pricing_series(
                            json.loads(file_content),
                            {**config, "scrape_time": scrape_time},
                            use_history=False,
                        )
                    )
                except JSONDecodeError:
                    # Means empty S3 file
                    pass
                except BulkWriteError as e:
                    # Means duplicate pricing object for one day
                    log_traceback(e)
                    pass
            logging.info(f"Ran pricing for {len(result)} feeds")

        except Exception as e:
            logging.error(e)
            log_traceback(e)
            return {"message": f"Could not read s3 file", "error": str(e)}
    except Exception as e:
        logging.error(e)
        log_traceback(e)
        return {"message": "Could not get handle configs", "error": str(e)}

    return json.dumps(result, default=str)


def handle_feed_with_config_for_pricing_series(
    feed: list, config: HandleConfig, use_history=True
):
    if not config["namespace"]:
        raise Exception("Config needs namespace")
    if not config["scrape_time"]:
        raise Exception("Config needs scrape_time")
    if not config["collection_name"]:
        raise Exception("Config needs collection_name")

    pricing_object_map: Dict[str, PriceHistoryRecord] = {}

    scrape_time = config["scrape_time"]
    scrape_time_string = scrape_time.strftime("%Y-%m-%d")

    for offer in feed:
        sku = next(
            (
                x
                for x in (
                    offer.get("provenanceId"),
                    offer.get("provenance_id"),
                    offer.get("sku"),
                )
                if x
            ),
            None,
        )
        if not sku:
            continue
        uri = get_product_uri(config["namespace"], sku)
        if not offer.get("price") > 0:
            continue

        pricing_object_map[uri] = {
            "price": offer["price"],
            "date": scrape_time_string,
        }

    pricing_collection = get_collection("offerpricinghistories")
    price_history_map: Dict[str, PriceHistoryForOffer] = {}
    if use_history:
        existing_price_histories: List[PriceHistoryForOffer] = pricing_collection.find(
            {"uri": {"$in": list(pricing_object_map.keys())}}
        )
        for price_history in existing_price_histories:
            price_history_map[price_history["uri"]] = price_history
    else:
        pass

    updates = []

    for uri, pricing_object in pricing_object_map.items():
        price_history = price_history_map.get(uri, None)
        if price_history:
            update_set = get_price_difference_update_set(
                price_history, config, pricing_object["price"]
            )
            updates.append(
                UpdateOne(
                    {"uri": uri},
                    {
                        "$set": update_set,
                        "$addToSet": {"history": pricing_object},
                    },
                )
            )
        else:
            updates.append(
                UpdateOne(
                    {"uri": uri},
                    {
                        "$set": {
                            "siteCollection": config["collection_name"],
                            "updatedAt": scrape_time,
                            "latestPrice": pricing_object["price"],
                        },
                        "$addToSet": {"history": pricing_object},
                    },
                    upsert=True,
                )
            )

    if os.getenv("STAGE") == "dev":
        result = pricing_collection.bulk_write(updates[:512])
    else:
        result = pricing_collection.bulk_write(updates)

    logging.debug(result)

    return result.matched_count


def handle_feed_with_config_for_pricing(
    feed: list, config: HandleConfig
) -> InsertManyResult:
    if not config["namespace"]:
        raise Exception("Config needs namespace")
    if not config["scrape_time"]:
        raise Exception("Config needs scrape_time")

    pricing_objects = []

    for offer in feed:
        sku = next(
            (
                x
                for x in (
                    offer.get("provenanceId"),
                    offer.get("provenance_id"),
                    offer.get("sku"),
                )
                if x
            ),
            None,
        )
        if not sku:
            continue
        uri = get_product_uri(config["namespace"], sku)
        if not offer.get("price"):
            continue

        scrape_time = config["scrape_time"]
        pricing_objects.append(
            {
                "uri": uri,
                "pricing": {"price": offer["price"]},
                "date": scrape_time.strftime("%Y-%m-%d"),
            }
        )

    if len(pricing_objects) == 0:
        return None

    mongo_collection = get_collection("offerpricings")

    uris = list(x["uri"] for x in pricing_objects)

    ten_days_before_scrape_time = scrape_time - timedelta(days=15)

    previous_prices = mongo_collection.aggregate(
        [
            {
                "$match": {
                    "uri": {"$in": uris},
                    "date": {"$gt": ten_days_before_scrape_time.strftime("%Y-%m-%d")},
                }
            },
            {"$sort": {"date": -1}},
            {"$group": {"_id": "$uri", "doc": {"$first": "$$ROOT"}}},
            {"$unwind": {"path": "$doc"}},
            {"$replaceRoot": {"newRoot": "$doc"}},
        ]
    )
    previous_prices_map = {}

    for x in previous_prices:
        previous_prices_map[x["uri"]] = x

    for x in pricing_objects:
        uri = x["uri"]
        previous_pricing = previous_prices_map.get(uri)
        if not previous_pricing:
            continue
        if previous_pricing["date"] == x["date"]:
            continue
        current_price = x["pricing"]["price"]
        previous_price = previous_pricing["pricing"]["price"]

        diff = current_price - previous_price
        diff_percentage = (diff / previous_price) * 100

        x["difference"] = diff
        x["differencePercentage"] = diff_percentage

    if os.getenv("STAGE") == "dev":
        result = mongo_collection.bulk_write(
            list(
                UpdateOne(
                    {"uri": x["uri"], "date": x["date"]}, {"$set": x}, upsert=True
                )
                for x in pricing_objects[:512]
            ),
            ordered=False,
        )
    else:
        result = mongo_collection.bulk_write(
            list(
                UpdateOne(
                    {"uri": x["uri"], "date": x["date"]}, {"$set": x}, upsert=True
                )
                for x in pricing_objects
            ),
            ordered=False,
        )

    logging.debug(result)

    return result.matched_count
