from unittest import TestCase

from config.mongo import get_collection
from storage.db import get_handle_config


class TestDb(TestCase):
    def setUp(self):
        pass

    def test_get_handle_config(self):
        result = get_handle_config("obsbygg")
        self.assertIsNotNone(result.get("collection_name"))

