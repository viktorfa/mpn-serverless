from unittest import TestCase

from scraper_feed.affiliate_links import (
    add_affiliate_links,
    add_se_amazon_affiliate_link,
)


class TestAffiliateLinks(TestCase):
    def test_add_se_amazon_affiliate_link(self):
        actual = add_se_amazon_affiliate_link(
            {"href": "https://amazon.se/dp/kjsdfkjsd"}
        )
        self.assertEqual(actual["href"], "https://amazon.se/dp/kjsdfkjsd")
        self.assertEqual(
            actual["ahref"], "https://amazon.se/dp/kjsdfkjsd?tag=mpn00e-21"
        )

    def test_add_affiliate_link_to_product(self):
        actual = list(add_affiliate_links([{"href": "https://amazon.se/dp/kjsdfkjsd"}]))
        self.assertEqual(actual[0]["href"], "https://amazon.se/dp/kjsdfkjsd")
        self.assertEqual(
            actual[0]["ahref"], "https://amazon.se/dp/kjsdfkjsd?tag=mpn00e-21"
        )
