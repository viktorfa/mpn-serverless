from scraper_feed.handle_products import handle_products
from storage.db import save_scraped_products

from util.enums import provenances


provenance_to_collection_name_map = {
    "mpnoffer": (
        provenances.GOTTEBITEN,
        provenances.YOOLANDO,
        provenances.MAXGODIS,
        provenances.SWECANDY,
        provenances.HOLDBART,
    ),
    "groceryoffer": (
        provenances.KOLONIAL,
        provenances.MENY,
        provenances.EUROPRIS,
        provenances.SHOPGUN,
    ),
    "herbvuoffer": (provenances.IHERB, provenances.VITACOST,),
}

DEFAULT_OFFER_COLLECTION_NAME = "mpnoffer"


def populate_config(config: dict) -> dict:
    offers_collection_name = next(
        (
            key
            for key, value in provenance_to_collection_name_map.items()
            if config["provenance"] in value
        ),
        DEFAULT_OFFER_COLLECTION_NAME,
    )

    config["offers_collection_name"] = offers_collection_name
    config["source"] = config.get("provenance")
    return config


def handle_feed(feed: list, config: dict) -> dict:
    """
    Handles a feed from Scrapy according to the provided config.
    """

    _config = populate_config(config)

    products = handle_products(feed, _config)
    result = save_scraped_products(products, _config["offers_collection_name"])
    return result
