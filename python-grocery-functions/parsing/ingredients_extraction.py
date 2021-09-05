from typing import List
from transform.offer import get_field_from_scraper_offer
from amp_types.amp_product import HandleConfig, ScraperOffer


def extract_ingredients(offer: ScraperOffer, config: HandleConfig) -> List[str]:
    result: List[str] = []
    for key in config["extractIngredientsFields"]:
        if len(result) > 0:
            continue
        raw_ingredients = get_field_from_scraper_offer(offer, key)
        if raw_ingredients:
            result.extend(raw_ingredients.split(", "))
    return result
