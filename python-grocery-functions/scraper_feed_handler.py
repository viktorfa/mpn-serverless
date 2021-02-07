import json
import logging
import os

import boto3
import sentry_sdk

from scraper_feed.handle_feed import handle_feed
from storage.s3 import get_s3_object
from config.vars import SENTRY_DSN

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()
logging.getLogger("botocore").setLevel(logging.WARNING)
logging.getLogger("boto3").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logger.setLevel(logging.INFO)
s3 = boto3.client("s3")

sentry_sdk.init(
    SENTRY_DSN,
    traces_sample_rate=1.0,
)


def scraper_feed_sns(event, context):
    logging.info("event")
    logging.info(event)
    try:
        sns_message = json.loads(event["Records"][0]["Sns"]["Message"])
        message_record = sns_message["Records"][0]
        bucket = message_record["s3"]["bucket"]["name"]
        key = message_record["s3"]["object"]["key"]
        s3_object = get_s3_object(bucket, key)
        file_content = s3_object["Body"].read().decode()
        scrape_time = s3_object["LastModified"]
        provenance = key.split("/")[0]
    except Exception:
        logging.exception("Could not get SNS message from event")
        return {"message": "no cannot"}

    try:
        config = dict(provenance=provenance, scrape_time=scrape_time)
        result = handle_feed(json.loads(file_content), config)

        return {
            "message": "Go Serverless v1.0! Your function executed successfully!",
            "event": event,
            "result": json.dumps(result.bulk_api_result, default=str),
        }
    except Exception:
        logging.exception("Could not handle scraped products")

    return {"message": "no cannot"}


def trigger_scraper_feed(event, context):
    logging.info("event")
    logging.info(event)
    try:
        bucket = os.environ["SCRAPER_FEED_BUCKET"]
        key = event["key"]
        s3_object = get_s3_object(bucket, key)
        file_content = s3_object["Body"].read().decode()
        scrape_time = s3_object["LastModified"]
        provenance = key.split("/")[0]
    except Exception:
        logging.exception("Could not handle feed.")
        return {"message": "no cannot"}

    try:
        config = dict(provenance=provenance, scrape_time=scrape_time)
        result = handle_feed(json.loads(file_content), config)

        return {
            "message": "Go Serverless v1.0! Your function executed successfully!",
            "event": event,
            "result": json.dumps(result.bulk_api_result, default=str),
        }
    except Exception:
        logging.exception("Could not handle scraped products")
        return {"message": "no cannot"}
