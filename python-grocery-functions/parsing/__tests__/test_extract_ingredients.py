from parsing.ingredients_extraction import (
    extract_e_number,
    get_ingredients_data,
    extract_individual_ingredients,
    get_extracted_ingredients,
)
from unittest import TestCase


class TestExtractIngredientsMethods(TestCase):
    def test_extract_e_number(self):
        self.assertEqual(extract_e_number("E450"), "E450")
        self.assertEqual(extract_e_number("E450b"), "E450b")
        self.assertEqual(extract_e_number("Sirup E450b"), "E450b")
        self.assertEqual(extract_e_number("Sirup E 450 b"), "E450b")
        self.assertEqual(extract_e_number("Sirup E 450 Kake"), "E450")
        self.assertEqual(extract_e_number("Sirup e 450 Kake"), "e450")
        self.assertEqual(extract_e_number("e450"), "e450")

    def test_extract_individual_ingredients(self):
        ingredients = "Vann, 20 % fruktjuice fra konsentrat (12 % druejuice, 8 % eplejuice), sukker, karbondioksid, syre (sitronsyre), aroma, konserveringsmiddel (natriumbenzoat, kaliumsorbat), farge (karamell E150b), antioksidant (askorbinsyre)"
        actual = extract_individual_ingredients(ingredients)
        self.assertGreater(len(actual), 0)
        self.assertIn("Vann", actual)

    def test_get_extracted_ingredients(self):
        ingredients = ["Vann", "Sukker", "e212", "natriumbenzoat"]
        actual = get_extracted_ingredients(ingredients)
        self.assertGreater(len(actual.keys()), 0)
        self.assertEqual(actual["e212"]["key"], "e212")
        self.assertEqual(actual["sugar"]["key"], "sugar")


class TestExtractIngredientsFromOffer(TestCase):
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

        actual = get_ingredients_data(offer, config)
        self.assertEqual(actual["ingredients"]["sugar"]["key"], "sugar")
        self.assertIsNotNone(actual["processedScore"])

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

        actual = get_ingredients_data(offer, config)
        self.assertEqual(actual["ingredients"]["seaSalt"]["key"], "seaSalt")
        self.assertEqual(actual["ingredients"]["e160a"]["key"], "e160a")
        self.assertEqual(
            actual["ingredients"]["modifiedStarch"]["key"], "modifiedStarch"
        )
        self.assertEqual(actual["ingredients"]["starch"]["key"], "starch")
        self.assertNotIn("salt", actual["ingredients"].keys())
        self.assertIsNotNone(actual["processedScore"])
        self.assertGreater(actual["processedScore"], 0)
