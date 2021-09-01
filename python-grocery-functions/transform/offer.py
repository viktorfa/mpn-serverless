import logging
from pydash import find, get

from amp_types.amp_product import ScraperOffer


def get_field_from_scraper_offer(offer: ScraperOffer, key: str, default=None):
    if get(offer, key):
        return get(offer, key, default)
    else:
        additional_property = find(
            offer.get("additionalProperties", []),
            lambda x: key and x.get("key", x.get("name", "")).lower() == key.lower(),
        )
        if not additional_property:
            return default
        try:
            return additional_property["value"]
        except KeyError:
            logging.warn("Additional property in scraper offer without value field.")
            logging.warn(additional_property)
