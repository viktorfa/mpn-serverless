import logging
from unittest import TestCase
from offer_feed.__tests__.assets import offers_with_products
from offer_feed.process_offers import process_offers


logging.basicConfig(level=logging.DEBUG)


class TestProcessOffers(TestCase):
    def test_basic(self):
        config = {
            "collection_name": "byggoffers",
            "product_collection": "byggproducts",
            "relation_collection": "bygg_producthasoffer",
        }
        actual = process_offers(offers_with_products, config)
        self.assertIsInstance(actual, dict)
