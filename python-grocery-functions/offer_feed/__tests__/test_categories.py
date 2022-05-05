import json
import logging
from unittest import TestCase
from offer_feed.categories import (
    get_mpn_categories_for_offer,
    get_mpn_categories_for_meny_offer,
)


logging.basicConfig(level=logging.DEBUG)


class TestGetCategories(TestCase):
    def test_with_no_categories(self):
        self.assertListEqual(
            get_mpn_categories_for_offer({"categories": []}, {}, {}), []
        )
        self.assertListEqual(
            get_mpn_categories_for_offer({"categories": ["Melk"]}, {}, {}), []
        )

    def test_with_existing_target(self):
        actual = get_mpn_categories_for_offer(
            {"categories": ["Melk"]},
            {json.dumps(["Melk"]): {"target": "melk"}},
            {"melk": {"key": "melk", "parent": None, "text": "Melk"}},
        )
        self.assertListEqual(actual, [{"text": "Melk", "key": "melk", "parent": None}])

    def test_with_existing_target_and_parent(self):
        actual = get_mpn_categories_for_offer(
            {"categories": ["Melk"]},
            {json.dumps(["Melk"]): {"target": "melk"}},
            {
                "melk": {"key": "melk", "parent": "meieri", "text": "Melk"},
                "meieri": {"key": "meieri", "parent": None, "text": "Meieri"},
            },
        )
        self.assertListEqual(
            actual,
            [
                {"key": "meieri", "parent": None, "text": "Meieri"},
                {"text": "Melk", "key": "melk", "parent": "meieri"},
            ],
        )

    def test_with_only_map_in_level_0(self):
        actual = get_mpn_categories_for_offer(
            {"categories": ["Meieri", "Melk"]},
            {json.dumps(["Meieri"]): {"target": "meieri"}},
            {
                "meieri": {"key": "meieri", "parent": None, "text": "Meieri"},
            },
        )
        self.assertListEqual(
            actual,
            [
                {"key": "meieri", "parent": None, "text": "Meieri"},
            ],
        )

    def test_for_meny_offer(self):
        self.assertListEqual(
            get_mpn_categories_for_meny_offer({"slugCategories": ["balla"]}, {}), []
        )

    def test_for_meny_offer_with_slugcat(self):
        self.assertListEqual(
            get_mpn_categories_for_meny_offer(
                {"slugCategories": ["frukt-gront"]},
                {"frukt-gront_0": {"key": "frukt-gront_0", "parent": None}},
            ),
            [{"key": "frukt-gront_0", "parent": None}],
        )

    def test_for_meny_offer_with_slugcat_and_parent(self):
        self.assertListEqual(
            get_mpn_categories_for_meny_offer(
                {"slugCategories": ["frukt-gront", "frukt"]},
                {
                    "frukt-gront_0": {"key": "frukt-gront_0", "parent": None},
                    "frukt_1": {"key": "frukt_1", "parent": "frukt-gront_0"},
                },
            ),
            [
                {"key": "frukt-gront_0", "parent": None},
                {"key": "frukt_1", "parent": "frukt-gront_0"},
            ],
        )
