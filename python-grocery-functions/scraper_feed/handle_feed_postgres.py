import logging
from datetime import datetime
import os
from typing import Iterable, Mapping

import botostubs
import pydash
import ijson
from ijson.common import IncompleteJSONError
import botocore.response

from util.mappings import get_offer_context_from_site_collection
from storage.db import save_book_offers
from amp_types.amp_product import (
    HandleConfig,
    IngredientType,
    ProcessedMpnOffer,
    ScraperOffer,
)
from scraper_feed.affiliate_links import add_affilite_link_to_product
from scraper_feed.helpers import get_book_gtins
from scraper_feed.filters import filter_product, transform_product
from parsing.ingredients_extraction import sort_db_ingredient_key
from storage.db import get_collection
from storage.postgres.scraper_feed import (
    handle_store_offer_batch,
    insert_handle_run_batch,
    update_handle_run_batch_status,
)


def handle_feed_with_config_postgres(
    feed_json_stream: botocore.response.StreamingBody, config: HandleConfig
):
    if not config["namespace"]:
        raise Exception("Config needs namespace")
    if not config["collection_name"]:
        raise Exception("Config needs collection_name")
    if not config["scrape_time"]:
        raise Exception("Config needs scrape_time")
    if not config["scrapeBatchId"]:
        raise Exception("Config needs scrapeBatchId")

    offer_context = get_offer_context_from_site_collection(config["collection_name"])

    start_time = datetime.now()

    inserted_scrape_batch = insert_handle_run_batch(
        config=config,
    )

    ingredients_data: Mapping[str, IngredientType] = {}
    if (
        config["collection_name"] in ["groceryoffers"]
        and len(config.get("extractIngredientsFields", [])) > 0
    ):
        ingredients_collection = get_collection("ingredients")
        db_ingredients: Iterable[IngredientType] = ingredients_collection.find({})
        for x in sorted(db_ingredients, key=sort_db_ingredient_key):
            ingredients_data[x["key"]] = x

    scrape_batch_id = config["scrapeBatchId"]
    filters = pydash.get(config, ["filters"], [])

    is_book_offers = config["collection_name"] == "bookoffers"

    offer_batch = []
    example_items = []
    total_offers = 0
    total_filtered_offers = 0

    try:
        for offer in ijson.items(feed_json_stream, "item"):
            total_offers += 1
            offer: ScraperOffer = offer
            transformed_offer = transform_product(
                offer=offer, config=config, ingredients_data=ingredients_data
            )
            should_keep = filter_product(product=transformed_offer, filters=filters)
            if not should_keep:
                continue
            total_filtered_offers += 1

            processed_offer: ProcessedMpnOffer = {
                **add_affilite_link_to_product(transformed_offer),
                "siteCollection": config["collection_name"],
                "scrapeBatchId": scrape_batch_id,
                "namespace": config["namespace"],
                "context": get_offer_context_from_site_collection(
                    config["collection_name"]
                ),
            }

            if is_book_offers:
                book_offer = {
                    **processed_offer,
                    "gtins": get_book_gtins(processed_offer),
                    "uri": processed_offer["book_uri"],
                    "ahref": processed_offer.get("trackingUrl"),
                }
                offer_batch.append(book_offer)
                if len(example_items) < 20:
                    example_items.append(book_offer)
            else:
                offer_batch.append(processed_offer)
                if len(example_items) < 20:
                    example_items.append(processed_offer)

            if os.getenv("STAGE") == "dev":
                if len(offer_batch) == 512:
                    break

            if len(offer_batch) == 1000:
                logging.info(f"Saving {len(offer_batch)} offers")
                if is_book_offers:
                    save_book_offers(offer_batch)
                else:
                    handle_store_offer_batch(
                        offers=offer_batch,
                        scrape_time=config["scrape_time"],
                        context=offer_context,
                    )
                offer_batch = []
    except IncompleteJSONError as e:
        logging.error(e)
        logging.error("Incomplete JSON error")
        return {
            "message": "Incomplete JSON error",
            "error": str(e),
        }
    finally:
        feed_json_stream.close()

    if len(offer_batch) > 0:
        logging.info(f"Saving last {len(offer_batch)} offers")
        if is_book_offers:
            save_book_offers(offer_batch)
        else:
            handle_store_offer_batch(
                offers=offer_batch,
                scrape_time=config["scrape_time"],
                context=offer_context,
            )
            # with open(f"./offers_for_save_{config['namespace']}.json", "w") as f:
            #    json.dump(offer_batch[:12], f, default=str)

    else:
        logging.info("No offers to save")

    update_handle_run_batch_status(inserted_scrape_batch, "COMPLETED")

    return {
        "items_handled": total_offers,
        "n_filtered_offers": total_filtered_offers,
    }
