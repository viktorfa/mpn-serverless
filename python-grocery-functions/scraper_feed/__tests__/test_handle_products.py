from unittest import TestCase
import json

from scraper_feed.handle_products import transform_product, get_categories
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
            "ignore_none": False,
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
            "ignore_none": False,
        }

        actual = transform_product(product, config)
        self.assertIsNotNone(actual["imageUrl"])
        self.assertIsNotNone(actual["dealer"])

    def test_transform_product_with_dealer(self):
        product = self.obsbygg_products[0]
        config = {
            "provenance": "obsbygg",
            "fieldMapping": get_field_mapping(),
            "categoriesLimits": [],
            "extractQuantityFields": ["title"],
            "ignore_none": False,
        }

        product["dealer"] = "HALLA"

        actual = transform_product(product, config)
        self.assertIn("HALLA", actual["uri"])

    def test_transform_product_with_ignore_none_fields(self):
        product = self.obsbygg_products[0]
        config = {
            "provenance": "obsbygg",
            "fieldMapping": get_field_mapping(),
            "categoriesLimits": [],
            "extractQuantityFields": [],
            "ignore_none": True,
        }

        actual = transform_product(product, config)
        self.assertIsNone(actual.get("quantity"))
        self.assertIn("obsbygg", actual["uri"])


class TestGetCategories(TestCase):
    def test_get_categories_remove_first(self):
        categories = ["Hjem", "Grønnsaker", "Bananer"]
        categories_limits = [1, None]

        actual = get_categories(categories, categories_limits)
        self.assertListEqual(actual, categories[1:])

    def test_get_categories_no_config(self):
        categories = ["Hjem", "Grønnsaker", "Bananer"]
        categories_limits = None

        actual = get_categories(categories, categories_limits)
        self.assertListEqual(actual, categories)

    def test_get_categories_remove_first_and_last(self):
        categories = ["Hjem", "Grønnsaker", "Bananer"]
        categories_limits = [1, -1]

        actual = get_categories(categories, categories_limits)
        self.assertListEqual(actual, ["Grønnsaker"])

