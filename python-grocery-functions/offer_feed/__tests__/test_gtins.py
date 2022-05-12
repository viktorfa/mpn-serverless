import logging
from unittest import TestCase
from offer_feed.gtins import (
    match_offers_with_gtins_map,
    get_lists_of_offers_with_same_gtins,
)

logging.basicConfig(level=logging.DEBUG)


class TestMatchOffersWithGtinsMap(TestCase):
    def test_match_offers_with_gtins_map_basic(self):
        offers = [{}]
        gtins_map = {"": []}

        actual = match_offers_with_gtins_map(offers, gtins_map)
        self.assertIsInstance(actual, list)

    def test_match_offers_with_gtins_map_with_matching_offers(self):
        offers = [
            {"gtins": {"gtin13": "1234567890123"}, "uri": "123", "provenance": "meny"}
        ]
        gtins_map = {"gtin13_1234567890123": [{"uri": "abc", "provenance": "kolonial"}]}

        actual = match_offers_with_gtins_map(offers, gtins_map)
        self.assertIsInstance(actual, list)
        self.assertGreater(actual, [])

    def test_get_lists_of_offers_with_same_gtins_basic(self):
        source_offers = []
        target_offers = []

        actual = get_lists_of_offers_with_same_gtins(source_offers, target_offers)
        self.assertIsInstance(actual, list)

    def test_get_lists_of_offers_with_same_gtins_with_matching_offers(self):
        source_offers = [
            {"gtins": {"gtin13": "1234567890123"}, "uri": "123", "provenance": "meny"}
        ]
        target_offers = [
            {
                "gtins": {"gtin13": "1234567890123"},
                "uri": "abc",
                "provenance": "kolonial",
            }
        ]

        actual = get_lists_of_offers_with_same_gtins(source_offers, target_offers)
        self.assertIsInstance(actual, list)
        self.assertGreater(actual, [])

    def test_get_lists_of_offers_with_same_gtins_with_matching_offers_ean_and_gtin13(
        self,
    ):
        source_offers = [
            {"gtins": {"gtin13": "1234567890123"}, "uri": "123", "provenance": "meny"}
        ]
        target_offers = [
            {
                "gtins": {"ean": "1234567890123"},
                "uri": "abc",
                "provenance": "kolonial",
            }
        ]

        actual = get_lists_of_offers_with_same_gtins(source_offers, target_offers)
        self.assertIsInstance(actual, list)
        self.assertGreater(actual, [])

    def test_get_lists_of_offers_with_same_gtins_without_matching_offers(self):
        source_offers = [
            {"gtins": {"gtin13": "1234567890123"}, "uri": "123", "provenance": "meny"}
        ]
        target_offers = [
            {
                "gtins": {"gtin13": "1234567890120"},
                "uri": "abc",
                "provenance": "kolonial",
            }
        ]

        actual = get_lists_of_offers_with_same_gtins(source_offers, target_offers)
        self.assertIsInstance(actual, list)
        self.assertEqual(len(actual), 0)

    def test_get_lists_of_offers_with_same_gtins_with_matching_offers_same_uri(self):
        source_offers = [
            {"gtins": {"gtin13": "1234567890123"}, "uri": "123", "provenance": "meny"}
        ]
        target_offers = [
            {
                "gtins": {"gtin13": "1234567890123"},
                "uri": "123",
                "provenance": "kolonial",
            }
        ]

        actual = get_lists_of_offers_with_same_gtins(source_offers, target_offers)
        self.assertIsInstance(actual, list)
        self.assertEqual(len(actual), 0)
