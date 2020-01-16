import logging
from datetime import datetime
from datetime import timedelta
from typing import List

import pydash

from util.helpers import get_product_uri
from util.enums import provenances
from util.quantity_extraction import analyze_quantity
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
)
from scraper_feed.scraper_configs import get_field_map


now = datetime.utcnow()
one_week_ahead = now + timedelta(7)


def handle_products(
    products: List[ScraperOffer], config: ScraperConfig
) -> List[MpnOffer]:
    now = datetime.utcnow()
    one_week_ahead = now + timedelta(7)
    mapping_config = get_field_map(config)
    logging.info("Using handle config:")
    logging.info(config)
    logging.info("Using mapping config:")
    logging.info(mapping_config)
    return list(map(lambda x: transform_product(x, mapping_config, config), products))


def transform_product(
    product: ScraperOffer, mapping_config: MappingConfig, config: ScraperConfig
) -> MpnOffer:
    # Still handle Shopgun offers a little differently..
    if config["source"] == provenances.SHOPGUN:
        return transform_shopgun_product(product)
    if config["source"] == provenances.SHOPGUN_BYGG:
        return transform_shopgun_product(product)
    result = {}
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
            if k in mapping_config["extractQuantityFields"]
        ),
        *list(
            v["value"]
            for k, v in additional_property_map.items()
            if k in mapping_config["extractQuantityFields"]
        ),
    ]
    analyzed_product = analyze_quantity(pydash.flatten(quantity_strings))
    transformed_additional_properties = {
        k: transform_field(v) for k, v in additional_property_map.items()
    }
    result["gtins"] = get_gtins({**product, **result})
    result["validThrough"] = one_week_ahead
    result["validFrom"] = now
    result["dealer"] = result.get("dealer", config["source"])

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

