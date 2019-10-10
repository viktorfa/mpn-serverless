from unittest import TestCase

from util.parsing import extract_number_unit_pairs, extract_unit
from util.enums import unit_types


class ExtractUnitPairs(TestCase):
    def setUp(self):
        pass

    def test_simple(self):
        string = '4stk'
        expected = [(4.0, 'stk')]
        actual = extract_number_unit_pairs(string)
        self.assertIsInstance(actual, list)
        self.assertListEqual(actual, expected)

    def test_with_prefix(self):
        string = 'Cloetta sjokolade 450g'
        expected = [(450.0, 'g')]
        actual = extract_number_unit_pairs(string)
        self.assertIsInstance(actual, list)
        self.assertListEqual(actual, expected)

    def test_with_comma(self):
        string = 'Pingvin Heksehyl Stang 50 st. 1,25 kg'
        expected = [(50, 'st.'), (1.25, 'kg')]
        actual = extract_number_unit_pairs(string)
        self.assertIsInstance(actual, list)
        self.assertListEqual(actual, expected)

    def test_with_multiple(self):
        string = 'Cloetta sjokolade 450g 75,00kr/kg'
        expected = [(450.0, 'g'), (75.0, 'kr/kg')]
        actual = extract_number_unit_pairs(string)
        self.assertIsInstance(actual, list)
        self.assertListEqual(actual, expected)

    def test_with_non_unit_number(self):
        string = 'kr 2,18/vask3-I-1 Pods 16stkAriel Color'
        expected = [
            (2.18, '/vask'),
            (3.0, '-I-'),
            (1.0, 'Pods'),
            (16.0, 'stkArielColor')
        ]
        actual = extract_number_unit_pairs(string)
        self.assertIsInstance(actual, list)
        self.assertListEqual(actual, expected)

    def test_with_multiple2(self):
        string = 'kr\u00a046,53/l750 Ml Bendit'
        expected = [(46.53, '/l'), (750.0, 'MlBendit')]
        actual = extract_number_unit_pairs(string)
        self.assertIsInstance(actual, list)
        self.assertListEqual(actual, expected)

    def test_with_multiplier_unit(self):
        string = 'kr 180,77/kgHomestyle 4x130g KandaPepperburger'
        expected = [
            (180.77, '/kgHomestyle'),
            (4.0, 'x'),
            (130.0, 'gKandaPepperburger')
        ]
        actual = extract_number_unit_pairs(string)
        self.assertIsInstance(actual, list)
        self.assertListEqual(actual, expected)


class ExtractUnit(TestCase):
    def setUp(self):
        pass

    def test_simple(self):
        string = 'ml'
        expected = dict(
            symbol='ml',
            type='quantity',
            si=dict(symbol='l', factor=0.001)
        )
        actual = extract_unit(string)
        self.assertDictEqual(actual, expected)

    def test_with_suffix(self):
        string = 'hgKrok'
        expected = dict(
            symbol='hg',
            type=unit_types.QUANTITY,
            si=dict(symbol='kg', factor=0.01)
        )
        actual = extract_unit(string)
        self.assertDictEqual(actual, expected)

    def test_pieces(self):
        string = 'stk'
        expected = dict(
            symbol='stk',
            type=unit_types.PIECE,
        )
        actual = extract_unit(string)
        self.assertDictEqual(actual, expected)

    def test_value(self):
        string = '/l'
        expected = dict(
            symbol='l',
            type=unit_types.QUANTITY_VALUE,
            si=dict(symbol='l', factor=1)
        )
        actual = extract_unit(string)
        self.assertDictEqual(actual, expected)

    def test_value_with_currency(self):
        string = 'kr/kg'
        expected = dict(
            symbol='kg',
            type=unit_types.QUANTITY_VALUE,
            si=dict(symbol='kg', factor=1)
        )
        actual = extract_unit(string)
        self.assertDictEqual(actual, expected)

    def test_value_with_pieces(self):
        string = 'krboks'
        expected = dict(
            symbol='boks',
            type=unit_types.PIECE_VALUE,
        )
        actual = extract_unit(string)
        self.assertDictEqual(actual, expected)

    def test_with_varying_case(self):
        string = 'MlBendit'
        expected = dict(
            symbol='ml',
            type=unit_types.QUANTITY,
            si=dict(symbol='l', factor=0.001)
        )
        actual = extract_unit(string)
        self.assertDictEqual(actual, expected)

    def test_with_no_valid_unit(self):
        string = '-I-'
        actual = extract_unit(string)
        self.assertIsNone(actual)

    def test_with_multiplier(self):
        string = 'x'
        expected = dict(
            symbol='x',
            type=unit_types.MULTIPLIER,
        )
        actual = extract_unit(string)
        self.assertDictEqual(actual, expected)
