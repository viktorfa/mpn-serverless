from unittest import TestCase, mock

from scraper_feed.filters import (
    filter_product,
    replace_offer_fields_with_meta,
)


class TestFilters(TestCase):
    def test_filter_with_has_operator(self):
        self.assertTrue(
            filter_product(
                {"categories": ["Matvarer"]},
                [{"operator": "has", "source": "categories", "target": "Matvarer"}],
            )
        )

    def test_filter_with_has_operator_different_case(self):
        self.assertTrue(
            filter_product(
                {"categories": ["matvarer", "barer"]},
                [{"operator": "has", "source": "categories", "target": "barer"}],
            )
        )

    def test_filter_with_has_operator_should_be_false(self):
        self.assertFalse(
            filter_product(
                {"categories": ["tights", "treningstights"]},
                [{"operator": "has", "source": "categories", "target": "matvarer"}],
            )
        )

    def test_filter_with_equal_operator(self):
        self.assertTrue(
            filter_product(
                {"brand": "Makita"},
                [{"operator": "eq", "source": "brand", "target": "makita"}],
            )
        )

    def test_filter_with_equal_operator_should_be_false(self):
        self.assertFalse(
            filter_product(
                {"brand": ""},
                [{"operator": "eq", "source": "brand", "target": "makita"}],
            )
        )


class TestAddMeta(TestCase):
    def test_add_basic_meta_to_offer(self):
        scraper_offer = {"title": "Byggryn", "price": 22, "quantityString": "64g"}
        meta_objects = {
            "manual": {
                "quantityString": {"key": "quantityString", "value": "100g"},
                "brand": {"key": "brand", "value": "Mølleren"},
            }
        }

        actual = replace_offer_fields_with_meta(scraper_offer, meta_objects)

        self.assertEqual(actual["quantityString"], "100g")
        self.assertEqual(actual["brand"], "Mølleren")
        self.assertEqual(actual["price"], 22)
