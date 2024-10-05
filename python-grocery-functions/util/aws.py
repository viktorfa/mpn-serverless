import os
import json
import boto3
import botostubs

is_online = not os.getenv("IS_LOCAL")


def get_lambda_client():
    if is_online:
        lambda_client = boto3.client("lambda")  # type: botostubs.Lambda
    else:
        print("Getting local lambda client")
        lambda_client = boto3.client(
            "lambda",
            api_version="2015-03-31",
            endpoint_url="http://localhost:3002",
        )  # type: botostubs.Lambda

    return lambda_client


def invoke_function(FunctionName: str, Payload: dict, InvocationType="Event"):
    lambda_client = get_lambda_client()
    return lambda_client.invoke(
        FunctionName=FunctionName,
        Payload=bytes(json.dumps(Payload), "utf-8"),
        InvocationType=InvocationType,
    )
