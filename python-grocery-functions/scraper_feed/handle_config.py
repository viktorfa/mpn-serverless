from pydash import get


from scraper_feed.scraper_configs import (
    get_field_mapping,
    DEFAULT_EXTRACT_QUANTITY_FIELDS,
)
from storage.db import get_handle_config
from amp_types.amp_product import HandleConfig, ScraperConfig
from util.errors import NoHandleConfigError

DEFAULT_OFFER_COLLECTION_NAME = "mpnoffer"


def generate_handle_config(config: dict) -> HandleConfig:
    result = {}
    result["provenance"] = config["provenance"]
    result["collection_name"] = config["collection_name"]
    result["categoriesLimits"] = get(
        config, ["additionalConfig", "categoriesLimits"], []
    )
    result["fieldMapping"] = get_field_mapping(config.get("fieldMapping", []))
    result["extractQuantityFields"] = config.get(
        "extractQuantityFields", DEFAULT_EXTRACT_QUANTITY_FIELDS
    )
    return result


def fetch_handle_config(config: ScraperConfig) -> HandleConfig:
    """
    Finds a handle config from a database or uses a default one.
    """
    result = {}

    try:
        result = {**config, **get_handle_config(config.get("provenance"))}
    except NoHandleConfigError:
        result = {**config}
        result["collection_name"] = DEFAULT_OFFER_COLLECTION_NAME
    return generate_handle_config(result)
