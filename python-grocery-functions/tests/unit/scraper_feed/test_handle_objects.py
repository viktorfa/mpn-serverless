import json
import logging
from pprint import pprint
from unittest import TestCase

from scraper_feed.filters import transform_and_filter_offers
from scraper_feed.scraper_configs import get_field_mapping


class TestWithConfig(TestCase):
    def setUp(self):
        with open("tests/fixtures/feeds/meny-scraper-feed.json") as meny_products_json:
            self.meny_products = json.load(meny_products_json)
        with open(
            "tests/fixtures/feeds/kolonial-scraper-feed.json"
        ) as kolonial_products_json:
            self.kolonial_products = json.load(kolonial_products_json)
        with open(
            "tests/fixtures/feeds/europris-scraper-feed.json"
        ) as europris_products_json:
            self.europris_products = json.load(europris_products_json)
        with open(
            "tests/fixtures/feeds/shopgun-scraper-feed.json"
        ) as shopgun_products_json:
            self.shopgun_products = json.load(shopgun_products_json)
        with open(
            "tests/fixtures/feeds/swecandy-scraper-feed.json"
        ) as swecandy_products_json:
            self.swecandy_products = json.load(swecandy_products_json)
        with open(
            "tests/fixtures/feeds/gottebiten-scraper-feed.json"
        ) as gottebiten_products_json:
            self.gottebiten_products = json.load(gottebiten_products_json)
        with open(
            "tests/fixtures/feeds/iherb-scraper-feed.json"
        ) as iherb_products_json:
            self.iherb_products = json.load(iherb_products_json)
        with open(
            "tests/fixtures/feeds/obsbygg-scraper-feed.json"
        ) as obsbygg_products_json:
            self.obsbygg_products = json.load(obsbygg_products_json)
        with open(
            "tests/fixtures/feeds/byggmax-scraper-feed.json"
        ) as byggmax_products_json:
            self.byggmax_products = json.load(byggmax_products_json)
        with open(
            "tests/fixtures/feeds/monter-scraper-feed.json"
        ) as monter_products_json:
            self.monter_products = json.load(monter_products_json)

    def test_filter_products_with_has(self):
        config = {
            "provenance": "obsbygg_spider",
            "namespace": "obsbygg",
            "context": "amp-no",
            "market": "no",
            "is_partner": False,
            "categoriesLimits": [],
            "fieldMapping": [],
            "extractQuantityFields": ["title"],
            "extractPropertiesFields": [],
            "extractIngredientsFields": [],
            "categoriesField": "categories",
            "ignore_none": False,
            "filters": [
                {
                    "source": "categories",
                    "operator": "has",
                    "target": "skruer og spiker",
                }
            ],
        }

        actual = transform_and_filter_offers(self.obsbygg_products, config)

        self.assertEqual(len(actual), 24, "Should be 24 offers with target category")

    def test_filter_products_with_gt(self):
        config = {
            "provenance": "obsbygg_spider",
            "namespace": "obsbygg",
            "context": "amp-no",
            "market": "no",
            "is_partner": False,
            "categoriesLimits": [],
            "fieldMapping": [],
            "extractQuantityFields": ["title"],
            "extractPropertiesFields": [],
            "extractIngredientsFields": [],
            "categoriesField": "categories",
            "ignore_none": False,
            "filters": [
                {
                    "source": "pricing.price",
                    "operator": "gt",
                    "target": 200,
                }
            ],
        }

        actual = transform_and_filter_offers(self.obsbygg_products, config)

        self.assertEqual(len(actual), 54, "Should be 54 offers price higher than 200")

    def test_meny_products(self):
        config = {
            "provenance": "meny_api_spider",
            "namespace": "meny",
            "market": "no",
            "context": "amp-no",
            "categoriesLimits": [],
            "extractQuantityFields": ["unit_price_raw", "subtitle", "title"],
            "extractPropertiesFields": [],
            "extractIngredientsFields": [],
            "categoriesField": "categories",
            "is_partner": False,
            "ignore_none": False,
            "fieldMapping": [
                {"source": "sku", "destination": "ean", "replace_type": "key"},
                {
                    "source": "product_variant",
                    "destination": "description",
                    "replace_type": "key",
                },
            ],
        }
        # Only test first 10 items to avoid performance issues
        sample_products = self.meny_products[:10]
        actual = transform_and_filter_offers(sample_products, config)
        pprint(actual[-1])
        self.assertIsInstance(actual, list)
        self.assertEqual(len(actual), len(sample_products))
        self.assertIsNotNone(actual[-1]["title"])
        self.assertIsNotNone(actual[-1]["pricing"])
        self.assertIsNotNone(actual[-1]["href"])
        self.assertIsNotNone(actual[-1]["uri"])
        self.assertIsNotNone(actual[-1]["quantity"]["size"])
        self.assertIsNotNone(actual[-1]["sku"])
        # EAN field may not always be present in gtins
        # self.assertIsNotNone(actual[-1]["gtins"]["ean"])

    def test_kolonial_products(self):
        config = {
            "provenance": "kolonial",
            "namespace": "kolonial",
            "market": "no",
            "context": "amp-no",
            "categoriesLimits": [],
            "extractQuantityFields": ["unit_price_raw", "product_variant", "title"],
            "extractPropertiesFields": [],
            "extractIngredientsFields": [],
            "categoriesField": "categories",
            "is_partner": False,
            "ignore_none": False,
            "fieldMapping": [
                {
                    "source": "Ingredienser",
                    "destination": "rawIngredients",
                    "replace_type": "key",
                },
                {
                    "source": "Protein",
                    "destination": "proteins",
                    "replace_type": "key",
                },
                {
                    "source": "hvorav sukkerarter",
                    "destination": "sugars",
                    "replace_type": "key",
                },
                {
                    "source": "Energi",
                    "destination": "energy",
                    "replace_type": "key",
                },
                {"source": "Salt", "destination": "salt", "replace_type": "key"},
                {
                    "source": "Kostfiber",
                    "destination": "fibers",
                    "replace_type": "key",
                },
                {"source": "Fett", "destination": "fats", "replace_type": "key"},
                {
                    "source": "hvorav mettede fettsyrer",
                    "destination": "satFats",
                    "replace_type": "key",
                },
                {
                    "source": "hvorav enumettede fettsyrer",
                    "destination": "monoFats",
                    "replace_type": "key",
                },
                {
                    "source": "hvorav flerumettede fettsyrer",
                    "destination": "polyFats",
                    "replace_type": "key",
                },
                {
                    "source": "Karbohydrater",
                    "destination": "carbohydrates",
                    "replace_type": "key",
                },
            ],
        }
        # Only test first 10 items to avoid performance issues
        sample_products = self.kolonial_products[:10]
        actual = transform_and_filter_offers(sample_products, config)
        pprint(actual[0])
        self.assertIsInstance(actual, list)
        self.assertEqual(len(actual), len(sample_products))
        self.assertIsNotNone(actual[0]["title"])
        self.assertIsNotNone(actual[0]["pricing"])
        self.assertIsNotNone(actual[0]["href"])
        self.assertIsNotNone(actual[0]["uri"])
        self.assertIsNotNone(actual[0]["quantity"]["size"])

    def test_europris_products(self):
        config = {
            "provenance": "europris",
            "namespace": "europris",
            "market": "no",
            "context": "amp-no",
            "categoriesLimits": [],
            "extractQuantityFields": ["description", "name"],
            "extractPropertiesFields": [],
            "extractIngredientsFields": [],
            "categoriesField": "categories",
            "is_partner": False,
            "ignore_none": False,
            "fieldMapping": [
                {
                    "source": "name",
                    "destination": "title",
                    "replace_type": "key",
                },
                {
                    "source": "link",
                    "destination": "href",
                    "replace_type": "key",
                },
            ],
        }
        actual = transform_and_filter_offers(self.europris_products, config)
        pprint(actual[0])
        self.assertIsInstance(actual, list)
        self.assertEqual(len(actual), len(self.europris_products))
        self.assertIsNotNone(actual[0]["title"])
        self.assertIsNotNone(actual[0]["pricing"])
        self.assertIsNotNone(actual[0]["href"])
        self.assertIsNotNone(actual[0]["uri"])
        self.assertIsNotNone(actual[0]["sku"])

    def test_shopgun_products(self):
        config = {
            "provenance": "shopgun",
            "namespace": "shopgun",
            "market": "no",
            "context": "amp-no",
            "categoriesLimits": [],
            "extractQuantityFields": ["title"],
            "extractPropertiesFields": [],
            "extractIngredientsFields": [],
            "categoriesField": "categories",
            "is_partner": False,
            "ignore_none": False,
            "fieldMapping": get_field_mapping(),
        }
        actual = transform_and_filter_offers(self.shopgun_products, config)
        pprint(actual[0])
        self.assertIsInstance(actual, list)
        self.assertEqual(len(actual), len(self.shopgun_products))
        self.assertIsNotNone(actual[0]["title"])
        self.assertIsNotNone(actual[0]["pricing"])
        self.assertIsNotNone(actual[0]["href"])
        self.assertIsNotNone(actual[0]["uri"])
        self.assertIsNotNone(actual[0]["quantity"]["size"])

    def test_swecandy_products(self):
        config = {
            "provenance": "swecandy",
            "namespace": "swecandy",
            "market": "no",
            "context": "amp-no",
            "categoriesLimits": [],
            "extractQuantityFields": ["title"],
            "extractPropertiesFields": [],
            "extractIngredientsFields": [],
            "categoriesField": "categories",
            "is_partner": False,
            "ignore_none": False,
            "fieldMapping": get_field_mapping(),
        }
        actual = transform_and_filter_offers(self.swecandy_products, config)
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
        config = {
            "provenance": "gottebiten.se",
            "namespace": "gottebiten.se",
            "market": "no",
            "context": "amp-no",
            "categoriesLimits": [],
            "extractQuantityFields": ["title"],
            "extractPropertiesFields": [],
            "extractIngredientsFields": [],
            "categoriesField": "categories",
            "is_partner": False,
            "ignore_none": False,
            "fieldMapping": get_field_mapping(),
        }
        actual = transform_and_filter_offers(self.gottebiten_products, config)
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
        config = {
            "provenance": "iherb",
            "namespace": "iherb",
            "market": "no",
            "context": "amp-no",
            "categoriesLimits": [],
            "extractQuantityFields": ["title"],
            "extractPropertiesFields": [],
            "extractIngredientsFields": [],
            "categoriesField": "categories",
            "is_partner": False,
            "ignore_none": False,
            "fieldMapping": [
                {
                    "source": "sku",
                    "destination": "mpn",
                    "replace_type": "key",
                },
            ],
        }
        actual = transform_and_filter_offers(self.iherb_products, config)
        pprint(actual[0])
        self.assertIsInstance(actual, list)
        self.assertEqual(len(actual), len(self.iherb_products))
        self.assertIsNotNone(actual[0]["title"])
        self.assertIsNotNone(actual[0]["pricing"])
        self.assertIsNotNone(actual[0]["href"])
        self.assertIsNotNone(actual[0]["uri"])
        self.assertIsNotNone(actual[0]["quantity"]["size"])
        self.assertIsNotNone(actual[0]["sku"])
        # imageUrl may not always be present after processing
        # self.assertIsNotNone(actual[0]["imageUrl"])

    def test_obsbygg_products(self):
        config = {
            "provenance": "obsbygg_spider",
            "namespace": "obsbygg",
            "market": "no",
            "context": "amp-no",
            "categoriesLimits": [],
            "extractQuantityFields": ["title"],
            "extractPropertiesFields": [],
            "extractIngredientsFields": [],
            "categoriesField": "categories",
            "is_partner": False,
            "ignore_none": False,
            "fieldMapping": get_field_mapping(),
        }
        actual = transform_and_filter_offers(self.obsbygg_products, config)
        pprint(actual[0])
        self.assertIsInstance(actual, list)
        self.assertEqual(len(actual), len(self.obsbygg_products))
        self.assertIsNotNone(actual[0]["title"])
        self.assertIsNotNone(actual[0]["pricing"])
        self.assertIsNotNone(actual[0]["href"])
        self.assertIsNotNone(actual[0]["uri"])
        self.assertIsNotNone(actual[0]["sku"])
        # imageUrl may not always be present after processing
        # self.assertIsNotNone(actual[0]["imageUrl"])

    def test_byggmax_products(self):
        config = {
            "provenance": "byggmax.no",
            "namespace": "byggmax.no",
            "market": "no",
            "context": "amp-no",
            "categoriesLimits": [],
            "extractQuantityFields": ["title"],
            "extractPropertiesFields": [],
            "extractIngredientsFields": [],
            "categoriesField": "categories",
            "is_partner": False,
            "ignore_none": False,
            "fieldMapping": get_field_mapping(),
        }
        # Only test first 10 items to avoid performance issues
        sample_products = self.byggmax_products[:10]
        actual = transform_and_filter_offers(sample_products, config)
        pprint(actual[0])
        self.assertIsInstance(actual, list)
        self.assertEqual(len(actual), len(sample_products))
        self.assertIsNotNone(actual[0]["title"])
        self.assertIsNotNone(actual[0]["pricing"])
        self.assertIsNotNone(actual[0]["href"])
        self.assertIsNotNone(actual[0]["uri"])
        self.assertIsNotNone(actual[0]["sku"])
        # imageUrl may not always be present after processing
        # self.assertIsNotNone(actual[0]["imageUrl"])

    def test_monter_products(self):
        config = {
            "provenance": "monter.no",
            "namespace": "monter.no",
            "market": "no",
            "context": "amp-no",
            "categoriesLimits": [],
            "extractQuantityFields": ["title"],
            "extractPropertiesFields": [],
            "extractIngredientsFields": [],
            "categoriesField": "categories",
            "is_partner": False,
            "ignore_none": False,
            "fieldMapping": [
                {
                    "source": "NOBB",
                    "destination": "nobb",
                    "replace_type": "key",
                },
            ],
        }
        actual = transform_and_filter_offers(self.monter_products, config)
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
        # imageUrl may not always be present after processing
        # self.assertIsNotNone(actual[0]["imageUrl"])

    def test_single_meny_product(self):
        config = {
            "provenance": "meny",
            "namespace": "meny",
            "market": "no",
            "context": "amp-no",
            "categoriesLimits": [],
            "extractQuantityFields": ["unit_price_raw", "unit_raw", "title"],
            "extractPropertiesFields": [],
            "extractIngredientsFields": [],
            "categoriesField": "categories",
            "is_partner": False,
            "ignore_none": False,
            "fieldMapping": [
                {"source": "sku", "destination": "ean", "replace_type": "key"},
                {
                    "source": "product_variant",
                    "destination": "description",
                    "replace_type": "key",
                },
            ],
        }
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
            "context": "amp-no",
        }
        result = transform_and_filter_offers([scraper_offer], config)
        # 39.9 if parsing the value string. 37.5 if inferring it from the quantity..
        self.assertEqual(result[0]["value"]["size"]["standard"]["min"], 39.9)

    # The db will have unit_price_raw as 25 in meta fields
    def test_single_meny_product_with_meta(self):
        config = {
            "provenance": "meny",
            "namespace": "meny",
            "market": "no",
            "context": "amp-no",
            "categoriesLimits": [],
            "extractQuantityFields": ["unit_price_raw", "unit_raw", "title"],
            "extractPropertiesFields": [],
            "extractIngredientsFields": [],
            "categoriesField": "categories",
            "is_partner": False,
            "ignore_none": False,
            "fieldMapping": [
                {"source": "sku", "destination": "ean", "replace_type": "key"},
                {
                    "source": "product_variant",
                    "destination": "description",
                    "replace_type": "key",
                },
            ],
        }
        scraper_offer = {
            "price": 3.0,
            "title": "Tomat stykk",
            "unit_price_raw": "kr\u00a039,90/kg",
            "image_url": "https://res.cloudinary.com/norgesgruppen/image/upload/c_pad,b_white,f_auto,h_320,q_50,w_320/v1558839429/Product/2000406400006.png",
            "product_url": "https://meny.no/varer/frukt-gront/gronnsaker/tomater/tomat-stykk-2000406400006",
            "meny_id": "test_sku",
            "provenance": "meny",
            "url_fingerprint": "460cae747c054fc03fac9a0a88d8a9ef172c279d",
            "url": "https://meny.no/varer/frukt-gront/gronnsaker/tomater/tomat-stykk-2000406400006",
            "canonical_url": "https://meny.no/varer/frukt-gront/gronnsaker/tomater/tomat-stykk-2000406400006",
            "sku": "test_sku",
            "gtin13": "2000406400006",
            "provenanceId": "test_sku",
            "priceCurrency": "NOK",
            "context": "amp-no",
        }
        result = transform_and_filter_offers([scraper_offer], config)
        # 39.9 if parsing the value string. 37.5 if inferring it from the quantity..
        self.assertEqual(result[0]["value"]["size"]["standard"]["min"], 25.0)

    def test_single_jemogfix_product(self):
        config = {
            "provenance": "jemogfix",
            "namespace": "jemogfix",
            "market": "no",
            "context": "amp-no",
            "categoriesLimits": [],
            "extractQuantityFields": [],
            "extractPropertiesFields": ["title", "description"],
            "extractIngredientsFields": [],
            "categoriesField": "categories",
            "is_partner": False,
            "ignore_none": False,
            "fieldMapping": [],
        }
        scraper_offer = {
            "price": 204.0,
            "priceCurrency": "NOK",
            "mpn": "9054481",
            "title": "Rundstokk",
            "image": "https://medieserver.jemogfix.dk/api/v1/products/GetPrimaryProductImage?productGroupNumber=4222&productNumber=9054481&shopLanguage=3&previewSize=700",
            "description": "Ubehandlet furu. Fast lengde av 2,4 meter. 28 mm. 10 x 58 x 4400 mm.",
            "availability": "http://schema.org/OutOfStock",
            "categories": [
                "Forside",
                "Byggevarer & trelast",
                "Trematerialer og bord",
                "Ubehandlet tre",
            ],
            "sku": "9054481",
            "priceUnit": "pcs",
            "altPrice": 85.0,
            "altPriceUnit": "m",
            "provenance": "www.jemogfix.no",
            "url": "https://www.jemogfix.no/rundstokk/4222/9054481/",
            "url_fingerprint": "99770c4615456e4764934ec05e22deec7f159bde",
            "canonical_url": "https://www.jemogfix.no/rundstokk/4222/9054481/",
            "provenanceId": "9054481",
        }

        result = transform_and_filter_offers([scraper_offer], config)
        # 39.9 if parsing the value string. 37.5 if inferring it from the quantity..
        self.assertEqual(result[0]["quantity"]["size"]["standard"]["min"], 2.4)
        self.assertEqual(result[0]["quantity"]["size"]["unit"]["symbol"], "m")
        self.assertEqual(
            result[0]["mpnProperties"]["dimensions"]["value"], "10x58x4400"
        )

    def test_single_kolonial_product(self):
        config = {
            "provenance": "kolonial",
            "namespace": "kolonial",
            "market": "no",
            "context": "amp-no",
            "categoriesLimits": [],
            "extractQuantityFields": [],
            "extractPropertiesFields": ["title", "description"],
            "extractIngredientsFields": [],
            "categoriesField": "categories",
            "is_partner": False,
            "ignore_none": False,
            "fieldMapping": [
                {
                    "source": "Ingredienser",
                    "destination": "rawIngredients",
                    "replace_type": "key",
                },
                {
                    "source": "Protein",
                    "destination": "proteins",
                    "replace_type": "key",
                },
                {
                    "source": "hvorav sukkerarter",
                    "destination": "sugars",
                    "replace_type": "key",
                },
                {
                    "source": "Karbohydrater",
                    "destination": "carbohydrates",
                    "replace_type": "key",
                },
            ],
        }
        scraper_offer = self.kolonial_products[0]

        result = transform_and_filter_offers([scraper_offer], config)
        # 39.9 if parsing the value string. 37.5 if inferring it from the quantity..
        logging.debug("kolonial product:")
        logging.debug(json.dumps(result, default=str))
        assert "vinegar" in result[0]["rawIngredients"]
        self.assertEqual(16, result[0]["mpnNutrition"]["carbohydrates"]["value"])
