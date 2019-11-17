import logging
from datetime import datetime
from datetime import timedelta
from typing import List, Dict, Optional
from urllib.parse import urlparse

from util.helpers import get_kolonial_image_url, get_shopgun_href, json_time_to_datetime, get_product_uri
from util.enums import currency_codes, provenances, dealers
from util.constants import quantity_units
from util.quantity_extraction import analyze_quantity


now = datetime.utcnow()
one_week_ahead = now + timedelta(7)


def get_provenance_id(product):
    candidates = (
        product.get('provenance_id'),
        product.get('sku'),
        product.get('id'),
        urlparse(product.get('url')).path[1:],
    )
    return next(x for x in candidates if x)


def handle_products(products: List[Dict], source: str) -> list:
    now = datetime.utcnow()
    one_week_ahead = now + timedelta(7)
    return list((get_standard_product(product, source) for product in products))


def get_standard_product(product: dict, source: str) -> dict:
    analyzed_product = analyze_quantity(
        get_quantity_fields(product, source))
    if source == provenances.MENY:
        provenance_id = get_provenance_id(product)
        return dict(
            provenance_id=provenance_id,
            provenance=provenances.MENY,
            dealer=dealers.MENY_NO,
            run_from=now,
            run_till=one_week_ahead,
            heading=product.get('title'),
            description=product.get('product_variant'),
            brand=product.get('brand'),
            href=product.get('product_url'),
            image_url=product.get('image_url'),
            uri=get_product_uri(source, provenance_id),
            pricing=get_product_pricing(product, source),
            ** analyzed_product,
        )
    elif source == provenances.KOLONIAL:
        provenance_id = get_provenance_id(product)
        return dict(
            provenance_id=provenance_id,
            provenance=provenances.KOLONIAL,
            dealer=dealers.KOLONIAL_NO,
            run_from=now,
            run_till=one_week_ahead,
            heading=product.get('title'),
            description=product.get('product_variant'),
            brand=product.get('brand'),
            href=product.get('product_url'),
            image_url=get_kolonial_image_url(product.get('image_url')),
            uri=get_product_uri(source, provenance_id),
            pricing=get_product_pricing(product, source),
            ** analyzed_product,
        )
    elif source == provenances.EUROPRIS:
        provenance_id = get_provenance_id(product)
        return dict(
            provenance_id=provenance_id,
            provenance=provenances.EUROPRIS,
            dealer=dealers.EUROPRIS_NO,
            run_from=now,
            run_till=one_week_ahead,
            heading=product.get('name'),
            description=product.get('description'),
            brand=product.get('brand'),
            href=product.get('link'),
            image_url=product.get('image_url'),
            uri=get_product_uri(source, provenance_id),
            pricing=get_product_pricing(product, source),
            **analyzed_product,
        )
    elif source == provenances.SHOPGUN:
        provenance_id = get_provenance_id(product)
        return dict(
            provenance_id=provenance_id,
            provenance=provenances.SHOPGUN,
            run_from=json_time_to_datetime(product.get('run_from')),
            run_till=json_time_to_datetime(product.get('run_till')),
            dealer=product.get('branding', {}).get('name'),
            heading=product.get('heading'),
            description=product.get('description'),
            brand=product.get('brand'),
            href=get_shopgun_href(product),
            image_url=product.get('images', {}).get('zoom'),
            uri=get_product_uri(source, provenance_id),
            pricing=get_product_pricing(product, source),
            **{
                **analyzed_product,
                **get_shopgun_quantity(product.get('quantity')),
            }
        )
    else:
        provenance_id = get_provenance_id(product)
        return {
            ** product,
            "provenance_id": provenance_id,
            "provenance": source,
            "dealer": source,
            "run_from": now,
            "run_till": one_week_ahead,
            "heading": product.get('title'),
            "description": product.get('description'),
            "brand": product.get('brand'),
            "href": product.get('url'),
            "image_url": product.get('image'),
            "uri": get_product_uri(source, provenance_id),
            "pricing": get_product_pricing(product, source),
            ** analyzed_product,
        }


def get_amount_from_shopgun_quantity(quantity: dict) -> dict:
    return shopgun_amount_to_amount(quantity.get("size"))


def shopgun_amount_to_amount(shopgun_amount: dict) -> dict:
    return dict(
        min=shopgun_amount.get("from"),
        max=shopgun_amount.get("to"),
    )


def get_shopgun_quantity(quantity: dict) -> dict:
    if not quantity.get("unit"):
        _quantity = dict()
    elif quantity.get("unit").get("symbol") in quantity_units:
        _quantity = dict(size=dict(
            amount=get_amount_from_shopgun_quantity(quantity),
            unit=quantity.get("unit")
        ))
    else:
        _quantity = dict(pieces=dict(
            amount=get_amount_from_shopgun_quantity(quantity),
            unit=quantity.get("unit")
        ))
    return dict(
        quantity=_quantity,
        items=shopgun_amount_to_amount(quantity.get("pieces"))
    )


def get_product_pricing(product: dict, source: str) -> Optional[dict]:
    if source == provenances.MENY:
        return dict(
            price=product.get('price'),
            currency=currency_codes.NOK,
            pre_price=product.get('undiscounted_price'),
        )
    elif source == provenances.KOLONIAL:
        return dict(
            price=product.get('price'),
            currency=currency_codes.NOK,
            pre_price=product.get('undiscounted_price'),
        )
    elif source == provenances.EUROPRIS:
        return dict(
            price=product.get('price'),
            currency=currency_codes.NOK,
            pre_price=product.get('oldprice'),
        )
    elif source == provenances.SHOPGUN:
        return product.get('pricing')
    else:
        return dict(
            price=product.get('price'),
            currency=product.get("priceCurrency", currency_codes.NOK),
            pre_price=product.get('prePrice'),
        )


def get_quantity_fields(product: dict, source: str) -> Optional[List[str]]:
    if source == provenances.MENY:
        quantity_fields = ['unit_price_raw', 'product_variant', 'title']
    elif source == provenances.KOLONIAL:
        quantity_fields = ['unit_price_raw', 'product_variant', 'title']
    elif source == provenances.EUROPRIS:
        quantity_fields = ['description', 'name']
    elif source == provenances.SHOPGUN:
        quantity_fields = ['description', 'heading']
    else:
        quantity_fields = ['title', 'description']
    return [product[key] if product[key] else "" for key in quantity_fields if key in product.keys()]
