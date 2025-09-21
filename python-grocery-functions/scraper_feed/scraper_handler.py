import json
import logging
import os

import aws_config
from scraper_feed.handle_config import generate_handle_config_postgres
from storage.postgres.pydantic_models import PydanticHandleConfig
from storage.postgres.scraper_feed import get_handle_configs
from util.logging import configure_lambda_logging
from util.utils import log_traceback

configure_lambda_logging()

is_online = not os.getenv("IS_LOCAL")


def scraper_feed_sns(event, context):
    logging.info("event")
    logging.info(event)
    aws_config.lambda_context = context
    try:
        sns_message = json.loads(event["Records"][0]["Sns"]["Message"])
        message_record = sns_message["Records"][0]
        feed_key = message_record["s3"]["object"]["key"]
        provenance = feed_key.split("/")[0]

        configs = list(generate_handle_config_postgres(x) for x in get_handle_configs(provenance))

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
        invocations = trigger_dramatiq_with_configs(configs, feed_key)
        return f"Invoked {len(invocations)} dramatiq events"

    except Exception as e:
        logging.error(e)
        log_traceback(e)
        return {
            "message": "Could not invoke dramatiq for handling feed",
            "error": str(e),
        }


def trigger_scraper_feed(event, context):
    logging.info("event")
    logging.info(event)
    aws_config.lambda_context = context

    try:
        feed_key = event["feed_key"]
        provenance: str = feed_key.split("/")[0]
        configs = list(generate_handle_config_postgres(x) for x in get_handle_configs(provenance))

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
        invocations = trigger_dramatiq_with_configs(configs, feed_key)
        return f"Invoked {len(invocations)} dramatiq events"

    except Exception as e:
        logging.error(e)
        log_traceback(e)
        return {
            "message": "Could not invoke lambda functions for handling feed",
            "error": str(e),
        }


def trigger_dramatiq_with_configs(configs: list[PydanticHandleConfig], feed_key: str):
    from dramatiq_app.actors import DramatiqHandleConfig, trigger_dramatiq_scraper_feed_with_config

    invocations = []
    for config in configs:
        logging.info("Handlin' feed with dramatiq")
        handle_args: DramatiqHandleConfig = {
            "id": config.id,
            "feed_key": feed_key,
            "use_postgres": True,
        }
        job_result = trigger_dramatiq_scraper_feed_with_config.send(handle_args)
        print("Task sent to the queue", job_result.message_id)
        invocations.append(job_result.message_id)

    return invocations
