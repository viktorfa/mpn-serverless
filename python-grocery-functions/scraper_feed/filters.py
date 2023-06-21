from typing import List
import pydash
import logging
from datetime import datetime, timedelta
from slugify import slugify

from storage.db import get_collection
from parsing.ingredients_extraction import get_ingredients_data
from parsing.nutrition_extraction import extract_nutritional_data
from parsing.category_extraction import extract_categories
from parsing.property_extraction import (
    extract_dimensions,
    extract_properties,
    standardize_additional_properties,
)

from util.helpers import is_integer_num

from transform.transform import transform_fields
from transform.offer import get_field_from_scraper_offer
from util.helpers import get_product_uri, json_time_to_datetime
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

from amp_types.amp_product import (
    MpnOffer,
    OfferFilterConfig,
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


def filter_product(product: MpnOffer, filters: List[OfferFilterConfig]):
    """
    Will return true if any of the filters are accepted. I.e. OR chaining."""

    if len(filters) == 0:
        return True

    for _filter in filters:
        op1 = pydash.get(product, _filter["source"])
        operator = _filter["operator"]
        op2 = _filter["target"]
        if not op1:
            continue
        if not op2:
            logging.error(_filter)
            raise Exception("Filter has no target operand")
        if type(op1) is str:
            op1 = op1.lower()
        elif type(op1) is list:
            op1 = list(x.lower() if type(x) is str else x for x in op1)
        if type(op2) is str:
            op2 = op2.lower()
        elif type(op2) is list:
            op2 = list(x.lower() if type(x) is str else x for x in op2)

        is_accepted = False

        if operator == "eq":
            is_accepted = op1 == op2
        elif operator == "has":
            is_accepted = op2 in op1
        elif operator == "in":
            is_accepted = op1 in op2
        elif operator == "gt":
            is_accepted = op1 > op2
        elif operator == "lt":
            is_accepted = op1 < op2
        if is_accepted:
            return True
    return False


def replace_offer_fields_with_meta(offer: ScraperOffer, offer_meta):
    for key, value in offer_meta.get("auto", {}).items():
        offer[key] = value["value"]
    for key, value in offer_meta.get("manual", {}).items():
        offer[key] = value["value"]
    return offer


def transform_product(
    offer: ScraperOffer,
    config: HandleConfig,
    ingredients_data,
) -> MpnOffer:
    time.set_time(config.get("scrape_time", datetime.utcnow()))
    result: MpnOffer = {}
    # Still handle Shopgun offers a little differently..
    namespace = config["namespace"]
    if "shopgun" in config["provenance"]:
        result = transform_shopgun_product(offer, config)
    else:
        # Start here for everything not Shopgun offer.
        result: MpnOffer = {}

        offer = transform_fields(offer, config["fieldMapping"])

        provenance_id = get_provenance_id(offer)

        offer["uri"] = get_product_uri(namespace, provenance_id)

        result["provenanceId"] = provenance_id
        result["href"] = offer["url"]
        result["ahref"] = offer.get("trackingUrl")

        result["uri"] = get_product_uri(namespace, provenance_id)
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
    if result["validThrough"].timestamp() > time.time.timestamp():
        result["isRecent"] = True
    else:
        result["isRecent"] = False
    result["market"] = config["market"]
    result["isPartner"] = config.get("is_partner", False)
    dealer_key = slugify(result["dealer"], separator="_")
    vendor_key = slugify(offer.get("vendor", "") or "", separator="_")
    brand_key = slugify(offer.get("brand", "") or "", separator="_")

    result["dealerKey"] = dealer_key
    if vendor_key:
        result["vendorKey"] = vendor_key
    if brand_key:
        result["brandKey"] = brand_key

    result["mpnProperties"] = standardize_additional_properties(offer, config)
    if config["collection_name"] in ["groceryoffers"]:
        result["mpnIngredients"] = get_ingredients_data(offer, config, ingredients_data)
    result["mpnNutrition"] = extract_nutritional_data(offer, config)
    if config["provenance"] == "meny_api_spider":
        result["mpnCategories"] = extract_categories({**offer, **result}, config)

    result = analyze_quantity({**offer, **result})
    result = standardize_quantity(result)
    quantity = result.get("quantity")

    # Only include necessary fields to save db space
    final_result = pydash.pick(
        {**offer, **result, **quantity},
        [
            "title",
            "subtitle",
            "shortDescription",
            "description",
            "categories",
            "provenance",
            "market",
            "dealer",
            "dealerKey",
            "brand",
            "brandKey",
            "vendor",
            "vendorKey",
            "pricing",
            "value",
            "quantity",
            "items",
            "uri",
            "href",
            "ahref",
            "trackingUrl",
            "imageUrl",
            "gtins",
            "mpnStock",
            "mpnNutrition",
            "mpnProperties",
            "mpnIngredients",
            "mpnCategories",
            "validFrom",
            "validThrough",
            "siteCollection",
            "isPartner",
            "isRecent",
            "provenanceId",
            "sku",
            "scrapeBatchId",
            # Book products
            "book_uri",
            "isbn",
            "isbn10",
            "isbn13",
        ],
    )

    if config["ignore_none"]:
        # Some offers with 2 provenances such as Byggmax.no and Byggmax feed will have ignore quantity
        # on Byggmax feed
        final_result = remove_none_fields(final_result)

    return final_result


def transform_and_filter_offers(
    offers: List[ScraperOffer], config: HandleConfig
) -> List[MpnOffer]:
    ingredients_data = {}
    if (
        config["collection_name"] in ["groceryoffers"]
        and len(config.get("extractIngredientsFields", [])) > 0
    ):
        ingredients_collection = get_collection("ingredients")
        db_ingredients = ingredients_collection.find({})
        for x in db_ingredients:
            ingredients_data[x["key"]] = x

    transformed_offers = (
        transform_product(
            x,
            config,
            ingredients_data=ingredients_data,
        )
        for x in offers
    )
    filters = pydash.get(config, ["filters"], [])

    if len(filters) == 0:
        return list(transformed_offers)

    filtered_offers = list(x for x in transformed_offers if filter_product(x, filters))

    return filtered_offers


def get_categories(categories, categories_limits):
    """
    Potentially shaves off the first or last or both entries in a product's category list, according
    to the handle config, since breadcrumbs often include the product name and the root category like "Home".
    """
    try:
        start_index, end_index = [*categories_limits, None, None][:2]
        if is_integer_num(start_index) and not is_integer_num(end_index):
            return categories[start_index:]
        elif is_integer_num(end_index) and not is_integer_num(start_index):
            return categories[:end_index]
        elif is_integer_num(start_index) and is_integer_num(end_index):
            return categories[start_index:end_index]
        return categories
    except Exception:
        return categories
