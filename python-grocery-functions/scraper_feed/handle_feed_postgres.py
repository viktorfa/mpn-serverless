import logging
import os

import botocore.response
import ijson
from ijson.common import IncompleteJSONError

from amp_types.amp_product import ProcessedMpnOffer, ScraperOffer
from scraper_feed.filters import filter_product, transform_product
from storage.postgres.pydantic_models import HandleFeedConfig
from storage.postgres.scraper_feed import handle_store_offer_batch, insert_handle_run_batch, update_handle_run_batch_status


def handle_feed_with_config_postgres(feed_json_stream: botocore.response.StreamingBody, config: HandleFeedConfig):
    logging.info("handle_feed_with_config_postgres")
    logging.info(config.model_dump_json())

    offer_context = config.context
    scrape_time = config.scrape_time
    namespace = config.namespace
    scrape_batch_id = config.scrapeBatchId

    inserted_scrape_batch = insert_handle_run_batch(scrape_time=scrape_time, scrape_batch_id=scrape_batch_id, id=config.id)

    filters = config.filters

    offer_batch: list[ProcessedMpnOffer] = []
    example_items: list[ProcessedMpnOffer] = []
    total_offers = 0
    total_filtered_offers = 0

    try:
        for offer in ijson.items(feed_json_stream, "item", use_float=True):
            total_offers += 1
            offer: ScraperOffer = offer
            transformed_offer = transform_product(offer=offer, config=config)
            should_keep = filter_product(product=transformed_offer, filters=filters)
            if not should_keep:
                continue
            total_filtered_offers += 1

            processed_offer: ProcessedMpnOffer = {
                **transformed_offer,
                "context": offer_context,
                "scrapeBatchId": scrape_batch_id,
                "namespace": namespace,
            }

            offer_batch.append(processed_offer)
            if len(example_items) < 20:
                example_items.append(processed_offer)

            if os.getenv("STAGE") == "dev":
                if len(offer_batch) == 512:
                    break

            if len(offer_batch) == 1000:
                logging.info(f"Saving {len(offer_batch)} offers")
                handle_store_offer_batch(
                    offers=offer_batch,
                    scrape_time=scrape_time,
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

        handle_store_offer_batch(
            offers=offer_batch,
            scrape_time=scrape_time,
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
