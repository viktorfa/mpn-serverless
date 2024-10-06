import logging
from typing import List, Set, Optional, Dict, Tuple
from uuid import UUID
from sqlalchemy.orm import Session

from storage.migrate.migrate_categories import CategoriesTable
from storage.postgres.pydantic_models import DbMarketInfo, MarketInfo
from amp_types.amp_product import ProcessedMpnOffer
from storage.postgres.postgres_tables import (
    CategoryMappingsTable,
    ProductMarketInfoTable,
)
from storage.postgres.utils import get_offer_from_gtin


def merge_market_info(existing: MarketInfo, new: MarketInfo) -> MarketInfo:
    return MarketInfo(
        market=existing.market or new.market,
        title=existing.title or new.title,
        description=existing.description or new.description,
        subtitle=existing.subtitle or new.subtitle,
        short_description=existing.short_description or new.short_description,
        brand_key=existing.brand_key or new.brand_key,
        vendor_key=existing.vendor_key or new.vendor_key,
        context=existing.context or new.context,
        category_key=existing.category_key or new.category_key,
    )


def collect_product_market_info_entries(
    session: Session,
    context: str,
    root_to_gtins: Dict[str, Set[str]],
    component_product_id: Dict[str, UUID],
    gtin_market_info_map: Dict[str, MarketInfo],
    gtin_offer_object_map: Dict[str, ProcessedMpnOffer],
) -> Dict[str, DbMarketInfo]:
    product_market_info_entries: Dict[str, DbMarketInfo] = {}

    existing_market_infos = (
        session.query(ProductMarketInfoTable)
        .filter(ProductMarketInfoTable.context == context)
        .filter(ProductMarketInfoTable.product_id.in_(component_product_id.values()))
        .all()
    )

    category_mappings = (
        session.query(CategoryMappingsTable, CategoriesTable)
        .join(
            CategoriesTable,
            (CategoryMappingsTable.context == CategoriesTable.context)
            & (CategoryMappingsTable.target == CategoriesTable.key),
        )
        .filter(CategoryMappingsTable.context == context)
        .all()
    )

    for root, component_gtins in root_to_gtins.items():
        product_id = component_product_id[root]
        # Get market info from one of the GTINs in the component
        new_market_info = MarketInfo(
            market="",
            title="",
            description=None,
            subtitle=None,
            short_description=None,
            brand_key=None,
            vendor_key=None,
            context=context,
            category_key=None,
        )
        for gtin in component_gtins:
            existing_market_info = next(
                (
                    mi
                    for mi in existing_market_infos
                    if UUID(str(mi.product_id)) == product_id
                ),
                None,
            )
            market_info_entry: Optional[MarketInfo] = gtin_market_info_map.get(gtin)
            if not market_info_entry:
                raise Exception(f"Market info not found for GTIN {gtin}")

            if category_mappings:
                offer = get_offer_from_gtin(gtin_offer_object_map, gtin)
                offer_cats = offer.get("categories")
                if offer_cats:
                    matched_categories: List[
                        Tuple[CategoryMappingsTable, CategoriesTable]
                    ] = []
                    for cat in offer_cats:
                        for mapping, category in category_mappings:
                            if cat in mapping.source:
                                matched_categories.append((mapping, category))
                                break
                    if matched_categories:
                        highest_level_matched_category = max(
                            matched_categories, key=lambda x: x[1].level
                        )

                        market_info_entry.category_key = str(
                            highest_level_matched_category[0].target
                        )
                        logging.debug(
                            f"Found category {market_info_entry.category_key} for GTIN {gtin}"
                        )

            new_market_info = merge_market_info(new_market_info, market_info_entry)
            entry = DbMarketInfo(
                product_id=product_id,
                **new_market_info.model_dump(),
            )

            if existing_market_info:
                if entry == existing_market_info:
                    continue

            product_market_info_entries[gtin] = entry

    return product_market_info_entries


def upsert_product_market_info(
    session: Session, product_market_info_entries: List[DbMarketInfo]
) -> None:
    from sqlalchemy.dialects.postgresql import insert as pg_insert

    if product_market_info_entries:
        # Remove duplicates based on (product_id, market)
        unique_entries_dict: Dict[Tuple[UUID, str], DbMarketInfo] = {
            (e.product_id, e.market): e for e in product_market_info_entries
        }
        unique_entries: List[DbMarketInfo] = list(unique_entries_dict.values())
        entries_to_insert = [entry.model_dump() for entry in unique_entries]
        product_market_info_stmt = pg_insert(ProductMarketInfoTable.__table__).values(
            entries_to_insert
        )
        update_columns = {
            "title": product_market_info_stmt.excluded.title,
            "description": product_market_info_stmt.excluded.description,
            "subtitle": product_market_info_stmt.excluded.subtitle,
            "short_description": product_market_info_stmt.excluded.short_description,
            "brand_key": product_market_info_stmt.excluded.brand_key,
            "vendor_key": product_market_info_stmt.excluded.vendor_key,
            "context": product_market_info_stmt.excluded.context,
            "category_key": product_market_info_stmt.excluded.category_key,
        }
        upsert_stmt = product_market_info_stmt.on_conflict_do_update(
            index_elements=["product_id", "market"], set_=update_columns
        )
        session.execute(upsert_stmt)

        print(f"Upserted {len(unique_entries)} product market info entries.")


def populate_market_info_with_categories(
    session: Session,
    context: str,
    product_market_info_entries: Dict[str, DbMarketInfo],
    gtin_offer_object_map: Dict[str, ProcessedMpnOffer],
) -> None:
    category_mappings = (
        session.query(CategoryMappingsTable)
        .filter(CategoryMappingsTable.context == context)
        .all()
    )

    if not category_mappings:
        return

    for gtin, market_info in product_market_info_entries.items():
        offer = get_offer_from_gtin(gtin_offer_object_map, gtin)
        offer_cats = offer.get("categories")
        if not offer_cats:
            continue

        matched_categories: List[CategoryMappingsTable] = []
        for cat in offer_cats:
            for mapping in category_mappings:
                if cat in mapping.source:
                    matched_categories.append(mapping)
                    break
        if not matched_categories:
            continue
        highest_level_matched_category = matched_categories[0]

        market_info.category_key = str(highest_level_matched_category.target)
        logging.debug(f"Found category {market_info.category_key} for GTIN {gtin}")

    return
