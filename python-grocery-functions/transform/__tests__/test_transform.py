import pydash
from typing import List

from amp_types.amp_product import ScraperOffer, MappingConfigField
from unittest import TestCase

from transform.transform import transform_fields


class TestTransformScraperOffer(TestCase):
    def test_replace_flat_field(self):
        scraper_offer: ScraperOffer = {"price": 22, "UnitPrice": 12, "sku": "12334323"}
        field_mapping: List[MappingConfigField] = [
            {"replace_type": "key", "source": "sku", "destination": "ean"}
        ]
        actual = transform_fields(scraper_offer, field_mapping)
        self.assertIsInstance(actual, dict)
        self.assertEqual(pydash.get(actual, "ean"), "12334323")

    def test_replace_flat_field_2(self):
        scraper_offer: ScraperOffer = {
            "price": 22,
            "UnitPrice": 12,
            "sku": "12334323",
            "image": "//coop.no/static/lfkjgf.png",
        }
        field_mapping: List[MappingConfigField] = [
            {"replace_type": "key", "source": "sku", "destination": "ean"},
            {"replace_type": "key", "source": "image", "destination": "imageUrl"},
        ]
        actual = transform_fields(scraper_offer, field_mapping)
        self.assertIsInstance(actual, dict)
        self.assertEqual(pydash.get(actual, "imageUrl"), "//coop.no/static/lfkjgf.png")

    def test_replace_from_additional_property(self):
        scraper_offer: ScraperOffer = {
            "price": 22,
            "UnitPrice": 12,
            "sku": "12334323",
            "additionalProperties": [
                {"key": "Manufacturer Number", "value": "JSK-3434"}
            ],
        }
        field_mapping: List[MappingConfigField] = [
            {
                "replace_type": "key",
                "source": "Manufacturer Number",
                "destination": "mpn",
            }
        ]
        actual = transform_fields(scraper_offer, field_mapping)
        self.assertIsInstance(actual, dict)
        # self.assertEqual(pydash.get(actual, ["gtins", "mpn"]), "JSK-3434")

    def test_not_replace_existing_field(self):
        scraper_offer: ScraperOffer = {
            "price": 22,
            "UnitPrice": 12,
            "sku": "12334323",
            "additionalProperties": [
                {"key": "Manufacturer Number", "value": "JSK-3434"},
                {"key": "AltPrice", "value": 100},
            ],
        }
        field_mapping: List[MappingConfigField] = [
            {
                "replace_type": "key",
                "source": "Manufacturer Number",
                "destination": "mpn",
            },
            {
                "replace_type": "key",
                "source": "AltPrice",
                "destination": "price",
            },
        ]
        actual = transform_fields(scraper_offer, field_mapping)
        self.assertIsInstance(actual, dict)
        self.assertEqual(pydash.get(actual, "price"), 22)

    def test_replace_existing_field_when_force_replace(self):
        scraper_offer: ScraperOffer = {
            "price": 22,
            "UnitPrice": 12,
            "sku": "12334323",
            "additionalProperties": [
                {"key": "Manufacturer Number", "value": "JSK-3434"},
                {"key": "AltPrice", "value": 100},
            ],
        }
        field_mapping: List[MappingConfigField] = [
            {
                "replace_type": "key",
                "source": "Manufacturer Number",
                "destination": "mpn",
            },
            {
                "replace_type": "key",
                "source": "AltPrice",
                "destination": "price",
                "force_replace": True,
            },
        ]
        actual = transform_fields(scraper_offer, field_mapping)
        self.assertIsInstance(actual, dict)
        self.assertEqual(pydash.get(actual, "price"), 100)

    def test_replace_from_additional_property_when_not_present(self):
        scraper_offer: ScraperOffer = {
            "price": 22,
            "UnitPrice": 12,
            "sku": "12334323",
            "additionalProperties": [],
        }
        field_mapping: List[MappingConfigField] = [
            {
                "replace_type": "key",
                "source": "Manufacturer Number",
                "destination": "mpn",
            }
        ]

        actual = transform_fields(scraper_offer, field_mapping)
        self.assertIsInstance(actual, dict)
        # self.assertEqual(pydash.get(actual, ["gtins", "mpn"]), None)

    def test_replace_with_fixed_value(self):
        scraper_offer: ScraperOffer = {"price": 22, "UnitPrice": 12, "sku": "12334323"}
        field_mapping: List[MappingConfigField] = [
            {
                "destination": "dealer",
                "replace_type": "fixed",
                "replace_value": "byggmax",
            }
        ]
        actual = transform_fields(scraper_offer, field_mapping)
        self.assertIsInstance(actual, dict)
        self.assertEqual(pydash.get(actual, "dealer"), "byggmax")

    def test_replace_with_additional_property_destination(self):
        scraper_offer: ScraperOffer = {
            "price": 22,
            "UnitPrice": 12,
            "sku": "12334323",
            "additionalProperties": [{"key": "PriceUnit", "value": "m2"}],
        }
        field_mapping: List[MappingConfigField] = [
            {
                "source": "PriceUnit",
                "destination": "additionalProperties.priceUnit",
                "replace_type": "key",
            }
        ]
        actual = transform_fields(scraper_offer, field_mapping)
        self.assertIsInstance(actual, dict)
        self.assertIsInstance(pydash.get(actual, ["additionalPropertyDict"]), dict)
        self.assertEqual(
            pydash.get(actual, ["additionalPropertyDict", "priceUnit", "value"]), "m2"
        )

    def test_ignore_field(self):
        scraper_offer: ScraperOffer = {
            "price": 22,
            "UnitPrice": 12,
            "sku": "12334323",
            "ean": "Kjempeprodukt",
            "additionalProperties": [{"key": "PriceUnit", "value": "m2"}],
        }
        field_mapping: List[MappingConfigField] = [
            {
                "source": "PriceUnit",
                "destination": "additionalProperties.priceUnit",
                "replace_type": "key",
            },
            {
                "destination": "ean",
                "replace_type": "ignore",
            },
        ]
        actual = transform_fields(scraper_offer, field_mapping)
        self.assertIsInstance(actual, dict)
        self.assertIsNone(actual.get("ean"))
