import json
import boto3

s3 = boto3.client('s3')


def get_s3_file_content(bucket: str, key: str):
    """
    Gets the raw content of an S3 object.
    """
    s3_object = s3.get_object(Bucket=bucket, Key=key)
    return s3_object['Body'].read().decode()


def scraper_feed(event, context):
    try:
        sns_message = json.loads(event['Records'][0]['Sns']['Message'])
        message_record = sns_message['Records'][0]
        bucket = message_record['s3']['bucket']['name']
        key = message_record['s3']['object']['key']
        file_content = get_s3_file_content(bucket, key)

        return {
            "message": file_content
        }
    except Exception as e:
        print("Could not get SNS message from event")
        print(e)
    return {
        "message": "no cannot"
    }
