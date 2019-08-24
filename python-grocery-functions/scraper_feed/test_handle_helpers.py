from unittest import TestCase

from scraper_feed.handle_products import get_shopgun_quantity


class TestHelpers(TestCase):
    def test_get_shopgun_quantity_simple(self):
        shopgun_quantity = dict(
            unit=None,
            size={"from": 1, "to": 1},
            pieces={"from": 1, "to": 1},
        )
        actual = get_shopgun_quantity(shopgun_quantity)

    def test_get_shopgun_quantity_size(self):
        shopgun_quantity = {
            "unit": {
                "symbol": "l",
                "si": {
                    "symbol": "l",
                    "factor": 1
                }
            },
            "size": {
                "from": 3,
                "to": 3
            },
            "pieces": {
                "from": 1,
                "to": 1
            }
        }
        actual = get_shopgun_quantity(shopgun_quantity)
