from unittest import TestCase
import pydash

from parsing.quantity_extraction import (
    extract_quantity,
    standardize_quantity,
    analyze_quantity,
)


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

    def test_with_safe_unit_list_not_parse(self):
        actual = extract_quantity(["4m"], ["l"])
        print("actual")
        print(actual)
        self.assertEqual(pydash.get(actual, "size.amount.min"), None)
        self.assertEqual(pydash.get(actual, "size.unit.symbol"), None)

    def test_with_safe_unit_list(self):
        actual = extract_quantity(["4m"], ["l", "m"])
        print("actual")
        print(actual)
        self.assertEqual(pydash.get(actual, "size.amount.min"), 4)
        self.assertEqual(pydash.get(actual, "size.unit.symbol"), "m")

    def test_with_safe_unit_list_not_si(self):
        actual = extract_quantity(["4dl"], ["l", "m"])
        print("actual")
        print(actual)
        self.assertEqual(pydash.get(actual, "size.amount.min"), 4)
        self.assertEqual(pydash.get(actual, "size.unit.symbol"), "dl")

    def test_with_number_that_can_raise_error(self):
        actual = extract_quantity(
            [
                "Kjente metallbiler i størrelse 1:43 (9-10cm). Velg mellom: BMW Z8 Softtop, BMW Z4 Roadster, VW New Beetle Cabrio, Porsche Carrera GT. Alder 3+."
            ],
        )
        print("actual")
        print(actual)


class TestAnalyzeQuantity(TestCase):
    def test_basic_without_size(self):
        offer = {
            "items": {"max": 1, "min": 1},
            "pricing": {"price": 44, "priceUnit": "/m"},
            "pieces": {},
            "quantity": {
                "size": {},
            },
        }
        actual = analyze_quantity(offer)
        self.assertEqual(pydash.get(actual, "quantity.size.amount.min"), 1)
        self.assertEqual(pydash.get(actual, "quantity.size.unit.symbol"), "m")

    def test_basic_without_size_and_non_si_unit(self):
        offer = {
            "items": {"max": 1, "min": 1},
            "pricing": {"price": 44, "priceUnit": "/lm"},
            "pieces": {},
            "quantity": {
                "size": {},
            },
        }
        actual = analyze_quantity(offer)
        self.assertEqual(pydash.get(actual, "quantity.size.amount.min"), 1)
        self.assertEqual(pydash.get(actual, "quantity.size.unit.symbol"), "m")

    def test_basic_without_size_and_piece_unit(self):
        offer = {
            "items": {"max": 1, "min": 1},
            "pricing": {"price": 44, "priceUnit": "/stk"},
            "pieces": {},
            "quantity": {
                "size": {},
            },
        }
        actual = analyze_quantity(offer)
        self.assertIsNone(pydash.get(actual, "quantity.size.amount.min"))
        self.assertIsNone(pydash.get(actual, "quantity.size.unit.symbol"))

    def test_basic_with_size(self):
        offer = {
            "items": {"max": 1, "min": 1},
            "pricing": {"price": 44, "priceUnit": "/m"},
            "pieces": {},
            "quantity": {
                "size": {
                    "amount": {"max": 100.0, "min": 100.0},
                    "unit": {
                        "si": {"factor": 0.001, "symbol": "kg"},
                        "symbol": "g",
                        "type": "quantity",
                    },
                },
            },
        }
        actual = analyze_quantity(offer)
        self.assertEqual(pydash.get(actual, "quantity.size.amount.min"), 1)
        self.assertEqual(pydash.get(actual, "quantity.size.unit.symbol"), "m")


class TestStandarizeQuantity(TestCase):
    def test_basic(self):
        offer = {
            "items": {"max": 1, "min": 1},
            "pieces": {},
            "quantity": {
                "size": {
                    "amount": {"max": 100.0, "min": 100.0},
                    "unit": {
                        "si": {"factor": 0.001, "symbol": "kg"},
                        "symbol": "g",
                        "type": "quantity",
                    },
                },
            },
        }

        actual = standardize_quantity(offer)
        self.assertIsInstance(actual, dict)
        self.assertEqual(
            pydash.get(actual, ["quantity", "size", "standard", "min"]), 0.1
        )
        self.assertEqual(
            pydash.get(actual, ["quantity", "size", "standard", "max"]), 0.1
        )

    def test_value_basic_2(self):
        offer = {
            "items": {"max": 1, "min": 1},
            "pieces": {},
            "pricing": {
                "price": 10,
                "currency": "NOK",
                "prePrice": 34.9,
                "priceUnit": "pcs",
            },
            "value": {},
            "quantity": {
                "size": {
                    "unit": {
                        "symbol": "g",
                        "type": "quantity",
                        "si": {"symbol": "kg", "factor": 0.001},
                    },
                    "amount": {"min": 500, "max": 500},
                    "standard": {"min": 0.5, "max": 0.5},
                },
                "pieces": {},
            },
        }
        analyzed = analyze_quantity(offer)
        print("analyzed")
        print(analyzed)
        actual = standardize_quantity(analyzed)
        print("actual")
        print(actual)
        self.assertIsInstance(actual, dict)
        self.assertEqual(pydash.get(actual, ["value", "size", "amount", "min"]), 0.02)
        self.assertEqual(pydash.get(actual, ["value", "size", "amount", "max"]), 0.02)
        self.assertEqual(pydash.get(actual, ["value", "size", "standard", "min"]), 20)
        self.assertEqual(pydash.get(actual, ["value", "size", "standard", "max"]), 20)

    def test_value_basic(self):
        offer = {
            "items": {"max": 1, "min": 1},
            "pieces": {},
            "quantity": {
                "size": {
                    "amount": {"max": 100.0, "min": 100.0},
                    "unit": {
                        "si": {"factor": 0.001, "symbol": "kg"},
                        "symbol": "g",
                        "type": "quantity",
                    },
                },
            },
            "value": {
                "size": {
                    "amount": {"max": 1, "min": 1},
                    "unit": {
                        "si": {"factor": 0.001, "symbol": "kg"},
                        "symbol": "g",
                        "type": "quantity",
                    },
                },
            },
        }

        actual = standardize_quantity(offer)
        self.assertIsInstance(actual, dict)
        self.assertEqual(pydash.get(actual, ["value", "size", "amount", "min"]), 1)
        self.assertEqual(pydash.get(actual, ["value", "size", "amount", "max"]), 1)
        self.assertEqual(pydash.get(actual, ["value", "size", "standard", "min"]), 1000)
        self.assertEqual(pydash.get(actual, ["value", "size", "standard", "max"]), 1000)
