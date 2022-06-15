import os
import logging


def configure_lambda_logging():
    logger = logging.getLogger()
    if os.getenv("STAGE") == "prod":
        logger.setLevel(logging.INFO)
        logging.basicConfig(level=logging.INFO)
    else:
        logger.setLevel(logging.DEBUG)
        logging.basicConfig(level=logging.DEBUG)

    logging.getLogger("botocore").setLevel(logging.WARNING)
    logging.getLogger("boto3").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
