from unittest import TestCase
import pydash

from parsing.parsing import (
    extract_number_unit_pairs,
    extract_unit,
    extract_numbers_with_context,
    extract_units_from_number_context,
)
from parsing.quantity_extraction import extract_quantity
from parsing.enums import unit_types


class TestExtractQuantity(TestCase):
    def test_basic(self):
        actual = extract_quantity(["kr 180,77/kgHomestyle 4x130g KandaPepperburger"])
        self.assertEqual(pydash.get(actual, "size.amount.min"), 520)
        self.assertEqual(pydash.get(actual, "size.unit.symbol"), "g")

    def test_with_multiplier_and_total(self):
        actual = extract_quantity(["6x0,5 liter, 3 l"])
        self.assertEqual(pydash.get(actual, "size.amount.min"), 3)
        self.assertEqual(pydash.get(actual, "size.unit.symbol"), "l")

    def test_with_full_string_unit(self):
        actual = extract_quantity(["0,5 liter"])
        print("actual")
        print(actual)
        self.assertEqual(pydash.get(actual, "size.amount.min"), 0.5)
        self.assertEqual(pydash.get(actual, "size.unit.symbol"), "l")

    def test_with_multiplier_last(self):
        actual = extract_quantity(["1,5lx8 flaske"])
        print("actual")
        print(actual)
        self.assertEqual(pydash.get(actual, "size.amount.min"), 12)
        self.assertEqual(pydash.get(actual, "size.unit.symbol"), "l")
