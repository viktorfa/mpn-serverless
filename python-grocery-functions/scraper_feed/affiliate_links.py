from typing import Iterable
from urllib.parse import quote

from amp_types.amp_product import MpnOffer


def encode_uri_component(x: str) -> str:
    return quote(x, safe="")


def add_byggmax_affiliate_link(product: dict) -> dict:
    if "track.adtraction.com" in product["href"]:
        return product
    escaped_original_href = product["href"]
    new_href = f"https://track.adtraction.com/t/t?a=708216731&as=1532500727&t=2&tk=1&url={escaped_original_href}"
    return {**product, "ahref": new_href}


def add_lampegiganten_affiliate_link(product: dict) -> dict:
    if "id.lampegiganten.no" in product["href"]:
        return product
    escaped_original_href = product["href"]
    new_href = f"https://id.lampegiganten.no/t/t?a=1493664807&as=1532500727&t=2&tk=1&url={escaped_original_href}"
    return {**product, "ahref": new_href}


def add_grontfokus_affiliate_link(product: dict) -> dict:
    if "track.adtraction.com" in product["href"]:
        return product
    escaped_original_href = product["href"]
    new_href = f"https://at.grontfokus.no/t/t?a=1095685414&as=1532500727&t=2&tk=1&url={escaped_original_href}"
    return {**product, "ahref": new_href}


def add_se_amazon_affiliate_link(product: dict) -> dict:
    ahref = product["href"]
    if "tag=" not in product["href"]:
        ahref = (
            f'{product["href"]}&tag=mpn00e-21'
            if "?" in product["href"]
            else f'{product["href"]}?tag=mpn00e-21'
        )

    return {**product, "ahref": ahref}


def add_de_amazon_affiliate_link(product: dict) -> dict:
    ahref = product["href"]
    if "tag=" not in product["href"]:
        ahref = (
            f'{product["href"]}&tag=mpn06e-21'
            if "?" in product["href"]
            else f'{product["href"]}?tag=mpn06e-21'
        )

    return {**product, "ahref": ahref}


def add_com_amazon_affiliate_link(product: dict) -> dict:
    ahref = product["href"]
    if "tag=" not in product["href"]:
        ahref = (
            f'{product["href"]}&tag=epstein0b-20'
            if "?" in product["href"]
            else f'{product["href"]}?tag=epstein0b-20'
        )

    return {**product, "ahref": ahref}


def add_sg_amazon_affiliate_link(product: dict) -> dict:
    ahref = product["href"]
    if "tag=" not in product["href"]:
        ahref = (
            f'{product["href"]}&tag=mpn00-22'
            if "?" in product["href"]
            else f'{product["href"]}?tag=mpn00-22'
        )

    return {**product, "ahref": ahref}


def add_uk_amazon_affiliate_link(product: dict) -> dict:
    ahref = product["href"]
    if "tag=" not in product["href"]:
        ahref = (
            f'{product["href"]}&tag=mpn0cb-21'
            if "?" in product["href"]
            else f'{product["href"]}?tag=mpn0cb-21'
        )

    return {**product, "ahref": ahref}


def add_fr_amazon_affiliate_link(product: dict) -> dict:
    ahref = product["href"]
    if "tag=" not in product["href"]:
        ahref = (
            f'{product["href"]}&tag=mpn029-21'
            if "?" in product["href"]
            else f'{product["href"]}?tag=mpn029-21'
        )

    return {**product, "ahref": ahref}


def add_nl_amazon_affiliate_link(product: dict) -> dict:
    ahref = product["href"]
    if "tag=" not in product["href"]:
        ahref = (
            f'{product["href"]}&tag=mpn01-21'
            if "?" in product["href"]
            else f'{product["href"]}?tag=mpn01-21'
        )

    return {**product, "ahref": ahref}


def add_au_amazon_affiliate_link(product: dict) -> dict:
    ahref = product["href"]
    if "tag=" not in product["href"]:
        ahref = (
            f'{product["href"]}&tag=???'
            if "?" in product["href"]
            else f'{product["href"]}?tag=???'
        )

    return {**product, "ahref": ahref}


def add_es_amazon_affiliate_link(product: dict) -> dict:
    ahref = product["href"]
    if "tag=" not in product["href"]:
        ahref = (
            f'{product["href"]}&tag=mpn00-21'
            if "?" in product["href"]
            else f'{product["href"]}?tag=mpn00-21'
        )

    return {**product, "ahref": ahref}


def add_pl_amazon_affiliate_link(product: dict) -> dict:
    ahref = product["href"]
    if "tag=mpn0a-21" not in product["href"]:
        ahref = (
            f'{product["href"]}&tag=mpn0a-21'
            if "?" in product["href"]
            else f'{product["href"]}?tag=mpn0a-21'
        )

    return {**product, "ahref": ahref}


