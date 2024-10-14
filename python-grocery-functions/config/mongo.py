import os
from dotenv import load_dotenv
import pymongo
import logging

logging.getLogger("pymongo").setLevel(logging.WARNING)


client = None

db = None


def get_collection(collection_name: str):
    dotenv_path = ".env.prod" if os.getenv("STAGE") == "prod" else ".env.dev"
    load_dotenv(dotenv_path=dotenv_path)
    MONGO_DATABASE = os.environ["MONGO_DATABASE"]
    MONGO_URI = os.environ["MONGO_URI"]
    global client
    global db
    logging.debug(
        f"Getting collection {collection_name} from {MONGO_URI} db {MONGO_DATABASE}"
    )
    if client is None:
        client = pymongo.MongoClient(MONGO_URI)
    if db is None:
        db = client.get_database(MONGO_DATABASE)
    return db.get_collection(collection_name)
