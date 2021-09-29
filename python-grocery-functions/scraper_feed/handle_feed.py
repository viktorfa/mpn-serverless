import logging
from datetime import datetime
import os
import boto3
import botostubs
import json
from pymongo.results import BulkWriteResult

import aws_config
from scraper_feed.handle_products import handle_products
from storage.db import save_scraped_products, store_handle_run, save_book_offers
from util.helpers import json_handler
from util.utils import log_traceback
from amp_types.amp_product import HandleConfig
from config.vars import SCRAPER_FEED_HANDLED_TOPIC_ARN, BOOK_FEED_HANDLED_TOPIC_ARN
from scraper_feed.affiliate_links import add_affiliate_links
from scraper_feed.helpers import get_book_gtins


def handle_feed_with_config(feed: list, config: HandleConfig) -> BulkWriteResult:
    if not config["namespace"]:
        raise Exception("Config needs namespace")
    if not config["collection_name"]:
        raise Exception("Config needs collection_name")
    if not config["scrape_time"]:
        raise Exception("Config needs scrape_time")

    start_time = datetime.now()

    sns_client = boto3.client("sns")  # type: botostubs.SNS

    products = handle_products(feed, config)
    products = (
        {**product, "siteCollection": config["collection_name"]} for product in products
    )

    products = add_affiliate_links(products)
    products = list(products)

    result = {}

    if config["collection_name"] == "bookoffers":
        try:
            products = list(
                {
                    **product,
                    "gtins": get_book_gtins(product),
                    "uri": product["book_uri"],
                }
                for product in products
            )
            result = {}
            # Only 512 offers when in dev to avoid filling up Elastic Search storage
            if os.getenv("STAGE") == "dev":
                result = save_book_offers(products[:512])
            else:
                result = save_book_offers(products)
            sns_message_data = {
                "namespace": config["namespace"],
            }
            sns_message = json.dumps(
                {"default": json.dumps(sns_message_data, default=json_handler)}
            )
            sns_client.publish(
                Message=sns_message,
                MessageStructure="json",
                TargetArn=BOOK_FEED_HANDLED_TOPIC_ARN,
            )
        except Exception as e:
            log_traceback(e)
            raise e
    else:
        try:
            # Only 512 offers when in dev to avoid filling up Elastic Search storage
            if os.getenv("STAGE") == "dev":
                result = save_scraped_products(products[:512])
            else:
                result = save_scraped_products(products)
        except Exception as e:
            log_traceback(e)
            raise e

        # To allow event-driven behaviour, we publish an sns topic when products are saved successfully.
        sns_message_data = {
            **config,
            "collection_name": config["collection_name"],
        }
        sns_message = json.dumps(
            {"default": json.dumps(sns_message_data, default=json_handler)}
        )
        sns_client.publish(
            Message=sns_message,
            MessageStructure="json",
            TargetArn=SCRAPER_FEED_HANDLED_TOPIC_ARN,
        )

    end_time = datetime.now()

    handle_run = {
        **config,
        "example_items": products[:20],
        "time_elapsed_seconds": (end_time - start_time).total_seconds(),
        "items_handled": len(products),
        "createdAt": end_time,
        "updatedAt": end_time,
        "logs": aws_config.get_log_group_url(),
    }
    if os.getenv("IS_LOCAL"):
        logging.info({**handle_run, "example_items": products[:1]})
    else:
        store_handle_run(handle_run)

    if len(products) == 0:
        return {"message": "No offers to save"}

    return result
