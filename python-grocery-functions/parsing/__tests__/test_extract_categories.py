from unittest import TestCase

from parsing.category_extraction import extract_categories


class TestExtractCategories(TestCase):
    def test_extract_categories_with_none(self):
        actual = extract_categories({"categories": [], "dealer": "kolonial"}, {})
        actual = extract_categories({"categories": None, "dealer": "kolonial"}, {})
        actual = extract_categories({"dealer": "kolonial"}, {})

    def test_extract_categories(self):
        actual = extract_categories(
            {"categories": ["Fiskepålegg og reker i lake"], "dealer": "kolonial"}, {}
        )
        self.assertEqual(actual[-1]["key"], "fiskepalegg_1")
        self.assertEqual(actual[0]["key"], "palegg-frokost_0")

    def test_extract_categories_with_2_as_key(self):
        actual = extract_categories(
            {"categories": ["Hundemat", "Snacks"], "dealer": "kolonial"}, {}
        )
        self.assertEqual(actual[-1]["key"], "hundemat_1")
        self.assertEqual(actual[0]["key"], "dyr_0")

    def test_extract_categories_with_coop(self):
        actual = extract_categories(
            {"categories": ["Engangsgrill"], "dealer": "coop"}, {}
        )
        self.assertEqual(actual[-1]["key"], "engangsgrill_2")
        self.assertEqual(actual[0]["key"], "hus-hjem_0")

    def test_extract_categories_with_meny(self):
        actual = extract_categories(
            {
                "slugCategories": [
                    "hus-hjem",
                    "borddekning",
                    "engangservice",
                    "cocktailpinner",
                ],
                "dealer": "meny",
            },
            {"categoriesField": "slugCategories"},
        )
        self.assertEqual(actual[-1]["key"], "cocktailpinner_3")
        self.assertEqual(actual[-2]["key"], "engangservice_2")
        self.assertEqual(actual[0]["key"], "hus-hjem_0")

    def test_extract_categories_with_meny_2(self):
        actual = extract_categories(
            {
                "slugCategories": ["frukt-gront", "frukt", "avocado"],
                "dealer": "meny",
            },
            {"categoriesField": "slugCategories"},
        )
        self.assertEqual(actual[2]["key"], "avocado_2")
        self.assertEqual(actual[1]["key"], "frukt_1")
        self.assertEqual(actual[0]["key"], "frukt-gront_0")
