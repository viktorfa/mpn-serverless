from unittest import TestCase
import json

from scraper_feed.handle_products import transform_product
from scraper_feed.scraper_configs import get_field_mapping


class TestHandleProducts(TestCase):
    def setUp(self):
        with open("assets/obsbygg-scraper-feed.json") as obsbygg_products_json:
            self.obsbygg_products = json.load(obsbygg_products_json)
        with open("assets/swecandy-scraper-feed.json") as swecandy_products_json:
            self.swecandy_products = json.load(swecandy_products_json)

    def test_transform_product(self):
        product = self.obsbygg_products[0]
        config = {
            "provenance": "obsbygg",
            "fieldMapping": get_field_mapping(),
            "categoriesLimits": [],
            "extractQuantityFields": ["title"],
        }

        actual = transform_product(product, config)
        self.assertIsNotNone(actual["imageUrl"])
        self.assertIsNotNone(actual["dealer"])

        product = self.swecandy_products[0]
        config = {
            "provenance": "swecandy.se",
            "fieldMapping": get_field_mapping(),
            "categoriesLimits": [],
            "extractQuantityFields": ["title"],
        }

        actual = transform_product(product, config)
        self.assertIsNotNone(actual["imageUrl"])
        self.assertIsNotNone(actual["dealer"])

