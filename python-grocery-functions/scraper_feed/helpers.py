import re
from urllib.parse import urlparse

from util.enums import currency_codes
from amp_types.amp_product import ScraperOffer, PricingField


def get_product_pricing(product: ScraperOffer) -> PricingField:
    return dict(
        price=product.get("price"),
        currency=product.get("priceCurrency", currency_codes.NOK),
        prePrice=product.get("prePrice"),
        priceUnit=product.get("priceUnit", "pcs"),
    )


def transform_field(field):
    try:
        return field["value"]
    except KeyError:
        return field


def transform_key(key: str) -> str:
    """Removes characters that can't be stored as keys in mongo db."""
    return re.sub(r"\.", "", key)


def get_gtins(offer: ScraperOffer) -> dict:
    result = {}
    for k, v in {
        _k: _v
        for _k, _v in offer.items()
        if _k in ["gtin", "gtin8", "gtin12", "gtin13", "upc", "ean", "nobb"]
        and re.match(r"^\d+$", str(_v))
    }.items():
        if k == "nobb":
            result["nobb"] = v
        elif len(v) == 8:
            result["gtin8"] = v
        elif len(v) == 12:
            result["gtin12"] = v
        elif len(v) == 13:
            result["gtin13"] = v
        else:
            result[k] = v
    return result


def get_provenance_id(product):
    candidates = (
        product.get("provenanceId"),
        product.get("sku"),
        product.get("id"),
        urlparse(product.get("url")).path[1:],
    )
    return next(x for x in candidates if x)


def get_stock_status(product):
    availability = product.get("availability")
    if not availability:
        return "OutOfStock"
    elif availability in [
        "InStock",
        "http://schema.org/InStock",
        "https://schema.org/InStock",
    ]:
        return "InStock"
    else:
        return availability

