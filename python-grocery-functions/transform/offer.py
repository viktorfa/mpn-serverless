import logging
from typing import Any, NotRequired, TypedDict

from pydash import get


class AdditionalProperty(TypedDict):
    key: NotRequired[str]
    name: NotRequired[str]
    value: Any


class Offer(TypedDict):
    additionalProperties: NotRequired[list[AdditionalProperty]]


def get_field_from_scraper_offer(offer: Offer, key: str, default: Any = None):
    if get(offer, key) is not None:
        return get(offer, key, default)
    # The original lambda function checked if the key was truthy, and would return the default otherwise.
    elif not key:
        return default
    else:
        # Get the list of additional properties from the offer, or empty list if none exists.
        additional_properties = offer.get("additionalProperties", [])
        # If there are no additional properties, return the default value.
        if not additional_properties:
            return default

        # Loop through additional properties to find matching key/name
        result_property = None
        # Find first item with matching key or name (case insensitive)
        for additional_property in additional_properties:
            # Check if property key or name matches the search key (case insensitive)
            # If match found, set result and break
            property_key_lower = additional_property.get("key", "").lower()
            property_name_lower = additional_property.get("name", "").lower()
            if key.lower() in [property_key_lower, property_name_lower]:
                result_property = additional_property
                break

        if result_property is None:
            return default
        try:
            return result_property["value"]
        except KeyError:
            logging.warning("Additional property in scraper offer without value field.")
            logging.warning(result_property)
