from transform.offer import get_field_from_scraper_offer
from amp_types.amp_product import MpnOffer
from typing import List
import pydash
import re

from parsing.parsing import (
    extract_numbers_with_context,
    extract_unit,
    extract_units_from_number_context,
)
from parsing.enums import unit_types
from amp_types.amp_product import MpnOffer, ScraperOffer, HandleConfig
from amp_types.quantity_types import (
    QuantityField,
    ItemsField,
    ExtractQuantityReturnType,
    SiConfig,
)
from parsing.constants import (
    quantity_units,
    piece_units,
    alt_unit_map,
)


def get_standard_si_amount(si_config: SiConfig, value: float, invert=False):
    return (
        (value / si_config["factor"])
        if invert is True
        else (value * si_config["factor"])
    )


def standardize_quantity(offer: MpnOffer):
    for quantity_type in ("quantity.size", "value.size"):
        try:
            standardized = {
                key: get_standard_si_amount(
                    pydash.get(offer, quantity_type)["unit"]["si"],
                    value,
                    quantity_type == "value.size",
                )
                for key, value in pydash.get(offer, quantity_type)["amount"].items()
            }
            pydash.get(offer, quantity_type)["standard"] = standardized
        except Exception as e:
            continue
    return offer


def analyze_quantity(offer: MpnOffer) -> MpnOffer:
    # Use price unit as size when the product price is denominated as a unit.
    price_unit_string: str = offer["pricing"].get("priceUnit")
    if price_unit_string:
        price_unit = extract_unit(price_unit_string)
        if price_unit and price_unit["type"] in (
            unit_types.QUANTITY,
            unit_types.QUANTITY_VALUE,
        ):
            if not pydash.get(offer, ["quantity", "size", "amount"]):
                offer["quantity"]["size"] = {
                    "amount": {"min": 1, "max": 1},
                    "unit": price_unit,
                }
    size_amount = pydash.get(offer, ["quantity", "size", "amount"])
    if size_amount and not pydash.get(offer, ["value", "size", "amount"]):
        # Has quantity but not value. Let's calculate value.
        try:
            price = offer["pricing"]["price"]
            offer["value"]["size"] = {
                "amount": {
                    "min": price / size_amount["min"],
                    "max": price / size_amount["max"],
                },
                "unit": pydash.get(offer, ["quantity", "size", "unit"]),
            }
        except Exception:
            pass
    value_amount = pydash.get(offer, ["value", "size", "amount"])
    if value_amount and not size_amount:
        # Has value but not quantity. Let's calculate quantity.
        try:
            price = offer["pricing"]["price"]
            offer["quantity"]["size"] = {
                "amount": {
                    "min": size_amount["min"] / price,
                    "max": size_amount["max"] / price,
                },
                "unit": pydash.get(offer, ["value", "size", "unit"]),
            }
        except Exception:
            pass
    return offer


def parse_quantity(strings: List[str], safe_units=None) -> ExtractQuantityReturnType:
    """Returns a dict describing the quantity and value with unitsextracted from strings.
    Quantity can be denominated in both size (kg, l, grams, etc.) or pieces (packs, bags, etc.)
    It also extracts value which is price divided by quantity. It does this only by parsing text, not by using the price then dividing it by the extracted quantity.
    """

    # TODO Also support extracting number of items. E.g. sometimes an offer describes a buy one get one free, or buy 4 for 50,00,-. The extracting currently doesn't realize this.

    _strings = list(s.lower() for s in strings)

    quantity = extract_quantity(_strings, safe_units)
    value = extract_value(_strings, safe_units)
    items = extract_items(_strings)

    return dict(quantity=quantity, value=value, items=items)


