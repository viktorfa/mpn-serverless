import json

import pydash


def get_sns_message(event: dict) -> dict:
    return json.loads(pydash.get(event, "Records.0.Sns.Message"))
