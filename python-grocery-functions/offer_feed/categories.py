import logging
import json
from typing import Optional
from datetime import datetime
from copy import deepcopy
from pymongo import UpdateOne
from bson.objectid import ObjectId

from storage.db import get_collection
from amp_types.amp_product import HandleConfig, MpnOffer


def get_offer_context_from_site_collection(site_collection: str) -> Optional[str]:
    if site_collection == "groceryoffers":
        return "amp-no"
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
    map_source = source_cat_map.get(json.dumps(offer["categories"]))
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
    now = datetime.now()
    offer_collection = get_collection("mpnoffers")
    offers = offer_collection.find(
        {
            "provenance": config["provenance"],
            "uri": {"$regex": f"^{config['namespace']}"},
            "validThrough": {"$gt": now},
            "categories.0": {"$exists": 1},
        },
        {"categories": 1, "slugCategories": 1},
    )
    logging.info(f"Trying to find categories for {offers.count()} offers")
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
            offer_mpn_categories = get_mpn_categories_for_meny_offer(
                offer, mpn_categories_map
            )
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
    logging.debug(len(updates))
    result = offer_collection.bulk_write(updates)
    return result.modified_count
