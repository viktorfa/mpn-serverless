import re
import json
import os
import logging
import pydash
from typing import Iterable, List

from transform.offer import get_field_from_scraper_offer
from amp_types.amp_product import HandleConfig, ScraperOffer


with open(
    os.path.join(os.path.dirname(os.path.realpath(__file__)), "ingredients-data.json")
) as ingredients_data_file:
    ingredients_data = json.load(ingredients_data_file)

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
    {"patterns": [r"acesulfam K", r"E950"], "property": "e950"},
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
    {"patterns": [r"fløtepulver"], "property": "dryCream"},
    {"patterns": [r"gjærekstrakt"], "property": "yeastExtract"},
    {"patterns": [r"ostepulver"], "property": "cheesePowder"},
    {"patterns": [r"avokadoolje"], "property": "avocadoOil"},
    {"patterns": [r"potet"], "property": "potato"},
    {"patterns": [r"peanøtter"], "property": "peanuts"},
    {"patterns": [r"rismel"], "property": "riceFlour"},
    {"patterns": [r"glukosesirup"], "property": "glucoseSyrup"},
    {"patterns": [r"eddik"], "property": "vinegar"},
    {"patterns": [r"so[jy]aolje"], "property": "soyOil"},
    {"patterns": [r"so[jy]aprotein"], "property": "soyProtein"},
    {"patterns": [r"mysepulver"], "property": "wheyPowder"},
    {"patterns": [r"kasein"], "property": "casein"},
    {"patterns": [r"laktose"], "property": "lactose"},
    {"patterns": [r"dekstrose", r"dextrose"], "property": "dextrose"},
    {"patterns": [r"polydekstrose", r"polydextrose"], "property": "polyDextrose"},
    {"patterns": [r"emulgator"], "property": "emulgator"},
    {"patterns": [r"betakaroten"], "property": "betakaroten"},
    {"patterns": [r"stabilisator"], "property": "stabilizer"},
    {"patterns": [r"pektin"], "property": "pectin"},
    {"patterns": [r"sheafett"], "property": "sheaFat"},
    {"patterns": [r"johannesbrødkjernemel"], "property": "e410"},
    {"patterns": [r"guarkjernemel"], "property": "e412"},
    {"patterns": [r"sitrusfiber"], "property": "citrusFiber"},
    {"patterns": [r"natriumsitrat"], "property": "sodiumCitrate"},
    {"patterns": [r"kaliumklorid"], "property": "potassiumChloride"},
    {"patterns": [r"kalsiumklorid"], "property": "calsiumChloride"},
    {"patterns": [r"askorbinsyre"], "property": "ascorbate"},
    {"patterns": [r"natriumnitritt"], "property": "sodiumNitrite"},
    {"patterns": [r"kaliumdisulfitt"], "property": "potassiumDiSulfite"},
    {"patterns": [r"kaliumsorbat"], "property": "potassiumSorbate"},
    {"patterns": [r"acetylert"], "property": "e1420"},
    {"patterns": [r"distivelsesadipat"], "property": "e1422"},
    {"patterns": [r"vegetabilsk olje"], "property": "vegetableOil"},
    {"patterns": [r"palmeolje"], "property": "palmOil"},
    {"patterns": [r"maisolje"], "property": "cornOil"},
    {"patterns": [r"rapsolje"], "property": "rapeOil"},
    {"patterns": [r"solsikkeolje"], "property": "sunflowerOil"},
    {"patterns": [r"peanøttolje"], "property": "peanutOil"},
    {"patterns": [r"kokosolje"], "property": "coconutOil"},
    {"patterns": [r"erteproteinisolat"], "property": "peaProteinIsolate"},
    {"patterns": [r"risprotein"], "property": "riceProtein"},
    {"patterns": [r"maltodekstrin"], "property": "maltodextrin"},
    {"patterns": [r"maltekstrakt"], "property": "maltExtract"},
    {"patterns": [r"inulin"], "property": "inulin"},
    {"patterns": [r"invertsukker"], "property": "invertSugar"},
    {"patterns": [r"kalsiumalginat"], "property": "calciumAlginate"},
    {"patterns": [r"natriumalginat"], "property": "sodiumAlginate"},
    {"patterns": [r"aroma"], "property": "aroma"},
    {"patterns": [r"E333", r"trikalsiumsitrat"], "property": "e333"},
    {"patterns": [r"E322", r"lecitin", r"lecithin"], "property": "e322"},
    {"patterns": [r"E631", r"dinatrium inosinat"], "property": "e631"},
    {"patterns": [r"E627", r"dinatrium guanylat"], "property": "e627"},
    {"patterns": [r"monosodium glutamat"], "property": "msg"},
    {"patterns": [r"benzoat"], "property": "benzoate"},
    {"patterns": [r"natriumbenzoat"], "property": "e211"},
    {"patterns": [r"glyserol"], "property": "glycerol"},
    {"patterns": [r"glyserider"], "property": "glycerides"},
    {"patterns": [r"gluten"], "property": "gluten"},
    {"patterns": [r"eggehvitepulver"], "property": "eggWhitePowder"},
    {"patterns": [r"dinatriumdifosfat"], "property": "e450"},
    {"patterns": [r"natriumhydrogenkarbonat"], "property": "e500"},
    {"patterns": [r"cellulose"], "property": "cellulose"},
    # Dangerous
    {"patterns": [r"E461", r"metylcellulose"], "property": "e461"},
    {"patterns": [r"E466", r"karboksymetylcellulose"], "property": "e466"},
    {"patterns": [r"E467", r"cellulosegummi"], "property": "e467"},
    {"patterns": [r"E433", r"polysorbat 80"], "property": "e433"},
    {"patterns": [r"E407", r"karragenan"], "property": "e407"},
    {"patterns": [r"E102", r"tatrazin"], "property": "e102"},
    {"patterns": [r"E104", r"kinolingult"], "property": "e104"},
    {"patterns": [r"E110", r"paraorange"], "property": "e110"},
    {"patterns": [r"E122", r"azorubin"], "property": "e122"},
    {"patterns": [r"E124", r"nykockin"], "property": "e124"},
    {"patterns": [r"E129", r"allurarød"], "property": "e129"},
]


