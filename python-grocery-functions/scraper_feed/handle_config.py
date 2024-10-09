import logging
import pydash
from typing import List

from scraper_feed.scraper_configs import (
    DEFAULT_EXTRACT_INGREDIENTS_FIELDS,
    DEFAULT_EXTRACT_PROPERTIES_FIELDS,
    get_field_mapping,
    DEFAULT_EXTRACT_QUANTITY_FIELDS,
    DEFAULT_EXTRACT_CATEGORIES_FIELD,
)
from storage.db import get_handle_configs, get_single_handle_config
from amp_types.amp_product import HandleConfig
from storage.postgres.postgres_tables import HandleConfigsTable
from storage.postgres.pydantic_models import PydanticHandleConfig
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
    categories_field = pydash.get(
        config,
        ["additionalConfig", "categoriesField"],
        DEFAULT_EXTRACT_CATEGORIES_FIELD,
    )
    result["categoriesField"] = (
        categories_field
        if type(categories_field) is str
        else DEFAULT_EXTRACT_CATEGORIES_FIELD
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


def fetch_single_handle_config(provenance: str) -> HandleConfig:
    """
    Finds a handle config from a database or uses a default one.
    """

    try:
        return generate_handle_config(get_single_handle_config(provenance))
    except NoHandleConfigError:
        logging.warn("No handle config found")
        raise NoHandleConfigError()


def generate_handle_config_postgres(config: HandleConfigsTable) -> PydanticHandleConfig:
    result = {}
    result["id"] = str(config.id)
    result["provenance"] = config.provenance
    result["namespace"] = config.namespace
    result["context"] = (
        config.context
    )  # Assuming `collection_name` is stored as `site_collection`
    result["market"] = config.market
    result["is_partner"] = config.is_partner

    # Get additionalConfig data from the JSONB column
    additional_config = (
        config.additional_config if bool(config.additional_config) else {}
    )

    result["categoriesLimits"] = pydash.get(additional_config, "categoriesLimits", [])
    result["filters"] = pydash.get(additional_config, "filters", [])

    # Process field_mapping
    result["fieldMapping"] = get_field_mapping(
        config.field_mapping if bool(config.field_mapping) else []
    )

    # Extract quantity fields
    extract_quantity_fields = (
        config.extract_quantity_fields
        if bool(config.extract_quantity_fields)
        else DEFAULT_EXTRACT_QUANTITY_FIELDS
    )
    result["extractQuantityFields"] = (
        extract_quantity_fields
        if isinstance(extract_quantity_fields, list)
        else DEFAULT_EXTRACT_QUANTITY_FIELDS
    )

    # Extract properties, ingredients, and categories fields with defaults
    extract_properties_fields = pydash.get(
        additional_config, "extractPropertiesFields", DEFAULT_EXTRACT_PROPERTIES_FIELDS
    )
    extract_ingredients_fields = pydash.get(
        additional_config,
        "extractIngredientsFields",
        DEFAULT_EXTRACT_INGREDIENTS_FIELDS,
    )
    categories_field = pydash.get(
        additional_config, "categoriesField", DEFAULT_EXTRACT_CATEGORIES_FIELD
    )

    result["categoriesField"] = (
        categories_field
        if isinstance(categories_field, str)
        else DEFAULT_EXTRACT_CATEGORIES_FIELD
    )
    result["extractPropertiesFields"] = (
        extract_properties_fields
        if isinstance(extract_properties_fields, list)
        else DEFAULT_EXTRACT_PROPERTIES_FIELDS
    )
    result["extractIngredientsFields"] = (
        extract_ingredients_fields
        if isinstance(extract_ingredients_fields, list)
        else DEFAULT_EXTRACT_INGREDIENTS_FIELDS
    )

    # Handle ignore_none field
    result["ignore_none"] = pydash.get(additional_config, "ignoreNone", False)

    return PydanticHandleConfig(**result)
