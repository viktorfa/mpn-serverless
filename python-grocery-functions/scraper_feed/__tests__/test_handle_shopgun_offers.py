from unittest import TestCase
from datetime import datetime
import pydash

from scraper_feed.handle_shopgun_offers import transform_shopgun_product


class TestHandleShopgunOffers(TestCase):
    def test_basic_with_default_config(self):
        shopgun_product = {
            "id": "f0f6fvLw",
            "ern": "ern:offer:f0f6fvLw",
            "heading": "Italiensk pizza",
            "description": "pepperoni/mozzarella, 365g, Folkets. 27,40/kg.",
            "catalog_page": 1,
            "pricing": {"price": 10, "pre_price": None, "currency": "NOK"},
            "quantity": {
                "unit": {"symbol": "g", "si": {"symbol": "kg", "factor": 0.001}},
                "size": {"from": 365, "to": 365},
                "pieces": {"from": 1, "to": 1},
            },
            "images": {
                "view": "https://d3ikkoqs9ddhdl.cloudfront.net/img/offer/crop/view/f0f6fvLw.jpg?m=pl2kfx",
                "zoom": "https://d3ikkoqs9ddhdl.cloudfront.net/img/offer/crop/zoom/f0f6fvLw.jpg?m=pl2kfx",
                "thumb": "https://d3ikkoqs9ddhdl.cloudfront.net/img/offer/crop/thumb/f0f6fvLw.png?m=pl2kfx",
            },
            "links": {"webshop": None},
            "run_from": "2019-01-13T23:00:00+0000",
            "run_till": "2019-01-20T22:59:59+0000",
            "dealer_url": "https://api.etilbudsavis.dk/v2/dealers/c062vm",
            "store_url": None,
            "catalog_url": "https://api.etilbudsavis.dk/v2/catalogs/784dsZx",
            "dealer_id": "c062vm",
            "store_id": None,
            "catalog_id": "784dsZx",
            "category_ids": [],
            "branding": {
                "name": "SPAR",
                "website": "http://spar.no",
                "description": "Velkommen til SPAR!",
                "logo": "https://d3ikkoqs9ddhdl.cloudfront.net/img/logo/default/00ibuk8530h13udw.png",
                "color": "D62631",
                "pageflip": {
                    "logo": "https://d3ikkoqs9ddhdl.cloudfront.net/img/logo/pageflip/00ibuk85a430w3f7.png",
                    "color": "D62631",
                },
            },
        }

        actual = transform_shopgun_product(
            shopgun_product, {"provenance": "shopgun_grocery"}
        )
        self.assertEqual(actual["title"], shopgun_product["heading"])
        self.assertEqual(
            pydash.get(actual, ["quantity", "size", "amount", "min"]), 365,
        )
        self.assertEqual(
            pydash.get(actual, ["quantity", "size", "unit", "symbol"]), "g",
        )
        self.assertEqual(
            actual["validThrough"], datetime.fromisoformat("2019-01-20T22:59:59")
        )