def extract_e_number(string: str):
    matches = re.findall(r"[Ee]\d{3}[a-z]?", re.sub(r"\s", "", string))
    if matches:
        return matches[0]
    else:
        return ""


def extract_individual_ingredients(raw_ingredients: str) -> List[str]:
    return raw_ingredients.split(", ")


def get_extracted_ingredients(raw_ingredients: Iterable[str]):
    result = {}
    for string in raw_ingredients:
        e_number = extract_e_number(string)
        if e_number:
            result[e_number.lower()] = {"text": string, "key": e_number}
            continue
        for config in ingredients_config:
            config_key = config["property"]
            if pydash.get(result, [config_key, "text"]) == string:
                break
            for pattern in config["patterns"]:
                if re.findall(pattern, string, re.IGNORECASE):
                    result[config_key] = {
                        "text": string,
                        "key": config_key,
                    }
                    break
    return result


def get_ingredients_data(offer: ScraperOffer, config: HandleConfig):
    raw_ingredients_fields: List[str] = []
    for key in config["extractIngredientsFields"]:
        raw_ingredients = get_field_from_scraper_offer(offer, key)
        if raw_ingredients and type(raw_ingredients) is str:
            raw_ingredients_fields.append(raw_ingredients)
    if len(raw_ingredients_fields) == 0:
        return None

    raw_ingredients_values: List[str] = []
    for raw_ingredients in raw_ingredients_fields:
        raw_ingredients_values.extend(extract_individual_ingredients(raw_ingredients))

    extracted_ingredients = get_extracted_ingredients(raw_ingredients_values)

    processed_score = 0
    for ingredient in extracted_ingredients.values():
        ingredient_data = ingredients_data.get(ingredient["key"])
        if not ingredient_data:
            continue
        processed_score += ingredient_data.get("processedValue", 0)
        ingredient["shortDescription"] = ingredient_data.get("shortDescription", "")
        ingredient["name"] = ingredient_data["name"]

    return {"ingredients": extracted_ingredients, "processedScore": processed_score}
