from typing import List
import pydash

from parsing.parsing import (
    extract_number_unit_pairs,
    extract_unit,
    extract_numbers_with_context,
    extract_units_from_number_context,
)
from parsing.enums import unit_types
from amp_types.quantity_types import (
    QuantityField,
    ValueField,
    ItemsField,
    ExtractQuantityReturnType,
)
from parsing.constants import (
    quantity_units,
    piece_units,
    quantity_value_units,
    piece_value_units,
    si_mappings,
)


def analyze_quantity(strings: List[str]) -> ExtractQuantityReturnType:
    """Returns a dict describing the quantity and value with unitsextracted from strings.
    Quantity can be denominated in both size (kg, l, grams, etc.) or pieces (packs, bags, etc.)
    It also extracts value which is price divided by quantity. It does this only by parsing text, not by using the price then dividing it by the extracted quantity.
    """

    # TODO Also support extracting number of items. E.g. sometimes an offer describes a buy one get one free, or buy 4 for 50,00,-. The extracting currently doesn't realize this.

    _strings = list(s.lower() for s in strings)

    quantity = extract_quantity(_strings)
    value = extract_value(_strings)
    items = extract_items(_strings)
    quantity["items"] = items
    return dict(quantity=quantity, value=value)


def extract_quantity(strings: List[str]) -> QuantityField:
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
        for (i, number) in enumerate(string):
            if number.get("unit") in quantity_units:
                size_value = number.get("value")
                size_amount = dict(min=size_value, max=size_value)
                size_unit = dict(
                    symbol=number.get("unit"),
                    type=unit_types.QUANTITY,
                    si=si_mappings.get(number.get("unit")),
                )
                size = dict(unit=size_unit, amount=size_amount)
                result = dict(size=size, pieces=dict())
            elif number.get("unit") in piece_units:
                pieces_value = number.get("value")
                pieces_amount = dict(min=pieces_value, max=pieces_value)
                pieces_unit = dict(symbol=number.get("unit"), type=unit_types.PIECE)
                pieces = dict(unit=pieces_unit, amount=pieces_amount)

    result = dict(size=size, pieces=pieces)
    return result


def extract_value(strings: List[str]) -> QuantityField:
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
            if number.get("unit") in quantity_value_units:
                size_value = number.get("value")
                size_amount = dict(min=size_value, max=size_value)
                size_unit = dict(
                    symbol=number.get("unit"),
                    type=unit_types.QUANTITY_VALUE,
                    si=si_mappings.get(number.get("unit")),
                )
                size = dict(unit=size_unit, amount=size_amount)
                result = dict(size=size, pieces=dict())
            elif number.get("unit") in piece_value_units:
                pieces_value = number.get("value")
                pieces_amount = dict(min=pieces_value, max=pieces_value)
                pieces_unit = dict(
                    symbol=number.get("unit"), type=unit_types.PIECE_VALUE
                )
                pieces = dict(unit=pieces_unit, amount=pieces_amount)

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
