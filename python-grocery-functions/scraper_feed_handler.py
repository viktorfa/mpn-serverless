import json
import boto3
from bson.json_util import dumps

from scraper_feed.handle_products import handle_products
from storage.db import save_scraped_products
from storage.s3 import get_s3_file_content


s3 = boto3.client('s3')


def scraper_feed(event, context):
    try:
        sns_message = json.loads(event['Records'][0]['Sns']['Message'])
        message_record = sns_message['Records'][0]
        bucket = message_record['s3']['bucket']['name']
        key = message_record['s3']['object']['key']
        file_content = get_s3_file_content(bucket, key)

        provenance = key.split('/')[0]

        products = handle_products(
            json.loads(file_content),
            provenance
        )
        result = save_scraped_products(products)
        return {
            "message": "Go Serverless v1.0! Your function executed successfully!",
            "event": event,
            "result": dumps(result.bulk_api_result)
        }
    except Exception as e:
        print("Could not get SNS message from event")
        print(e)
    return {
        "message": "no cannot"
    }