def add_it_amazon_affiliate_link(product: dict) -> dict:
    ahref = product["href"]
    if "tag=" not in product["href"]:
        ahref = (
            f'{product["href"]}&tag=mpn023-21'
            if "?" in product["href"]
            else f'{product["href"]}?tag=mpn023-21'
        )

    return {**product, "ahref": ahref}


def add_elimport_affiliate_link(product: dict) -> dict:
    if "tradedoubler" in product["href"]:
        return product
    escaped_original_href = product["href"]
    new_href = f"https://clk.tradedoubler.com/click?p=308985&a=3191775&url={escaped_original_href}"
    return {**product, "ahref": new_href}


def add_cdon_affiliate_link(product: dict) -> dict:
    if "tradedoubler" in product["href"]:
        return product
    escaped_original_href = encode_uri_component(product["href"])
    new_href = f"https://clk.tradedoubler.com/click?p=116&a=3191774&url={escaped_original_href}"
    return {**product, "ahref": new_href}


def add_slikkepott_affiliate_link(product: dict) -> dict:
    if "tt=" in product["href"]:
        return product
    escaped_original_href = product["href"]
    new_href = (
        f"https://slikkepott.no/tt/?tt=19005_12_392741_&r={escaped_original_href}"
    )
    return {**product, "ahref": new_href}


def add_natur_no_affiliate_link(product: dict) -> dict:
    if "?___store=nno&aff_id=1119" in product["href"]:
        return product
    new_href = f"{product['href']}?___store=nno&aff_id=1119"
    return {**product, "ahref": new_href}


def add_se_matsmart_affiliate_link(product: dict) -> dict:
    if "id.matsmart.se" in product["href"]:
        return product
    escaped_original_href = product["href"]
    new_href = f"https://id.matsmart.se/t/t?a=1136290811&as=1573089692&t=2&tk=1&url={escaped_original_href}"
    return {**product, "ahref": new_href}


def add_se_hemkop_affiliate_link(product: dict) -> dict:
    if "track.adtraction.com" in product["href"]:
        return product
    escaped_original_href = product["href"]
    new_href = f"https://track.adtraction.com/t/t?a=1479128955&as=1573089692&t=2&tk=1&url={escaped_original_href}"
    return {**product, "ahref": new_href}


def add_se_mat_se_affiliate_link(product: dict) -> dict:
    if "on.mat.se" in product["href"]:
        return product
    escaped_original_href = product["href"]
    new_href = f"https://on.mat.se/t/t?a=1123786747&as=1573089692&t=2&tk=1&url={escaped_original_href}"
    return {**product, "ahref": new_href}


def add_mathem_se_affiliate_link(product: dict) -> dict:
    if "dot.mathem.se" in product["href"]:
        return product
    escaped_original_href = product["href"]
    new_href = f"https://dot.mathem.se/t/t?a=1468601138&as=1573089692&t=2&tk=1&url={escaped_original_href}"
    return {**product, "ahref": new_href}


def add_se_beijerbygg_affiliate_link(product: dict) -> dict:
    if "dot.beijerbygg.se" in product["href"]:
        return product
    escaped_original_href = product["href"]
    new_href = f"https://dot.beijerbygg.se/t/t?a=1127510938&as=1573089698&t=2&tk=1&url={escaped_original_href}"
    return {**product, "ahref": new_href}


def add_se_skanska_affiliate_link(product: dict) -> dict:
    if "ion.skanskabyggvaror.se" in product["href"]:
        return product
    escaped_original_href = product["href"]
    new_href = f"https://ion.skanskabyggvaror.se/t/t?a=1064671461&as=1573089698&t=2&tk=1&url={escaped_original_href}"
    return {**product, "ahref": new_href}


def add_se_byggmax_affiliate_link(product: dict) -> dict:
    if "track.adtraction.com" in product["href"]:
        return product
    escaped_original_href = product["href"]
    new_href = f"https://track.adtraction.com/t/t?a=23959178&as=1573089698&t=2&tk=1&url={escaped_original_href}"
    return {**product, "ahref": new_href}


def add_buildor_se_affiliate_link(product: dict) -> dict:
    escaped_original_href = encode_uri_component(product["href"])
    ahref = f"https://clk.tradedoubler.com/click?p=287168&a=3213987&url={escaped_original_href}"
    return {**product, "ahref": ahref}


def add_strawberrynet_affiliate_link(product: dict) -> dict:
    ahref = f"{product['href']}?trackid=3001500004"
    return {**product, "ahref": ahref}


def add_davidsen_affiliate_link(product: dict) -> dict:
    if "track.adtraction.com" in product["href"]:
        return product
    escaped_original_href = product["href"]
    new_href = f"https://track.adtraction.com/t/t?a=1659447672&as=1685097411&t=2&tk=1&url={escaped_original_href}"
    return {**product, "ahref": new_href}


