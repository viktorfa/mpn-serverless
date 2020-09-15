import json
from bson import json_util
import logging
from pymongo import UpdateOne, InsertOne

import boto3
from typing import Iterable, TypedDict
from pymongo.results import InsertManyResult

from offer_feed.process_offers import MpnOfferWithProduct, OfferConfig, process_offers

from storage.db import (
    get_collection,
    get_insert_product_has_offer,
    get_offers_with_product,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()
logging.getLogger("botocore").setLevel(logging.WARNING)
logging.getLogger("boto3").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logger.setLevel(logging.DEBUG)
s3 = boto3.client("s3")


class SnsMessage(TypedDict):
    collection_name: str
    scrape_time: str
    provenance: str


def handle_offers(offers: Iterable[MpnOfferWithProduct], config: OfferConfig):
    """
    Handles newly scraped products after they are initially processed and standardized.
    """

    _offers = list(offers)
    logging.info(f"Handling {len(_offers)} offers.")
    result = process_offers(_offers, config)

    insert_product_data = result["insert_product_data"]
    update_product_operations = result["update_product_operations"]
    relation_operations = result["relation_operations"]

    logging.info(f"{len(insert_product_data)} insert_product_data.")
    if len(insert_product_data) > 0:
        product_collection = get_collection(config["product_collection"])
        relation_collection = get_collection(config["relation_collection"])
        product_docs = list(x["operation"]._doc for x in insert_product_data)
        insert_many_result = product_collection.insert_many(product_docs, ordered=True)
        # First we inserted the products, now we insert the product has offer relations.
        offers = list(x["offer"] for x in insert_product_data)
        logging.info(f"Inserted {len(insert_many_result.inserted_ids)} products.")
        bulk_write_result = relation_collection.bulk_write(
            list(
                get_insert_product_has_offer(offer["_id"], product_id, "new")
                for offer, product_id in zip(offers, insert_many_result.inserted_ids)
            )
        )
        logging.info(json_util.dumps(bulk_write_result.bulk_api_result))

    logging.info(f"{len(update_product_operations)} update_product_operations.")
    if len(update_product_operations) > 0:
        product_collection = get_collection(config["product_collection"])
        bulk_write_result = product_collection.bulk_write(update_product_operations)
        logging.info(json_util.dumps(bulk_write_result.bulk_api_result))

    logging.info(f"{len(relation_operations)} relation operations.")
    if len(relation_operations) > 0:
        relation_collection = get_collection(config["relation_collection"])
        bulk_write_result = relation_collection.bulk_write(relation_operations)
        logging.info(json_util.dumps(bulk_write_result.bulk_api_result))

    return {"message": "Dale Costa Rica"}


def offer_feed_sns(event, context):
    logging.info("event")
    logging.info(event)
    try:
        sns_message: SnsMessage = json.loads(event["Records"][0]["Sns"]["Message"])
        collection = get_collection(sns_message["collection_name"])
        config = {"collection": collection}
        offers = get_offers_with_product(
            event["provenance"],
            event["collection_name"],
            event["target_collection_name"],
            event["relation_collection_name"],
        )
        return handle_offers(offers, config)
    except Exception as e:
        logging.error(e)
    return {"message": "no cannot"}


def offer_feed_trigger(event, context):
    try:
        collection = get_collection(event["collection_name"])
        config = {
            "collection": collection,
            "provenance": event["provenance"],
            "product_collection": event["target_collection_name"],
            "relation_collection": event["relation_collection_name"],
        }
        offers = get_offers_with_product(
            event["provenance"],
            event["collection_name"],
            event["target_collection_name"],
            event["relation_collection_name"],
            limit=0,
        )
        return handle_offers(offers, config)
    except Exception as e:
        logging.error(e)
    return {"message": "no cannot"}
