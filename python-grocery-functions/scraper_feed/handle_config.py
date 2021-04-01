import logging
from typing import List
from pydash import get


from scraper_feed.scraper_configs import (
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
    result["categoriesLimits"] = get(
        config, ["additionalConfig", "categoriesLimits"], []
    )
    result["filters"] = get(config, ["additionalConfig", "filters"], [])
    result["fieldMapping"] = get_field_mapping(config.get("fieldMapping", []))
    extract_quantity_fields = config.get(
        "extractQuantityFields", DEFAULT_EXTRACT_QUANTITY_FIELDS
    )
    result["extractQuantityFields"] = (
        extract_quantity_fields
        if type(extract_quantity_fields) is list
        else DEFAULT_EXTRACT_QUANTITY_FIELDS
    )
    result["ignore_none"] = get(config, ["additionalConfig", "ignoreNone"], False)
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
