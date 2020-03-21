import re
import json
import boto3
import pickle
from io import BytesIO

from storage.utils import unpickle
from config.vars import ML_MODELS_BUCKET

if not re.match(r"^[a-zA-Z0-9.\-_]{1,255}$", ML_MODELS_BUCKET):
    ML_MODELS_BUCKET = "python-mpn-ml-dev-mlmodelsbucket-us16pfe040o3"

s3 = boto3.client("s3")


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


def get_s3_object(bucket: str, key: str):
    """
    Gets an s3 file object.
    """
    return s3.get_object(Bucket=bucket, Key=key)


def save_json_to_s3(bucket: str, key: str, data):
    """
    Saves a json string as a file to S3.
    """
    return s3.put_object(
        Key=key, Bucket=bucket, Body=data, ContentType="application/json"
    )


def save_to_s3(bucket: str, key: str, data, **kwargs):
    """
    Saves a json string as a file to S3.
    """
    return s3.put_object(Key=key, Bucket=bucket, Body=data, **kwargs)


def save_model_to_s3(model: dict, collection_name: str):
    print(f"BUCKET NAME: {ML_MODELS_BUCKET}")
    fitted_pipeline = pickle.dumps(model["fitted_pipeline"])
    tf_idf_matrix = pickle.dumps(model["tf_idf_matrix"])
    index_to_uri_map = json.dumps(model["index_to_uri_map"])

    return [
        save_json_to_s3(
            ML_MODELS_BUCKET,
            f"{collection_name}/index_to_uri_map.json",
            index_to_uri_map,
        ),
        save_to_s3(
            ML_MODELS_BUCKET, f"{collection_name}/fitted_pipeline.pkl", fitted_pipeline,
        ),
        save_to_s3(
            ML_MODELS_BUCKET, f"{collection_name}/tf_idf_matrix.pkl", tf_idf_matrix,
        ),
    ]


def load_model_from_s3(collection_name: str):
    with BytesIO() as fitted_pipeline_file, BytesIO() as tf_idf_matrix_file:
        s3.download_fileobj(
            ML_MODELS_BUCKET,
            f"{collection_name}/fitted_pipeline.pkl",
            fitted_pipeline_file,
        )
        s3.download_fileobj(
            ML_MODELS_BUCKET, f"{collection_name}/tf_idf_matrix.pkl", tf_idf_matrix_file
        )
        fitted_pipeline_file.seek(0)
        tf_idf_matrix_file.seek(0)
        fitted_pipeline = unpickle(fitted_pipeline_file)
        tf_idf_matrix = unpickle(tf_idf_matrix_file)
    index_to_uri_map = get_s3_file_content(
        ML_MODELS_BUCKET, f"{collection_name}/index_to_uri_map.json"
    )
    return dict(
        fitted_pipeline=fitted_pipeline,
        tf_idf_matrix=tf_idf_matrix,
        index_to_uri_map=json.loads(index_to_uri_map),
    )
