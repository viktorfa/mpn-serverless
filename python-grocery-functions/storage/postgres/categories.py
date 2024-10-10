from typing import List, Optional, Tuple, Dict
import logging

from storage.migrate.migrate_categories import CategoriesTable
from storage.postgres.postgres_tables import CategoryMappingsTable


def get_categories_for_market_info(
    offer_cats: List[str],
    category_mappings: List[Tuple[CategoriesTable, Optional[CategoryMappingsTable]]],
) -> List[str]:
    """
    Processes offer categories and category mappings to return a list of category keys
    for market information.

    Args:
        offer_cats (List[str]): The list of categories from the offer.
        category_mappings (List[Tuple[CategoriesTable, Optional[CategoryMappingsTable]]]):
            A list of tuples containing categories and optional category mappings.

    Returns:
        List[str]: A list of category keys or empty list if no matching categories are found.
    """
    if not offer_cats:
        return []

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

    matched_categories = []

    # Attempt to find mappings by reducing the offer categories
    offer_categories = offer_cats.copy()
    while len(offer_categories) > 0:
        map_source = source_cat_map.get(tuple(offer_categories))
        if map_source:
            # Found a mapping; get the target category
            target_category_key = map_source.target
            matched_category = categories_by_key.get(target_category_key)
            if matched_category:
                matched_categories.append(matched_category)
            else:
                logging.debug(f"No target category found for key {target_category_key}")
            # Do not break; continue to find more mappings
        offer_categories = offer_categories[:-1]

    # Attempt to match offer categories directly to category names
    for offer_cat in offer_cats:
        category = categories_by_name.get(offer_cat)
        if category:
            matched_categories.append(category)

    if not matched_categories:
        # No matching categories found
        logging.debug(
            f"No matching categories found for offer categories: {offer_cats}"
        )
        return []

    # Select the matched category with the highest level
    matched_category = max(matched_categories, key=lambda c: c.level)

    # Build the list of category keys by traversing up the parent chain
    category_keys = []
    current_category = matched_category
    while current_category:
        category_keys.insert(0, current_category.key)
        parent_key = current_category.parent
        if parent_key:
            current_category = categories_by_key.get(parent_key)
        else:
            current_category = None

    return category_keys
