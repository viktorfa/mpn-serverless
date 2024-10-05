import json
import logging
import os
from util.aws import invoke_function
from scraper_feed.handle_config import generate_handle_config_postgres
from scraper_feed.handle_feed_postgres import handle_feed_with_config_postgres
from storage.postgres.scraper_feed import get_handle_configs
from util.logging import configure_lambda_logging
from util.utils import log_traceback
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

is_online = not os.getenv("IS_LOCAL")


def scraper_feed_sns(event, context):
    logging.info("event")
    logging.info(event)
    aws_config.lambda_context = context
    try:
        sns_message = json.loads(event["Records"][0]["Sns"]["Message"])
        message_record = sns_message["Records"][0]
        key = message_record["s3"]["object"]["key"]
        provenance = key.split("/")[0]

        configs = list(
            generate_handle_config_postgres(x) for x in get_handle_configs(provenance)
        )

        logging.debug("configs")
        logging.debug(configs)
    except Exception as e:
        logging.error(e)
        log_traceback(e)
        return {"message": "Could not get handle configs", "error": str(e)}

    try:
        invocations = []

        for config in configs:
            if is_online:
                invocations.append(
                    invoke_function(
                        FunctionName=os.environ["HANDLE_SCRAPER_FEED_FUNCTION_NAME"],
                        Payload={**config.model_dump(), "feed_key": key},
                        InvocationType="Event",
                    )
                )
            if os.getenv("STAGE") in ["local", "dev"]:
                invocations.append(
                    invoke_function(
                        FunctionName=os.environ["HANDLE_SCRAPER_FEED_FUNCTION_NAME"],
                        Payload={
                            **config.model_dump(),
                            "feed_key": key,
                            "use_postgres": True,
                        },
                        InvocationType="Event",
                    )
                )
            if is_online:
                invocations.append(
                    invoke_function(
                        FunctionName=os.environ[
                            "HANDLE_SCRAPER_FEED_PRICING_FUNCTION_NAME"
                        ],
                        Payload={**config.model_dump(), "feed_key": key},
                        InvocationType="Event",
                    )
                )
        return f"Invoked {len(invocations)} lambda functions"
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
        provenance: str = key.split("/")[0]
        configs = list(
            generate_handle_config_postgres(x) for x in get_handle_configs(provenance)
        )

        logging.debug("configs")
        logging.debug(configs)

        if not configs:
            logging.warning(f"No configs found for provenance {provenance}")
            return {"message": f"No configs found for provenance {provenance}"}
    except Exception as e:
        logging.error(e)
        log_traceback(e)
        return {"message": "Could not get handle configs", "error": str(e)}

    try:
        invocations = []
        for config in configs:
            if is_online:
                invocations.append(
                    invoke_function(
                        FunctionName=os.environ["HANDLE_SCRAPER_FEED_FUNCTION_NAME"],
                        Payload={**config.model_dump(), "feed_key": key},
                        InvocationType="Event",
                    )
                )
            if os.getenv("STAGE") in ["local", "dev"]:
                invocations.append(
                    invoke_function(
                        FunctionName=os.environ["HANDLE_SCRAPER_FEED_FUNCTION_NAME"],
                        Payload={
                            **config.model_dump(),
                            "feed_key": key,
                            "use_postgres": True,
                        },
                        InvocationType="Event",
                    )
                )
            if is_online:
                invocations.append(
                    invoke_function(
                        FunctionName=os.environ[
                            "HANDLE_SCRAPER_FEED_PRICING_FUNCTION_NAME"
                        ],
                        Payload={**config.model_dump(), "feed_key": key},
                        InvocationType="Event",
                    )
                )

        return f"Invoked {len(invocations)} lambda functions"

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

    config: EventHandleConfig = event

    try:
        bucket = os.environ["SCRAPER_FEED_BUCKET"]
        key = config["feed_key"]

        if not is_online and "id" not in config:
            logging.info("Getting handle config from key")
            provenance: str = key.split("/")[0]
            handle_configs = get_handle_configs(provenance)
            config = generate_handle_config_postgres(handle_configs[0]).model_dump()

            print("config", config)

        s3_object = get_s3_object(bucket, key)
        scrape_time = s3_object["LastModified"]
        file_content_stream: botocore.response.StreamingBody = s3_object["Body"]
    except Exception as e:
        logging.error(e)
        log_traceback(e)
        raise

    if not file_content_stream:
        logging.warning("No items in scraper feed")
        return {"message": "No items in scraped feed"}

    try:
        if event.get("use_postgres"):
            result = handle_feed_with_config_postgres(
                file_content_stream,
                {
                    **config,
                    "scrape_time": scrape_time,
                    "scrapeBatchId": s3_object["VersionId"],
                },
            )
        else:
            result = handle_feed_with_config(
                file_content_stream,
                {
                    **config,
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
