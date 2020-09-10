import logging
from typing import List

from pydash import get

from amp_types.amp_product import (
    MappingConfigField,
    ScraperOffer,
)
from transform.offer import get_field_from_scraper_offer


def add_to_destination(
    offer: ScraperOffer, value, field_config: MappingConfigField
) -> ScraperOffer:
    result = {**offer}
    a, *b = field_config["destination"].split(".")
    if a == "additionalProperties":
        destination = b[0]
        additional_property_item = {
            "key": destination,
            "value": value,
            "text": field_config.get("text"),
        }
        if get(result, ["additionalPropertyDict", destination]):
            if field_config.get("force_replace") is True:
                logging.debug(f"Replacing {field_config['destination']}.")
                result["additionalPropertyDict"][destination] = additional_property_item
            else:
                logging.debug(f"Avoid replacing {field_config['destination']}")
        else:
            logging.debug(f"Creating new field {field_config['destination']}.")
            if result.get("additionalPropertyDict"):
                result["additionalPropertyDict"][destination] = additional_property_item
            else:
                result["additionalPropertyDict"] = {
                    destination: additional_property_item
                }
    else:
        existing_value = offer.get(a)
        if existing_value:
            if field_config.get("force_replace") is True:
                logging.debug(f"Replacing {a}.")
                result[a] = value
            else:
                logging.debug(f"Avoid replacing {a}")
        else:
            logging.debug(f"Creating new field {a}.")
            result[a] = value
    return result


def transform_fields(
    offer: ScraperOffer, field_mapping: List[MappingConfigField]
) -> ScraperOffer:
    result = {**offer}
    for field_config in field_mapping:
        if field_config["replace_type"] == "fixed":
            result = add_to_destination(
                result, field_config["replace_value"], field_config
            )
        elif field_config["replace_type"] == "key":
            value = get_field_from_scraper_offer(offer, field_config["source"])
            result = add_to_destination(result, value, field_config)
        elif field_config["replace_type"] == "ignore":
            del result[field_config["destination"]]

    return result
