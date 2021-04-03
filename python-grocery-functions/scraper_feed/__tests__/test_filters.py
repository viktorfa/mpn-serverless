from unittest import TestCase, mock

from scraper_feed.filters import filter_product


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
