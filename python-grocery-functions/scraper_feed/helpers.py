import re
from urllib.parse import urlparse

from util.enums import currency_codes
from amp_types.amp_product import ScraperOffer, PricingField


def get_product_pricing(product: ScraperOffer) -> PricingField:
    currency = product.get("priceCurrency") or product.get("currency") or ""
    return dict(
        price=product.get("price"),
        currency=currency,
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


def get_book_gtins(offer: ScraperOffer) -> dict:
    result = {}
    for k, v in {
        _k: _v
        for _k, _v in offer.items()
        if _k in ["isbn", "isbn10", "isbn13"] and re.match(r"^\d+$", str(_v))
    }.items():
        if len(v) == 10:
            result["isbn10"] = v
        elif len(v) == 13:
            result["isbn13"] = v
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
    if availability is None:
        return "Unknown"
    elif availability in [
        "Auf Lager.",
        "I lager",
        "På lager",
        "På nettlager",
        "in stock",
        "in_stock",
        "instock",
        "yes",
        "Ja",
        "True",
        "true",
        "1",
        1,
    ]:
        return "InStock"
    elif availability in [
        "Ikke på lager",
        "Ikke på nettlager",
        "out of stock",
        "out_of_stock",
        "not_in_stock",
        "outofstock",
        "no",
        "Nei",
        "Nej",
        "False",
        "false",
        "0",
        0,
    ]:
        return "OutOfStock"
    elif "OutOfStock" in str(availability):
        return "OutOfStock"
    elif "InStock" in str(availability):
        return "InStock"
    elif "InStoreOnly" in str(availability):
        return "InStoreOnly"
    elif "PreOrder" in str(availability):
        return "PreOrder"
    elif "SoldOut" in str(availability):
        return "SoldOut"
    elif "OnlineOnly" in str(availability):
        return "OnlineOnly"
    elif "LimitedAvailability" in str(availability):
        return "LimitedAvailability"
    elif "Discontinued" in str(availability):
        return "Discontinued"
    elif "BackOrder" in str(availability):
        return "BackOrder"
    else:
        return "Unknown"


def remove_none_fields(offer: dict) -> dict:
    result = {}
    for k, v in offer.items():
        if v and v != {} and v != []:
            result[k] = v
    return result
