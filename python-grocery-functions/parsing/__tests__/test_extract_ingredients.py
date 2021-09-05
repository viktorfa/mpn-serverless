from parsing.ingredients_extraction import extract_ingredients
from unittest import TestCase

from parsing.nutrition_extraction import extract_nutritional_data
from scraper_feed.handle_config import generate_handle_config


class TestExtractIngredients(TestCase):
    def test_with_kolonial_offer(self):
        offer = {
            "additionalProperties": [
                {
                    "@type": "PropertyValue",
                    "name": "Størrelse",
                    "value": "1,50",
                    "unitText": "liter",
                },
                {
                    "@type": "PropertyValue",
                    "name": "Utleveringsdager",
                    "value": "Alle dager",
                },
                {"value": "1,50 liter", "key": "Størrelse", "type": None},
                {"value": "Alle dager", "key": "Utleveringsdager", "type": None},
                {
                    "value": "Vann, 20 % fruktjuice fra konsentrat (12 % druejuice, 8 % eplejuice), sukker, karbondioksid, syre (sitronsyre), aroma, konserveringsmiddel (natriumbenzoat, kaliumsorbat), farge (karamell E150b), antioksidant (askorbinsyre)",
                    "key": "Ingredienser",
                    "type": None,
                },
                {"value": "Kr 3,00", "key": "Pant", "type": None},
                {"value": "Norge", "key": "Opprinnelsesland", "type": None},
                {"value": "Ringnes AS", "key": "Leverandør", "type": None},
                {
                    "value": "167 kJ /\n                                    39 kcal",
                    "key": "Energi",
                    "type": None,
                },
                {"value": "0 g", "key": "Fett", "type": None},
                {"value": "0 g", "key": "hvorav mettede fettsyrer", "type": None},
                {"value": "9,70 g", "key": "Karbohydrater", "type": None},
                {"value": "9,70 g", "key": "hvorav sukkerarter", "type": None},
                {"value": "0 g", "key": "Kostfiber", "type": None},
                {"value": "0 g", "key": "Protein", "type": None},
                {"value": "0 g", "key": "Salt", "type": None},
                {"value": "0 g", "key": "Natrium", "type": None},
            ],
        }
        config = {
            "extractIngredientsFields": ["Ingredienser"],
        }

        actual = extract_ingredients(offer, config)
        self.assertIn("sukker", actual)
