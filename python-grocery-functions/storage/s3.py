import json
import os

import boto3

is_in_aws = os.getenv("AWS_EXECUTION_ENV") is not None


def get_s3_client():
    if is_in_aws:
        return boto3.client("s3")
    else:
        return boto3.client(
            "s3",
            aws_access_key_id=os.environ["OFFLINE_AWS_ACCESS_KEY_ID"],
            aws_secret_access_key=os.environ["OFFLINE_AWS_SECRET_ACCESS_KEY"],
            region_name="eu-central-1",
        )


def get_sns_file_content(event):
    """
    Gets the file content from a SNS event triggered by S3 file upload.
    """
    s3_client = get_s3_client()
    inner_message = json.loads(event["Records"][0]["Sns"]["Message"])
    source_bucket = inner_message["Records"][0]["s3"]["bucket"]["name"]
    object_key = inner_message["Records"][0]["s3"]["object"]["key"]
    s3_object = s3_client.get_object(Bucket=source_bucket, Key=object_key)
    return s3_object["Body"].read().decode()


def get_s3_file_content(bucket: str, key: str):
    """
    Gets the raw content of an S3 object.
    """
    s3_client = get_s3_client()
    s3_object = s3_client.get_object(Bucket=bucket, Key=key)
    return s3_object["Body"].read().decode()


def get_s3_object(bucket: str, key: str, version=""):
    """
    Gets an s3 object.
    """
    s3_client = get_s3_client()
    if version:
        return s3_client.get_object(Bucket=bucket, Key=key, VersionId=version)
    else:
        return s3_client.get_object(Bucket=bucket, Key=key)


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
    s3_client = get_s3_client()
    return s3_client.put_object(Key=key, Bucket=bucket, Body=data, ContentType="application/json")
