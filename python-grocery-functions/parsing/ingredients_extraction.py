import re
from collections.abc import Mapping, Sequence

from amp_types.amp_product import HandleConfig, IngredientType, ScraperOffer
from storage.migrate.migrate_ingredients import IngredientsTable
from transform.offer import get_field_from_scraper_offer


def extract_e_number(string: str):
    matches = re.findall(r"[Ee]\d{3,4}[a-z]?", re.sub(r"\s", "", string))
    if matches:
        return str.lower(matches[0])
    else:
        return ""


def sort_db_ingredient_key(ingredient: IngredientType):
    if ingredient.get("patterns") and len(ingredient["patterns"]) > 0:
        longest_pattern = sorted(
            ingredient["patterns"], key=lambda x: len(x), reverse=True
        )[0]
        return -len(longest_pattern)
    else:
        return -len(ingredient["key"])


def extract_individual_ingredients(raw_ingredients: str) -> list[str]:
    return raw_ingredients.split(", ")


def get_extracted_ingredients(
    raw_ingredients: Sequence[str], ingredients_data: Mapping[str, IngredientType]
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


def get_extracted_ingredients_postgres(
    raw_ingredients: Sequence[str], ingredients_data: list[IngredientsTable]
) -> list[IngredientsTable]:
    result: list[IngredientsTable] = []
    for string in raw_ingredients:
        e_number = extract_e_number(string)
        if e_number:
            database_e_number = next(
                (x for x in ingredients_data if str(x.e_number) == e_number),
                None,
            )
            if not database_e_number:
                continue
            result.append(database_e_number)
            continue
        for db_ingredient in ingredients_data:
            for pattern in (
                db_ingredient.patterns if bool(db_ingredient.patterns) else []
            ):
                if re.findall(re.compile(str(pattern), re.IGNORECASE), string):
                    result.append(db_ingredient)
                    break
    return result


def get_ingredients_data(
    offer: ScraperOffer,
    config: HandleConfig,
    ingredients_data: Mapping[str, IngredientType],
):
    raw_ingredients_values: list[str] = get_raw_ingredients_list(offer, config)

    if not raw_ingredients_values:
        return None

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


def get_raw_ingredients_list(offer: ScraperOffer, config: HandleConfig) -> list[str]:
    raw_ingredients_fields: list[str] = []
    for key in config["extractIngredientsFields"]:
        raw_ingredients = get_field_from_scraper_offer(offer, key)
        if raw_ingredients and type(raw_ingredients) is str:
            raw_ingredients_fields.append(raw_ingredients)
    if len(raw_ingredients_fields) == 0:
        return []

    return get_raw_ingredients_from_strings(raw_ingredients_fields)


def get_raw_ingredients_from_strings(raw_ingredients: list[str]) -> list[str]:
    result: list[str] = []
    for raw_ingredient_string in raw_ingredients:
        result.extend(extract_individual_ingredients(raw_ingredient_string))

    return result
