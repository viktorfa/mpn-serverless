from parsing.constants import quantity_units
from util.helpers import (
    get_shopgun_href,
    json_time_to_datetime,
    get_product_uri,
)
from util.enums import provenances
from scraper_feed.helpers import get_provenance_id, get_product_pricing
from parsing.quantity_extraction import parse_quantity
from amp_types.amp_product import MpnOffer


def transform_shopgun_product(product: dict) -> MpnOffer:
    analyzed_product = parse_quantity(
        list(v for k, v in product.items() if k in ["description", "heading"] and v)
    )
    provenanceId = get_provenance_id(product)
    quantity = get_shopgun_quantity(product.get("quantity"))
    return dict(
        provenanceId=provenanceId,
        provenance=provenances.SHOPGUN,
        validFrom=json_time_to_datetime(product.get("run_from")),
        validThrough=json_time_to_datetime(product.get("run_till")),
        dealer=product.get("branding", {}).get("name"),
        title=product.get("heading"),
        description=product.get("description"),
        brand=product.get("brand"),
        href=get_shopgun_href(product),
        imageUrl=product.get("images", {}).get("zoom"),
        uri=get_product_uri("shopgun", provenanceId),
        stores=product.get("stores", []),
        pricing=get_product_pricing(
            {
                "price": product.get("pricing").get("price"),
                "prePrice": product.get("pricing").get("pre_price"),
                "priceCurrency": product.get("pricing").get("currency"),
            }
        ),
        **{**analyzed_product, **quantity,},
    )


def get_amount_from_shopgun_quantity(quantity: dict) -> dict:
    return shopgun_amount_to_amount(quantity.get("size"))


def shopgun_amount_to_amount(shopgun_amount: dict) -> dict:
    return dict(min=shopgun_amount.get("from"), max=shopgun_amount.get("to"),)


def get_shopgun_quantity(quantity: dict) -> dict:
    if not quantity.get("unit"):
        _quantity = dict()
    elif quantity.get("unit").get("symbol") in quantity_units:
        _quantity = dict(
            size=dict(
                amount=get_amount_from_shopgun_quantity(quantity),
                unit=quantity.get("unit"),
            )
        )
    else:
        _quantity = dict(
            pieces=dict(
                amount=get_amount_from_shopgun_quantity(quantity),
                unit=quantity.get("unit"),
            )
        )
    return dict(
        quantity=_quantity, items=shopgun_amount_to_amount(quantity.get("pieces"))
    )
