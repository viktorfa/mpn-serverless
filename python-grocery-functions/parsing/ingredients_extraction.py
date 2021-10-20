import re
import logging
import pydash
from typing import List

from transform.offer import get_field_from_scraper_offer
from amp_types.amp_product import HandleConfig, ScraperOffer

ingredients_config = [
    {"patterns": [r"sukker"], "property": "sugar"},
    {"patterns": [r"egg"], "property": "egg"},
    {"patterns": [r"maismel"], "property": "cornMeal"},
    {"patterns": [r"rapsolje"], "property": "rapeSeedOil"},
    {"patterns": [r"glukosesirup"], "property": "glucoseSyrup"},
    {"patterns": [r"xantangummi"], "property": "xantanGum"},
    {"patterns": [r"melkepulver"], "property": "milkPowder"},
    {"patterns": [r"karbondioksid", r"kullsyre"], "property": "co2"},
    {"patterns": [r"sitronsyre"], "property": "citricAcid"},
    {"patterns": [r"aspartam"], "property": "aspartam"},
    {"patterns": [r"stevia"], "property": "stevia"},
    {"patterns": [r"kokosolje"], "property": "coconutOil"},
    {"patterns": [r"modifisert stivelse"], "property": "modifiedStarch"},
    {"patterns": [r"stivelse"], "property": "starch"},
    {"patterns": [r"havsalt"], "property": "seaSalt"},
    {"patterns": [r"risprotein"], "property": "riceProtein"},
    {"patterns": [r"aroma"], "property": "aroma"},
    {"patterns": [r"olivenekstrakt"], "property": "oliveExtract"},
    {"patterns": [r"vann"], "property": "aqua"},
    {"patterns": [r"kaffein"], "property": "caffeine"},
    {"patterns": [r"havre"], "property": "oats"},
    {"patterns": [r"kakaosmør"], "property": "cocoaButter"},
    {"patterns": [r"kakaomasse"], "property": "cocoaMass"},
    {"patterns": [r"lime"], "property": "lime"},
    {"patterns": [r"melkspulver"], "property": "milkPowder"},
    {"patterns": [r"tørrmelk"], "property": "dryMilk"},
    {"patterns": [r"hasselnøtter"], "property": "hazelNuts"},
    {"patterns": [r"dekstrose"], "property": "dextrose"},
    {"patterns": [r"fløtepulver"], "property": "dryCream"},
    {"patterns": [r"gjærekstrakt"], "property": "yeastExtract"},
    {"patterns": [r"ostepulver"], "property": "cheesePowder"},
    {"patterns": [r"avokadoolje"], "property": "avocadoOil"},
    {"patterns": [r"potet"], "property": "potato"},
    {"patterns": [r"peanøtter"], "property": "peanuts"},
    {"patterns": [r"rismel"], "property": "riceFlour"},
    {"patterns": [r"glukosesirup"], "property": "glucoseSyrup"},
    {"patterns": [r"eddik"], "property": "vinegar"},
]


def extract_e_number(string: str):
    matches = re.findall(r"[Ee]\d{3}[a-z]?", re.sub(r"\s", "", string))
    if matches:
        return matches[0]
    else:
        return ""


def extract_ingredients(offer: ScraperOffer, config: HandleConfig) -> List[str]:
    result: dict = {}
    for key in config["extractIngredientsFields"]:
        if len(result.keys()) > 0:
            continue
        raw_ingredients = get_field_from_scraper_offer(offer, key)
        if raw_ingredients:
            for string in raw_ingredients.split(", "):
                e_number = extract_e_number(string)
                if e_number:
                    result[e_number.lower()] = {"name": string, "key": e_number}
                    continue
                for config in ingredients_config:
                    config_key = config["property"]
                    if pydash.get(result, [config_key, "name"]) == string:
                        break
                    for pattern in config["patterns"]:
                        if re.findall(pattern, string, re.IGNORECASE):
                            result[config_key] = {"name": string, "key": config_key}
                            break

    return result
