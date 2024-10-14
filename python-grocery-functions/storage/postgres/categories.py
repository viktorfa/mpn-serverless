from typing import List, Tuple, Dict
import logging

from storage.migrate.migrate_categories import CategoriesTable
from storage.postgres.postgres_tables import CategoryMappingsTable


def get_categories_for_market_info(
    offer_cats: List[str],
    categories_by_key: Dict[str, CategoriesTable],
    categories_by_name: Dict[str, CategoriesTable],
    source_cat_map: Dict[Tuple[str, ...], CategoryMappingsTable],
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

    matched_categories = []
    category_name_to_mappings: Dict[str, List[CategoryMappingsTable]] = {}

    for mapping in source_cat_map.values():
        for source_cat in mapping.source:
            category_name_to_mappings.setdefault(source_cat, []).append(mapping)

    # Collect mappings based on offer categories
    possible_mappings = []
    for cat in offer_cats:
        mappings = category_name_to_mappings.get(cat, [])
        possible_mappings.extend(mappings)

    # Filter mappings that match the offer categories completely
    for mapping in possible_mappings:
        if all(cat in offer_cats for cat in mapping.source):
            target_category = categories_by_key.get(mapping.target)
            if target_category:
                matched_categories.append(target_category)

    # Proceed with direct matches as before
    for offer_cat in offer_cats:
        category = categories_by_name.get(offer_cat)
        if category:
            matched_categories.append(category)

    # Rest of the function remains the same
    if not matched_categories:
        logging.debug(
            f"No matching categories found for offer categories: {offer_cats}"
        )
        return []

    matched_category = max(matched_categories, key=lambda c: c.level)
    # Build the category keys by traversing up the parent chain
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
