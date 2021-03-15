from urllib.parse import quote


def encode_uri_component(x: str) -> str:
    return quote(x, safe="")


def add_byggmax_affiliate_link(product: dict) -> dict:
    if "track.adtraction.com" in product["href"]:
        return product
    escaped_original_href = product["href"]
    new_href = f"https://track.adtraction.com/t/t?a=708216731&as=1532500727&t=2&tk=1&url={escaped_original_href}"
    return {**product, "href": new_href, "ahref": new_href}


def add_staypro_affiliate_link(product: dict) -> dict:
    if "track.adtraction.com" in product["href"]:
        return product
    escaped_original_href = product["href"]
    new_href = f"https://track.adtraction.com/t/t?a=1263494185&as=1532500727&t=2&tk=1&url={escaped_original_href}"
    return {**product, "href": new_href, "ahref": new_href}


def add_lampegiganten_affiliate_link(product: dict) -> dict:
    if "id.lampegiganten.no" in product["href"]:
        return product
    escaped_original_href = product["href"]
    new_href = f"https://id.lampegiganten.no/t/t?a=1493664807&as=1532500727&t=2&tk=1&url={escaped_original_href}"
    return {**product, "href": new_href, "ahref": new_href}


def add_grontfokus_affiliate_link(product: dict) -> dict:
    if "track.adtraction.com" in product["href"]:
        return product
    escaped_original_href = product["href"]
    new_href = f"https://at.grontfokus.no/t/t?a=1095685414&as=1532500727&t=2&tk=1&url={escaped_original_href}"
    return {**product, "href": new_href, "ahref": new_href}


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
    return {**product, "href": new_href, "ahref": new_href}


def add_cdon_affiliate_link(product: dict) -> dict:
    if "tradedoubler" in product["href"]:
        return product
    escaped_original_href = product["href"]
    new_href = f"https://clk.tradedoubler.com/click?p=116&a=3191774&url={escaped_original_href}"
    return {**product, "href": new_href, "ahref": new_href}


def add_slikkepott_affiliate_link(product: dict) -> dict:
    if "tt=" in product["href"]:
        return product
    escaped_original_href = product["href"]
    new_href = (
        f"https://slikkepott.no/tt/?tt=19005_12_392741_&r={escaped_original_href}"
    )
    return {**product, "href": new_href, "ahref": new_href}


def add_natur_no_affiliate_link(product: dict) -> dict:
    if "?___store=nno&aff_id=1119" in product["href"]:
        return product
    new_href = f"{product['href']}?___store=nno&aff_id=1119"
    return {**product, "href": new_href, "ahref": new_href}


def add_se_matsmart_affiliate_link(product: dict) -> dict:
    if "id.matsmart.se" in product["href"]:
        return product
    escaped_original_href = product["href"]
    new_href = f"https://id.matsmart.se/t/t?a=1136290811&as=1573089692&t=2&tk=1&url={escaped_original_href}"
    return {**product, "href": new_href, "ahref": new_href}


def add_se_hemkop_affiliate_link(product: dict) -> dict:
    if "track.adtraction.com" in product["href"]:
        return product
    escaped_original_href = product["href"]
    new_href = f"https://track.adtraction.com/t/t?a=1479128955&as=1573089692&t=2&tk=1&url={escaped_original_href}"
    return {**product, "href": new_href, "ahref": new_href}


def add_se_mat_se_affiliate_link(product: dict) -> dict:
    if "on.mat.se" in product["href"]:
        return product
    escaped_original_href = product["href"]
    new_href = f"https://on.mat.se/t/t?a=1123786747&as=1573089692&t=2&tk=1&url={escaped_original_href}"
    return {**product, "href": new_href, "ahref": new_href}


def add_se_proffsmagasinet_affiliate_link(product: dict) -> dict:
    if "go.proffsmagasinet.se" in product["href"]:
        return product
    escaped_original_href = product["href"]
    new_href = f"https://go.proffsmagasinet.se/t/t?a=1263488714&as=1573089698&t=2&tk=1&url={escaped_original_href}"
    return {**product, "href": new_href, "ahref": new_href}


def add_se_beijerbygg_affiliate_link(product: dict) -> dict:
    if "dot.beijerbygg.se" in product["href"]:
        return product
    escaped_original_href = product["href"]
    new_href = f"https://dot.beijerbygg.se/t/t?a=1127510938&as=1573089698&t=2&tk=1&url={escaped_original_href}"
    return {**product, "href": new_href, "ahref": new_href}


def add_se_skanska_affiliate_link(product: dict) -> dict:
    if "ion.skanskabyggvaror.se" in product["href"]:
        return product
    escaped_original_href = product["href"]
    new_href = f"https://ion.skanskabyggvaror.se/t/t?a=1064671461&as=1573089698&t=2&tk=1&url={escaped_original_href}"
    return {**product, "href": new_href, "ahref": new_href}


def add_se_byggmax_affiliate_link(product: dict) -> dict:
    if "track.adtraction.com" in product["href"]:
        return product
    escaped_original_href = product["href"]
    new_href = f"https://track.adtraction.com/t/t?a=23959178&as=1573089698&t=2&tk=1&url={escaped_original_href}"
    return {**product, "href": new_href, "ahref": new_href}


def get_affiliate_handler(product: dict):
    if "byggmax.no" in product["href"]:
        return add_byggmax_affiliate_link
    elif "amazon.se" in product["href"]:
        return add_se_amazon_affiliate_link
    elif "grontfokus.no" in product["href"]:
        return add_grontfokus_affiliate_link
    elif "staypro.no" in product["href"]:
        return add_staypro_affiliate_link
    elif "lampegiganten.no" in product["href"]:
        return add_lampegiganten_affiliate_link
    elif "elektroimportoren.no" in product["href"]:
        return add_elimport_affiliate_link
    elif "cdon.no" in product["href"]:
        return add_cdon_affiliate_link
    elif "matsmart.se" in product["href"]:
        return add_se_matsmart_affiliate_link
    elif "hemkop.se" in product["href"]:
        return add_se_hemkop_affiliate_link
    elif "mat.se" in product["href"]:
        return add_se_mat_se_affiliate_link
    elif "proffsmagasinet.se" in product["href"]:
        return add_se_proffsmagasinet_affiliate_link
    elif "beijerbygg.se" in product["href"]:
        return add_se_beijerbygg_affiliate_link
    elif "skanskabyggvaror.se" in product["href"]:
        return add_se_skanska_affiliate_link
    elif "byggmax.se" in product["href"]:
        return add_se_byggmax_affiliate_link
    elif "www.slikkepott.no" in product["href"]:
        return add_slikkepott_affiliate_link
    elif "natur.no" in product["href"]:
        return add_natur_no_affiliate_link


def add_affilite_link_to_product(product: dict) -> dict:
    handler = get_affiliate_handler(product)
    if handler is None:
        return product
    else:
        return handler(product)


def add_affiliate_links(products: list) -> list:
    return list(add_affilite_link_to_product(product) for product in products)
