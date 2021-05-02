from unittest import TestCase

from transform.offer import get_field_from_scraper_offer


class TestGetFieldFromOffer(TestCase):
    def test_get_field_from_offer_with_additional_property(self):
        actual = get_field_from_scraper_offer(
            {"additionalProperties": [{"key": "unitPrice", "value": "55"}]}, "unitPrice"
        )
        self.assertEqual(actual, "55")

    def test_get_field_from_offer(self):
        actual = get_field_from_scraper_offer({"dealer": "rusta"}, "dealer")
        self.assertEqual(actual, "rusta")

    def test_get_field_from_offer_when_has_none(self):
        actual = get_field_from_scraper_offer({"dealer": "rusta"}, "price")
        self.assertEqual(actual, None)
