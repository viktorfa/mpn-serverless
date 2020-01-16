import json
from datetime import datetime
from unittest import TestCase

from util.helpers import json_time_to_datetime, json_handler, get_nested


class TestHelpers(TestCase):
    def test_json_time_to_datetime(self):
        json_time = "2019-01-20T22:59:59+0000"
        actual = json_time_to_datetime(json_time)
        self.assertIsInstance(actual, datetime)

    def test_json_handler_for_normal_object(self):
        obj = dict(hei="per", hallo=5)
        actual = json.dumps(obj, default=json_handler)
        self.assertIsInstance(actual, str)
        self.assertIn("per", actual)
        self.assertIn("5", actual)

    def test_json_handler_for_object_with_special_type(self):
        obj = dict(hei="per", hallo=5, run_till=datetime.utcnow())
        actual = json.dumps(obj, default=json_handler)
        self.assertIsInstance(actual, str)
        self.assertIn("per", actual)
        self.assertIn("run_till", actual)

    def test_get_nested(self):
        self.assertEqual(get_nested({1: {2: {3: "yay"}}}, [1, 2, 3]), "yay")
        self.assertEqual(get_nested({1: "yay"}, [1]), "yay")
        self.assertEqual(get_nested({"a": {"b": {"c": "yay"}}}, "a.b.c"), "yay")
        self.assertEqual(get_nested({"a": "yay"}, "a"), "yay")
