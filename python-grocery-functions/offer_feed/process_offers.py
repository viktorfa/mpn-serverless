import logging
from typing import List, TypedDict
from bson.objectid import ObjectId
from bson import json_util

from amp_types.amp_product import MpnOffer
from storage.db import (
    get_update_product_with_offer,
    get_insert_product_has_offer,
    get_insert_product_with_offer,
)


class MpnOfferWithProduct(MpnOffer):
    _id: ObjectId
    gtin_products: List[dict]
    product_relations: List[dict]


class OfferConfig(TypedDict):
    collection_name: str
    product_collection: str
    relation_collection: str


def process_offers(offers: List[MpnOfferWithProduct], config: OfferConfig):
    operation_items = (process_offer(x) for x in offers)
    insert_product_data = []
    update_product_operations = []
    relation_operations = []
    for operation_item in operation_items:
        operation_type = operation_item["type"]
        operation = operation_item["operation"]
        if operation_type == "insert_product":
            insert_product_data.append(
                {"operation": operation, "offer": operation_item["offer"]}
            )
        elif operation_type == "update_product":
            update_product_operations.append(operation)
        elif operation_type == "insert_relation":
            relation_operations.append(operation)
    return {
        "insert_product_data": insert_product_data,
        "update_product_operations": update_product_operations,
        "relation_operations": relation_operations,
    }


def process_offer(offer: MpnOfferWithProduct) -> dict:
    filtered_product_relations = list(
        x for x in offer["product_relations"] if x.get("isFalsePositive") is not True
    )

    if len(filtered_product_relations) > 0:
        # Offer already has a product. Should update price etc.
        logging.info(f"Offer already has product {offer['uri']}")

        if len(filtered_product_relations) > 1:
            logging.warn(f"Offer has more than one product relation {offer['uri']}")
        return {
            "type": "update_product",
            "operation": get_update_product_with_offer(
                offer, filtered_product_relations[0]
            ),
        }
    filtered_gtin_products = []
    for x in offer["gtin_products"]:
        if x["_id"] in (y["product"] for y in offer["product_relations"]):
            logging.info(
                f"Excluded product with same gtin because is in product relations {offer['uri']}, {x['title']}"
            )
        else:
            if x["provenance"] != offer["provenance"]:
                logging.info(
                    f"Found offer with existing product from different provenance. {offer['uri']}"
                )
            filtered_gtin_products.append(x)
    if len(filtered_gtin_products) > 0:
        # Offer does not have a product, but a product has the same gtin as the offers.
        # Should create a relation between the product and this offer.
        logging.info(f"Adding offer to product because of gtin {offer['uri']}")
        if len(filtered_gtin_products) > 1:
            logging.warn(f"Found more than 1 gtin relations for offer {offer['uri']}")
        return {
            "type": "insert_relation",
            "operation": get_insert_product_has_offer(
                offer["_id"], filtered_gtin_products[0]["_id"], reason="gtin"
            ),
        }
    # Could not find a product for this offer.
    # Should create new product with this offer.
    logging.info(f"Creating new product from offer {offer['uri']}")
    return {
        "type": "insert_product",
        "offer": offer,
        "operation": get_insert_product_with_offer(offer),
    }


def handle_offer_without_product(offer: MpnOffer):
    return get_insert_product_with_offer
