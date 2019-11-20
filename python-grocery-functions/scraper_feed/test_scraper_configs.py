from unittest import TestCase

from scraper_feed.scraper_configs import get_field_map


class TestGetFieldMap(TestCase):
    def test_basic(self):
        actual = get_field_map({"source": "www.iherb.com"})
        self.assertIn("title", actual["fields"].keys())

    def test_add_field(self):
        actual = get_field_map({"source": "meny"})
        self.assertSetEqual(set(["sku", "ean"]), set(actual["fields"]["sku"]))
