from unittest import TestCase

from parsing.nutrition_extraction import extract_nutritional_data
from scraper_feed.handle_config import generate_handle_config


class TestExtractNutrionalData(TestCase):
    def test_with_kolonial_offer(self):
        offer = {
            "provenance": "kolonial_spider",
            "quantity_info": "1,5 l",
            "canonical_url": "https://oda.com/no/products/494-ringnes-mozell-eple-drue/",
            "brand": "Ringnes",
            "itemCondition": "http://schema.org/NewCondition",
            "price": 30.6,
            "url": "https://oda.com/no/products/494-ringnes-mozell-eple-drue/",
            "url_fingerprint": "2d76b138d3e5bb688862d10a7668aadd568714ab",
            "unit_price_raw": "kr 20,40 per l",
            "subtitle": "1,5 l",
            "title": "Mozell Eple & Drue 1,5 l",
            "priceCurrency": "NOK",
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
            "availability": "http://schema.org/InStock",
            "image": "https://bilder.kolonial.no/produkter/587689a0-91c0-4b1c-ab08-df137863fe2a.jpeg?fit=max&w=500&s=21758f8bdabfd723181f7de6b6c20b4b",
            "categories": ["Alle varer", "Drikke", "Brus", "Brus med sukker"],
            "provenanceId": "494",
            "description": "Kjøp Ringnes Mozell Eple & Drue 1,5 l og alt annet av dagligvarer billig på nett! Varene får du levert hjem, ferdig pakket.",
            "sku": "494",
            "sugars": "9,70 g",
        }
        config = {}
        actual = extract_nutritional_data(offer, config)
        self.assertEqual(actual["sugars"]["value"], 9.7)

    def test_with_europris_offer(self):
        offer = {
            "satFats": "0",
            "carbohydrates": "52",
            "provenance": "europris",
            "gtins": {"gtin13": "7028630000835"},
            "canonical_url": "https://www.europris.no/p-melkesjokolade-300-g-hval-105964",
            "siteCollection": "groceryoffers",
            "pieces": {},
            "validFrom": "2021-09-04T02:44:27.000Z",
            "energy": "558",
            "price": 59.9,
            "validThrough": "2021-09-14T06:44:27.000Z",
            "mpnStock": "På nettlager",
            "href": "https://www.europris.no/p-melkesjokolade-300-g-hval-105964",
            "uri": "europris:product:105964",
            "ahref": None,
            "gtin": "7028630000835",
            "properties": [],
            "url_fingerprint": "210189beba4021b444723fecd0c6d9c660c538af",
            "imageUrl": "https://images.europris.no/produkter/vw370/105964/Melkesjokoladejpg",
            "salt": "0",
            "fats": "35.8",
            "sugars": "50",
        }
        config = {}
        actual = extract_nutritional_data(offer, config)
        self.assertEqual(actual["sugars"]["value"], 50)
        self.assertEqual(actual["fats"]["value"], 35.8)
        self.assertEqual(actual["salt"]["value"], 0)
