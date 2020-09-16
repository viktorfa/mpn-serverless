from amp_types.quantity_types import MpnUnit
import re
import logging
from typing import Optional

import pydash

from parsing.constants import (
    quantity_units,
    si_mappings,
    piece_units,
    piece_value_units,
    quantity_value_units,
    alt_unit_map,
)
from parsing.enums import unit_types


def extract_number(string: str) -> Optional[float]:
    try:
        pattern = r"(\d+,\d+)"
        matches = re.findall(pattern, string)
        if len(matches) > 0:
            return matches[0]
        else:
            return None
    except AttributeError as exc:
        logging.warning("" + str(exc) + "Could not extract number from: ")
        return None


def extract_numbers_with_context(string: str) -> Optional[list]:
    """
    Finds numbers and returns a list of tuples with the number and its prefix and suffix.
    """
    number_pattern = r"(\d+(?:,\d+)?)"
    compiled_number_pattern = re.compile(number_pattern, re.A)
    number_matches = re.finditer(number_pattern, string)
    number_matches = list(number_matches)
    result = list(
        [string[: x.span(0)[0]], x.group(0), string[x.span(0)[1] :]]
        for x in number_matches
    )
    return result


def extract_units_from_number_context(context: list) -> list:
    """
    Extracts likely and known units from numbers.
    """
    known_prefixes = [
        {"symbol": "x"},
    ]
    known_suffixes = [
        *list({"symbol": x} for x in piece_units),
        *list({"symbol": x} for x in quantity_units),
        *list({"symbol": x} for x in quantity_value_units),
        *list({"symbol": x} for x in piece_value_units),
        {"symbol": "x"},
    ]
    prefix, number, suffix = context
    prefix = re.sub(r" $", "", prefix)
    suffix = re.sub(r"^ ", "", suffix)
    prefix_unit = re.split(r" ", prefix)[-1]
    # prefix_unit = re.sub(r"[^a-zA-Z/]", "", prefix_unit)
    suffix_unit = re.split(r" ", suffix)[0]
    suffix_unit = re.sub(r"[^a-zA-Z/]", "", suffix_unit)
    result = {}
    for x in known_prefixes:
        if prefix_unit == x["symbol"]:
            result["unit"] = x["symbol"]
            result["value"] = float(format_number(number))
            break
    for x in known_suffixes:
        if suffix_unit == x["symbol"]:
            result["unit"] = x["symbol"]
            result["value"] = float(format_number(number))
            break

    # Handle cases like 4x130g. Get the x as a unit even though there are no spaces.
    if not result.get("unit") and pydash.get(suffix_unit, "0") == "x":
        result["unit"] = "x"
        result["value"] = float(format_number(number))
    if (
        not result.get("unit")
        and pydash.get(prefix_unit, "-1") == "x"
        and not re.match(r"[0-9]", pydash.get(prefix_unit, "-2"))
    ):
        result["unit"] = "x"
        result["value"] = float(format_number(number))
    return result


def extract_number_unit_pairs(string: str) -> Optional[list]:
    try:
        # matches formats like "kr 50,00" or "kr 5"
        number_pattern = r"(\d+(?:,\d+)?)"
        # matches what comes after a number
        unit_pattern = r"\d+(?:,\d+)?(\D+)"
        string = string.replace(" ", "")
        number_matches = re.findall(number_pattern, string)
        number_matches = list(map(float, map(format_number, number_matches)))
        unit_matches = re.findall(unit_pattern, string)

        number_of_pairs = min(len(number_matches), len(unit_matches))
        if number_of_pairs > 0:
            return list(zip(number_matches, unit_matches))
    except AttributeError:
        return None


def format_number(string: str, loader_context: dict = dict()) -> Optional[str]:
    try:
        return string.replace(",", ".")
    except AttributeError as exc:
        logging.warning(
            ""
            + str(exc)
            + "Could not extract number from: "
            + str(loader_context.items())
        )
        return None


def extract_unit(string: str) -> Optional[MpnUnit]:
    string = string.lower()
    quantity_unit_pattern = r"^({})".format(r"|".join(quantity_units))
    quantity_unit_matches = re.findall(quantity_unit_pattern, string)
    if quantity_unit_matches:
        unit = quantity_unit_matches[0]
        unit = alt_unit_map[unit] if unit in alt_unit_map.keys() else unit
        return dict(symbol=unit, type=unit_types.QUANTITY, si=get_si(unit))

    quantity_value_pattern = r"^({})".format(r"|".join(quantity_value_units))
    quantity_value_matches = re.findall(quantity_value_pattern, string)
    if quantity_value_matches:
        unit = extract_quantity_unit(quantity_value_matches[0])
        unit = unit.replace("/", "")
        unit = alt_unit_map[unit] if unit in alt_unit_map.keys() else unit
        return dict(symbol=unit, type=unit_types.QUANTITY_VALUE, si=get_si(unit))

    piece_unit_pattern = r"^({})".format(r"|".join(piece_units))
    piece_unit_matches = re.findall(piece_unit_pattern, string)
    if piece_unit_matches:
        unit = piece_unit_matches[0]
        return dict(symbol=unit, type=unit_types.PIECE)

    piece_value_pattern = r"^({})".format(r"|".join(piece_value_units))
    piece_value_matches = re.findall(piece_value_pattern, string)
    if piece_value_matches:
        unit = extract_piece_unit(piece_value_matches[0])
        unit = unit.replace("/", "")
        return dict(symbol=unit, type=unit_types.PIECE_VALUE)

    if string == "x":
        return dict(symbol="x", type=unit_types.MULTIPLIER)


def extract_quantity_unit(string: str) -> Optional[str]:
    quantity_unit_pattern = r"({})".format(r"|".join(quantity_units))
    quantity_unit_matches = re.findall(quantity_unit_pattern, string)
    if quantity_unit_matches:
        return quantity_unit_matches[0]


def extract_piece_unit(string: str) -> Optional[str]:
    piece_unit_pattern = r"({})".format(r"|".join(piece_units))
    piece_unit_matches = re.findall(piece_unit_pattern, string)
    if piece_unit_matches:
        return piece_unit_matches[0]


def get_si(unit: str) -> Optional[dict]:
    unit = alt_unit_map[unit] if unit in alt_unit_map.keys() else unit
    return si_mappings[unit] if unit in si_mappings.keys() else None
