from typing import Iterable
from operator import itemgetter


def meta_fields_result_to_dict(meta_fields: Iterable) -> dict:
    result = {}
    for x in meta_fields:
        uri, field = itemgetter("uri", "field")(x)
        result[uri] = [field, *result[uri]] if uri in result.keys() else [field]
    return result


def remove_protected_fields(products: Iterable, uri_field_dict: dict) -> Iterable:
    return map(
        lambda x: remove_protected_fields_from_product(x, uri_field_dict), products
    )


def remove_protected_fields_from_product(product: dict, uri_field_dict: dict) -> dict:
    uri = product["uri"]
    if uri in uri_field_dict.keys():
        for field in uri_field_dict[uri]:
            try:
                del product[field]
            except KeyError:
                pass
    return product
