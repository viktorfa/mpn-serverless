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
        # Get the list of additional properties from the offer, or make it an empty list if the offer does not have an additionalProperties field.
        additional_properties = offer.get("additionalProperties", [])
        # If there are no additional properties, return the default value.
        if not additional_properties:
            return default

        # This loop iterates through the additional properties and finds the item with the correct key/name, or the result is None.
        result_property = None
        # A for in loop that breaks when the first item is found, and assigns this item to a variable, accomplishes the same as a find function.
        for additional_property in additional_properties:
            # Checking if either the additional property key or name in lowercase is equal to the key in lowercase is what the original lambda function did.
            # If this is true, the result property is set to the first additional property for which it is true and the loop stops iterating.
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


example_offer = {
    "additionalProperties": [
        {"key": "key1", "name": "name1", "value": "ap_value1"},
        {"key": "key2", "name": "name2", "value": "ap_value2"},
    ],
    "key1": "offer_value1",
    "key3": "offer_value3",
}

print(
    get_field_from_scraper_offer(example_offer, "key1", "default_value")
)  # Should print "offer_value1"
print(
    get_field_from_scraper_offer(example_offer, "key2", "default_value")
)  # Should print "ap_value2"
print(
    get_field_from_scraper_offer(example_offer, "key3", "default_value")
)  # Should print "offer_value3"
print(
    get_field_from_scraper_offer(example_offer, "key4", "default_value")
)  # Should print "default_value"
