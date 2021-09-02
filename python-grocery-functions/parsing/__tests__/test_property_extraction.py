from unittest import TestCase

from parsing.property_extraction import (
    extract_dimensions,
    extract_properties,
    get_dimensions_object_from_string,
    standardize_additional_properties,
)


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

    def test_extract_dimensions_without_space(self):
        actual = extract_dimensions(
            [
                "28x120 Terrassebord, rillet",
            ]
        )
        self.assertEqual(actual, "28x120")

    def test_extract_dimensions_without_space_and_3(self):
        actual = extract_dimensions(
            [
                "28X120X2600 Terrassebord, rillet",
            ]
        )
        self.assertEqual(actual, "28x120x2600")

    def test_extract_dimensions_with_nothing(self):
        actual = extract_dimensions(
            [
                "Furu terrassebord ",
                "Impregnert 4,8m Farge: Royal brun",
            ]
        )
        self.assertIsNone(actual)


class TestExtractProperties(TestCase):
    def test_extract_properties(self):
        actual = extract_properties(
            [
                "Furu terrassebord 28 X 120 c24",
                "Impregnert CU\nRoyalimpregnert\nMeget holdbar i forhold til råte og insektangrep\n4,8 meter\nFarge: Royal brun",
            ]
        )
        self.assertIn({"property": "styrkegrad", "value": "c24"}, actual)

    def test_extract_properties_with_dimensions(self):
        actual = extract_properties(
            ["Ubehandlet furu. Fast lengde av 2,4 meter. 28 mm. 10 x 58 x 4400 mm."]
        )
        print(actual)
        self.assertIn({"property": "dimensions", "value": "10x58x4400"}, actual)


class TestExtractPropertiesFromOffer(TestCase):
    def test_standardize_additional_properties(self):
        actual = standardize_additional_properties(
            {"title": "Furu terrassebord 28 X 120 c24", "subtitle": ""},
            {
                "extractPropertiesFields": ["title"],
            },
        )
        self.assertDictEqual(
            {"property": "styrkegrad", "value": "c24"}, actual["styrkegrad"]
        )


class TestGetDimensionsFromString(TestCase):
    def test_with_3_dimensions(self):
        actual = get_dimensions_object_from_string("12x40x80")
        self.assertDictEqual(actual, dict(d=12, b=40, l=80))

    def test_with_2_dimensions(self):
        actual = get_dimensions_object_from_string("40x80")
        self.assertDictEqual(actual, dict(d=40, b=80))
