from urllib.parse import quote


def encode_uri_component(x: str) -> str:
    return quote(x, safe="")


def add_byggmax_affiliate_link(product: dict) -> dict:
    if "track.adtraction.com" in product["href"]:
        return product
    escaped_original_href = product["href"]
    new_href = f"https://track.adtraction.com/t/t?a=708216731&as=1532500727&t=2&tk=1&url={escaped_original_href}"
    return {**product, "href": new_href}


def add_staypro_affiliate_link(product: dict) -> dict:
    if "track.adtraction.com" in product["href"]:
        return product
    escaped_original_href = product["href"]
    new_href = f"https://track.adtraction.com/t/t?a=1263494185&as=1532500727&t=2&tk=1&url={escaped_original_href}"
    return {**product, "href": new_href}


affiliate_handlers = {
    "byggmax.no": add_byggmax_affiliate_link,
    "www.byggmax.no": add_byggmax_affiliate_link,
    "www.staypro.no": add_staypro_affiliate_link,
}


def get_affiliate_handler(product: dict):
    if "byggmax.no" in product["href"]:
        return add_byggmax_affiliate_link
    elif "staypro.no" in product["href"]:
        return add_staypro_affiliate_link


def add_affilite_link_to_product(product: dict) -> dict:
    handler = get_affiliate_handler(product)
    if handler is None:
        return product
    else:
        return handler(product)


def add_affiliate_links(products: list) -> list:
    return list(add_affilite_link_to_product(product) for product in products)
