from amp_types.amp_product import (
    HandleConfig,
    ScraperOffer,
)


def standardize_additional_properties(offer: ScraperOffer, config: HandleConfig):
    return offer.get("additionalProperties", [])