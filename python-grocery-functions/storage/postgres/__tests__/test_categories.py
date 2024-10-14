import unittest
from dataclasses import dataclass
from typing import Dict, Optional, List, Tuple

from storage.postgres.categories import get_categories_for_market_info


@dataclass
class CategoryMappingsTable:
    source: List[str]
    target: str


@dataclass
class CategoriesTable:
    key: str
    level: int
    parent: Optional[str]
    title: str


class TestGetCategoriesForMarketInfo(unittest.TestCase):
    def test_get_categories_for_market_info_kolonial(self):
        # Sample offer categories
        offer_cats = ["Frukt og grønt", "Grønnsaker"]

        # Sample category mappings
        category_mappings = [
            (
                CategoriesTable(
                    key="sopp_2", level=2, parent="gronnsaker_1", title="Sopp"
                ),
                CategoryMappingsTable(
                    source=["Frukt og grønt", "Grønnsaker", "Sopp"], target="sopp_2"
                ),
            ),
            (
                CategoriesTable(
                    key="frukt-gront_0", level=0, parent=None, title="Frukt og grønt"
                ),
                CategoryMappingsTable(
                    source=["Frukt og grønt"], target="frukt-gront_0"
                ),
            ),
            (
                CategoriesTable(
                    key="gronnsaker_1",
                    level=1,
                    parent="frukt-gront_0",
                    title="Grønnsaker",
                ),
                None,
            ),
        ]

        # Build data structures for quick lookup
        categories_by_key: Dict[str, CategoriesTable] = {}
        categories_by_name: Dict[str, CategoriesTable] = {}
        source_cat_map: Dict[Tuple[str, ...], CategoryMappingsTable] = {}

        for category, mapping in category_mappings:
            categories_by_key[category.key] = category
            if category.title:
                categories_by_name[category.title] = category
            if mapping:
                source_tuple = tuple(mapping.source)
                source_cat_map[source_tuple] = mapping

        expected_category_keys = ["frukt-gront_0", "gronnsaker_1"]

        result = get_categories_for_market_info(
            offer_cats, categories_by_key, categories_by_name, source_cat_map
        )

        print("result", result)
        self.assertEqual(result, expected_category_keys)

    def test_multiple_mappings(self):
        offer_cats = ["Electronics", "Computers", "Laptops"]

        category_mappings = [
            (
                CategoriesTable(
                    key="laptops_2", level=2, parent="computers_1", title="Laptops"
                ),
                CategoryMappingsTable(
                    source=["Electronics", "Computers", "Laptops"], target="laptops_2"
                ),
            ),
            (
                CategoriesTable(
                    key="computers_1",
                    level=1,
                    parent="electronics_0",
                    title="Computers",
                ),
                CategoryMappingsTable(
                    source=["Electronics", "Computers"], target="computers_1"
                ),
            ),
            (
                CategoriesTable(
                    key="electronics_0", level=0, parent=None, title="Electronics"
                ),
                CategoryMappingsTable(source=["Electronics"], target="electronics_0"),
            ),
        ]

        # Build data structures for quick lookup
        categories_by_key: Dict[str, CategoriesTable] = {}
        categories_by_name: Dict[str, CategoriesTable] = {}
        source_cat_map: Dict[Tuple[str, ...], CategoryMappingsTable] = {}

        for category, mapping in category_mappings:
            categories_by_key[category.key] = category
            if category.title:
                categories_by_name[category.title] = category
            if mapping:
                source_tuple = tuple(mapping.source)
                source_cat_map[source_tuple] = mapping

        expected_category_keys = ["electronics_0", "computers_1", "laptops_2"]

        result = get_categories_for_market_info(
            offer_cats, categories_by_key, categories_by_name, source_cat_map
        )

        self.assertEqual(result, expected_category_keys)

    def test_no_mappings_direct_match(self):
        offer_cats = ["Home", "Kitchen", "Appliances"]

        category_mappings = [
            (
                CategoriesTable(key="home_0", level=0, parent=None, title="Home"),
                None,
            ),
            (
                CategoriesTable(
                    key="kitchen_1", level=1, parent="home_0", title="Kitchen"
                ),
                None,
            ),
            (
                CategoriesTable(
                    key="appliances_2", level=2, parent="kitchen_1", title="Appliances"
                ),
                None,
            ),
        ]

        # Build data structures for quick lookup
        categories_by_key: Dict[str, CategoriesTable] = {}
        categories_by_name: Dict[str, CategoriesTable] = {}
        source_cat_map: Dict[Tuple[str, ...], CategoryMappingsTable] = {}

        for category, mapping in category_mappings:
            categories_by_key[category.key] = category
            if category.title:
                categories_by_name[category.title] = category
            if mapping:
                source_tuple = tuple(mapping.source)
                source_cat_map[source_tuple] = mapping

        expected_category_keys = ["home_0", "kitchen_1", "appliances_2"]

        result = get_categories_for_market_info(
            offer_cats, categories_by_key, categories_by_name, source_cat_map
        )
        self.assertEqual(result, expected_category_keys)

    def test_mapping_and_direct_match(self):
        offer_cats = ["Books", "Fiction"]

        category_mappings = [
            (
                CategoriesTable(key="books_0", level=0, parent=None, title="Books"),
                CategoryMappingsTable(source=["Books"], target="books_0"),
            ),
            (
                CategoriesTable(
                    key="fiction_1", level=1, parent="books_0", title="Fiction"
                ),
                None,
            ),
        ]

        # Build data structures for quick lookup
        categories_by_key: Dict[str, CategoriesTable] = {}
        categories_by_name: Dict[str, CategoriesTable] = {}
        source_cat_map: Dict[Tuple[str, ...], CategoryMappingsTable] = {}

        for category, mapping in category_mappings:
            categories_by_key[category.key] = category
            if category.title:
                categories_by_name[category.title] = category
            if mapping:
                source_tuple = tuple(mapping.source)
                source_cat_map[source_tuple] = mapping

        expected_category_keys = ["books_0", "fiction_1"]

        result = get_categories_for_market_info(
            offer_cats, categories_by_key, categories_by_name, source_cat_map
        )
        self.assertEqual(result, expected_category_keys)


if __name__ == "__main__":
    unittest.main()
