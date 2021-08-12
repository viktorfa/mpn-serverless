from unittest import TestCase

from parsing.dimension_extraction import extract_dimensions


class TestExtractDimensions(TestCase):
    def test_extract_dimensions(self):
        actual = extract_dimensions(
            [
                "Furu terrassebord 28 X 120",
                "Impregnert CU\nRoyalimpregnert\nMeget holdbar i forhold til råte og insektangrep\n4,8 meter\nFarge: Royal brun",
            ]
        )
        self.assertEqual(actual, "28x120")

    def test_extract_dimensions_with_null_field(self):
        actual = extract_dimensions(
            [
                None,
                "Furu terrassebord 28 X 120",
                "Impregnert CU\nRoyalimpregnert\nMeget holdbar i forhold til råte og insektangrep\n4,8 meter\nFarge: Royal brun",
            ]
        )
        self.assertEqual(actual, "28x120")

    def test_extract_dimensions_with_nothing(self):
        actual = extract_dimensions(
            [
                "Furu terrassebord ",
                "Impregnert 4,8m Farge: Royal brun",
            ]
        )
        self.assertIsNone(actual)