import json
from datetime import datetime
from typing import Union

from util.enums import currency_codes, provenances, select_methods


def flatten(l: list) -> list:
    return [item for sublist in l for item in sublist]


def get_nested(gettable, path: Union[list, str], default=None):
    """Gets a nested value of a dict.
    Does not support number keys if path is string.
    """
    try:
        if type(path) is str:
            return get_nested(gettable, path.split("."))
        if len(path) == 1:
            return gettable.get(path[0])
        else:
            return get_nested(gettable.get(path[0]), path[1:])
    except AttributeError:
        return default


def get_kolonial_image_url(url: str) -> str:
    if url[0] == "/":
        return "https://kolonial.no" + url.replace("list", "detail")
    else:
        return url


def get_shopgun_href(product) -> str:
    return "https://shopgun.com/publications/paged/{}/pages/{}".format(
        product.get("catalog_id"), product.get("catalog_page")
    )


def json_handler(obj):
    if hasattr(obj, "isoformat"):
        return obj.isoformat()
    else:
        return json.dumps(obj)


def json_time_to_datetime(json_time_string: str) -> datetime:
    return datetime.strptime(json_time_string, "%Y-%m-%dT%H:%M:%S+0000")


def get_product_uri(provenance: str, _id: str) -> str:
    return "{}:product:{}".format(provenance, _id)
