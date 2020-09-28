import pymongo

from config.vars import MONGO_URI, MONGO_DATABASE

client = None

db = None


def get_collection(collection_name: str):
    global client
    global db
    if client is None:
        client = pymongo.MongoClient(MONGO_URI)
    if db is None:
        db = client[MONGO_DATABASE]

    return db[collection_name]
