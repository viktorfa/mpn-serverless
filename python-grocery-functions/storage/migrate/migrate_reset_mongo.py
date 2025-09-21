from config.mongo import get_collection


def reset_mongo():
    vetduat_collection = get_collection("vetduat_items")
    mpnoffers_collection = get_collection("mpnoffers")
    print("Removing migrated_pg_at and migrated_at fields from vetduat and mpnoffers")
    vetduat_response = vetduat_collection.update_many(
        {"detailFetchedAt": {"$exists": True}, "migrated_pg_at": {"$exists": True}},
        {"$unset": {"migrated_pg_at": ""}},
    )
    offers_response = mpnoffers_collection.update_many(
        {"migrated_at": {"$exists": True}},
        {"$unset": {"migrated_at": ""}},
    )
    print(f"Removed migrated_pg_at from {vetduat_response.modified_count} vetduat items")
    print(f"Removed migrated_at from {offers_response.modified_count} mpnoffers")
    return


if __name__ == "__main__":
    reset_mongo()
