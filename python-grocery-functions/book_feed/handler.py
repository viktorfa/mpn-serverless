import os
import json
import logging


import sentry_sdk
from sentry_sdk.integrations.aws_lambda import AwsLambdaIntegration

from book_feed.process_books import process_books, merge_similar_books
from util.logging import configure_lambda_logging


if not os.getenv("IS_LOCAL"):
    sentry_sdk.init(
        integrations=[AwsLambdaIntegration()],
    )


configure_lambda_logging()


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
