import logging
from datetime import datetime
import pydash
from pymongo import UpdateOne, InsertOne

from storage.db import get_collection


def process_books():
    now = datetime.now()
    offer_collection = get_collection("bookoffers")
    book_collection = get_collection("bookproducts")
    scraped_offers = offer_collection.find(
        {
            "validThrough": {"$gt": now},
        },
        {
            "uri": 1,
            "provenance": 1,
            "gtins": 1,
            "dealer": 1,
            "price": 1,
            "href": 1,
            "title": 1,
        },
    )

    inserts = []
    updates = []

    all_books = book_collection.find({})

    isbn_to_book_map = {}

    for book in all_books:
        isbn = pydash.get(book, ["gtins", "isbn13"])
        if isbn:
            isbn_to_book_map[isbn] = book

    for offer in scraped_offers:
        offer_gtin = pydash.get(offer, ["gtins", "isbn13"])
        if not offer_gtin:
            continue
        existing_book = isbn_to_book_map.get(offer_gtin)
        book_offer_key = offer["uri"]
        book_offer = {
            "price": offer.get("price"),
            "href": offer["href"],
            "uri": offer["uri"],
            "dealer": offer["dealer"],
            "title": offer["title"],
            "author": offer["author"],
            "book_type": offer["book_type"],
            "updated": now,
        }
        if existing_book:
            updates.append(
                UpdateOne(
                    {"gtins.isbn13": offer_gtin},
                    {"$set": {f"offers.{book_offer_key}": book_offer}},
                )
            )
        else:
            new_book = {
                "title": offer["title"],
                "gtins": offer["gtins"],
                "offers": {book_offer_key: book_offer},
            }
            inserts.append(InsertOne(new_book))

    mongo_requests = [*inserts, *updates]

    logging.debug(f"Writing {len(mongo_requests)} updates and inserts")

    return book_collection.bulk_write(mongo_requests).bulk_api_result
