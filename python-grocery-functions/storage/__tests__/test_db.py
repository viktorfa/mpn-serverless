from unittest import TestCase

from storage.db import get_handle_configs


class TestDb(TestCase):
    def setUp(self):
        pass

    def test_get_handle_config(self):
        result = get_handle_configs("obsbygg_spider")
        self.assertIsNotNone(result[0].get("collection_name"))
