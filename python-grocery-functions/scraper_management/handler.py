import json
import logging

from boto3 import client as boto_client
import os
from bson.objectid import ObjectId

from config.mongo import get_collection
from scraper_feed.handle_config import fetch_handle_configs

lambda_client = boto_client("lambda")


def handle_scrape(event, context):
    logging.info(json.dumps(event))
    print(json.dumps(event))

    scraper_config_id = event["pathParameters"]["id"]

    auth_header = event["headers"]["Authorization"]

    if auth_header != "Mpn Hei":
        return {"statusCode": 403, "body": "NOT AUTHORIZED"}

    spider_config_collection = get_collection("spiderconfigs")

    spider_config = spider_config_collection.find_one(
        {"_id": ObjectId(scraper_config_id)}
    )

    lambda_response = lambda_client.invoke(
        FunctionName=os.environ["SCRAPE_FUNCTION_NAME"],
        InvocationType="Event",
        Payload=json.dumps([spider_config], default=str),
    )

    return {
        "statusCode": 200,
        "body": json.dumps(spider_config, default=str),
    }


def handle_feed(event, context):
    logging.info(json.dumps(event))
    print(json.dumps(event))

    scraper_run_id = event["pathParameters"]["id"]

    auth_header = event["headers"]["Authorization"]

    if auth_header != "Mpn Hei":
        return {"statusCode": 403, "body": "NOT AUTHORIZED"}

    spider_run_collection = get_collection("spiderruns")

    spider_run = spider_run_collection.find_one({"_id": ObjectId(scraper_run_id)})

    feed_uri = spider_run["feed_uri"]
    feed_key = "/".join(feed_uri.split("/")[-2:])
    provenance = feed_key.split("/")[0]
    handle_configs = fetch_handle_configs(provenance)

    result = []

    for config in handle_configs:
        lambda_response = lambda_client.invoke(
            FunctionName=os.environ["HANDLE_SCRAPER_FEED_FUNCTION_NAME"],
            InvocationType="Event",
            Payload=json.dumps({**config, "feed_key": feed_key}, default=str),
        )
        result.append(lambda_response)

    return {"statusCode": 200, "body": json.dumps(result, default=str)}
