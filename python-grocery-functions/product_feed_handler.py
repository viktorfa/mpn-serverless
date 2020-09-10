import json
import logging

import boto3
from typing import TypedDict


from storage.db import get_collection

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


def handle_products_sns(event, context):
    """
    Handles newly scraped products after they are initially processed and standardized.
    """
    logging.info("event")
    logging.info(event)
    try:
        sns_message: SnsMessage = json.loads(event["Records"][0]["Sns"]["Message"])
        collection = get_collection(sns_message["collection_name"])
        products = collection.find({"provenance": sns_message["provenance"]})

    except Exception:
        logging.exception("Could not get SNS message from event")
        return {"message": "no cannot"}

    return {"message": "no cannot"}

