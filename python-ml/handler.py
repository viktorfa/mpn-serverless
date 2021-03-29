from util.helpers import get_sns_message
from lib import create_models, add_similar_offers, add_identical_offers


N_HIGHEST = 12
OFFER_LIMIT = 2 ** 18


def create_models_sns(event, context):
    try:
        event_message = get_sns_message(event)
    except TypeError:
        event_message = event
    collection_name = event_message["collection_name"]
    offer_limit = event_message.get("offerLimit", OFFER_LIMIT)

    result = create_models(collection_name, offer_limit)

    return {"result": result, "event": event}


def create_models_trigger(event, context):
    collection_name = event["collection_name"]
    offer_limit = event.get("offerLimit", OFFER_LIMIT)

    result = create_models(collection_name, offer_limit)

    return {"result": result, "event": event}



def add_similar_offers_trigger(event, context):
    collection_name = event["collection_name"]
    offer_limit = event.get("offerLimit", OFFER_LIMIT)
    n_highest = event.get("nHighest", N_HIGHEST)
    provenance = event.get("provenance")

    result = add_similar_offers(collection_name, offer_limit, n_highest, provenance)

    return {"result": result, "event": event}


def add_similar_offers_sns(event, context):
    try:
        event_message = get_sns_message(event)
    except TypeError:
        event_message = event
    collection_name = event_message["collection_name"]
    offer_limit = event_message.get("offerLimit", OFFER_LIMIT)
    n_highest = event_message.get("nHighest", N_HIGHEST)
    provenance = event_message.get("provenance")

    result = add_similar_offers(collection_name, offer_limit, n_highest, provenance)

    return {"result": result, "event": event}

def add_identical_offers_trigger(event, context):
    collection_name = event["collection_name"]
    offer_limit = event.get("offerLimit", OFFER_LIMIT)
    n_highest = event.get("nHighest", N_HIGHEST)
    provenance = event.get("provenance")

    result = add_identical_offers(collection_name, offer_limit, n_highest, provenance)

    return {"result": result, "event": event}


def add_identical_offers_sns(event, context):
    try:
        event_message = get_sns_message(event)
    except TypeError:
        event_message = event
    collection_name = event_message["collection_name"]
    offer_limit = event_message.get("offerLimit", OFFER_LIMIT)
    n_highest = event_message.get("nHighest", N_HIGHEST)
    provenance = event_message.get("provenance")

    result = add_identical_offers(collection_name, offer_limit, n_highest, provenance)

    return {"result": result, "event": event}
