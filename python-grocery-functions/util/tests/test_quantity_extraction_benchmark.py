from unittest import TestCase
from pprint import pprint

from util.quantity_extraction import analyze_quantity
from util.helpers import get_nested


"""
We test a bunch of input strings and see how well the parser is able to extract
the correct units and quantities.
Since the extractor will never be perfect, this is not a test that needs to be 100% correct.
"""


class TestQuantityExtractionBenchmark(TestCase):
    def setUp(self):
        pass

    def test_basic(self):
        self.assertTrue(True)

    def test_extract(self):
        input_assertions_pairs = [
            (["89,90. Hel. Pr kg. 109,00"], [
                (lambda x: get_nested(x, "value.size.amount.min"), 109.0),
                (lambda x: get_nested(x, "value.size.unit.symbol"), 'kg'),
            ]),
            (["SMART KUPP. MAKS 5 STK PR HUSSTAND. NORVEGIA. Original. 1,3 kg. Pr kg 76,15"], [
                (lambda x: get_nested(x, "quantity.size.amount.min"), 1.3),
                (lambda x: get_nested(x, "quantity.size.unit.symbol"), 'kg'),
            ]),
            (["SMART KUPP. MAKS 5 STK PR HUSSTAND. NORVEGIA. Original. 1,3 kg. Pr kg 76,15"], [
                (lambda x: get_nested(x, "value.size.amount.min"), 76.15),
                (lambda x: get_nested(x, "value.size.unit.symbol"), 'kg'),
            ]),
            # https://allematpriser.no/tilbud/shopgun:product:a91bLdxT
            (["7x6-pk 29,90/stk"], [
                (lambda x: get_nested(x, "value.pieces.amount.min"), 29.9),
                (lambda x: get_nested(x, "value.pieces.unit.symbol"), 'stk'),
            ]),
            (["7x6-pk 29,90/stk"], [
                (lambda x: get_nested(x, "quantity.pieces.amount.min"), 42),
            ]),
            (["7x6-pk 29,90/stk"], [
                (lambda x: get_nested(x, "items.min"), 7),
            ]),
            (["Kina, 400 g"], [
                (lambda x: get_nested(x, "quantity.size.amount.min"), 400),
                (lambda x: get_nested(x, "quantity.size.unit.symbol"), 'g'),
            ]),
            (["Spisemoden, Peru, 1 stk"], [
                (lambda x: get_nested(x, "quantity.pieces.amount.min"), 1),
                (lambda x: get_nested(x, "quantity.pieces.unit.symbol"), 'stk'),
            ]),
            (["Brasil/Mexico, 2 stk"], [
                (lambda x: get_nested(x, "quantity.pieces.amount.min"), 2),
                (lambda x: get_nested(x, "quantity.pieces.unit.symbol"), 'stk'),
            ]),
            (["0,45 kg"], [
                (lambda x: get_nested(x, "quantity.size.amount.min"), 0.45),
                (lambda x: get_nested(x, "quantity.size.unit.symbol"), 'kg'),
            ]),
            (["stort utvalg, 0,8l + pant. 2,49/l ferdig bl"], [
                (lambda x: get_nested(x, "quantity.size.amount.min"), 0.8),
                (lambda x: get_nested(x, "quantity.size.unit.symbol"), 'l'),
            ]),
            (["200 Pr. FUN LIGHT. 14 varianter. 0,8 l. Fra 3,13/l ferdig blandet. 1 flaske fra 37,90 Fra"], [
                (lambda x: get_nested(x, "quantity.size.amount.min"), 0.8),
                (lambda x: get_nested(x, "quantity.size.unit.symbol"), 'l'),
            ]),
            (["200 g Fra 150,00/kg. 1 pose 39,90"], [
                (lambda x: get_nested(x, "quantity.size.amount.min"), 200),
                (lambda x: get_nested(x, "quantity.size.unit.symbol"), 'g'),
            ]),
            (["200 g Fra 150,00/kg. 1 pose 39,90"], [
                (lambda x: get_nested(x, "value.size.amount.min"), 150.0),
                (lambda x: get_nested(x, "value.size.unit.symbol"), 'kg'),
            ]),
            (["175 g. Pr kg 285,14"], [
                (lambda x: get_nested(x, "quantity.size.amount.min"), 175),
                (lambda x: get_nested(x, "quantity.size.unit.symbol"), 'g'),
            ]),
            (["175 g. Pr kg 285,14"], [
                (lambda x: get_nested(x, "value.size.amount.min"), 285.14),
                (lambda x: get_nested(x, "value.size.unit.symbol"), 'kg'),
            ]),
            (["Lambi tørke-/toalettpapir", "4/8 pk. Pr 100 m fra 20,53"], [
                (lambda x: get_nested(x, "quantity.pieces.amount.min"), 4),
                (lambda x: get_nested(x, "quantity.pieces.amount.max"), 8),
            ]),
            # Extremely hard
            (["Lambi tørke-/toalettpapir", "4/8 pk. Pr 100 m fra 20,53"], [
                (lambda x: get_nested(x, "value.size.amount.min"), 0.2053),
                (lambda x: get_nested(x, "value.size.amount.max"), 0.4106),
                (lambda x: get_nested(x, "quantity.size.unit.symbol"), 'm'),
            ]),
        ]
        errors = []
        for _input, assertions in input_assertions_pairs:
            result = analyze_quantity(_input)
            correct = True
            for f, expected in assertions:
                try:
                    self.assertEqual(f(result), expected)
                except AssertionError as e:
                    print("Extracted wrong:")
                    print(e)
                    print(_input)
                    if correct is True:
                        errors.append((_input, expected))
                    correct = False
        # print(errors)
        print("{} correct, {} wrong".format(
            len(input_assertions_pairs) - len(errors),
            len(errors)
        ))

    def test_extract_false(self):
        input_assertions_pairs = [
            (["stort utvalg, 0,8l + pant. 2,49/l ferdig bl"], [
                (lambda x: get_nested(x, "value.size.amount.min"), None),
                (lambda x: get_nested(x, "value.size.unit.symbol"), None),
            ]),
            (["stort utvalg, 0,8l + pant. 2,49/l ferdig bl"], [
                (lambda x: get_nested(x, "value.pieces.amount.min"), None),
                (lambda x: get_nested(x, "value.pieces.unit.symbol"), None),
            ]),
            (["200 Pr. FUN LIGHT. 14 varianter. 0,8 l. Fra 3,13/l ferdig blandet. 1 flaske fra 37,90 Fra"], [
                (lambda x: get_nested(x, "value.pieces.amount.min"), None),
                (lambda x: get_nested(x, "value.pieces.unit.symbol"), None),
            ]),
            (["200 Pr. FUN LIGHT. 14 varianter. 0,8 l. Fra 3,13/l ferdig blandet. 1 flaske fra 37,90 Fra"], [
                (lambda x: get_nested(x, "value.size.amount.min"), None),
                (lambda x: get_nested(x, "value.size.unit.symbol"), None),
            ]),
            (["Laks", "89,90. Hel. Pr kg. 109,00"], [
                (lambda x: get_nested(x, "value.size.amount.min"), None),
                (lambda x: get_nested(x, "value.size.unit.symbol"), None),
            ]),
            (["Laks", "89,90. Hel. Pr kg. 109,00"], [
                (lambda x: get_nested(x, "quantity.size.amount.min"), None),
                (lambda x: get_nested(x, "quantity.size.unit.symbol"), None),
            ]),
            (["200 g Fra 150,00/kg. 1 pose 39,90"], [
                (lambda x: get_nested(x, "quantity.pieces.amount.min"), None),
                (lambda x: get_nested(x, "quantity.pieces.unit.symbol"), None),
            ]),
            (["Lambi tørke-/toalettpapir", "4/8 pk. Pr 100 m fra 20,53"], [
                (lambda x: get_nested(x, "quantity.size.amount.min"), None),
                (lambda x: get_nested(x, "quantity.size.unit.symbol"), None),
            ]),
        ]
        errors = []
        for _input, assertions in input_assertions_pairs:
            result = analyze_quantity(_input)
            correct = True
            for f, expected in assertions:
                try:
                    self.assertEqual(f(result), expected)
                except AssertionError as e:
                    print("Extracted wrong:")
                    print(e)
                    print(_input)
                    if correct is True:
                        errors.append((_input, expected))
                    correct = False
        # print(errors)
        print("{} true negatives, {} false positives".format(
            len(input_assertions_pairs) - len(errors),
            len(errors)
        ))
