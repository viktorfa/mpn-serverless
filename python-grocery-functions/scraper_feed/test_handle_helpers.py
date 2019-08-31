from unittest import TestCase

from scraper_feed.handle_products import get_shopgun_quantity, get_provenance_id


class TestHelpers(TestCase):
    def test_get_shopgun_quantity_simple(self):
        shopgun_quantity = dict(
            unit=None,
            size={"from": 1, "to": 1},
            pieces={"from": 1, "to": 1},
        )
        actual = get_shopgun_quantity(shopgun_quantity)

    def test_get_provenance_id(self):
        self.assertEqual(get_provenance_id({"sku": "123"}), "123")
        self.assertEqual(
            get_provenance_id({"url": "https://hei.com/123"}),
            "123"
        )
        self.assertEqual(
            get_provenance_id({"sku": "321", "url": "https://hei.com/123"}),
            "321"
        )

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
