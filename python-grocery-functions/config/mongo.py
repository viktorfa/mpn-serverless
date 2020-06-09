import pymongo

from config.vars import (
    MONGO_HOST,
    MONGO_PORT,
    MONGO_USER,
    MONGO_PASSWORD,
    MONGO_DATABASE,
)

if MONGO_USER:
    _client = pymongo.MongoClient(
        MONGO_HOST, int(MONGO_PORT), username=MONGO_USER, password=MONGO_PASSWORD
    )
else:
    _client = pymongo.MongoClient(MONGO_HOST, int(MONGO_PORT))

_db = _client.get_database(MONGO_DATABASE)


def get_collection(collection_name: str) -> pymongo.collection:
    return _db.get_collection(collection_name)
