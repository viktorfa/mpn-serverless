import logging
import pydash
from typing import List


from scraper_feed.scraper_configs import (
    DEFAULT_EXTRACT_INGREDIENTS_FIELDS,
    DEFAULT_EXTRACT_PROPERTIES_FIELDS,
    get_field_mapping,
    DEFAULT_EXTRACT_QUANTITY_FIELDS,
)
from storage.db import get_handle_configs
from amp_types.amp_product import HandleConfig, ScraperConfig
from util.errors import NoHandleConfigError


def generate_handle_config(config: dict) -> HandleConfig:
    result = {}
    result["provenance"] = config["provenance"]
    result["namespace"] = config["namespace"]
    result["collection_name"] = config["collection_name"]
    result["market"] = config["market"]
    result["is_partner"] = config.get("is_partner", False)
    result["categoriesLimits"] = pydash.get(
        config, ["additionalConfig", "categoriesLimits"], []
    )
    result["filters"] = pydash.get(config, ["additionalConfig", "filters"], [])
    result["fieldMapping"] = get_field_mapping(config.get("fieldMapping", []))
    extract_quantity_fields = config.get(
        "extractQuantityFields", DEFAULT_EXTRACT_QUANTITY_FIELDS
    )

    result["extractQuantityFields"] = (
        extract_quantity_fields
        if type(extract_quantity_fields) is list
        else DEFAULT_EXTRACT_QUANTITY_FIELDS
    )
    extract_properties_fields = pydash.get(
        config,
        ["additionalConfig", "extractPropertiesFields"],
        DEFAULT_EXTRACT_PROPERTIES_FIELDS,
    )
    extract_ingredients_fields = pydash.get(
        config,
        ["additionalConfig", "extractIngredientsFields"],
        DEFAULT_EXTRACT_INGREDIENTS_FIELDS,
    )
    result["extractPropertiesFields"] = (
        extract_properties_fields
        if type(extract_properties_fields) is list
        else DEFAULT_EXTRACT_PROPERTIES_FIELDS
    )
    result["extractIngredientsFields"] = (
        extract_ingredients_fields
        if type(extract_ingredients_fields) is list
        else DEFAULT_EXTRACT_INGREDIENTS_FIELDS
    )
    result["ignore_none"] = pydash.get(
        config, ["additionalConfig", "ignoreNone"], False
    )
    return result


def fetch_handle_configs(provenance: str) -> List[HandleConfig]:
    """
    Finds a handle config from a database or uses a default one.
    """

    try:
        return list(generate_handle_config(x) for x in get_handle_configs(provenance))
    except NoHandleConfigError:
        logging.warn("No handle config found")
        raise NoHandleConfigError()
