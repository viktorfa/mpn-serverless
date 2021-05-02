import logging
from datetime import datetime
import pydash
from pymongo import UpdateOne, InsertOne, ASCENDING
from bson import ObjectId

from storage.db import get_collection


def merge_similar_books():
    book_collection = get_collection("bookproducts")
    all_books = book_collection.find(
        {"mergedTo": None}, {"isbns": 1, "offers.author": 1, "offers.title": 1}
    ).sort("_id", ASCENDING)

    title_to_book_map = {}
    updates = []

    for book in all_books:
        title = book["offers"][0]["title"]
        existing_book = title_to_book_map.get(title)

        if existing_book:
            logging.info(f"Found existing book: {title}")
            author = pydash.get(book, ["offers", 0, "author"])
            existing_book_author = pydash.get(existing_book, ["offers", 0, "author"])
            if author and author == existing_book_author:
                logging.info(f"Merging book")
                updates.append(
                    UpdateOne(
                        {"_id": ObjectId(book["_id"])},
                        {"$set": {"mergedTo": ObjectId(existing_book["_id"])}},
                    )
                )
                updates.append(
                    UpdateOne(
                        {"_id": ObjectId(existing_book["_id"])},
                        {"$addToSet": {"isbns": {"$each": book["isbns"]}}},
                    )
                )
        else:
            title_to_book_map[title] = book

    logging.debug(f"Writing {len(updates)} updates")

    return book_collection.bulk_write(updates).bulk_api_result


def process_books(offer_filter={}):
    now = datetime.now()
    offer_collection = get_collection("bookoffers")
    book_collection = get_collection("bookproducts")
    scraped_offers = offer_collection.find(
        {"validThrough": {"$gt": now}, **offer_filter},
        {
            "uri": 1,
            "provenance": 1,
            "gtins": 1,
            "dealer": 1,
            "price": 1,
            "href": 1,
            "title": 1,
            "author": 1,
            "book_type": 1,
        },
    )

    inserts = []
    updates = []

    all_books = book_collection.find({"mergedTo": None}, {"isbns": 1, "offers.uri": 1})

    isbn_to_book_map = {}

    for book in all_books:
        for isbn in book["isbns"]:
            isbn_to_book_map[isbn] = book

    for offer in scraped_offers:
        offer_gtin = pydash.get(offer, ["gtins", "isbn13"])
        if not offer_gtin:
            continue
        existing_book = isbn_to_book_map.get(offer_gtin)
        book_offer = {
            "price": offer.get("price"),
            "href": offer["href"],
            "uri": offer["uri"],
            "dealer": offer["dealer"],
            "title": offer["title"],
            "author": offer.get("author", ""),
            "book_type": offer["book_type"],
            "updated": now,
        }
        if existing_book:
            updated_book_offers = existing_book["offers"]
            if next(
                (x for x in existing_book["offers"] if x["uri"] == offer["uri"]),
                None,
            ):
                updates.append(
                    UpdateOne(
                        {"isbns": offer_gtin, "mergedTo": None},
                        {"$set": {"offers.$[elem]": book_offer}},
                        upsert=False,
                        array_filters=[{"elem.uri": offer["uri"]}],
                    )
                )
            else:
                updates.append(
                    UpdateOne(
                        {"isbns": offer_gtin, "mergedTo": None},
                        {"$push": {"offers": book_offer}},
                    )
                )

        else:
            new_book = {
                "title": offer["title"],
                "gtins": offer["gtins"],
                "offers": [book_offer],
                "isbns": [offer_gtin],
                "mergedTo": None,
            }
            inserts.append(InsertOne(new_book))
            isbn_to_book_map[offer_gtin] = new_book

    mongo_requests = [*inserts, *updates]

    logging.debug(f"Writing {len(mongo_requests)} updates and inserts")

    return book_collection.bulk_write(mongo_requests).bulk_api_result
