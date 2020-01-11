import logging

from scraper_feed.handle_products import handle_products
from storage.db import save_scraped_products, get_handle_config

from util.enums import provenances
from util.errors import NoHandleConfigError

DEFAULT_OFFER_COLLECTION_NAME = "mpnoffer"


def _get_handle_config(config: dict) -> dict:
    """
    Finds a handle config from a database or uses a default one.
    """
    result = {}

    try:
        result = {**get_handle_config(config.get("provenance"))}
    except NoHandleConfigError:
        result = {**config}
        result["collection_name"] = DEFAULT_OFFER_COLLECTION_NAME
    result["source"] = config.get("provenance")
    _result = {k: v for k, v in result.items() if v is not None}
    return _result


def handle_feed(feed: list, config: dict) -> dict:
    """
    Handles a feed from Scrapy according to the provided config.
    """

    _config = _get_handle_config(config)

    products = handle_products(feed, _config)
    result = save_scraped_products(products, _config["collection_name"])
    return result
