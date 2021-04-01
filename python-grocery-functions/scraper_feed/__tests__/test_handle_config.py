from unittest import TestCase, mock

from scraper_feed import handle_config
from scraper_feed.handle_config import (
    fetch_handle_config,
)
from util.errors import NoHandleConfigError


class TestHandleConfig(TestCase):
    def test_get_handle_config(self):
        handle_config.get_handle_config = mock.patch
        expected_collection_name = "groceryoffer"
        with mock.patch.object(
            handle_config,
            "get_handle_config",
            return_value={
                "provenance": "shopgun",
                "market": "no",
                "namespace": "meny",
                "collection_name": expected_collection_name,
            },
        ) as mock_method:
            self.assertEqual(
                fetch_handle_config({"provenance": "halla"})["collection_name"],
                expected_collection_name,
            )

    def test_get_handle_config_without_config(self):
        handle_config.get_handle_config = mock.patch
        try:
            with mock.patch.object(
                handle_config, "get_handle_config", side_effect=NoHandleConfigError
            ) as mock_method:
                self.assertIsNone(
                    fetch_handle_config({"provenance": "halla"})["collection_name"]
                )
            self.fail("Should throw error and not come this far")
        except NoHandleConfigError:
            pass
