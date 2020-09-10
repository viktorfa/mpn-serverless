import logging
from datetime import datetime
from datetime import timedelta
from typing import List

import pydash

from transform.transform import transform_fields
from transform.offer import get_field_from_scraper_offer
from util.helpers import get_product_uri, is_integer_num
from util.enums import provenances
from parsing.quantity_extraction import (
    analyze_quantity,
    parse_quantity,
    standardize_quantity,
)
from amp_types.amp_product import (
    HandleConfig,
    MpnOffer,
    ScraperOffer,
)
from scraper_feed.handle_shopgun_offers import transform_shopgun_product
from scraper_feed.helpers import (
    get_gtins,
    get_product_pricing,
    get_provenance_id,
    get_stock_status,
)


class MyTime(object):
    def __init__(self):
        self.set_time(datetime.utcnow())

    def set_time(self, time):
        self._time = time
        self._one_week_ahead = self._time + timedelta(7)

    @property
    def time(self):
        return self._time

    @property
    def one_week_ahead(self):
        return self._one_week_ahead


global time
time = MyTime()


def handle_products(
    products: List[ScraperOffer], config: HandleConfig
) -> List[MpnOffer]:
    """
    Transforms products straight from the scraper feed into MpnOffers.
    """
    time.set_time(config.get("scrape_time", datetime.utcnow()))
    logging.info("Using handle config:")
    logging.info(config)
    return list(transform_product(x, config) for x in products)


def get_categories(categories, categories_limits):
    """
    Potentially shaves off the first or last or both entries in a product's category list, according
    to the handle config, since breadcrumbs often include the product name and the root category like "Home".
    """
    try:
        start_index, end_index = categories_limits
        if is_integer_num(start_index) and not is_integer_num(end_index):
            return categories[start_index:]
        elif is_integer_num(end_index) and not is_integer_num(start_index):
            return categories[:end_index]
        elif is_integer_num(start_index) and is_integer_num(end_index):
            return categories[start_index:end_index]
        return categories
    except Exception:
        return categories


def transform_product(product: ScraperOffer, config: HandleConfig) -> MpnOffer:
    result: MpnOffer = {}
    # Still handle Shopgun offers a little differently..
    if config["provenance"] == provenances.SHOPGUN:
        result = transform_shopgun_product(product)
    elif config["provenance"] == provenances.SHOPGUN_BYGG:
        result = transform_shopgun_product(product)
    else:
        # Start here for everything not Shopgun offer.
        product = transform_fields(product, config["fieldMapping"])
        result: MpnOffer = {}

        provenanceId = get_provenance_id(product)
        result["provenanceId"] = provenanceId
        result["uri"] = get_product_uri(config["provenance"], provenanceId)
        result["pricing"] = get_product_pricing({**product, **result})
        result["validThrough"] = time.one_week_ahead
        result["validFrom"] = time.time
        result["dealer"] = result.get("dealer", config["provenance"])
        result["gtins"] = get_gtins({**product, **result})

        quantity_strings = list(
            get_field_from_scraper_offer(product, key)
            for key in config["extractQuantityFields"]
        )
        analyzed_product = parse_quantity(list(x for x in quantity_strings if x))
        result["mpnStock"] = get_stock_status(product)
        result["categories"] = get_categories(
            pydash.get(product, "categories"), config["categoriesLimits"],
        )
        result = {**result, **analyzed_product}

    result = analyze_quantity(result)
    result = standardize_quantity(result)
    quantity = result.get("quantity")

    return {**product, **result, **quantity}
