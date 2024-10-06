from typing import List, Set, Dict, Tuple
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import case

from storage.postgres.postgres_tables import OfferHasGtinTable, GtinsTable


def insert_new_gtins(
    session: Session, new_gtins: Set[str], gtin_to_product_map: Dict[str, UUID]
) -> None:
    from sqlalchemy.dialects.postgresql import insert as pg_insert

    if new_gtins:
        gtins_to_insert = [
            {
                "gtin": gtin,
                "product_id": gtin_to_product_map[gtin],
            }
            for gtin in new_gtins
        ]
        gtin_insert_stmt = (
            pg_insert(GtinsTable.__table__)
            .values(gtins_to_insert)
            .on_conflict_do_nothing(index_elements=["gtin"])
        )
        session.execute(gtin_insert_stmt)
        print(f"Inserted {len(gtins_to_insert)} new GTINs.")


def update_gtins(session: Session, gtins_to_update: List[Dict[str, str]]) -> None:
    if gtins_to_update:
        # Prepare data for bulk update
        gtin_update_mapping: Dict[str, str] = {
            item["gtin"]: item["product_id"] for item in gtins_to_update
        }
        gtins_to_update_list = list(gtin_update_mapping.keys())

        # Build a CASE statement for bulk update
        case_stmt = case(
            *[
                (GtinsTable.gtin == gtin, gtin_update_mapping[gtin])
                for gtin in gtins_to_update_list
            ],
            else_=GtinsTable.product_id,
        )

        update_stmt = (
            GtinsTable.__table__.update()
            .where(GtinsTable.gtin.in_(gtins_to_update_list))
            .values(product_id=case_stmt)
        )
        session.execute(update_stmt)
        print(f"Updated {len(gtins_to_update)} GTINs to new product IDs.")


def upsert_offer_has_gtin(
    session: Session, offer_has_gtin_list: List[Dict[str, str]]
) -> None:
    from sqlalchemy.dialects.postgresql import insert as pg_insert

    if offer_has_gtin_list:
        offer_has_gtin_stmt = (
            pg_insert(OfferHasGtinTable.__table__)
            .values(offer_has_gtin_list)
            .on_conflict_do_nothing(index_elements=["offer_uri", "gtin"])
        )
        session.execute(offer_has_gtin_stmt)
        print(f"Upserted {len(offer_has_gtin_list)} offer_has_gtin entries.")


def find_existing_gtins(
    session: Session, offer_gtins: Set[str]
) -> Tuple[Dict[str, UUID], Set[str], Set[str]]:
    existing_gtin_rows = (
        session.query(GtinsTable).filter(GtinsTable.gtin.in_(offer_gtins)).all()
    )

    print(f"Found {len(existing_gtin_rows)} existing GTINs.")

    gtin_to_product_map: Dict[str, UUID] = {
        row.gtin: UUID(str(row.product_id))
        for row in existing_gtin_rows
        if bool(row.product_id)
    }
    existing_gtins: Set[str] = set(gtin_to_product_map.keys())
    new_gtins: Set[str] = offer_gtins - existing_gtins

    return gtin_to_product_map, existing_gtins, new_gtins
