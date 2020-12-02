import os
import boto3
import json
from pymongo.results import BulkWriteResult

from scraper_feed.handle_config import fetch_handle_config
from scraper_feed.handle_products import handle_products
from storage.db import save_scraped_products
from util.helpers import json_handler
from util.utils import log_traceback
from amp_types.amp_product import ScraperConfig
from config.vars import SCRAPER_FEED_HANDLED_TOPIC_ARN
from scraper_feed.affiliate_links import add_affiliate_links


def handle_feed(feed: list, config: ScraperConfig) -> BulkWriteResult:
    """
    Handles a feed from Scrapy according to the provided config.
    """

    sns_client = boto3.client("sns")

    _config = fetch_handle_config(config)

    products = handle_products(feed, _config)
    products = list(
        {**product, "siteCollection": _config["collection_name"]}
        for product in products
    )

    products = add_affiliate_links(products)

    try:
        # Only 512 offers when in dev to avoid filling up Elastic Search storage
        if os.getenv("STAGE") == "dev":
            result = save_scraped_products(products[:512], _config["collection_name"])
        else:
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
