from unittest import TestCase

from storage.helpers import meta_fields_result_to_dict, remove_protected_fields_from_product, remove_protected_fields


class TestHelpers(TestCase):
    def test_meta_fields_result_to_dict(self):
        self.assertDictEqual(
            meta_fields_result_to_dict([
                dict(uri="123", field="abc")
            ]),
            {"123": ["abc"]}
        )
        self.assertDictEqual(
            meta_fields_result_to_dict([
                dict(uri="123", field="def"),
                dict(uri="123", field="abc"),
            ]),
            {"123": ["abc", "def"]}
        )
        self.assertDictEqual(
            meta_fields_result_to_dict([
                dict(uri="123", field="def"),
                dict(uri="123", field="abc"),
                dict(uri="456", field="xyz"),
            ]),
            {"123": ["abc", "def"], "456": ["xyz"]}
        )

    def test_remove_protected_fields_from_product(self):
        self.assertDictEqual(
            remove_protected_fields_from_product(
                dict(uri="123", brand="Kims", name="fishnacks"),
                {"123": ["brand", "reports"]}
            ),
            dict(uri="123", name="fishnacks")
        )
        self.assertDictEqual(
            remove_protected_fields_from_product(
                dict(uri="123", brand="Kims", name="fishnacks"),
                dict()
            ),
            dict(uri="123", brand="Kims", name="fishnacks")
        )

    def test_remove_protected_fields(self):
        self.assertListEqual(list(remove_protected_fields([], dict())), [])
        self.assertListEqual(
            list(remove_protected_fields(
                [dict(uri="123", heading="abc")],
                dict()
            )),
            [dict(uri="123", heading="abc")]
        )
