import json
import logging

from boto3 import client as boto_client
import os
from bson.objectid import ObjectId

from config.mongo import get_collection

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