def add_locamo_de_affiliate_link(product: dict) -> dict:
    if "pin.locamo.de" in product["href"]:
        return product
    escaped_original_href = encode_uri_component(product["href"])
    new_href = f"https://pin.locamo.de/t/t?a=1714038695&as=1650547786&t=2&tk=1&url={escaped_original_href}"
    return {**product, "ahref": new_href}


def add_urtesenteret_no_affiliate_link(product: dict) -> dict:
    if "promo_id" in product["href"]:
        return product
    original_href = product["href"]
    new_href = f"{original_href}?promo_id=36861"
    return {**product, "ahref": new_href}


def add_amoi_no_affiliate_link(product: dict) -> dict:
    if "to.amoi.no" in product["href"]:
        return product
    escaped_original_href = encode_uri_component(product["href"])
    new_href = f"https://to.amoi.no/t/t?a=1846807883&as=1532500672&t=2&tk=1&url={escaped_original_href}"
    return {**product, "ahref": new_href}


def add_morrisons_uk_affiliate_link(product: dict) -> dict:
    if "www.linkbux.com" in product["href"]:
        return product
    escaped_original_href = encode_uri_component(product["href"])
    new_href = f"https://www.linkbux.com/track?pid=LB00006527&mid=14214&url={escaped_original_href}"
    return {**product, "ahref": new_href}


def get_affiliate_handler(product: MpnOffer):
    if "byggmax.no" in product["href"]:
        return
    # elif "byggmax.no" in product["href"]:
    #    return add_byggmax_affiliate_link
    elif "amazon.se" in product["href"]:
        return add_se_amazon_affiliate_link
    elif "amazon.es" in product["href"]:
        return add_es_amazon_affiliate_link
    elif "amazon.it" in product["href"]:
        return add_it_amazon_affiliate_link
    elif "amazon.de" in product["href"]:
        return add_de_amazon_affiliate_link
    elif "amazon.com" in product["href"]:
        return add_com_amazon_affiliate_link
    elif "amazon.sg" in product["href"]:
        return add_sg_amazon_affiliate_link
    elif "amazon.co.uk" in product["href"]:
        return add_uk_amazon_affiliate_link
    elif "amazon.fr" in product["href"]:
        return add_fr_amazon_affiliate_link
    elif "amazon.nl" in product["href"]:
        return add_nl_amazon_affiliate_link
    elif "amazon.pl" in product["href"]:
        return add_pl_amazon_affiliate_link
    elif "grontfokus.no" in product["href"]:
        return add_grontfokus_affiliate_link
    elif "lampegiganten.no" in product["href"]:
        return add_lampegiganten_affiliate_link
    elif "cdon.no" in product["href"]:
        return add_cdon_affiliate_link
    elif "matsmart.se" in product["href"]:
        return add_se_matsmart_affiliate_link
    elif "hemkop.se" in product["href"]:
        return add_se_hemkop_affiliate_link
    # elif "mat.se" in product["href"]:
    #    return add_se_mat_se_affiliate_link
    elif "mathem.se" in product["href"]:
        return add_mathem_se_affiliate_link
    elif "beijerbygg.se" in product["href"]:
        return add_se_beijerbygg_affiliate_link
    elif "skanskabyggvaror.se" in product["href"]:
        return add_se_skanska_affiliate_link
    # elif "byggmax.se" in product["href"]:
    #    return add_se_byggmax_affiliate_link
    elif "www.slikkepott.no" in product["href"]:
        return add_slikkepott_affiliate_link
    elif "natur.no" in product["href"]:
        return add_natur_no_affiliate_link
    elif "www.buildor.se" in product["href"]:
        return add_buildor_se_affiliate_link
    elif "www.strawberrynet.com" in product["href"]:
        return add_strawberrynet_affiliate_link
    elif "www.davidsenshop.dk" in product["href"]:
        return add_davidsen_affiliate_link
    elif "www.locamo.de" in product["href"]:
        return add_locamo_de_affiliate_link
    elif "urtesenteret.no" in product["href"]:
        return add_urtesenteret_no_affiliate_link
    elif "amoi.no" in product["href"]:
        return add_amoi_no_affiliate_link
    elif "groceries.morrisons.com" in product["href"]:
        return add_morrisons_uk_affiliate_link


def add_affilite_link_to_product(product: MpnOffer) -> MpnOffer:
    if not not product.get("ahref"):
        return product
    handler = get_affiliate_handler(product)
    if handler is None:
        return product
    else:
        return handler(product)


def add_affiliate_links(products: Iterable[MpnOffer]) -> Iterable[MpnOffer]:
    return (add_affilite_link_to_product(product) for product in products)
