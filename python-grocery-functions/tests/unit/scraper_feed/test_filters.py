from unittest import TestCase

from scraper_feed.filters import filter_product
from scraper_feed.helpers import get_product_pricing


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


class TestGetProductPricing(TestCase):
    def test_get_product_pricing(self):
        scraper_offer = {
            "price": 870.0,
            "priceCurrency": "SEK",
        }
        actual = get_product_pricing(scraper_offer)

        self.assertEqual(actual["price"], 870.0)
        self.assertEqual(actual["currency"], "SEK")

    def test_get_product_pricing_with_string(self):
        scraper_offer = {
            "price": "870.0",
            "priceCurrency": "SEK",
        }
        actual = get_product_pricing(scraper_offer)
        self.assertEqual(actual["price"], 870.0)
        self.assertEqual(actual["currency"], "SEK")

    def test_get_product_pricing_with_string_and_comma(self):
        scraper_offer = {
            "price": "870,00",
            "priceCurrency": "SEK",
        }
        actual = get_product_pricing(scraper_offer)
        self.assertEqual(actual["price"], 870.0)
        self.assertEqual(actual["currency"], "SEK")
