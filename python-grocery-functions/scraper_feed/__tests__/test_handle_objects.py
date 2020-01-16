import json
from unittest import TestCase, mock
from pprint import pprint

from util.enums import provenances
from scraper_feed.handle_products import handle_products


class TestWithConfig(TestCase):
    def setUp(self):
        with open("assets/meny-scraper-feed.json") as meny_products_json:
            self.meny_products = json.load(meny_products_json)
        with open("assets/kolonial-scraper-feed.json") as kolonial_products_json:
            self.kolonial_products = json.load(kolonial_products_json)
        with open("assets/europris-scraper-feed.json") as europris_products_json:
            self.europris_products = json.load(europris_products_json)
        with open("assets/shopgun-scraper-feed.json") as shopgun_products_json:
            self.shopgun_products = json.load(shopgun_products_json)
        with open("assets/swecandy-scraper-feed.json") as swecandy_products_json:
            self.swecandy_products = json.load(swecandy_products_json)
        with open("assets/gottebiten-scraper-feed.json") as gottebiten_products_json:
            self.gottebiten_products = json.load(gottebiten_products_json)
        with open("assets/iherb-scraper-feed.json") as iherb_products_json:
            self.iherb_products = json.load(iherb_products_json)
        with open("assets/obsbygg-scraper-feed.json") as obsbygg_products_json:
            self.obsbygg_products = json.load(obsbygg_products_json)

    def test_meny_products(self):
        actual = handle_products(
            self.meny_products,
            {
                "source": "meny",
                "extractQuantityFields": ["unit_price_raw", "product_variant", "title"],
                "fields": {"sku": "ean", "product_variant": "description"},
            },
        )
        pprint(actual[0])
        self.assertIsInstance(actual, list)
        self.assertEqual(len(actual), len(self.meny_products))
        self.assertIsNotNone(actual[0]["title"])
        self.assertIsNotNone(actual[0]["pricing"])
        self.assertIsNotNone(actual[0]["href"])
        self.assertIsNotNone(actual[0]["uri"])
        self.assertIsNotNone(actual[0]["size"])
        self.assertIsNotNone(actual[0]["sku"])
        self.assertIsNotNone(actual[0]["gtins"]["gtin13"])

    def test_kolonial_products(self):
        actual = handle_products(
            self.kolonial_products,
            {
                "source": "kolonial",
                "extractQuantityFields": ["unit_price_raw", "product_variant", "title"],
                "fields": {"product_variant": "description"},
            },
        )
        pprint(actual[0])
        self.assertIsInstance(actual, list)
        self.assertEqual(len(actual), len(self.kolonial_products))
        self.assertIsNotNone(actual[0]["title"])
        self.assertIsNotNone(actual[0]["pricing"])
        self.assertIsNotNone(actual[0]["href"])
        self.assertIsNotNone(actual[0]["uri"])
        self.assertIsNotNone(actual[0]["size"])

    def test_europris_products(self):
        actual = handle_products(
            self.europris_products,
            {
                "source": "europris",
                "extractQuantityFields": ["description", "name"],
                "fields": {"name": "title", "link": "href"},
            },
        )
        pprint(actual[0])
        self.assertIsInstance(actual, list)
        self.assertEqual(len(actual), len(self.europris_products))
        self.assertIsNotNone(actual[0]["title"])
        self.assertIsNotNone(actual[0]["pricing"])
        self.assertIsNotNone(actual[0]["href"])
        self.assertIsNotNone(actual[0]["uri"])
        self.assertIsNotNone(actual[0]["sku"])

    def test_shopgun_products(self):
        actual = handle_products(self.shopgun_products, {"source": "shopgun"})
        pprint(actual[0])
        self.assertIsInstance(actual, list)
        self.assertEqual(len(actual), len(self.shopgun_products))
        self.assertIsNotNone(actual[0]["title"])
        self.assertIsNotNone(actual[0]["pricing"])
        self.assertIsNotNone(actual[0]["href"])
        self.assertIsNotNone(actual[0]["uri"])
        self.assertIsNotNone(actual[0]["size"])

    def test_swecandy_products(self):
        actual = handle_products(self.swecandy_products, {"source": "swecandy.se"})
        pprint(actual[0])
        self.assertIsInstance(actual, list)
        self.assertEqual(len(actual), len(self.swecandy_products))
        self.assertIsNotNone(actual[0]["title"])
        self.assertIsNotNone(actual[0]["pricing"])
        self.assertIsNotNone(actual[0]["href"])
        self.assertIsNotNone(actual[0]["uri"])
        self.assertIsNotNone(actual[0]["size"])
        self.assertIsNotNone(actual[0]["categories"])

    def test_gottebiten_products(self):
        actual = handle_products(self.gottebiten_products, {"source": "gottebiten.se"})
        pprint(actual[0])
        self.assertIsInstance(actual, list)
        self.assertEqual(len(actual), len(self.gottebiten_products))
        self.assertIsNotNone(actual[0]["title"])
        self.assertIsNotNone(actual[0]["pricing"])
        self.assertIsNotNone(actual[0]["href"])
        self.assertIsNotNone(actual[0]["uri"])
        self.assertIsNotNone(actual[0]["size"])
        self.assertIsNotNone(actual[0]["provenanceId"])

    def test_iherb_products(self):
        actual = handle_products(
            self.iherb_products, {"source": "iherb", "fields": {"sku": "mpn"}}
        )
        pprint(actual[0])
        self.assertIsInstance(actual, list)
        self.assertEqual(len(actual), len(self.iherb_products))
        self.assertIsNotNone(actual[0]["title"])
        self.assertIsNotNone(actual[0]["pricing"])
        self.assertIsNotNone(actual[0]["href"])
        self.assertIsNotNone(actual[0]["uri"])
        self.assertIsNotNone(actual[0]["size"])
        self.assertIsNotNone(actual[0]["mpn"])
        self.assertIsNotNone(actual[0]["sku"])
        self.assertIsNotNone(actual[0]["imageUrl"])

    def test_obsbygg_products(self):
        actual = handle_products(self.iherb_products, {"source": "obsbygg"})
        pprint(actual[0])
        self.assertIsInstance(actual, list)
        self.assertEqual(len(actual), len(self.iherb_products))
        self.assertIsNotNone(actual[0]["title"])
        self.assertIsNotNone(actual[0]["pricing"])
        self.assertIsNotNone(actual[0]["href"])
        self.assertIsNotNone(actual[0]["uri"])
        self.assertIsNotNone(actual[0]["sku"])
        self.assertIsNotNone(actual[0]["imageUrl"])
