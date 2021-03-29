from pymongo import UpdateOne

from config.mongo import get_collection


def get_update_one(product, id_field: str = "uri"):
    return UpdateOne({id_field: product[id_field]}, {"$set": product}, upsert=True)


def save_similar_offers(updates: list):
    collection = get_collection("mpnoffers")
    requests = list(
        [
            UpdateOne(
                dict(uri=update["uri"]),
                {"$set": dict(similarOffers=update["similarOffers"])},
            )
            for update in updates
        ]
    )
    return collection.bulk_write(requests)

