import json
import logging
import os
from util.utils import log_traceback

import aws_config
from scraper_feed.handle_feed import handle_feed
from storage.s3 import get_s3_object

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
logger.setLevel(logging.INFO)


def scraper_feed_sns(event, context):
    logging.info("event")
    logging.info(event)
    aws_config.lambda_context = context
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
    if not file_content:
        logging.warn("No items in scraper feed")
        return {"message": "No items in scraped feed"}
    try:
        config = dict(provenance=provenance, scrape_time=scrape_time)
        result = handle_feed(json.loads(file_content), config)

        return {
            "message": "Go Serverless v1.0! Your function executed successfully!",
            "event": event,
            "result": json.dumps(result.bulk_api_result, default=str),
        }
    except Exception as e:
        logging.error(e)
        log_traceback(e)
        return {"message": str(e)}


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
    if not file_content:
        logging.warn("No items in scraper feed")
        return {"message": "No items in scraped feed"}
    try:
        config = dict(provenance=provenance, scrape_time=scrape_time)
        result = handle_feed(json.loads(file_content), config)

        return {
            "message": "Go Serverless v1.0! Your function executed successfully!",
            "event": event,
            "result": json.dumps(result.bulk_api_result, default=str),
        }
    except Exception as e:
        logging.error(e)
        log_traceback(e)
        return {"message": str(e)}
