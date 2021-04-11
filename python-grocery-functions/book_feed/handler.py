import json

from book_feed.process_books import process_books


def handle_book_offers_trigger(event, context):
    return json.dumps(process_books(), default=str)