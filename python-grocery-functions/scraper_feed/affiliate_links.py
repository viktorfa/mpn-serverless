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


def add_grontfokus_affiliate_link(product: dict) -> dict:
    if "track.adtraction.com" in product["href"]:
        return product
    escaped_original_href = product["href"]
    new_href = f"https://at.grontfokus.no/t/t?a=1095685414&as=1532500727&t=2&tk=1&url={escaped_original_href}"
    return {**product, "href": new_href}


def add_se_amazon_affiliate_link(product: dict) -> dict:
    if "tag=" in product["href"]:
        return product
    return {
        **product,
        "href": f'{product["href"]}&tag=mpn00e-21'
        if "?" in product["href"]
        else f'{product["href"]}?tag=mpn00e-21',
    }


def add_elimport_affiliate_link(product: dict) -> dict:
    if "tradedoubler" in product["href"]:
        return product
    escaped_original_href = product["href"]
    new_href = f"https://clk.tradedoubler.com/click?p=308985&a=3191775&url={escaped_original_href}"
    return {**product, "href": new_href}


def get_affiliate_handler(product: dict):
    if "byggmax.no" in product["href"]:
        return add_byggmax_affiliate_link
    elif "amazon.se" in product["href"]:
        return add_se_amazon_affiliate_link
    elif "grontfokus.no" in product["href"]:
        return add_grontfokus_affiliate_link
    elif "staypro.no" in product["href"]:
        return add_staypro_affiliate_link
    elif "elektroimportoren.no" in product["href"]:
        return add_elimport_affiliate_link


def add_affilite_link_to_product(product: dict) -> dict:
    handler = get_affiliate_handler(product)
    if handler is None:
        return product
    else:
        return handler(product)


def add_affiliate_links(products: list) -> list:
    return list(add_affilite_link_to_product(product) for product in products)
