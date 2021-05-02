import os
import json
import logging


import sentry_sdk
from sentry_sdk.integrations.aws_lambda import AwsLambdaIntegration

from book_feed.process_books import process_books, merge_similar_books


if not os.getenv("IS_LOCAL"):
    sentry_sdk.init(
        integrations=[AwsLambdaIntegration()],
    )

logger = logging.getLogger()
logging.getLogger("botocore").setLevel(logging.WARNING)
logging.getLogger("boto3").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
if os.getenv("IS_LOCAL"):
    logging.basicConfig(level=logging.DEBUG)
    logger.setLevel(logging.DEBUG)
else:
    logging.basicConfig(level=logging.INFO)
    logger.setLevel(logging.INFO)


def handle_book_offers_trigger(event, context):
    namespace = event.get("namespace")
    offer_filter = {}
    if namespace:
        offer_filter["dealer"] = namespace
    return json.dumps(process_books(offer_filter), default=str)


def handle_book_offers_sns(event, context):
    sns_message = json.loads(event["Records"][0]["Sns"]["Message"])
    namespace = sns_message["namespace"]
    offer_filter = {}
    if namespace:
        offer_filter["dealer"] = namespace
    return json.dumps(process_books(offer_filter), default=str)


def process_books_trigger(event, context):
    return json.dumps(merge_similar_books(), default=str)
