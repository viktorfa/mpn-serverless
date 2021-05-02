import json
from pathlib import Path

from parsing.quantity_extraction import parse_explicit_quantity
from unittest.case import TestCase

with open(
    Path(__file__).parent.absolute().joinpath("jemogfix_item.json")
) as jemogfix_item_file:
    jemogfix_item = json.load(jemogfix_item_file)


class ParseExplicitQuantity(TestCase):
    def test_no_explicit_quantity_fields(self):
        self.assertDictEqual(parse_explicit_quantity({}, {}), {})

    def test_with_size_and_unit(self):
        actual = parse_explicit_quantity(
            {
                "additionalProperties": [
                    {"key": "quantityValue", "value": "4"},
                    {"key": "quantityUnit", "value": "l"},
                ]
            },
            {},
        )
        self.assertEqual(actual["quantity"]["size"]["amount"]["min"], 4)

    def test_with_size_string(self):
        actual = parse_explicit_quantity(
            {
                "additionalProperties": [
                    {"key": "quantityString", "value": "10lm"},
                ]
            },
            {},
        )
        self.assertEqual(actual["quantity"]["size"]["amount"]["min"], 10)

    def test_with_value_string(self):
        actual = parse_explicit_quantity(
            {
                "additionalProperties": [
                    {"key": "quantityString", "value": "0.5kr/kvm"},
                ]
            },
            {},
        )
        self.assertEqual(actual["value"]["size"]["amount"]["min"], 0.5)

    def test_with_value_and_unit(self):
        actual = parse_explicit_quantity(
            {
                "additionalProperties": [
                    {"key": "unitPrice", "value": "16"},
                    {"key": "unitPriceUnit", "value": "g"},
                ]
            },
            {},
        )
        self.assertEqual(actual["value"]["size"]["amount"]["min"], 16)

    def test_with_item(self):
        actual = parse_explicit_quantity(jemogfix_item, {})
        self.assertEqual(actual["value"]["size"]["amount"]["min"], 22.9)