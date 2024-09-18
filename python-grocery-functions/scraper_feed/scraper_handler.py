import json
import logging
import os
from scraper_feed.handle_config import fetch_handle_configs
from util.logging import configure_lambda_logging
from util.utils import log_traceback
import boto3
import botostubs
import botocore.response

from amp_types.amp_product import EventHandleConfig
import aws_config
from scraper_feed.handle_feed import handle_feed_with_config
from storage.s3 import get_s3_object

import sentry_sdk
from sentry_sdk.integrations.aws_lambda import AwsLambdaIntegration

if not os.getenv("IS_LOCAL"):
    sentry_sdk.init(
        integrations=[AwsLambdaIntegration()],
    )


configure_lambda_logging()


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
    logging.info(type(event))
    aws_config.lambda_context = context

    try:
        bucket = os.environ["SCRAPER_FEED_BUCKET"]
        key = event["feed_key"]
        s3_object = get_s3_object(bucket, key)
        scrape_time = s3_object["LastModified"]
        file_content_stream: botocore.response.StreamingBody = s3_object["Body"]
    except Exception as e:
        logging.error(e)
        log_traceback(e)
        raise e

    if not file_content_stream:
        logging.warning("No items in scraper feed")
        return {"message": "No items in scraped feed"}

    try:
        result = handle_feed_with_config(
            file_content_stream,
            {
                **event,
                "scrape_time": scrape_time,
                "scrapeBatchId": s3_object["VersionId"],
            },
        )

        return {
            "message": "Go Serverless v1.0! Your function executed successfully!",
        }
    except Exception as e:
        logging.error(e)
        log_traceback(e)
        return {"message": str(e)}
