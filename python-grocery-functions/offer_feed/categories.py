import logging
import json
from typing import Optional
from datetime import datetime
from copy import deepcopy
from pymongo import UpdateOne
from bson.objectid import ObjectId

from storage.db import chunked_iterable, get_collection
from amp_types.amp_product import HandleConfig, MpnOffer
from util.utils import log_traceback


def get_offer_context_from_site_collection(site_collection: str) -> Optional[str]:
    if site_collection == "groceryoffers":
        return "amp-no"
    elif site_collection == "degroceryoffers":
        return "amp-de"
    elif site_collection == "dkgroceryoffers":
        return "amp-dk"
    elif site_collection == "segroceryoffers":
        return "amp-se"
    elif site_collection == "byggoffers":
        return "bygg-no"
    elif site_collection == "debyggoffers":
        return "bygg-de"
    elif site_collection == "dkbyggoffers":
        return "bygg-dk"
    elif site_collection == "sebyggoffers":
        return "bygg-se"
    elif site_collection == "beautyoffers":
        return "beauty-no"
    return None


def get_mpn_categories_for_meny_offer(offer: MpnOffer, target_cat_map):
    last_category = offer["slugCategories"][-1]
    cat_key = f"{last_category}_{len(offer['slugCategories'])-1}"
    offer_mpn_category = target_cat_map.get(cat_key)
    temp = deepcopy(offer_mpn_category)
    if not temp:
        return []
    offer_mpn_categories = [temp]
    while temp.get("parent"):
        temp = target_cat_map[temp["parent"]]
        offer_mpn_categories.insert(0, temp)
    return offer_mpn_categories


def get_mpn_categories_for_offer(offer: MpnOffer, source_cat_map, target_cat_map):
    offer_categories = deepcopy(offer["categories"])
    map_source = None
    while len(offer_categories) > 0 and not map_source:
        map_source = source_cat_map.get(json.dumps(offer_categories))
        offer_categories = offer_categories[: len(offer_categories) - 1]
    if not map_source:
        logging.debug(f"No map_source for {json.dumps(offer['categories'])}")
        return []
    offer_mpn_category = target_cat_map.get(map_source["target"])
    temp = deepcopy(offer_mpn_category)
    if not temp:
        return []
    offer_mpn_categories = [temp]
    while temp.get("parent"):
        temp = target_cat_map[temp["parent"]]
        offer_mpn_categories.insert(0, temp)
    return offer_mpn_categories


def handle_offers_for_categories(config: HandleConfig):
    logging.info("handle_offers_for_categories")
    now = datetime.now()
    offer_collection = get_collection("mpnoffers")
    provenance = config["provenance"]
    offers = offer_collection.find(
        {
            "provenance": provenance,
            "validThrough": {"$gt": now},
            "categories.0": {"$exists": 1},
        },
        {"categories": 1, "slugCategories": 1},
    )
    logging.info(f"Trying to find categories for offers with provenance {provenance}")
    offer_context = get_offer_context_from_site_collection(config["collection_name"])
    if not offer_context:
        return None
    category_mappings = get_collection("mpncategorymappings").find(
        {"context": offer_context}
    )
    category_mappings_map = {}
    for x in category_mappings:
        category_mappings_map[json.dumps(x["source"])] = x
    mpn_categories = get_collection("mpncategories").find({"context": offer_context})
    mpn_categories_map = {}
    for x in mpn_categories:
        mpn_categories_map[x["key"]] = x
    updates = []

    for offer in offers:
        if config["provenance"] == "meny_api_spider":
            pass
        else:
            offer_mpn_categories = get_mpn_categories_for_offer(
                offer, category_mappings_map, mpn_categories_map
            )
            updates.append(
                UpdateOne(
                    {"_id": ObjectId(offer["_id"])},
                    {"$set": {"mpnCategories": offer_mpn_categories}},
                )
            )
    logging.debug(f"Updates: {len(updates)}")

    result = 0
    for chunk in chunked_iterable(updates, 1000):
        try:
            # Can get a write error here, probably due to high write load on Mongo
            cursor = offer_collection.bulk_write(list(chunk))
            result += cursor.modified_count
        except Exception as e:
            logging.error(e)
            log_traceback(e)
    return result
