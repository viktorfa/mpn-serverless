from pydash import find

from unittest import TestCase

from scraper_feed.scraper_configs import get_field_mapping


class TestGetFieldMap(TestCase):
    def test_basic_with_default_config(self):
        actual = get_field_mapping()
        self.assertIsInstance(actual, list)
        self.assertIsInstance(
            find(actual, lambda x: x["source"] == "url"), dict,
        )

    def test_get_field_map(self):
        field_mapping = [
            {
                "replace_type": "key",
                "source": "Manufacturer Number",
                "destination": "mpn",
            }
        ]
        actual = get_field_mapping(field_mapping)
        self.assertDictEqual(
            find(actual, lambda x: x["destination"] == "mpn"), field_mapping[0],
        )

