import json
from unittest import TestCase
from pprint import pprint

from scraper_feed.handle_config import generate_handle_config
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
        with open("assets/byggmax-scraper-feed.json") as byggmax_products_json:
            self.byggmax_products = json.load(byggmax_products_json)
        with open("assets/monter-scraper-feed.json") as monter_products_json:
            self.monter_products = json.load(monter_products_json)

    def test_meny_products(self):
        config = generate_handle_config(
            {
                "provenance": "meny",
                "collection_name": "groceryoffer",
                "categoriesLimits": [],
                "extractQuantityFields": ["unit_price_raw", "subtitle", "title"],
                "fieldMapping": [
                    {"source": "sku", "destination": "ean", "replace_type": "key"},
                    {
                        "source": "product_variant",
                        "destination": "description",
                        "replace_type": "key",
                    },
                ],
            }
        )
        actual = handle_products(self.meny_products, config)
        pprint(actual[0])
        self.assertIsInstance(actual, list)
        self.assertEqual(len(actual), len(self.meny_products))
        self.assertIsNotNone(actual[0]["title"])
        self.assertIsNotNone(actual[0]["pricing"])
        self.assertIsNotNone(actual[0]["href"])
        self.assertIsNotNone(actual[0]["uri"])
        self.assertIsNotNone(actual[0]["quantity"]["size"])
        self.assertIsNotNone(actual[0]["sku"])
        self.assertIsNotNone(actual[0]["gtins"]["gtin13"])

    def test_kolonial_products(self):
        config = generate_handle_config(
            {
                "provenance": "kolonial",
                "collection_name": "groceryoffer",
                "categoriesLimits": [],
                "extractQuantityFields": ["unit_price_raw", "product_variant", "title"],
                "fieldMapping": [
                    {
                        "source": "product_variant",
                        "destination": "description",
                        "replace_type": "key",
                    },
                ],
            }
        )
        actual = handle_products(self.kolonial_products, config)
        pprint(actual[0])
        self.assertIsInstance(actual, list)
        self.assertEqual(len(actual), len(self.kolonial_products))
        self.assertIsNotNone(actual[0]["title"])
        self.assertIsNotNone(actual[0]["pricing"])
        self.assertIsNotNone(actual[0]["href"])
        self.assertIsNotNone(actual[0]["uri"])
        self.assertIsNotNone(actual[0]["quantity"]["size"])

    def test_europris_products(self):
        config = generate_handle_config(
            {
                "provenance": "europris",
                "collection_name": "groceryoffer",
                "categoriesLimits": [],
                "extractQuantityFields": ["description", "name"],
                "fieldMapping": [
                    {"source": "name", "destination": "title", "replace_type": "key",},
                    {"source": "link", "destination": "href", "replace_type": "key",},
                ],
            }
        )
        actual = handle_products(self.europris_products, config)
        pprint(actual[0])
        self.assertIsInstance(actual, list)
        self.assertEqual(len(actual), len(self.europris_products))
        self.assertIsNotNone(actual[0]["title"])
        self.assertIsNotNone(actual[0]["pricing"])
        self.assertIsNotNone(actual[0]["href"])
        self.assertIsNotNone(actual[0]["uri"])
        self.assertIsNotNone(actual[0]["sku"])

    def test_shopgun_products(self):
        config = generate_handle_config(
            {"provenance": "shopgun", "collection_name": "groceryoffer",}
        )
        actual = handle_products(self.shopgun_products, config)
        pprint(actual[0])
        self.assertIsInstance(actual, list)
        self.assertEqual(len(actual), len(self.shopgun_products))
        self.assertIsNotNone(actual[0]["title"])
        self.assertIsNotNone(actual[0]["pricing"])
        self.assertIsNotNone(actual[0]["href"])
        self.assertIsNotNone(actual[0]["uri"])
        self.assertIsNotNone(actual[0]["quantity"]["size"])

    def test_swecandy_products(self):
        config = generate_handle_config(
            {"provenance": "swecandy", "collection_name": "groceryoffer",}
        )
        actual = handle_products(self.swecandy_products, config)
        pprint(actual[0])
        self.assertIsInstance(actual, list)
        self.assertEqual(len(actual), len(self.swecandy_products))
        self.assertIsNotNone(actual[0]["title"])
        self.assertIsNotNone(actual[0]["pricing"])
        self.assertIsNotNone(actual[0]["href"])
        self.assertIsNotNone(actual[0]["uri"])
        self.assertIsNotNone(actual[0]["quantity"]["size"])
        self.assertIsNotNone(actual[0]["categories"])

    def test_gottebiten_products(self):
        config = generate_handle_config(
            {"provenance": "gottebiten.se", "collection_name": "groceryoffer",}
        )
        actual = handle_products(self.gottebiten_products, config)
        pprint(actual[0])
        self.assertIsInstance(actual, list)
        self.assertEqual(len(actual), len(self.gottebiten_products))
        self.assertIsNotNone(actual[0]["title"])
        self.assertIsNotNone(actual[0]["pricing"])
        self.assertIsNotNone(actual[0]["href"])
        self.assertIsNotNone(actual[0]["uri"])
        self.assertIsNotNone(actual[0]["quantity"]["size"])
        self.assertIsNotNone(actual[0]["provenanceId"])

    def test_iherb_products(self):
        config = generate_handle_config(
            {
                "provenance": "iherb",
                "collection_name": "iherboffers",
                "fieldMapping": [
                    {"source": "sku", "destination": "mpn", "replace_type": "key",},
                ],
            }
        )
        actual = handle_products(self.iherb_products, config)
        pprint(actual[0])
        self.assertIsInstance(actual, list)
        self.assertEqual(len(actual), len(self.iherb_products))
        self.assertIsNotNone(actual[0]["title"])
        self.assertIsNotNone(actual[0]["pricing"])
        self.assertIsNotNone(actual[0]["href"])
        self.assertIsNotNone(actual[0]["uri"])
        self.assertIsNotNone(actual[0]["quantity"]["size"])
        self.assertIsNotNone(actual[0]["mpn"])
        self.assertIsNotNone(actual[0]["sku"])
        self.assertIsNotNone(actual[0]["imageUrl"])

    def test_obsbygg_products(self):
        config = generate_handle_config(
            {"provenance": "obsbygg", "collection_name": "byggoffers",}
        )
        actual = handle_products(self.obsbygg_products, config)
        pprint(actual[0])
        self.assertIsInstance(actual, list)
        self.assertEqual(len(actual), len(self.obsbygg_products))
        self.assertIsNotNone(actual[0]["title"])
        self.assertIsNotNone(actual[0]["pricing"])
        self.assertIsNotNone(actual[0]["href"])
        self.assertIsNotNone(actual[0]["uri"])
        self.assertIsNotNone(actual[0]["sku"])
        self.assertIsNotNone(actual[0]["imageUrl"])

    def test_byggmax_products(self):
        config = generate_handle_config(
            {"provenance": "byggmax.no", "collection_name": "byggoffers",}
        )
        actual = handle_products(self.byggmax_products, config)
        pprint(actual[0])
        self.assertIsInstance(actual, list)
        self.assertEqual(len(actual), len(self.byggmax_products))
        self.assertIsNotNone(actual[0]["title"])
        self.assertIsNotNone(actual[0]["pricing"])
        self.assertIsNotNone(actual[0]["href"])
        self.assertIsNotNone(actual[0]["uri"])
        self.assertIsNotNone(actual[0]["sku"])
        self.assertIsNotNone(actual[0]["imageUrl"])

    def test_monter_products(self):
        config = generate_handle_config(
            {
                "provenance": "monter.no",
                "collection_name": "byggoffers",
                "fieldMapping": [
                    {"source": "NOBB", "destination": "nobb", "replace_type": "key",},
                ],
            }
        )
        actual = handle_products(self.monter_products, config)
        pprint(actual[0])
        self.assertIsInstance(actual, list)
        self.assertEqual(len(actual), len(self.monter_products))
        self.assertEqual(len(actual), len(self.monter_products))
        self.assertIsNotNone(actual[0]["gtins"])
        self.assertIsNotNone(actual[0]["gtins"]["nobb"])
        self.assertIsNotNone(actual[0]["title"])
        self.assertIsNotNone(actual[0]["pricing"])
        self.assertIsNotNone(actual[0]["href"])
        self.assertIsNotNone(actual[0]["uri"])
        self.assertIsNotNone(actual[0]["sku"])
        self.assertIsNotNone(actual[0]["imageUrl"])

    def test_single_meny_product(self):
        config = generate_handle_config(
            {
                "provenance": "meny",
                "collection_name": "groceryoffer",
                "categoriesLimits": [],
                "extractQuantityFields": ["unit_price_raw", "unit_raw", "title"],
                "fieldMapping": [
                    {"source": "sku", "destination": "ean", "replace_type": "key"},
                    {
                        "source": "product_variant",
                        "destination": "description",
                        "replace_type": "key",
                    },
                ],
            }
        )
        scraper_offer = {
            "price": 3.0,
            "title": "Tomat stykk",
            "unit_price_raw": "kr\u00a039,90/kg",
            "unit_raw": "80\u00a0g",
            "quantity_info": "80\u00a0g",
            "image_url": "https://res.cloudinary.com/norgesgruppen/image/upload/c_pad,b_white,f_auto,h_320,q_50,w_320/v1558839429/Product/2000406400006.png",
            "product_url": "https://meny.no/varer/frukt-gront/gronnsaker/tomater/tomat-stykk-2000406400006",
            "meny_id": "2000406400006",
            "provenance": "meny",
            "url_fingerprint": "460cae747c054fc03fac9a0a88d8a9ef172c279d",
            "url": "https://meny.no/varer/frukt-gront/gronnsaker/tomater/tomat-stykk-2000406400006",
            "canonical_url": "https://meny.no/varer/frukt-gront/gronnsaker/tomater/tomat-stykk-2000406400006",
            "sku": "2000406400006",
            "gtin13": "2000406400006",
            "provenanceId": "2000406400006",
            "priceCurrency": "NOK",
        }
        result = handle_products([scraper_offer], config)
        # 39.9 if parsing the value string. 37.5 if inferring it from the quantity..
        self.assertEqual(result[0]["value"]["size"]["standard"]["min"], 37.5)

