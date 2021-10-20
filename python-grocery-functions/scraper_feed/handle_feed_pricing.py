import json
from json.decoder import JSONDecodeError
import logging
import os

from pymongo.errors import BulkWriteError
from pymongo.results import InsertManyResult
from config.mongo import get_collection
from scraper_feed.handle_config import fetch_single_handle_config
from util.utils import log_traceback
import boto3
import botostubs

import aws_config
from util.helpers import get_product_uri
from amp_types.amp_product import EventHandleConfig, HandleConfig
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
        result = handle_feed_with_config_for_pricing(
            json.loads(file_content), {**event, "scrape_time": scrape_time}
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
        key = event["key"]
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
                        handle_feed_with_config_for_pricing(
                            json.loads(file_content),
                            {**config, "scrape_time": scrape_time},
                        )
                    )
                except JSONDecodeError:
                    # Means empty S3 file
                    pass
                except BulkWriteError:
                    # Means duplicate pricing object for one day
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
        pricing_objects.append(
            {
                "uri": uri,
                "pricing": {"price": offer["price"]},
                "date": config["scrape_time"].strftime("%Y-%m-%d"),
            }
        )

    if len(pricing_objects) == 0:
        return None

    mongo_collection = get_collection("offerpricings")

    if os.getenv("STAGE") == "dev":
        result = mongo_collection.insert_many(pricing_objects[:512], ordered=False)
    else:
        result = mongo_collection.insert_many(pricing_objects, ordered=False)

    logging.debug(result)

    return len(result.inserted_ids)
