from unittest import TestCase

from parsing.ingredients_extraction import (
    extract_e_number,
    extract_individual_ingredients,
)


class TestExtractIngredientsSimpleMethods(TestCase):
    def test_extract_e_number(self):
        self.assertEqual(extract_e_number("E450"), "e450")
        self.assertEqual(extract_e_number("E450b"), "e450b")
        self.assertEqual(extract_e_number("Sirup E450b"), "e450b")
        self.assertEqual(extract_e_number("Sirup E 450 b"), "e450b")
        self.assertEqual(extract_e_number("Sirup E 450 Kake"), "e450")
        self.assertEqual(extract_e_number("Sirup e 450 Kake"), "e450")
        self.assertEqual(extract_e_number("e450"), "e450")
        self.assertEqual(extract_e_number("farge (karamell E150b)"), "e150b")

    def test_extract_individual_ingredients(self):
        ingredients = "Vann, 20 % fruktjuice fra konsentrat (12 % druejuice, 8 % eplejuice), sukker, karbondioksid, syre (sitronsyre), aroma, konserveringsmiddel (natriumbenzoat, kaliumsorbat), farge (karamell E150b), antioksidant (askorbinsyre)"
        actual = extract_individual_ingredients(ingredients)
        self.assertGreater(len(actual), 0)
        self.assertIn("Vann", actual)
