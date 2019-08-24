import json
from unittest import TestCase

from util.enums import provenances
from scraper_feed.handle_products import handle_products


class Basic(TestCase):
    def setUp(self):
        with open('assets/meny-scraper-feed.json') as meny_products_json:
            self.meny_products = json.load(meny_products_json)
        with open('assets/kolonial-scraper-feed.json') as kolonial_products_json:
            self.kolonial_products = json.load(kolonial_products_json)
        with open('assets/europris-scraper-feed.json') as europris_products_json:
            self.europris_products = json.load(europris_products_json)
        with open('assets/shopgun-scraper-feed.json') as shopgun_products_json:
            self.shopgun_products = json.load(shopgun_products_json)

    def test_meny_products(self):
        actual = handle_products(self.meny_products, provenances.MENY)
        self.assertIsInstance(actual, list)
        self.assertEqual(len(actual), len(self.meny_products))
        self.assertIsNotNone(actual[0]['run_till'])
        self.assertIsNotNone(actual[0]['run_from'])
        print(actual[0]['run_till'])
        print(type(actual[0]['run_till']))

    def test_kolonial_products(self):
        actual = handle_products(self.kolonial_products, provenances.KOLONIAL)
        self.assertIsInstance(actual, list)
        self.assertEqual(len(actual), len(self.kolonial_products))

    def test_europris_products(self):
        actual = handle_products(self.europris_products, provenances.EUROPRIS)
        self.assertIsInstance(actual, list)
        self.assertEqual(len(actual), len(self.europris_products))

    def test_shopgun_products(self):
        actual = handle_products(self.shopgun_products, provenances.SHOPGUN)
        self.assertIsInstance(actual, list)
        self.assertEqual(len(actual), len(self.shopgun_products))
        self.assertIsNotNone(actual[0]['run_till'])
        self.assertIsNotNone(actual[0]['run_from'])
        print(actual[0]['run_till'])
        print(type(actual[0]['run_till']))
