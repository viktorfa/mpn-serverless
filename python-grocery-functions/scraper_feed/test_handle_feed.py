from unittest import TestCase

from scraper_feed.handle_feed import populate_config, DEFAULT_OFFER_COLLECTION_NAME


class TestHandleFeed(TestCase):
    def test_populate_config(self):
        self.assertEqual(populate_config(
            {"provenance": "kolonial"})["offers_collection_name"], "groceryoffer")
        self.assertEqual(populate_config(
            {"provenance": "halla"})["offers_collection_name"], DEFAULT_OFFER_COLLECTION_NAME)
        self.assertEqual(populate_config(
            {"provenance": "iherb"})["offers_collection_name"], "herbvuoffer")
