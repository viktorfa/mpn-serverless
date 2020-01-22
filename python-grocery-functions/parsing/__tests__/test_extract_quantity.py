from unittest import TestCase

from parsing.parsing import (
    extract_number_unit_pairs,
    extract_unit,
    extract_numbers_with_context,
    extract_units_from_number_context,
)
from parsing.quantity_extraction import _extract_quantity
from parsing.enums import unit_types


class ExtractQuantity(TestCase):
    def test_basic(self):
        actual = _extract_quantity(
            ["kr 180,77/kgHomestyle 4x130g KandaPepperburger", ""]
        )
        print("actual")
        print(actual)
