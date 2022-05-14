import json
import logging
import os
from scraper_feed.handle_config import fetch_handle_configs
from util.utils import log_traceback
import boto3
import botostubs

from amp_types.amp_product import EventHandleConfig, HandleConfig
import aws_config
from scraper_feed.handle_feed import handle_feed_with_config
from storage.s3 import get_s3_object

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


def scraper_feed_sns(event, context):
    logging.info("event")
    logging.info(event)
    aws_config.lambda_context = context
    try:
        sns_message = json.loads(event["Records"][0]["Sns"]["Message"])
        message_record = sns_message["Records"][0]
        key = message_record["s3"]["object"]["key"]
        provenance = key.split("/")[0]
        configs = fetch_handle_configs(provenance)
        lambda_client = boto3.client("lambda")  # type: botostubs.Lambda

        logging.debug("configs")
        logging.debug(configs)
    except Exception as e:
        logging.error(e)
        log_traceback(e)
        return {"message": "Could not get handle configs", "error": str(e)}

    try:
        invocations = []
        for config in configs:
            invocations.append(
                json.dumps(
                    lambda_client.invoke(
                        InvocationType="Event",
                        FunctionName=os.environ["HANDLE_SCRAPER_FEED_FUNCTION_NAME"],
                        Payload=bytes(json.dumps({**config, "feed_key": key}), "utf-8"),
                    ),
                    default=str,
                )
            )
            invocations.append(
                json.dumps(
                    lambda_client.invoke(
                        InvocationType="Event",
                        FunctionName=os.environ[
                            "HANDLE_SCRAPER_FEED_PRICING_FUNCTION_NAME"
                        ],
                        Payload=bytes(json.dumps({**config, "feed_key": key}), "utf-8"),
                    ),
                    default=str,
                )
            )
        return invocations
    except Exception as e:
        logging.error(e)
        log_traceback(e)
        return {
            "message": "Could not invoke lambda functions for handling feed",
            "error": str(e),
        }


def trigger_scraper_feed(event, context):
    logging.info("event")
    logging.info(event)
    aws_config.lambda_context = context

    try:
        key = event["feed_key"]
        provenance = key.split("/")[0]
        configs = fetch_handle_configs(provenance)
        lambda_client = boto3.client("lambda")  # type: botostubs.Lambda

        logging.debug("configs")
        logging.debug(configs)
    except Exception as e:
        logging.error(e)
        log_traceback(e)
        return {"message": "Could not get handle configs", "error": str(e)}

    try:
        invocations = []
        for config in configs:
            invocations.append(
                json.dumps(
                    lambda_client.invoke(
                        InvocationType="Event",
                        FunctionName=os.environ["HANDLE_SCRAPER_FEED_FUNCTION_NAME"],
                        Payload=bytes(json.dumps({**config, "feed_key": key}), "utf-8"),
                    ),
                    default=str,
                )
            )
            invocations.append(
                json.dumps(
                    lambda_client.invoke(
                        InvocationType="Event",
                        FunctionName=os.environ[
                            "HANDLE_SCRAPER_FEED_PRICING_FUNCTION_NAME"
                        ],
                        Payload=bytes(json.dumps({**config, "feed_key": key}), "utf-8"),
                    ),
                    default=str,
                )
            )
        return invocations

    except Exception as e:
        logging.error(e)
        log_traceback(e)
        return {
            "message": "Could not invoke lambda functions for handling feed",
            "error": str(e),
        }


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
        result = handle_feed_with_config(
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
