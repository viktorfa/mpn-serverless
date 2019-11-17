import json
import logging

import boto3

from scraper_feed.handle_feed import handle_feed
from storage.s3 import get_s3_file_content


s3 = boto3.client('s3')


def scraper_feed(event, context):
    logging.info("event")
    logging.info(event)
    try:
        sns_message = json.loads(event['Records'][0]['Sns']['Message'])
        message_record = sns_message['Records'][0]
        bucket = message_record['s3']['bucket']['name']
        key = message_record['s3']['object']['key']
        file_content = get_s3_file_content(bucket, key)

        provenance = key.split('/')[0]
    except Exception:
        logging.exception("Could not get SNS message from event")
        return {
            "message": "no cannot"
        }

    try:
        config = dict(provenance=provenance)
        result = handle_feed(json.loads(file_content), config)

        return {
            "message": "Go Serverless v1.0! Your function executed successfully!",
            "event": event,
            "result": json.dumps(result, default=str)
        }
    except Exception:
        logging.exception("Could not handle scraped products")

    return {
        "message": "no cannot"
    }
