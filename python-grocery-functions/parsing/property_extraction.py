from transform.offer import get_field_from_scraper_offer
from typing import List
import re
import logging
import pydash
from amp_types.amp_product import (
    HandleConfig,
    ScraperOffer,
)

known_property_names = {
    "depth": {"type": "number", "property": "depth"},
    "breadth": {"type": "number", "property": "breadth"},
    "length": {"type": "number", "property": "length"},
}


def standardize_additional_properties(offer: ScraperOffer, config: HandleConfig):
    property_strings = list(
        get_field_from_scraper_offer(offer, key) for key in ["title", "subtitle"]
    )
    property_strings = list(x for x in property_strings if x)

    dimensions = extract_dimensions(property_strings)
    direct_properties = []

    for property_config in known_property_names.values():
        offer_value = get_field_from_scraper_offer(offer, property_config["property"])
        if offer_value:
            direct_properties.append(
                {"property": property_config["property"], "value": offer_value}
            )

    parsed_properties = extract_properties(
        [
            *property_strings,
            *list(
                prop.get("value", "")
                for prop in offer.get("additionalProperties", []) or []
            ),
        ]
    )

    return {
        prop["property"]: {"value": prop["value"], "property": prop["property"]}
        for prop in reversed([*direct_properties, *parsed_properties])
    }


dimension_pattern = (
    r"((?:\d+(?:,\d+)?)(?:\s*x\s*\d+(?:,\d+)?){1,2})"  # 30x40 or 40x40x0.5
)


def get_dimensions_object_from_string(dimension_string: str):
    dimensions = dimension_string.split("x")

    result = {}

    try:
        result["d"] = float(dimensions[0])
        result["b"] = float(dimensions[1])
    except IndexError:
        return {}
    try:
        result["l"] = float(dimensions[2])
    except IndexError:
        pass
    return result


def extract_dimensions(strings: List[str]):
    try:
        matches = pydash.flatten(
            list(
                re.findall(dimension_pattern, string.lower())
                for string in strings
                if string
            )
        )
        if len(matches) > 0:
            return re.sub(r"\s*", "", matches[0])
        else:
            return None
    except AttributeError as exc:
        logging.warning("" + str(exc) + "Could not extract number from: ")
        return None


def extract_properties(strings: List[str]):
    property_configs = [
        {
            "patterns": [r"c24", r"c34"],
            "property": "styrkegrad",
        },
        {
            "patterns": [r"tg2", r"tg4"],
            "property": "knotOgFjer",
        },
        {
            "patterns": [r"kl.1", r"kl1"],
            "property": "kvistKlasse",
            "value": "kl1",
        },
        {
            "patterns": [r"kl.2", r"kl2"],
            "property": "kvistKlasse",
            "value": "kl2",
        },
        {
            "patterns": [r"cuimp", r"impregnert"],
            "value": "impregnert",
            "property": "impreg",
        },
        {
            "patterns": [r"royalimpregnert"],
            "property": "impreg",
        },
        {
            "patterns": [r"furu"],
            "property": "treeSort",
        },
    ]
    properties: List = []
    for config in property_configs:
        for string in strings:
            if not string:
                continue
            for pattern in config["patterns"]:
                match = re.findall(pattern, string)
                if match:
                    value = config.get("value", match[0])
                    properties.append({"property": config["property"], "value": value})
    dimensions_string = extract_dimensions(strings)
    if dimensions_string:
        properties.append({"value": dimensions_string, "property": "dimensions"})
    return properties