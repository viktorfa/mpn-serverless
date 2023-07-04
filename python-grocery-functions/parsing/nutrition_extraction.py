import pydash
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
    "energyKcal",
    "energyKj",
    "kcals",
    "kjs",
]


def extract_nutritional_data(offer: ScraperOffer, config: HandleConfig):
    result = {}
    for key in macro_names:
        value_string = get_field_from_scraper_offer(offer, key)

        if value_string != 0 and not value_string:
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
        elif number is not None:
            result[key] = {
                "key": key,
                "value": number,
            }
    if result.get("energy") and result.get("energy").get("unit") == "kj":
        result["energy"]["value"] = round(result["energy"]["value"] * 0.2390057)
        result["energy"]["unit"] = result["energy"]["unit"] = "kcal"
    if pydash.get(result, "kcals.value") is not None:
        result["energyKcal"] = {
            "value": pydash.get(result, "kcals.value"),
            "key": "energyKcal",
        }
    elif pydash.get(result, "kjs.value") is not None:
        result["energyKcal"] = {
            "value": pydash.get(result, "kjs.value") * 0.2390057,
            "key": "energyKcal",
        }
    elif pydash.get(result, "energy.value") is not None:
        result["energyKcal"] = {
            "value": pydash.get(result, "energy.value"),
            "key": "energyKcal",
        }
    return result
