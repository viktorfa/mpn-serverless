import json
import aws_config
import logging
from typing import TypedDict
from datetime import datetime
from storage.models import mpn_offer_store_fields
import time
from storage.db import get_collection
from util.logging import configure_lambda_logging


configure_lambda_logging()


class SnsMessage(TypedDict):
    collection_name: str
    scrape_time: str
    provenance: str


def handle_market_offers_sns(event, context):
    aws_config.lambda_context = context
    logging.info(json.dumps(event))
    sns_message: SnsMessage = json.loads(event["Records"][0]["Sns"]["Message"])
    provenance = sns_message["provenance"]
    market = sns_message["market"]
    scrape_batch_id = sns_message.get("scrapeBatchId")

    if scrape_batch_id:
        return handle_market_offers_with_scrape_batch(scrape_batch_id, market)
    elif provenance:
        return handle_market_offers_with_provenance(provenance, market)


def handle_market_offers_trigger(event, context):
    aws_config.lambda_context = context
    logging.info(json.dumps(event))
    provenance = event["provenance"]
    scrape_batch_id = event.get("scrapeBatchId")
    market = event["market"]

    if scrape_batch_id:
        return handle_market_offers_with_scrape_batch(scrape_batch_id, market)
    elif provenance:
        return handle_market_offers_with_provenance(provenance, market)


def handle_market_offers_with_provenance(provenance: str, market: str):
    logging.warn("Handling offer relations with provenance")
    offer_filter = {
        "provenance": provenance,
        "isRecent": True,
        "validThrough": {"$gt": datetime.now()},
    }
    return save_offers_to_market_collection(offer_filter, market)


def handle_market_offers_with_scrape_batch(scrape_batch_id: str, market: str):
    offer_filter = {
        "scrapeBatchId": scrape_batch_id,
    }

    return save_offers_to_market_collection(offer_filter, market)


def save_offers_to_market_collection(offer_filter: dict, market: str):
    timer_start = time.perf_counter_ns()
    offer_collection = get_collection("mpnoffers")
    projection = {}
    for field_name in mpn_offer_store_fields:
        projection[field_name] = 1
    update_view_response = offer_collection.aggregate(
        [
            {"$match": offer_filter},
            {"$project": projection},
            {
                "$merge": {
                    "into": f"mpnoffers_{market}",
                    "on": "_id",
                    "whenMatched": "replace",
                    "whenNotMatched": "insert",
                }
            },
        ]
    )

    logging.info(
        f"Finish update view {int((time.perf_counter_ns() - timer_start) / 1e6)} ms for market {market}"
    )
    logging.info(update_view_response)
    timer_start = time.perf_counter_ns()
    return json.dumps(update_view_response, default=str)
