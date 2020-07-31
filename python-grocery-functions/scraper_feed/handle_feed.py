import boto3
import json

from scraper_feed.handle_products import handle_products
from storage.db import save_scraped_products, get_handle_config
from util.helpers import json_handler
from util.utils import log_traceback


from config.vars import SCRAPER_FEED_HANDLED_TOPIC_ARN
from util.enums import provenances
from util.errors import NoHandleConfigError

DEFAULT_OFFER_COLLECTION_NAME = "mpnoffer"


def _get_handle_config(config: dict) -> dict:
    """
    Finds a handle config from a database or uses a default one.
    """
    result = {}

    try:
        result = {**config, **get_handle_config(config.get("provenance"))}
    except NoHandleConfigError:
        result = {**config}
        result["collection_name"] = DEFAULT_OFFER_COLLECTION_NAME
    result["source"] = config.get("provenance")
    _result = {k: v for k, v in result.items() if v is not None}
    return _result


def handle_feed(feed: list, config: dict) -> dict:
    """
    Handles a feed from Scrapy according to the provided config.
    """

    sns_client = boto3.client("sns")

    _config = _get_handle_config(config)

    products = handle_products(feed, _config)
    products = list(
        {**product, "siteCollection": _config["collection_name"]}
        for product in products
    )
    try:
        result = save_scraped_products(products, _config["collection_name"])
    except Exception as e:
        log_traceback(e)
        raise e
    # To allow event-driven behaviour, we publish an sns topic when products are saved successfully.
    sns_message_data = {
        **config,
        "collection_name": _config["collection_name"],
    }
    sns_message = json.dumps(
        {"default": json.dumps(sns_message_data, default=json_handler)}
    )
    sns_client.publish(
        Message=sns_message,
        MessageStructure="json",
        TargetArn=SCRAPER_FEED_HANDLED_TOPIC_ARN,
    )
    return result
