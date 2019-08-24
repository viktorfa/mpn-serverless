import json
from bson.json_util import dumps

from storage.s3 import save_to_s3, get_s3_file_content
from scraper_feed.handle_products import handle_products
from storage.db import save_scraped_products
from util.enums import provenances
from util.helpers import json_handler
from config.vars import BUCKET_NAME


def shopgun_feed(event, context):
    file_content = get_s3_file_content(
        BUCKET_NAME, "shopgun_scraper_feed/shopgun_catalog_spider-latest.json")
    products = handle_products(json.loads(file_content), provenances.SHOPGUN)
    save_to_s3(
        BUCKET_NAME,
        'shopgun_products/products-latest.json',
        json.dumps(products, default=json_handler)
    )
    result = save_scraped_products(products)
    return {
        "message": "Go Serverless v1.0! Your function executed successfully!",
        "event": event,
        "result": dumps(result.bulk_api_result)

    }


def kolonial_feed(event, context):
    file_content = get_s3_file_content(
        BUCKET_NAME, "kolonial_scraper_feed/simple_kolonial_spider-latest.json")
    products = handle_products(json.loads(file_content), provenances.KOLONIAL)
    save_to_s3(
        BUCKET_NAME,
        'kolonial_products/products-latest.json',
        json.dumps(products, default=json_handler)
    )
    result = save_scraped_products(products)
    return {
        "message": "Go Serverless v1.0! Your function executed successfully!",
        "event": event,
        "result": dumps(result.bulk_api_result)
    }


def meny_feed(event, context):
    file_content = get_s3_file_content(
        BUCKET_NAME, "meny_scraper_feed/meny_spider-latest.json")
    products = handle_products(json.loads(file_content), provenances.MENY)
    save_to_s3(
        BUCKET_NAME,
        'meny_products/products-latest.json',
        json.dumps(products, default=json_handler)
    )
    result = save_scraped_products(products)
    return {
        "message": "Go Serverless v1.0! Your function executed successfully!",
        "event": event,
        "result": dumps(result.bulk_api_result)
    }


def europris_feed(event, context):
    file_content = get_s3_file_content(
        BUCKET_NAME, "europris_scraper_feed/europris_spider-latest.json")
    products = handle_products(json.loads(file_content), provenances.EUROPRIS)
    save_to_s3(
        BUCKET_NAME,
        'europris_products/products-latest.json',
        json.dumps(products, default=json_handler)
    )
    result = save_scraped_products(products)
    return {
        "message": "Go Serverless v1.0! Your function executed successfully!",
        "event": event,
        "result": dumps(result.bulk_api_result)
    }
