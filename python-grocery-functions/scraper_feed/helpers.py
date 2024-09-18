import re
from urllib.parse import urlparse
from gtin import has_valid_check_digit

from util.enums import currency_codes
from amp_types.amp_product import ScraperOffer, PricingField


def get_product_pricing(product: ScraperOffer) -> PricingField:
    currency = product.get("priceCurrency") or product.get("currency") or ""
    price = product.get("price")
    pre_price = product.get("prePrice")
    return dict(
        price=float(price) if price else None,
        currency=currency,
        prePrice=float(pre_price) if pre_price else None,
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


def is_valid_ean(ean: str) -> bool:
    if not type(ean) is str:
        return False
    if len(ean) != 13:
        return False
    if not has_valid_check_digit(ean):
        return False
    if ean.startswith("000000"):
        return False
    if ean.startswith("2"):  # 2 prefix reserved for internal use
        return False
    if re.match(r"^02[0-9]", ean):
        # 020-029 are for internal use and not globally unique
        return False
    return True


def is_valid_gtin12(gtin12: str) -> bool:
    if not type(gtin12) is str:
        return False
    if len(gtin12) != 12:
        return False
    if not has_valid_check_digit(gtin12):
        return False
    if gtin12.startswith("000000"):
        return False
    return True


def is_valid_nobb(nobb: str) -> bool:
    return len(nobb) == 8 and not nobb.startswith("000000")


def get_gtins(offer: ScraperOffer) -> dict:
    result = {}
    for k, v in {
        _k: str(_v)
        for _k, _v in offer.items()
        if _k in ["gtin13", "ean", "nobb", "gtin", "gtin8", "gtin12"]
        and re.match(r"^\d+$", str(_v))
        and not str(_v).startswith("000000")
    }.items():
        if k == "nobb" and is_valid_nobb(v):
            result["nobb"] = v
        elif k == "gtin8" and len(v) == 8 and has_valid_check_digit(v):
            result["gtin8"] = v
        elif k == "gtin12" and len(v) == 12 and is_valid_gtin12(v):
            result["gtin12"] = v
        elif k in ["ean", "gtin13"] and is_valid_ean(v):
            result["ean"] = v
        elif k == "gtin" and has_valid_check_digit(v):
            result["gtin"] = v
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
