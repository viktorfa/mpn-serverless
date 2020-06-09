import logging
from datetime import datetime
from datetime import timedelta
from typing import List

import pydash

from util.helpers import get_product_uri
from util.enums import provenances
from parsing.quantity_extraction import analyze_quantity
from amp_types.amp_product import (
    MpnOffer,
    ScraperOffer,
    ScraperConfig,
    MappingConfig,
)
from scraper_feed.handle_shopgun_offers import transform_shopgun_product
from scraper_feed.helpers import (
    get_gtins,
    get_product_pricing,
    get_provenance_id,
    transform_field,
    get_stock_status,
)
from scraper_feed.scraper_configs import get_field_map


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
    products: List[ScraperOffer], config: ScraperConfig
) -> List[MpnOffer]:
    time.set_time(config.get("scrape_time", datetime.utcnow()))
    mapping_config = get_field_map(config)
    logging.info("Using handle config:")
    logging.info(config)
    logging.info("Using mapping config:")
    logging.info(mapping_config)
    return list(map(lambda x: transform_product(x, mapping_config, config), products))


def is_integer_num(n):
    if isinstance(n, int):
        return True
    if isinstance(n, float):
        return n.is_integer()
    return False


def get_categories(categories, categories_limits):
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


def transform_product(
    product: ScraperOffer, mapping_config: MappingConfig, config: ScraperConfig
) -> MpnOffer:
    # Still handle Shopgun offers a little differently..
    if config["source"] == provenances.SHOPGUN:
        return transform_shopgun_product(product)
    if config["source"] == provenances.SHOPGUN_BYGG:
        return transform_shopgun_product(product)
    result = {}
    ignore_fields = pydash.get(config, "additionalConfig.ignoreFields") or []
    for field_name in ignore_fields:
        del product[field_name]
    additional_property_map = {
        x["key"]: x for x in product.get("additionalProperty") or []
    }
    for original_key, target_key in mapping_config["fields"].items():
        value = pydash.get(product, original_key)
        if value is not None:
            if type(target_key) is str:
                result[target_key] = value
            elif type(target_key) is list:
                for _tk in target_key:
                    result[_tk] = value

    result["pricing"] = get_product_pricing({**product, **result})
    provenance_id = get_provenance_id(product)
    result["uri"] = get_product_uri(config["source"], provenance_id)
    result["provenanceId"] = provenance_id

    quantity_strings = [
        *list(
            v
            for k, v in product.items()
            if k in mapping_config["extractQuantityFields"] and v
        ),
        *list(
            v["value"]
            for k, v in additional_property_map.items()
            if k in mapping_config["extractQuantityFields"] and v
        ),
    ]
    analyzed_product = analyze_quantity(pydash.flatten(quantity_strings))
    transformed_additional_properties = {
        k: transform_field(v) for k, v in additional_property_map.items()
    }
    result["gtins"] = get_gtins({**product, **result})
    result["validThrough"] = time.one_week_ahead
    result["validFrom"] = time.time
    result["dealer"] = result.get("dealer", config["source"])
    result["mpnStock"] = get_stock_status(product)
    result["categories"] = get_categories(
        pydash.get(product, "categories"),
        pydash.get(config, "additionalConfig.categoriesLimits"),
    )

    analyzed_quantity = analyzed_product.get("quantity", None) or {
        "size": None,
        "pieces": None,
    }
    return {
        **result,
        **analyzed_quantity,
        **analyzed_product,
        **transformed_additional_properties,
    }
