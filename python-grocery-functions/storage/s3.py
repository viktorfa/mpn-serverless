import json
import boto3
import botostubs
from typing import Optional

s3 = boto3.client("s3")  # type: botostubs.S3


def get_sns_file_content(event):
    """
    Gets the file content from a SNS event triggered by S3 file upload.
    """
    inner_message = json.loads(event["Records"][0]["Sns"]["Message"])
    source_bucket = inner_message["Records"][0]["s3"]["bucket"]["name"]
    object_key = inner_message["Records"][0]["s3"]["object"]["key"]
    s3_object = s3.get_object(Bucket=source_bucket, Key=object_key)
    return s3_object["Body"].read().decode()


def get_s3_file_content(bucket: str, key: str):
    """
    Gets the raw content of an S3 object.
    """
    s3_object = s3.get_object(Bucket=bucket, Key=key)
    return s3_object["Body"].read().decode()


def get_s3_object(bucket: str, key: str, version=""):
    """
    Gets an s3 object.
    """
    if version:
        return s3.get_object(Bucket=bucket, Key=key, VersionId=version)
    else:
        return s3.get_object(Bucket=bucket, Key=key)


def get_s3_object_versions(bucket: str, key: str):
    """
    Gets an s3 object.
    """
    bucket_obj = boto3.resource("s3").Bucket(bucket)
    return bucket_obj.object_versions.filter(Prefix=key)


def save_to_s3(bucket: str, key: str, data):
    """
    Saves a json string as a file to S3.
    """
    return s3.put_object(
        Key=key, Bucket=bucket, Body=data, ContentType="application/json"
    )
