import os
import json
from config.mongo import get_collection

from parsing.ingredients_extraction import (
    extract_e_number,
    get_ingredients_data,
    extract_individual_ingredients,
    get_extracted_ingredients,
    sort_db_ingredient_key,
)
from unittest import TestCase


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
        ingredients = "Vann, 20 % fruktjuice fra konsentrat (12 % druejuice, 8 % eplejuice), sukker, karbondioksid, syre (sitronsyre), aroma, konserveringsmiddel (natriumbenzoat, kaliumsorbat), farge (karamell E150b), antioksidant (askorbinsyre)"
        actual = extract_individual_ingredients(ingredients)
        self.assertGreater(len(actual), 0)
        self.assertIn("Vann", actual)


class TestExtractIngredientsMethods(TestCase):
    @classmethod
    def setUpClass(self):
        self.ingredients_data = {}
        ingredients_collection = get_collection("ingredients")
        db_ingredients = ingredients_collection.find({})

        for ingredient in sorted(db_ingredients, key=sort_db_ingredient_key):
            self.ingredients_data[ingredient["key"]] = ingredient

    def test_get_extracted_ingredients(self):
        ingredients = ["Vann", "Sukker", "e212", "natriumbenzoat"]
        actual = get_extracted_ingredients(ingredients, self.ingredients_data)
        self.assertGreater(len(actual.keys()), 0)
        self.assertEqual(actual["e212"]["key"], "e212")
        self.assertEqual(actual["sugar"]["key"], "sugar")


class TestExtractIngredientsFromOffer(TestCase):
    @classmethod
    def setUpClass(self):
        self.ingredients_data = {}
        ingredients_collection = get_collection("ingredients")
        db_ingredients = ingredients_collection.find({})

        for ingredient in db_ingredients:
            self.ingredients_data[ingredient["key"]] = ingredient

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

        actual = get_ingredients_data(offer, config, self.ingredients_data)
        self.assertEqual(actual["ingredients"]["sugar"]["key"], "sugar")
        self.assertEqual(actual["ingredients"]["sugar"]["name"], "Sukker")
        self.assertEqual(actual["ingredients"]["benzoate"]["key"], "benzoate")
        self.assertEqual(actual["ingredients"]["benzoate"]["name"], "Benzoat")
        self.assertEqual(actual["ingredients"]["citricAcid"]["key"], "citricAcid")
        self.assertEqual(actual["ingredients"]["citricAcid"]["name"], "Sitronsyre")
        self.assertEqual(actual["ingredients"]["e150b"]["key"], "e150b")
        self.assertIsNotNone(actual["processedScore"])

    def test_with_meny_offer(self):
        offer = {
            "rawIngredients": "Fløde/fløte (25%), vand, sukker, kondenseret skummetmælk/skummetmelk, hvedemel/hvetemel, brun farin, kakaopulver, æggeblomme/eggeplomme fra fritgående høns, smør, sojaolie/soyaolje, fedtfattigt kakaopulver, æg/egg, invertsukker, kakaomasse, melassesirup, tørret æggehvide/eggehvite, vaniljeekstrakt, stabilisatorer (guargummi, carrageenan), salt, kakaosmør, naturlig vaniljearoma med andre naturlige aromaer, naturlig smøraroma, emulgator (sojalecithin/soyalecitin), maltet bygmel/byggmel, bagepulver (natriumhydrogenkarbonat)."
        }
        config = {
            "extractIngredientsFields": ["rawIngredients"],
        }

        actual = get_ingredients_data(offer, config, self.ingredients_data)
        self.assertEqual(actual["ingredients"]["sugar"]["key"], "sugar")
        self.assertEqual(actual["ingredients"]["sugar"]["name"], "Sukker")
        self.assertEqual(actual["ingredients"]["e407"]["key"], "e407")
        self.assertEqual(actual["ingredients"]["e407"]["name"], "Karragenan")
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

        actual = get_ingredients_data(offer, config, self.ingredients_data)
        self.assertEqual(actual["ingredients"]["seaSalt"]["key"], "seaSalt")
        self.assertEqual(actual["ingredients"]["e160a"]["key"], "e160a")
        self.assertEqual(
            actual["ingredients"]["modifiedStarch"]["key"], "modifiedStarch"
        )
        self.assertEqual(actual["ingredients"]["starch"]["key"], "starch")
        self.assertNotIn("salt", actual["ingredients"].keys())
        self.assertIsNotNone(actual["processedScore"])
        self.assertGreater(actual["processedScore"], 0)
