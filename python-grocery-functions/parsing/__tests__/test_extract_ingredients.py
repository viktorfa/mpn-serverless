from parsing.ingredients_extraction import extract_e_number, extract_ingredients
from unittest import TestCase


class TestExtractIngredients(TestCase):
    def test_extract_e_number(self):
        self.assertEqual(extract_e_number("E450"), "E450")
        self.assertEqual(extract_e_number("E450b"), "E450b")
        self.assertEqual(extract_e_number("Sirup E450b"), "E450b")
        self.assertEqual(extract_e_number("Sirup E 450 b"), "E450b")
        self.assertEqual(extract_e_number("Sirup E 450 Kake"), "E450")

    def test_with_kolonial_offer(self):
        offer = {
            "additionalProperties": [
                {
                    "value": "Vann, 20 % fruktjuice fra konsentrat (12 % druejuice, 8 % eplejuice), sukker, karbondioksid, syre (sitronsyre), aroma, konserveringsmiddel (natriumbenzoat, kaliumsorbat), farge (karamell E150b), antioksidant (askorbinsyre)",
                    "key": "Ingredienser",
                    "type": None,
                },
            ],
        }
        config = {
            "extractIngredientsFields": ["Ingredienser"],
        }

        actual = extract_ingredients(offer, config)
        self.assertEqual(actual["sugar"]["key"], "sugar")

    def test_with_partially_duplicate_names(self):
        offer = {
            "additionalProperties": [
                {
                    "value": "Vann, stivelse, modifisert stivelse, kokosolje 17%, havsalt, risprotein, aroma, olivenekstrakt, fargestoff: betakaroten e160a.",
                    "key": "Ingredienser",
                    "type": None,
                },
            ],
        }
        config = {
            "extractIngredientsFields": ["Ingredienser"],
        }

        actual = extract_ingredients(offer, config)
        self.assertEqual(actual["seaSalt"]["key"], "seaSalt")
        self.assertEqual(actual["e160a"]["key"], "e160a")
        self.assertEqual(actual["modifiedStarch"]["key"], "modifiedStarch")
        self.assertEqual(actual["starch"]["key"], "starch")
        self.assertNotIn("salt", actual.keys())
