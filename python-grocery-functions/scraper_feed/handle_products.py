import logging

from typing import Iterable, List

from scraper_feed.filters import transform_and_filter_offers

from amp_types.amp_product import (
    HandleConfig,
    MpnOffer,
    ScraperOffer,
)


def handle_products(
    products: List[ScraperOffer], config: HandleConfig
) -> Iterable[MpnOffer]:
    """
    Transforms products straight from the scraper feed into MpnOffers.
    """
    logging.info("Using handle config:")
    logging.info(config)

    filtered_offers = transform_and_filter_offers(products, config)

    return filtered_offers
