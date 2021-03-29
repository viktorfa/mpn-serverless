import json

import pydash


def get_sns_message(event: dict) -> dict:
    return json.loads(pydash.get(event, "Records.0.Sns.Message"))

def get_real_quantity(offer):
    try:
        return pydash.get(offer, "quantity.size.amount.min") * pydash.get(offer, "quantity.size.unit.si.factor")
    except Exception:
        return None

