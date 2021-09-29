import logging
from datetime import datetime
from datetime import timedelta
from parsing.ingredients_extraction import extract_ingredients
from parsing.nutrition_extraction import extract_nutritional_data
from parsing.category_extraction import extract_categories
from parsing.property_extraction import (
    extract_dimensions,
    extract_properties,
    standardize_additional_properties,
)
from typing import Iterable, List

import pydash

from transform.transform import transform_fields
from transform.offer import get_field_from_scraper_offer
from util.helpers import get_product_uri, is_integer_num, json_time_to_datetime
from scraper_feed.filters import filter_product
from parsing.quantity_extraction import (
    analyze_quantity,
    parse_quantity,
    standardize_quantity,
    parse_explicit_quantity,
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
    remove_none_fields,
)


class MyTime(object):
    def __init__(self):
        self.set_time(datetime.utcnow())

    def set_time(self, time):
        self._time = time
        self._one_week_ahead = self._time + timedelta(days=7, hours=4)
        self._ten_days_ahead = self._time + timedelta(days=10, hours=4)

    @property
    def time(self):
        return self._time

    @property
    def one_week_ahead(self):
        return self._one_week_ahead

    @property
    def ten_days_ahead(self):
        return self._ten_days_ahead


global time
time = MyTime()


def handle_products(
    products: List[ScraperOffer], config: HandleConfig
) -> Iterable[MpnOffer]:
    """
    Transforms products straight from the scraper feed into MpnOffers.
    """
    time.set_time(config.get("scrape_time", datetime.utcnow()))
    logging.info("Using handle config:")
    logging.info(config)
    transformed_products = (transform_product(x, config) for x in products)
    filters = pydash.get(config, ["filters"], [])
    if len(filters) == 0:
        return list(transformed_products)
    else:
        return list(x for x in transformed_products if filter_product(x, filters))


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


def transform_product(offer: ScraperOffer, config: HandleConfig) -> MpnOffer:
    result: MpnOffer = {}
    # Still handle Shopgun offers a little differently..
    if "shopgun" in config["provenance"]:
        result = transform_shopgun_product(offer, config)
    else:
        # Start here for everything not Shopgun offer.
        offer = transform_fields(offer, config["fieldMapping"])
        result: MpnOffer = {}

        namespace = config["namespace"]
        provenanceId = get_provenance_id(offer)
        result["provenanceId"] = provenanceId
        result["href"] = offer["url"]
        result["ahref"] = offer.get("trackingUrl")

        result["uri"] = get_product_uri(namespace, provenanceId)
        result["pricing"] = get_product_pricing({**offer, **result})
        try:
            result["validThrough"] = json_time_to_datetime(offer["validThrough"])
        except Exception:
            result["validThrough"] = time.ten_days_ahead
        try:
            result["validFrom"] = json_time_to_datetime(offer["validFrom"])
        except Exception:
            result["validFrom"] = time.time

        result["dealer"] = offer.get("dealer", namespace)
        result["gtins"] = get_gtins({**offer, **result})

        result["dimensions"] = extract_dimensions(
            [
                get_field_from_scraper_offer(offer, "dimensions"),
                offer.get("title"),
                offer.get("description", ""),
                offer.get("subtitle", ""),
            ]
        )
        result["properties"] = extract_properties(
            [
                offer.get("title"),
                offer.get("description", ""),
                offer.get("subtitle", ""),
            ]
        )

        try:
            result["imageUrl"] = result["imageUrl"].replace("http://", "https://")
        except Exception:
            pass

        # Handle quantity from scraper by parsing it like a string
        extra_quantity_string = " ".join(
            (
                str(offer[key])
                for key in ("rawQuantity", "rawValue", "quantityValue", "quantityUnit")
                if offer.get(key)
            ),
        )

        parse_quantity_strings = list(
            get_field_from_scraper_offer(offer, key)
            for key in config["extractQuantityFields"]
        )
        if extra_quantity_string:
            parse_quantity_strings.append(extra_quantity_string)

        safe_unit_list = ["l", "kg"] if "grocery" in config["collection_name"] else None

        parsed_quantity = parse_quantity(
            list(x for x in parse_quantity_strings if x), safe_unit_list
        )
        if config["ignore_none"]:
            for k, v in parsed_quantity.items():
                if remove_none_fields(v):
                    parsed_quantity[k] = v
                else:
                    parsed_quantity[k] = {}

        parsed_explicit_quantity = parse_explicit_quantity(offer, config)
        parsed_quantity = {
            **parsed_quantity,
            **parsed_explicit_quantity,
        }
        result["mpnStock"] = get_stock_status(offer)
        result["categories"] = get_categories(
            pydash.get(offer, "categories"),
            config["categoriesLimits"],
        )
        result = {**result, **parsed_quantity}

    result["market"] = config["market"]
    result["isPartner"] = config.get("is_partner", False)

    result["mpnProperties"] = standardize_additional_properties(offer, config)
    result["mpnIngredients"] = extract_ingredients(offer, config)
    result["mpnNutrition"] = extract_nutritional_data(offer, config)
    result["mpnCategories"] = extract_categories({**offer, **result}, config)

    result = analyze_quantity({**offer, **result})
    result = standardize_quantity(result)
    quantity = result.get("quantity")

    final_result = {**offer, **result, **quantity}

    if config["ignore_none"]:
        # Some offers with 2 provenances such as Byggmax.no and Byggmax feed will have ignore quantity
        # on Byggmax feed
        final_result = remove_none_fields(final_result)

    return final_result
