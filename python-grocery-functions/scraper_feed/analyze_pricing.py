import json
from json.decoder import JSONDecodeError
import logging
import os
from datetime import datetime

from pymongo.errors import BulkWriteError
from pymongo.results import InsertManyResult
from config.mongo import get_collection
from scraper_feed.handle_config import fetch_single_handle_config
from util.logging import configure_lambda_logging
from util.utils import log_traceback
import boto3
import botostubs

import aws_config
from util.helpers import get_product_uri
from amp_types.amp_product import EventHandleConfig, HandleConfig
from storage.s3 import get_s3_object, get_s3_object_versions

import sentry_sdk
from sentry_sdk.integrations.aws_lambda import AwsLambdaIntegration


configure_lambda_logging()


def analyze_pricing(event, config):
    if not event["namespace"]:
        raise Exception("Config needs namespace")

    product_mongo_collection = get_collection("mpnoffers")
    pricing_mongo_collection = get_collection("offerpricings")

    products = product_mongo_collection.find(
        {
            "dealer": "kolonial",
            "validThrough": {"$gt": datetime.now()},
            "isRecent": True,
        },
        {"uri": 1},
        limit=128,
    )

    product_uris = list(product["uri"] for product in products)

    pricing_objects = pricing_mongo_collection.find(
        {"uri": {"$in": product_uris}, "date": {"$gt": "2022-02"}}, sort=[("date", -1)]
    )

    product_pricings = {}
    _product_pricings = {}

    for pricing_object in pricing_objects:
        uri = pricing_object["uri"]
        if product_pricings.get(uri):
            product_pricings[uri].append(pricing_object)
        else:
            product_pricings[uri] = [pricing_object]

    for k, v in product_pricings.items():
        if len(v) > 1:
            _product_pricings[k] = v

    logging.debug(_product_pricings)
    for uri, pricing in _product_pricings.items():
        current, prev = list(x["pricing"]["price"] for x in pricing[:2])

        diff = current - prev
        diff_percentage = (diff / prev) * 100

        print(uri)
        print(f"difference: {diff}, {diff_percentage}%")
