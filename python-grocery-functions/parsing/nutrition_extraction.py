import logging

from transform.offer import get_field_from_scraper_offer
from amp_types.amp_product import HandleConfig, ScraperOffer
from parsing.parsing import extract_number_unit_pairs, extract_number

macro_names = [
    "fats",
    "carbohydrates",
    "proteins",
    "satFats",
    "monoFats",
    "polyFats",
    "salt",
    "polyols",
    "fibers",
    "starch",
    "sugars",
    "energy",
    "kcals",
    "kjs",
]


def extract_nutritional_data(offer: ScraperOffer, config: HandleConfig):
    result = {}
    for key in macro_names:
        value_string = get_field_from_scraper_offer(offer, key)

        if not value_string:
            continue

        try:
            number = float(value_string)
            result[key] = {
                "key": key,
                "value": number,
            }
            continue
        except ValueError:
            pass
        unit_pairs = extract_number_unit_pairs(value_string)
        number = extract_number(value_string)

        if unit_pairs:
            idx = 0
            if key == "energy":
                for i, pair in enumerate(unit_pairs):
                    if pair[1].lower() == "kcal":
                        idx = i
                        break
            elif key == "kcals":
                for i, pair in enumerate(unit_pairs):
                    if pair[1].lower() == "kcal":
                        idx = i
                        break
            if key == "kjs":
                for i, pair in enumerate(unit_pairs):
                    if pair[1].lower() == "kj":
                        idx = i
                        break

            result[key] = {
                "key": key,
                "value": unit_pairs[idx][0],
                "unit": unit_pairs[idx][1],
            }
        elif number:
            result[key] = {
                "key": key,
                "value": number,
            }
    return result