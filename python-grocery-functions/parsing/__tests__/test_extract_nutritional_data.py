from unittest import TestCase

from parsing.nutrition_extraction import extract_nutritional_data
from transform.transform import transform_fields


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

    def test_with_kolonial_offer_2(self):
        offer = {
            "price": 22.3,
            "priceCurrency": "NOK",
            "brand": "Tine",
            "title": "Tine Lettmelk Med Sjokoladesmak 1 l",
            "url": "https://oda.com/no/products/28341-tine-tine-lettmelk-med-sjokoladesmak/",
            "image": "https://bilder.kolonial.no/produkter/b67c01e3-243c-4672-9d6c-0f5603158ad3.jpeg?fit=max&w=500&s=40956a8d20e671056fcc846b967349a2",
            "description": "Inneholder ekte kakao, noe som gir en mild og god sjokoladesmak. Den er uten tilsatt sukker, men med et naturlig innhold av sukker fra melken. Lett Tinemelk® Sjokolade har et lavt fettinnhold, er laktoseredusert og tilsatt vitamin D. Prøv den gjerne oppvarmet med krem – verdens kanskje enkleste kopp med kakao. Sett farge på hverdagen med Tinemelk® Sjokolade!",
            "availability": "http://schema.org/InStock",
            "itemCondition": "http://schema.org/NewCondition",
            "additionalProperties": [
                {
                    "@type": "PropertyValue",
                    "name": "Størrelse",
                    "value": "1",
                    "unitText": "liter",
                },
                {
                    "@type": "PropertyValue",
                    "name": "Utleveringsdager",
                    "value": "Alle dager",
                },
                {"value": "1 liter", "key": "Størrelse", "type": None},
                {"value": "Alle dager", "key": "Utleveringsdager", "type": None},
                {
                    "value": "lettmelk, kakao, aroma, stabilisator (karragenan), vitamin D Allergikere kan reagere på: lettmelk",
                    "key": "Ingredienser",
                    "type": None,
                },
                {"value": "Norge", "key": "Opprinnelsesland", "type": None},
                {"value": "Tine SA", "key": "Leverandør", "type": None},
                {
                    "value": "Kjølevare Må oppbevares mellom 0-4°C",
                    "key": "Oppbevaring",
                    "type": None,
                },
                {
                    "value": "7 dager Les mer...",
                    "key": "Holdbarhetsgaranti",
                    "type": None,
                },
                {"value": "188 kJ / 45 kcal", "key": "Energi", "type": None},
                {"value": "1,30 g", "key": "Fett", "type": None},
                {"value": "0,90 g", "key": "hvorav mettede fettsyrer", "type": None},
                {"value": "4,60 g", "key": "Karbohydrater", "type": None},
                {"value": "4,50 g", "key": "hvorav sukkerarter", "type": None},
                {"value": "3,70 g", "key": "Protein", "type": None},
                {"value": "0,10 g", "key": "Salt", "type": None},
            ],
            "categories": ["Alle varer", "Meieri, ost og egg", "Melk", "Melk med smak"],
            "canonical_url": "https://oda.com/no/products/28341-tine-tine-lettmelk-med-sjokoladesmak/",
            "sku": "28341",
            "unit_price_raw": "kr 22,30 per l",
            "quantity_info": "1 l",
            "subtitle": "1 l",
            "provenance": "kolonial_spider",
            "url_fingerprint": "65086aa852388fc703a2b9ec2f9e8be26e32987b",
            "provenanceId": "28341",
        }
        config = {}
        offer = transform_fields(
            offer,
            [
                {
                    "source": "Ingredienser",
                    "destination": "rawIngredients",
                    "replace_type": "key",
                },
                {"source": "Protein", "destination": "proteins", "replace_type": "key"},
                {
                    "source": "hvorav sukkerarter",
                    "destination": "sugars",
                    "replace_type": "key",
                },
                {"source": "Energi", "destination": "energy", "replace_type": "key"},
                {"source": "Salt", "destination": "salt", "replace_type": "key"},
                {"source": "Kostfiber", "destination": "fibers", "replace_type": "key"},
                {"source": "Fett", "destination": "fats", "replace_type": "key"},
                {
                    "source": "hvorav mettede fettsyrer",
                    "destination": "satFats",
                    "replace_type": "key",
                },
                {
                    "source": "hvorav enumettede fettsyrer",
                    "destination": "monoFats",
                    "replace_type": "key",
                },
                {
                    "source": "hvorav flerumettede fettsyrer",
                    "destination": "polyFats",
                    "replace_type": "key",
                },
                {
                    "source": "Karbohydrater",
                    "destination": "carbohydrates",
                    "replace_type": "key",
                },
            ],
        )
        actual = extract_nutritional_data(offer, config)
        self.assertEqual(actual["proteins"]["value"], 3.7)

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
