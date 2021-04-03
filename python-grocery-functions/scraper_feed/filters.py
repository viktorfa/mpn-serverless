from typing import List
import pydash
import logging

from amp_types.amp_product import (
    MpnOffer,
    OfferFilterConfig,
)


def filter_product(product: MpnOffer, filters: List[OfferFilterConfig]):
    """
    Will return true if any of the filters are accepted. I.e. OR chaining."""
    for _filter in filters:
        op1 = pydash.get(product, _filter["source"])
        operator = _filter["operator"]
        op2 = _filter["target"]
        if not op1:
            continue
        if not op2:
            logging.error(_filter)
            raise Exception("Filter has no target operand")
        if type(op1) is str:
            op1 = op1.lower()
        elif type(op1) is list:
            op1 = list(x.lower() if type(x) is str else x for x in op1)
        if type(op2) is str:
            op2 = op2.lower()
        elif type(op2) is list:
            op2 = list(x.lower() if type(x) is str else x for x in op2)

        is_accepted = False

        if operator == "eq":
            is_accepted = op1 == op2
        elif operator == "has":
            is_accepted = op2 in op1
        elif operator == "in":
            is_accepted = op1 in op2
        elif operator == "gt":
            is_accepted = op1 > op2
        elif operator == "lt":
            is_accepted = op1 < op2
        if is_accepted:
            return True
    return False