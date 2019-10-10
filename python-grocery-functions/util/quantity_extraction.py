from typing import List

from util.parsing import extract_number_unit_pairs, extract_unit
from util.enums import unit_types
from amp_types.quantity_types import QuantityField, ValueField, ItemsField, ExtractQuantityReturnType


def analyze_quantity(strings: List[str]) -> ExtractQuantityReturnType:
    """Returns a dict describing the quantity and value with unitsextracted from strings.
    Quantity can be denominated in both size (kg, l, grams, etc.) or pieces (packs, bags, etc.)
    It also extracts value which is price divided by quantity. It does this only by parsing text, not by using the price then dividing it by the extracted quantity.
    """

    # TODO Also support extracting number of items. E.g. sometimes an offer describes a buy one get one free, or buy 4 for 50,00,-. The extracting currently doesn't realize this.

    return dict(
        quantity=extract_quantity(strings),
        value=extract_value(strings),
        items=extract_items(strings),
    )


def extract_quantity(strings: List[str]) -> QuantityField:
    number_unit_pairs = extract_number_unit_pairs(''.join(strings))

    if number_unit_pairs:
        number_unit_dicts = [
            {'value': value,
             'unit': extract_unit(string)
             } for value, string in number_unit_pairs]
        # Some product descriptions have 'x' as multiplier of quantity
        for (i, x) in enumerate(number_unit_dicts):
            try:
                if x['unit']['type'] == unit_types.MULTIPLIER:
                    number_unit_dicts[i+1]['value'] *= x['value']
            except Exception:
                pass

        size = next((x['value'] for x in number_unit_dicts if x['unit']
                     and x['unit']['type'] == unit_types.QUANTITY), None)

        pieces = next((x['value'] for x in number_unit_dicts if x['unit']
                       and x['unit']['type'] == unit_types.PIECE), None)
        size_amount = dict(min=size, max=size)
        piece_amount = dict(min=pieces, max=pieces)
        size_unit = next(
            (x['unit'] for x in number_unit_dicts if x['unit']
             and x['unit']['type'] == unit_types.QUANTITY), None)
        piece_unit = next(
            (x['unit'] for x in number_unit_dicts if x['unit']
             and x['unit']['type'] == unit_types.PIECE), None)

        size = dict(
            unit=size_unit,
            amount=size_amount
        )
        pieces = dict(
            unit=piece_unit,
            amount=piece_amount
        )
        return dict(
            size=size,
            pieces=pieces,
        )

    return None


def extract_value(strings: List[str]) -> ValueField:
    number_unit_pairs = extract_number_unit_pairs(''.join(strings))

    if number_unit_pairs:
        number_unit_dicts = [
            {'value': value,
             'unit': extract_unit(string)
             } for value, string in number_unit_pairs]
        # Some product descriptions have 'x' as multiplier of quantity
        for (i, x) in enumerate(number_unit_dicts):
            try:
                if x['unit']['type'] == unit_types.MULTIPLIER:
                    number_unit_dicts[i+1]['value'] *= x['value']
            except Exception:
                pass

        min_size = min((x['value'] for x in number_unit_dicts if x['unit']
                        and x['unit']['type'] == unit_types.QUANTITY_VALUE), default=None)
        max_size = max((x['value'] for x in number_unit_dicts if x['unit']
                        and x['unit']['type'] == unit_types.QUANTITY_VALUE), default=None)
        min_pieces = min((x['value'] for x in number_unit_dicts if x['unit']
                          and x['unit']['type'] == unit_types.PIECE_VALUE), default=None)
        max_pieces = max((x['value'] for x in number_unit_dicts if x['unit']
                          and x['unit']['type'] == unit_types.PIECE_VALUE), default=None)
        size_amount = dict(min=min_size, max=max_size)
        piece_amount = dict(min=min_pieces, max=max_pieces)

        size_unit = next(
            (x['unit'] for x in number_unit_dicts if x['unit']
             and x['unit']['type'] == unit_types.QUANTITY_VALUE), None)
        piece_unit = next(
            (x['unit'] for x in number_unit_dicts if x['unit']
             and x['unit']['type'] == unit_types.PIECE_VALUE), None)

        size = dict(
            unit=size_unit,
            amount=size_amount
        )
        pieces = dict(
            unit=piece_unit,
            amount=piece_amount
        )
        return dict(
            size=size,
            pieces=pieces,
        )
    return dict(quantity_value=None, piece_value=None)


def extract_items(strings: List[str]) -> ItemsField:
    return dict(max=1, min=1)
