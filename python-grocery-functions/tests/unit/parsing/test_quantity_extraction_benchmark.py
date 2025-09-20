from unittest import TestCase
import pydash

from parsing.quantity_extraction import parse_quantity


"""
We test a bunch of input strings and see how well the parser is able to extract
the correct units and quantities.
Since the extractor will never be perfect, this is not a test that needs to be 100% correct.
"""


class TestQuantityExtractionBenchmark(TestCase):
    def setUp(self):
        pass

    def test_extract_simple(self):
        input_assertions_pairs = [
            (
                ["225 ml"],
                [
                    (lambda x: pydash.get(x, "quantity.size.amount.min"), 225),
                    (lambda x: pydash.get(x, "quantity.size.unit.symbol"), "ml"),
                ],
            ),
            (
                ["m/Sjokolade 21g United Bakeries"],
                [
                    (lambda x: pydash.get(x, "quantity.size.amount.min"), 21),
                    (lambda x: pydash.get(x, "quantity.size.unit.symbol"), "g"),
                ],
            ),
            (
                ["m/Sjokolade 21 g United Bakeries"],
                [
                    (lambda x: pydash.get(x, "quantity.size.amount.min"), 21),
                    (lambda x: pydash.get(x, "quantity.size.unit.symbol"), "g"),
                ],
            ),
            (
                ["520g Gilde"],
                [
                    (lambda x: pydash.get(x, "quantity.size.amount.min"), 520),
                    (lambda x: pydash.get(x, "quantity.size.unit.symbol"), "g"),
                ],
            ),
            (
                ["0,5l boks"],
                [
                    (lambda x: pydash.get(x, "quantity.size.amount.min"), 0.5),
                    (lambda x: pydash.get(x, "quantity.size.unit.symbol"), "l"),
                ],
            ),
            (
                ["1kg M\u00f8llerens"],
                [
                    (lambda x: pydash.get(x, "quantity.size.amount.min"), 1),
                    (lambda x: pydash.get(x, "quantity.size.unit.symbol"), "kg"),
                ],
            ),
            (
                ["1 kg M\u00f8llerens"],
                [
                    (lambda x: pydash.get(x, "quantity.size.amount.min"), 1),
                    (lambda x: pydash.get(x, "quantity.size.unit.symbol"), "kg"),
                ],
            ),
            (
                ["2 varianter. 4 x 125 g. 179,80/kg"],
                [
                    (lambda x: pydash.get(x, "quantity.size.amount.min"), 500),
                    (lambda x: pydash.get(x, "quantity.size.unit.symbol"), "g"),
                ],
            ),
            (
                ["1 gressklipper M\u00f8llerens"],
                [
                    (lambda x: pydash.get(x, "quantity.size.amount.min"), None),
                    (lambda x: pydash.get(x, "quantity.size.unit.symbol"), None),
                ],
            ),
            (
                ["1 gressklipper M\u00f8llerens"],
                [
                    (lambda x: pydash.get(x, "quantity.size.amount.min"), None),
                    (lambda x: pydash.get(x, "quantity.size.unit.symbol"), None),
                ],
            ),
        ]
        errors = []
        for _input, assertions in input_assertions_pairs:
            result = parse_quantity(_input)
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
        print("RESULT")
        print(
            "{} correct, {} wrong".format(
                len(input_assertions_pairs) - len(errors), len(errors)
            )
        )

    def test_extract(self):
        input_assertions_pairs = [
            (
                ["1,5lx8 flaske"],
                [
                    (lambda x: pydash.get(x, "quantity.size.amount.min"), 12),
                    (lambda x: pydash.get(x, "quantity.size.unit.symbol"), "l"),
                ],
            ),
            (
                ["Extra Crispy 3x160g Green Giant"],
                [
                    (lambda x: pydash.get(x, "quantity.size.amount.min"), 480),
                    (lambda x: pydash.get(x, "quantity.size.unit.symbol"), "g"),
                ],
            ),
            (
                ["89,90. Hel. Pr kg. 109,00"],
                [
                    (lambda x: pydash.get(x, "value.size.amount.min"), 109.0),
                    (lambda x: pydash.get(x, "value.size.unit.symbol"), "kg"),
                ],
            ),
            (
                [
                    "SMART KUPP. MAKS 5 STK PR HUSSTAND. NORVEGIA. Original. 1,3 kg. Pr kg 76,15"
                ],
                [
                    (lambda x: pydash.get(x, "quantity.size.amount.min"), 1.3),
                    (lambda x: pydash.get(x, "quantity.size.unit.symbol"), "kg"),
                ],
            ),
            (
                [
                    "SMART KUPP. MAKS 5 STK PR HUSSTAND. NORVEGIA. Original. 1,3 kg. Pr kg 76,15"
                ],
                [
                    (lambda x: pydash.get(x, "value.size.amount.min"), 76.15),
                    (lambda x: pydash.get(x, "value.size.unit.symbol"), "kg"),
                ],
            ),
            # https://allematpriser.no/tilbud/shopgun:product:a91bLdxT
            (
                ["7x6-pk 29,90/stk"],
                [
                    (lambda x: pydash.get(x, "value.pieces.amount.min"), 29.9),
                    (lambda x: pydash.get(x, "value.pieces.unit.symbol"), "/stk"),
                ],
            ),
            (
                ["kr 39,90/kg"],
                [
                    (lambda x: pydash.get(x, "value.size.amount.min"), 39.9),
                    (lambda x: pydash.get(x, "value.pieces.unit.symbol"), "/kg"),
                ],
            ),
            (
                ["7x6-pk 29,90/stk"],
                [(lambda x: pydash.get(x, "quantity.pieces.amount.min"), 42),],
            ),
            (["7x6-pk 29,90/stk"], [(lambda x: pydash.get(x, "items.min"), 7),]),
            (
                ["Kina, 400 g"],
                [
                    (lambda x: pydash.get(x, "quantity.size.amount.min"), 400),
                    (lambda x: pydash.get(x, "quantity.size.unit.symbol"), "g"),
                ],
            ),
            (
                ["Spisemoden, Peru, 1 stk"],
                [
                    (lambda x: pydash.get(x, "quantity.pieces.amount.min"), 1),
                    (lambda x: pydash.get(x, "quantity.pieces.unit.symbol"), "stk"),
                ],
            ),
            (
                ["Brasil/Mexico, 2 stk"],
                [
                    (lambda x: pydash.get(x, "quantity.pieces.amount.min"), 2),
                    (lambda x: pydash.get(x, "quantity.pieces.unit.symbol"), "stk"),
                ],
            ),
            (
                ["0,45 kg"],
                [
                    (lambda x: pydash.get(x, "quantity.size.amount.min"), 0.45),
                    (lambda x: pydash.get(x, "quantity.size.unit.symbol"), "kg"),
                ],
            ),
            (
                ["stort utvalg, 0,8l + pant. 2,49/l ferdig bl"],
                [
                    (lambda x: pydash.get(x, "quantity.size.amount.min"), 0.8),
                    (lambda x: pydash.get(x, "quantity.size.unit.symbol"), "l"),
                ],
            ),
            (
                [
                    "200 Pr. FUN LIGHT. 14 varianter. 0,8 l. Fra 3,13/l ferdig blandet. 1 flaske fra 37,90 Fra"
                ],
                [
                    (lambda x: pydash.get(x, "quantity.size.amount.min"), 0.8),
                    (lambda x: pydash.get(x, "quantity.size.unit.symbol"), "l"),
                ],
            ),
            (
                ["200 g Fra 150,00/kg. 1 pose 39,90"],
                [
                    (lambda x: pydash.get(x, "quantity.size.amount.min"), 200),
                    (lambda x: pydash.get(x, "quantity.size.unit.symbol"), "g"),
                ],
            ),
            (
                ["200 g Fra 150,00/kg. 1 pose 39,90"],
                [
                    (lambda x: pydash.get(x, "value.size.amount.min"), 150.0),
                    (lambda x: pydash.get(x, "value.size.unit.symbol"), "/kg"),
                ],
            ),
            (
                ["175 g. Pr kg 285,14"],
                [
                    (lambda x: pydash.get(x, "quantity.size.amount.min"), 175),
                    (lambda x: pydash.get(x, "quantity.size.unit.symbol"), "g"),
                ],
            ),
            (
                ["200gram"],
                [
                    (lambda x: pydash.get(x, "quantity.size.amount.min"), 200),
                    (lambda x: pydash.get(x, "quantity.size.unit.symbol"), "g"),
                ],
            ),
            (
                ["175 g. Pr kg 285,14"],
                [
                    (lambda x: pydash.get(x, "value.size.amount.min"), 285.14),
                    (lambda x: pydash.get(x, "value.size.unit.symbol"), "/kg"),
                ],
            ),
            (
                ["Lambi tørke-/toalettpapir", "4/8 pk. Pr 100 m fra 20,53"],
                [
                    (lambda x: pydash.get(x, "quantity.pieces.amount.min"), 4),
                    (lambda x: pydash.get(x, "quantity.pieces.amount.max"), 8),
                ],
            ),
            # Extremely hard
            (
                ["Lambi tørke-/toalettpapir", "4/8 pk. Pr 100 m fra 20,53"],
                [
                    (lambda x: pydash.get(x, "value.size.amount.min"), 0.2053),
                    (lambda x: pydash.get(x, "value.size.amount.max"), 0.4106),
                    (lambda x: pydash.get(x, "quantity.size.unit.symbol"), "m"),
                ],
            ),
            (
                ["6x0,5 liter, 3 l"],
                [
                    (lambda x: pydash.get(x, "quantity.size.amount.min"), 3),
                    (lambda x: pydash.get(x, "quantity.size.unit.symbol"), "l"),
                ],
            ),
            (
                ["u/Sukker 0,9l Lerum"],
                [
                    (lambda x: pydash.get(x, "quantity.size.amount.min"), 0.9),
                    (lambda x: pydash.get(x, "quantity.size.unit.symbol"), "l"),
                ],
            ),
            (
                ["Sukker 0,9l Lerum"],
                [
                    (lambda x: pydash.get(x, "quantity.size.amount.min"), 0.9),
                    (lambda x: pydash.get(x, "quantity.size.unit.symbol"), "l"),
                ],
            ),
            (
                ["FUGESAND HERREGÅRD 25 KG"],
                [
                    (lambda x: pydash.get(x, "quantity.size.amount.min"), 25),
                    (lambda x: pydash.get(x, "quantity.size.unit.symbol"), "kg"),
                ],
            ),
            (
                ["kr\u00a05\u00a0647,06/kg"],
                [
                    (lambda x: pydash.get(x, "value.size.amount.min"), 647.06),
                    (lambda x: pydash.get(x, "value.size.unit.symbol"), "/kg"),
                ],
            ),
        ]
        errors = []
        for _input, assertions in input_assertions_pairs:
            result = parse_quantity(_input)
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
        print("RESULT")
        print(
            "{} correct, {} wrong".format(
                len(input_assertions_pairs) - len(errors), len(errors)
            )
        )

    def test_extract_false(self):
        """
        Test strings that seem to have a value, but is not the number we want.
        """
        input_assertions_pairs = [
            (
                # This is tricky. It should not extract value because it's "ferdig blandet".
                # It's way too early to worry about this now.
                ["stort utvalg, 0,8l + pant. 2,49/l ferdig bl"],
                [
                    (lambda x: pydash.get(x, "value.size.amount.min"), None),
                    (lambda x: pydash.get(x, "value.size.unit.symbol"), None),
                ],
            ),
            (
                ["stort utvalg, 0,8l + pant. 2,49/l ferdig bl"],
                [
                    (lambda x: pydash.get(x, "value.pieces.amount.min"), None),
                    (lambda x: pydash.get(x, "value.pieces.unit.symbol"), None),
                ],
            ),
            (
                [
                    "200 Pr. FUN LIGHT. 14 varianter. 0,8 l. Fra 3,13/l ferdig blandet. 1 flaske fra 37,90 Fra"
                ],
                [
                    (lambda x: pydash.get(x, "value.pieces.amount.min"), None),
                    (lambda x: pydash.get(x, "value.pieces.unit.symbol"), None),
                ],
            ),
            (
                [
                    "200 Pr. FUN LIGHT. 14 varianter. 0,8 l. Fra 3,13/l ferdig blandet. 1 flaske fra 37,90 Fra"
                ],
                [
                    (lambda x: pydash.get(x, "value.size.amount.min"), None),
                    (lambda x: pydash.get(x, "value.size.unit.symbol"), None),
                ],
            ),
            (
                ["Laks", "89,90. Hel. Pr kg. 109,00"],
                [
                    (lambda x: pydash.get(x, "value.size.amount.min"), None),
                    (lambda x: pydash.get(x, "value.size.unit.symbol"), None),
                ],
            ),
            (
                ["Laks", "89,90. Hel. Pr kg. 109,00"],
                [
                    (lambda x: pydash.get(x, "quantity.size.amount.min"), None),
                    (lambda x: pydash.get(x, "quantity.size.unit.symbol"), None),
                ],
            ),
            (
                ["200 g Fra 150,00/kg. 1 pose 39,90"],
                [
                    (lambda x: pydash.get(x, "quantity.pieces.amount.min"), None),
                    (lambda x: pydash.get(x, "quantity.pieces.unit.symbol"), None),
                ],
            ),
            (
                ["Lambi tørke-/toalettpapir", "4/8 pk. Pr 100 m fra 20,53"],
                [
                    (lambda x: pydash.get(x, "quantity.size.amount.min"), None),
                    (lambda x: pydash.get(x, "quantity.size.unit.symbol"), None),
                ],
            ),
        ]
        errors = []
        for _input, assertions in input_assertions_pairs:
            result = parse_quantity(_input)
            correct = True
            for f, expected in assertions:
                try:
                    self.assertEqual(f(result), expected)
                except AssertionError as e:
                    print("Extracted wrong:")
                    print(_input)
                    print(e)
                    if correct is True:
                        errors.append((_input, expected))
                    correct = False
        # print(errors)
        print("RESULT")
        print(
            "{} true negatives (correct), {} false positives (wrong)".format(
                len(input_assertions_pairs) - len(errors), len(errors)
            )
        )
