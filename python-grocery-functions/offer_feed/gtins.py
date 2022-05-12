import logging
from typing import List, Mapping
import pydash
from datetime import datetime


def match_offers_with_gtins_map(offers, gtin_offer_map):
    now = datetime.now()

    offers_list = []
    for offer in offers:
        identical_offers = [offer]
        for gtin_key, gtin_value in offer.get("gtins", {}).items():
            # gtin13 and ean are different names for the same field
            if gtin_key == "ean":
                gtin_key = "gtin13"
            gtin = f"{gtin_key}_{gtin_value}"
            # Remove self from identical offers
            offers_with_same_gtin = gtin_offer_map.get(gtin, [])
            identical_offers.extend(offers_with_same_gtin)
        unique_identical_offers = pydash.uniq_by(identical_offers, "uri")
        if len(unique_identical_offers) > 1:
            offers_list.append(unique_identical_offers)

    logging.debug(
        f"{datetime.now() - now} Matched offers to gtin map {len(offers_list)}"
    )

    return offers_list


def get_lists_of_offers_with_same_gtins(source_offers, target_offers):
    now = datetime.now()
    gtin_offer_map: Mapping[str, List[dict]] = {}
    for offer in target_offers:
        for gtin_key, gtin_value in offer.get("gtins", {}).items():
            # gtin13 and ean are different names for the same field
            if gtin_key == "ean":
                gtin_key = "gtin13"
            gtin = f"{gtin_key}_{gtin_value}"
            try:
                gtin_offer_map[gtin].append(offer)
            except KeyError:
                gtin_offer_map[gtin] = [offer]

    logging.debug(
        f"{datetime.now() - now} Made gtin offer map {len(gtin_offer_map.keys())}"
    )

    return match_offers_with_gtins_map(source_offers, gtin_offer_map)
