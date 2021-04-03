from unittest import TestCase, mock

from scraper_feed import handle_config
from scraper_feed.affiliate_links import add_se_amazon_affiliate_link
from util.errors import NoHandleConfigError


class TestAffiliateLinks(TestCase):
    def test_add_se_amazon_affiliate_link(self):
        actual = add_se_amazon_affiliate_link(
            {"href": "https://amazon.se/dp/kjsdfkjsd"}
        )
        self.assertEqual(actual["href"], "https://amazon.se/dp/kjsdfkjsd")
        self.assertEqual(
            actual["ahref"], "https://amazon.se/dp/kjsdfkjsd?tag=mpn00e-21"
        )
