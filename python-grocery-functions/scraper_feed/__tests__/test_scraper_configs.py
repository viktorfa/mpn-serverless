from unittest import TestCase

from scraper_feed.scraper_configs import get_field_map


class TestGetFieldMap(TestCase):
    def test_basic_with_default_config(self):
        actual = get_field_map({"source": "not_real"})
        self.assertIn("title", actual["fields"].keys())

    def test_get_field_map(self):
        actual = get_field_map({"source": "obsbygg"})
        self.assertIn("title", actual["fields"].keys())
        self.assertIn("image", actual["fields"].keys())
        self.assertEqual(actual["fields"]["image"], "imageUrl")