def extract_quantity(strings: List[str], safe_units=None) -> QuantityField:
    extracted_strings = []
    for string in strings:
        context = extract_numbers_with_context(string)
        extracted_numbers = (
            pydash.chain(context).map(extract_units_from_number_context).value()
        )
        extracted_numbers = handle_multipliers(extracted_numbers)
        extracted_strings.append(extracted_numbers)
    size = {}
    pieces = {}
    for string in extracted_strings:
        for (i, number) in enumerate(x for x in string if x):
            unit = number.get("unit")
            unit = alt_unit_map[unit] if unit in alt_unit_map.keys() else unit
            unit = extract_unit(unit)

            if unit["type"] not in (unit_types.QUANTITY, unit_types.PIECE):
                continue
            if unit["symbol"] in quantity_units:
                if safe_units and unit["si"]["symbol"] not in safe_units:
                    continue
                size_value = number.get("value")
                size_amount = dict(min=size_value, max=size_value)
                size = dict(unit=unit, amount=size_amount)
                result = dict(size=size, pieces=dict())
            elif unit["symbol"] in piece_units:
                pieces_value = number.get("value")
                pieces_amount = dict(min=pieces_value, max=pieces_value)
                pieces = dict(unit=unit, amount=pieces_amount)

    result = dict(size=size, pieces=pieces)
    return result


def extract_value(strings: List[str], safe_units=None) -> QuantityField:
    extracted_strings = []
    for string in strings:
        context = extract_numbers_with_context(string)
        extracted_numbers = (
            pydash.chain(context)
            .map(extract_units_from_number_context)
            .filter(lambda x: not not x)
            .value()
        )
        extracted_numbers = handle_multipliers(extracted_numbers)

        extracted_strings.append(extracted_numbers)

    size = {}
    pieces = {}
    for string in extracted_strings:
        for (i, number) in enumerate(string):
            unit = extract_unit(number.get("unit"))
            if safe_units and unit["symbol"] not in safe_units:
                continue
            if unit["type"] not in (unit_types.QUANTITY_VALUE, unit_types.PIECE_VALUE):
                continue
            if unit["symbol"] in quantity_units:
                if safe_units and unit["si"]["symbol"] not in safe_units:
                    continue
                size_value = number.get("value")
                size_amount = dict(min=size_value, max=size_value)
                size = dict(unit=unit, amount=size_amount)
                result = dict(size=size, pieces=dict())
            elif unit["symbol"] in piece_units:
                pieces_value = number.get("value")
                pieces_amount = dict(min=pieces_value, max=pieces_value)
                pieces = dict(unit=unit, amount=pieces_amount)

    result = dict(size=size, pieces=pieces)

    return result


def handle_multipliers(extracted_numbers):
    for (i, number) in enumerate(extracted_numbers):
        if number.get("unit") in ["x"] and pydash.get(
            extracted_numbers, [i + 1, "value"]
        ):
            extracted_numbers[i + 1]["value"] *= number.get("value")
        elif (
            number.get("unit") in ["x"]
            and pydash.get(extracted_numbers, [i - 1, "value"])
            and i > 0
        ):
            extracted_numbers[i - 1]["value"] *= number.get("value")

    return extracted_numbers


def extract_items(strings: List[str]) -> ItemsField:
    return dict(max=1, min=1)


def parse_explicit_quantity(offer: ScraperOffer, config: HandleConfig):
    parsed_quantity = parse_quantity(get_explicit_quantity_strings(offer, config))
    return {
        k: v
        for k, v in parsed_quantity.items()
        if v
        and v.get("pieces") not in ({}, None) != {}
        or v.get("size") not in ({}, None)
    }


def get_explicit_quantity_strings(offer: ScraperOffer, config: HandleConfig):
    explicit_quantity = get_field_from_scraper_offer(offer, "quantityValue")
    explicit_quantity_unit = get_field_from_scraper_offer(offer, "quantityUnit")

    explicit_unit_price = get_field_from_scraper_offer(offer, "unitPrice")
    explicit_unit_price_unit = get_field_from_scraper_offer(offer, "unitPriceUnit")

    explicit_quantity_string = get_field_from_scraper_offer(offer, "quantityString")
    explicit_value_string = get_field_from_scraper_offer(offer, "valueString")

    result = []
    if explicit_quantity and explicit_quantity_unit:
        result.append(f"{explicit_quantity}{explicit_quantity_unit}")
    if explicit_unit_price and explicit_unit_price_unit:
        result.append(
            f"{explicit_unit_price}/{re.sub(r'/', '',explicit_unit_price_unit)}"
        )
    if explicit_quantity_string:
        result.append(explicit_quantity_string)
    if explicit_value_string:
        result.append(explicit_value_string)

    return result
