import json
from pathlib import Path
from unittest import TestCase

from scraper_feed.filters import get_categories, transform_product
from scraper_feed.scraper_configs import get_field_mapping


class TestHandleProducts(TestCase):
    def setUp(self):
        fixtures_path = Path(__file__).parent.parent.parent / "fixtures" / "feeds"
        with open(fixtures_path / "obsbygg-scraper-feed.json") as obsbygg_products_json:
            self.obsbygg_products = json.load(obsbygg_products_json)
        with open(
            fixtures_path / "swecandy-scraper-feed.json"
        ) as swecandy_products_json:
            self.swecandy_products = json.load(swecandy_products_json)
        with open(
            fixtures_path / "shopgun-scraper-feed-new.json"
        ) as shopgun_products_json:
            self.shopgun_products = json.load(shopgun_products_json)

    def test_transform_product(self):
        product = self.obsbygg_products[0]
        config = {
            "provenance": "obsbygg_spider",
            "namespace": "obsbygg",
            "market": "no",
            "fieldMapping": get_field_mapping(),
            "categoriesLimits": [],
            "extractQuantityFields": ["title"],
            "extractPropertiesFields": [],
            "extractIngredientsFields": [],
            "categoriesField": "categories",
            "is_partner": False,
            "ignore_none": False,
            "context": "amp-no",
        }

        actual = transform_product(product, config)
        self.assertIsNotNone(actual["imageUrl"])
        self.assertIsNotNone(actual["dealer"])

        product = self.swecandy_products[0]
        config = {
            "provenance": "swecandy.se",
            "namespace": "swecandy",
            "market": "no",
            "fieldMapping": get_field_mapping(),
            "categoriesLimits": [],
            "extractQuantityFields": ["title"],
            "extractPropertiesFields": [],
            "extractIngredientsFields": [],
            "categoriesField": "categories",
            "is_partner": False,
            "ignore_none": False,
            "context": "amp-no",
        }

        actual = transform_product(product, config)
        self.assertIsNotNone(actual["imageUrl"])
        self.assertIsNotNone(actual["dealer"])

    def test_transform_product_with_namespace(self):
        product = self.obsbygg_products[0]
        config = {
            "provenance": "obsbygg_spider",
            "namespace": "HALLA",
            "market": "no",
            "fieldMapping": get_field_mapping(),
            "categoriesLimits": [],
            "extractQuantityFields": ["title"],
            "extractPropertiesFields": [],
            "extractIngredientsFields": [],
            "categoriesField": "categories",
            "is_partner": False,
            "ignore_none": False,
            "context": "amp-no",
        }

        actual = transform_product(product, config)
        self.assertIn("HALLA", actual["uri"])

    def test_transform_product_with_ignore_none_fields(self):
        product = self.obsbygg_products[0]
        config = {
            "provenance": "obsbygg_spider",
            "namespace": "obsbygg",
            "market": "no",
            "fieldMapping": get_field_mapping(),
            "categoriesLimits": [],
            "extractQuantityFields": [],
            "extractPropertiesFields": [],
            "extractIngredientsFields": [],
            "categoriesField": "categories",
            "is_partner": False,
            "ignore_none": True,
            "context": "amp-no",
        }

        actual = transform_product(product, config)
        self.assertIsNone(actual.get("quantity"))
        self.assertIn("obsbygg", actual["uri"])

    def test_transform_product_shopgun(self):
        config = {
            "provenance": "shopgun",
            "namespace": "shopgun",
            "market": "no",
            "fieldMapping": get_field_mapping(),
            "categoriesLimits": [],
            "extractQuantityFields": [],
            "extractPropertiesFields": [],
            "extractIngredientsFields": [],
            "categoriesField": "categories",
            "is_partner": False,
            "ignore_none": True,
            "context": "amp-no",
        }

        actual = list(
            [
                transform_product(product, config)
                for product in self.shopgun_products[:100]
            ]
        )
        self.assertIsNotNone(actual[0].get("validThrough"))
        self.assertIn("shopgun", actual[0]["uri"])

    def test_transform_product_parfymklick(self):
        config = {
            "provenance": "parfymklick_se_spider",
            "namespace": "parfymklick",
            "market": "se",
            "fieldMapping": get_field_mapping(),
            "categoriesLimits": [],
            "extractQuantityFields": [],
            "extractPropertiesFields": [],
            "extractIngredientsFields": [],
            "categoriesField": "categories",
            "is_partner": False,
            "ignore_none": True,
            "context": "beauty-se",
        }

        actual = transform_product(
            {
                "price": 870.0,
                "priceCurrency": "SEK",
                "sku": "51871",
                "brand": "/Aftershave/Yves-Saint-Laurent/",
                "title": "Yves Saint Laurent Y Eau de Toilette 60ml Sprej",
                "url": "https://www.parfym-klick.se/Yves-Saint-Laurent-Y-Eau-de-Toilette-60ml-Sprej-s51871/",
                "image": "https://299df094394db9cc1de4-60c51f90a91f2305b52a889e5c1d7548.ssl.cf3.rackcdn.com/110746_xl_7.jpg",
                "description": "Yves Saint Laurent Y Eau de Toilette 60ml Sprej Y for Men av Yves Saint Laurent är en träig och aromatisk doft för män. Sammansättningen av Eau de Toilette börjar med rena noter av vita aldehyder, ingefära och bergamott som utvecklas med geranium, violetta blad och salvia i hjärtat med stöd av en maskulär bas av gran balsam, rökelse, ambergris, mysk och cederträ. Eau de Parfum delar dessa noter berikade med äpple i öppningen, enbär i hjärtat och olibanum i basen. Båda versionerna finns i en minimalistisk linjär flaska med en metallaccent som bara verkar ha märkesnamnet när du ser framsidan av flaskan, men om du vänder det visar det sig vara basen i bokstaven Y. Y skapades för att ge den generation som föddes på 80- och 90-talet en säker och mångsidig doft till skillnad från någon annan. EDT-versionen av Y for Men lanserades 2017 följt av en EDP 2018.",
                "availability": "http://schema.org/InStock",
                "itemCondition": "http://schema.org/NewCondition",
                "categories": [
                    "Parfym Klick",
                    "Dofter",
                    "För Honom",
                    "Yves Saint Laurent",
                    "Y",
                ],
                "canonical_url": "https://www.parfym-klick.se/Yves-Saint-Laurent-Y-Eau-de-Toilette-60ml-Sprej-s51871/",
                "provenance": "parfyme_klikk_se_spider",
                "url_fingerprint": "ec66ee66d93af84db49cdee0f95ee33bc89053e3",
                "provenanceId": "51871",
            },
            config,
        )
        self.assertIsNotNone(actual.get("validThrough"))
        self.assertEqual(870.0, actual["pricing"]["price"])


class TestGetCategories(TestCase):
    def test_get_categories_remove_first(self):
        categories = ["Hjem", "Grønnsaker", "Bananer"]
        categories_limits = [1, None]

        actual = get_categories(categories, categories_limits)
        self.assertListEqual(actual, categories[1:])

    def test_get_categories_remove_first_array_length_1(self):
        categories = ["Hjem", "Grønnsaker", "Bananer"]
        categories_limits = [1]

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
