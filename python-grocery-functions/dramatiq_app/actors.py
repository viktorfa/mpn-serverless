import logging
import os
from typing import TypedDict

import dramatiq

from dramatiq_app.redis_file import ensure_broker_initialized

ensure_broker_initialized()
is_online = not os.getenv("IS_LOCAL")


class DramatiqHandleConfig(TypedDict):
    id: str
    feed_key: str
    use_postgres: bool


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
def trigger_dramatiq_scraper_feed_with_config(event: DramatiqHandleConfig):
    import botocore.response

    from scraper_feed.handle_config import generate_handle_config_postgres
    from scraper_feed.handle_feed_postgres import handle_feed_with_config_postgres
    from storage.postgres.pydantic_models import HandleFeedConfig
    from storage.postgres.scraper_feed import get_handle_config_by_id
    from storage.s3 import get_s3_object
    from util.logging import configure_lambda_logging
    from util.utils import log_traceback

    configure_lambda_logging()
    logging.info("event")
    logging.info(event)
    logging.info(type(event))

    try:
        bucket = os.environ["SCRAPER_FEED_BUCKET"]
        key = event["feed_key"]

        config_id = event["id"]
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
        handle_feed_config = HandleFeedConfig(**config, scrape_time=scrape_time, scrapeBatchId=s3_object["VersionId"])
        result = handle_feed_with_config_postgres(file_content_stream, handle_feed_config)

        return None
    except Exception as e:
        logging.error(e)
        log_traceback(e)
        raise
