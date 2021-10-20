import json
from pathlib import Path
import pydash
from typing import Union

from amp_types.amp_product import HandleConfig, MpnOffer

categories = {}

with open(Path(Path(__file__).parent, "category-hierarchy.json")) as category_file:
    categories = json.load(category_file)
with open(Path(Path(__file__).parent, "category-extra.json")) as extra_category_file:
    extra_categories = json.load(extra_category_file)
with open(
    Path(Path(__file__).parent, "category-hierarchy-bygg.json")
) as nobb_category_file:
    nobb_categories = json.load(nobb_category_file)

categories = {**extra_categories, **categories}


def extract_categories(offer: MpnOffer, config: HandleConfig) -> Union[dict, None]:
    try:
        categories_field: str = pydash.get(config, ["categoriesField"], "categories")
        last_two_categories = str(offer[categories_field][-2:])
        last_category = offer[categories_field][-1]
        dealer = offer["dealer"]
        category = None
        if dealer == "meny":
            cat_key = f"{last_category}_{len(offer[categories_field])-1}"
            category = categories.get(cat_key)
        else:
            category = pydash.get(category_mappings, [dealer, last_two_categories])
            if not category:
                category = pydash.get(category_mappings, [dealer, last_category])
        result = []
        current_cat = category
        while current_cat:
            result.insert(0, current_cat)
            current_cat = categories.get(current_cat["parent"])
        return result
    except Exception as e:
        return None


def extract_meny_categories(offer: MpnOffer, config: HandleConfig):
    categories_field: str = pydash.get(config, ["categoriesField"], "categories")
    last_category = offer[categories_field][-1]
    cat_key = f"{last_category}_{len(offer[categories_field])-1}"
    category = categories.get(cat_key)
    result = []
    current_cat = category
    while current_cat:
        result.insert(0, current_cat)
        current_cat = categories.get(current_cat["parent"])
    return result
