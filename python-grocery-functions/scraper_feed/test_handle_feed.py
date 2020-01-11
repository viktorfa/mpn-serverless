from unittest import TestCase, mock

from scraper_feed.handle_feed import _get_handle_config, DEFAULT_OFFER_COLLECTION_NAME
from scraper_feed import handle_feed
from util.errors import NoHandleConfigError


class TestHandleFeed(TestCase):
    def test_get_handle_config(self):
        handle_feed.get_handle_config = mock.patch
        expected_collection_name = "groceryoffer"
        with mock.patch.object(
            handle_feed,
            "get_handle_config",
            return_value={
                "provenance": "shopgun",
                "collection_name": expected_collection_name,
            },
        ) as mock_method:
            self.assertEqual(
                _get_handle_config({"provenance": "halla"})["collection_name"],
                expected_collection_name,
            )

    def test_get_handle_config_without_config(self):
        handle_feed.get_handle_config = mock.patch
        with mock.patch.object(
            handle_feed, "get_handle_config", side_effect=NoHandleConfigError
        ) as mock_method:
            self.assertEqual(
                _get_handle_config({"provenance": "halla"})["collection_name"],
                DEFAULT_OFFER_COLLECTION_NAME,
            )
