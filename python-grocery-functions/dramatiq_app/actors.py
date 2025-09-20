import logging
import os

import botocore.response
import dramatiq

from amp_types.amp_product import EventHandleConfig
from dramatiq_app.redis_file import ensure_broker_initialized
from scraper_feed.handle_config import generate_handle_config_postgres
from scraper_feed.handle_feed_postgres import handle_feed_with_config_postgres
from storage.postgres.scraper_feed import get_handle_config_by_id, get_handle_configs
from storage.s3 import get_s3_object
from util.logging import configure_lambda_logging
from util.utils import log_traceback

ensure_broker_initialized()
is_online = not os.getenv("IS_LOCAL")


@dramatiq.actor(
    max_retries=3,
    min_backoff=15 * 1000,
    max_backoff=1 * 24 * 60 * 60 * 1000,
    priority=50,
    time_limit=30 * 1000,
)
def example_task(x: int, y: int):
    result = x + y
    print(f"The result is {result}")


@dramatiq.actor(
    max_retries=2,
    min_backoff=15 * 1000,
    max_backoff=1 * 3 * 60 * 60 * 1000,
    priority=50,
    time_limit=60 * 60 * 1000,
)
def trigger_dramatiq_scraper_feed_with_config(event: EventHandleConfig):
    configure_lambda_logging()
    logging.info("event")
    logging.info(event)
    logging.info(type(event))

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
        else:
            config_id = config["id"]
            db_config = get_handle_config_by_id(config_id)
            print(f"Getting handle config from id {config_id}")
            if not db_config:
                logging.error(f"Could not find handle config with id {config_id}")
                raise Exception(f"Could not find handle config with id {config_id}")
            config = generate_handle_config_postgres(db_config).model_dump()

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
        result = handle_feed_with_config_postgres(
            file_content_stream,
            {
                **config,
                "scrape_time": scrape_time,
                "scrapeBatchId": s3_object["VersionId"],
            },
        )

        return None
    except Exception as e:
        logging.error(e)
        log_traceback(e)
        raise
