import pymongo

from config.vars import MONGO_URI, MONGO_DATABASE

_client = pymongo.MongoClient(MONGO_URI)

_db = _client.get_database(MONGO_DATABASE)


def get_collection(collection_name: str):
    return _db.get_collection(collection_name)

