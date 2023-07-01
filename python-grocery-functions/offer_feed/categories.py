import aws_config
import logging
import json
import pydash
from typing import Iterable, Optional
from datetime import datetime
from copy import deepcopy
from pymongo import UpdateOne
from bson.objectid import ObjectId
from typing import Iterable, TypedDict

from storage.db import chunked_iterable, get_collection
from amp_types.amp_product import HandleConfig, MpnOffer
from util.utils import log_traceback
from util.logging import configure_lambda_logging
from util.helpers import is_null_or_empty

configure_lambda_logging()


class SnsMessage(TypedDict):
    collection_name: str
    scrape_time: str
    provenance: str


def offer_feed_sns_for_categories(event, context):
    logging.info("event")
    logging.info(event)
    aws_config.lambda_context = context
    sns_message: SnsMessage = json.loads(event["Records"][0]["Sns"]["Message"])
    provenance = sns_message["provenance"]
    result = []

    try:
        result.append(handle_offers_for_categories(sns_message))
    except Exception as e:
        logging.error(e)
        log_traceback(e)
        result.append({"message": str(e)})
    return result


def offer_feed_trigger_for_categories(event, context):
    logging.info("event")
    logging.info(event)
    aws_config.lambda_context = context
    provenance = event["provenance"]
    result = []

    try:
        result.append(handle_offers_for_categories(event))
    except Exception as e:
        logging.error(e)
        log_traceback(e)
        result.append({"message": str(e)})
    return result


def get_offer_context_from_site_collection(site_collection: str) -> Optional[str]:
    if site_collection == "groceryoffers":
        return "amp-no"
    elif site_collection == "degroceryoffers":
        return "amp-de"
    elif site_collection == "dkgroceryoffers":
        return "amp-dk"
    elif site_collection == "segroceryoffers":
        return "amp-se"
    elif site_collection == "figroceryoffers":
        return "amp-fi"
    elif site_collection == "plgroceryoffers":
        return "amp-pl"
    elif site_collection == "nlgroceryoffers":
        return "amp-nl"
    elif site_collection == "frgroceryoffers":
        return "amp-fr"
    elif site_collection == "esgroceryoffers":
        return "amp-es"
    elif site_collection == "ukgroceryoffers":
        return "amp-uk"
    elif site_collection == "itgroceryoffers":
        return "amp-it"
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


safe_categories_for_not_processed = [
    "frukt-gront_0",
    "kjott_0",
    "fisk_0",
    "kylling-og-fjrkre_0",
    "vann_1",
]


def handle_offers_for_categories(config: HandleConfig):
    logging.info("handle_offers_for_categories")
    now = datetime.now()
    provenance = config["provenance"]
    scrape_batch_id = config.get("scrapeBatchId")
    logging.info(f"Trying to find categories for offers with provenance {provenance}")
    offer_context = get_offer_context_from_site_collection(config["collection_name"])
    if not offer_context:
        return None
    category_mappings = get_collection("mpncategorymappings").find(
        {"context": offer_context}
    )

    category_mappings = list(category_mappings)
    if len(category_mappings) == 0:
        logging.info(
            f"No category mappings for provenance {provenance} and context {offer_context}"
        )
        return None

    offer_collection = get_collection("mpnoffers")

    offers: Iterable = []

    if scrape_batch_id:
        offers = offer_collection.find(
            {
                "scrapeBatchId": scrape_batch_id,
            },
            {"categories": 1, "slugCategories": 1, "mpnNutrition": 1},
        )
    else:
        offers = offer_collection.find(
            {"provenance": provenance, "validThrough": {"$gt": now}, "isRecent": True},
            {"categories": 1, "slugCategories": 1, "mpnNutrition": 1},
        )

    offers = (
        offer
        for offer in offers
        if pydash.get(offer, "categories.0") or pydash.get(offer, "slugCategories.0")
    )
    category_mappings_map = {}
    for x in category_mappings:
        category_mappings_map[json.dumps(x["source"])] = x
    mpn_categories = get_collection("mpncategories").find(
        {"context": offer_context},
        {"_id": 1, "name": 1, "key": 1, "parent": 1, "level": 1},
    )
    mpn_categories_map = {}
    for x in mpn_categories:
        mpn_categories_map[x["key"]] = x
    updates = []

    for offer in offers:
        offer_mpn_categories = get_mpn_categories_for_offer(
            offer, category_mappings_map, mpn_categories_map
        )

        update_set = {"mpnCategories": offer_mpn_categories}

        # Some products have no ingredients, so we mark them as not processed here.
        if len(
            set(safe_categories_for_not_processed).intersection(
                set((x["key"] for x in offer_mpn_categories))
            )
        ) > 0 and is_null_or_empty(
            pydash.get(offer, ["mpnIngredients", "ingredients"])
        ):
            update_set["mpnIngredients"] = {
                "processedScore": 0,
                "ingredients": pydash.get(offer, ["mpnIngredients", "ingredients"], {}),
            }
        updates.append(
            UpdateOne(
                {"_id": ObjectId(offer["_id"])},
                {"$set": update_set},
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
