from unittest import TestCase

from scraper_feed.affiliate_links import add_se_amazon_affiliate_link
from scraper_feed.filters import get_affiliate_link_from_href


class TestAffiliateLinks(TestCase):
    def test_add_se_amazon_affiliate_link(self):
        actual = add_se_amazon_affiliate_link({"href": "https://amazon.se/dp/kjsdfkjsd"})
        self.assertEqual(actual["href"], "https://amazon.se/dp/kjsdfkjsd")
        self.assertEqual(actual["ahref"], "https://amazon.se/dp/kjsdfkjsd?tag=mpn00e-21")

    def test_get_affiliate_link_from_href(self):
        actual = get_affiliate_link_from_href("https://amazon.se/dp/kjsdfkjsd")
        assert actual == "https://amazon.se/dp/kjsdfkjsd?tag=mpn00e-21"

    def test_get_affiliate_link_from_href_empty(self):
        actual = get_affiliate_link_from_href("")
        assert actual is None

    def test_get_affiliate_link_from_href_not_affiliate_domain(self):
        actual = get_affiliate_link_from_href("https://slkdjfkls.com/kdfk")
        assert actual is None
