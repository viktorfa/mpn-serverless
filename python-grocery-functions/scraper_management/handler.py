import json
import logging

from boto3 import client as boto_client

from storage.postgres.spider_configs import (
    get_spider_config_by_id,
    get_spider_config_by_mongo_id,
)

lambda_client = boto_client("lambda")


def get_cors_headers(event):
    cors_origin = event["headers"]["origin"]
    cors_headers = event["headers"].get("access-control-request-headers")
    cors_method = event["headers"].get("access-control-request-method")

    headers = {
        "access-control-allow-origin": cors_origin,
    }
    if cors_headers:
        headers["access-control-allow-headers"] = cors_headers
    if cors_method:
        headers["access-control-allow-methods"] = cors_method

    return headers


def handle_options(event, context):
    return {"statusCode": 204, "body": "", "headers": get_cors_headers(event)}


def handle_scrape(event, context):
    logging.info(json.dumps(event))
    print(json.dumps(event))

    scraper_config_id = event["pathParameters"]["id"]

    auth_header = event["headers"]["Authorization"]

    if auth_header != "Mpn Hei":
        return {"statusCode": 403, "body": "NOT AUTHORIZED"}

    try:
        # Try to get by UUID first, fallback to mongo_id for backward compatibility
        spider_config = get_spider_config_by_id(scraper_config_id)
        if not spider_config:
            spider_config = get_spider_config_by_mongo_id(scraper_config_id)

        if not spider_config:
            return {"statusCode": 404, "body": "Spider config not found"}

        # TODO: Implement scraping logic based on spider_config
        # This would trigger the actual scraping process

        return {
            "statusCode": 200,
            "body": json.dumps(
                {
                    "message": "Scraping triggered successfully",
                    "spider_name": spider_config.spider_name,
                    "config_id": str(spider_config.id),
                }
            ),
        }

    except Exception as e:
        logging.error(f"Error in handle_scrape: {e}")
        return {"statusCode": 500, "body": f"Error: {str(e)}"}


def handle_feed(event, context):
    logging.info(json.dumps(event))
    print(json.dumps(event))

    scraper_run_id = event["pathParameters"]["id"]

    auth_header = event["headers"]["Authorization"]

    if auth_header != "Mpn Hei":
        return {"statusCode": 403, "body": "NOT AUTHORIZED"}

    # TODO: Spider runs not yet migrated to PostgreSQL
    # Need to create SpiderRunsTable and migration script
    logging.warning(f"Handle feed called for run {scraper_run_id} but spider runs not yet migrated to PostgreSQL")

    return {
        "statusCode": 501,
        "body": json.dumps(
            {
                "message": "Spider runs not yet migrated to PostgreSQL",
                "run_id": scraper_run_id,
            }
        ),
    }
