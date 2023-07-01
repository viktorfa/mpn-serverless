import re
import json
import os
import logging
import pydash
from typing import Iterable, List
from typing import Mapping

from transform.offer import get_field_from_scraper_offer
from amp_types.amp_product import HandleConfig, ScraperOffer, IngredientType


def extract_e_number(string: str):
    matches = re.findall(r"[Ee]\d{3,4}[a-z]?", re.sub(r"\s", "", string))
    if matches:
        return str.lower(matches[0])
    else:
        return ""


def extract_individual_ingredients(raw_ingredients: str) -> List[str]:
    return raw_ingredients.split(", ")


def get_extracted_ingredients(
    raw_ingredients: Iterable[str], ingredients_data: Mapping[str, IngredientType]
):
    result = {}
    for string in raw_ingredients:
        e_number = extract_e_number(string)
        if e_number:
            database_e_number = next(
                (x for x in ingredients_data.values() if x.get("eNumber") == e_number),
                None,
            )
            if not database_e_number:
                continue
            result[database_e_number["key"]] = {
                "text": string,
                "key": database_e_number["key"],
            }
            continue
        for config_key, config in ingredients_data.items():
            for pattern in config.get("patterns", []):
                if re.findall(re.compile(pattern, re.IGNORECASE), string):
                    result[config_key] = {
                        "text": string,
                        "key": config_key,
                    }
                    break
    return result


def get_ingredients_data(
    offer: ScraperOffer,
    config: HandleConfig,
    ingredients_data: Mapping[str, IngredientType],
):
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

    extracted_ingredients = get_extracted_ingredients(
        raw_ingredients_values, ingredients_data
    )

    processed_score = 0
    for ingredient in extracted_ingredients.values():
        ingredient_data = ingredients_data.get(ingredient["key"])
        if not ingredient_data:
            continue
        processed_score += ingredient_data.get("processedValue", 0)
        ingredient["shortDescription"] = ingredient_data.get("shortDescription", "")
        ingredient["name"] = ingredient_data["name"]

    return {"ingredients": extracted_ingredients, "processedScore": processed_score}
