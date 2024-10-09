import logging
from datetime import datetime
from typing import Dict, Sequence
import re
from string import capwords
from uuid import UUID
from slugify import slugify
from sqlalchemy.orm import Session
import pydash

from storage.postgres.common import get_pg_engine
from storage.postgres.pydantic_models import PgOffer
from amp_types.amp_product import ProcessedMpnOffer
from storage.postgres.postgres_tables import (
    BrandsTable,
    DealersTable,
    OfferPricesTable,
    OffersTable,
    VendorsTable,
)

pg_engine = get_pg_engine()


def processed_offer_to_pg_offer(offer: ProcessedMpnOffer) -> PgOffer:
    uri = f"{offer['namespace']}:{offer['provenanceId']}"
    dealer_key = slugify(offer["dealer"], separator="_")
    return PgOffer(
        uri=uri,
        dealer_key=dealer_key,
        brand=offer.get("brand"),
        brand_key=offer.get("brandKey"),
        vendor_key=offer.get("vendorKey"),
        href=offer["href"],
        image=offer.get("imageUrl"),
        mpn_stock=offer.get("mpn"),
        price=offer["pricing"].get("price"),
        currency=offer["pricing"].get("currency"),
        pre_price=offer["pricing"].get("prePrice"),
        price_unit=offer["pricing"].get("priceUnit"),
        provenance=offer["provenance"],
        provenance_id=offer["provenanceId"],
        quantity_unit=pydash.get(offer, ["quantity", "size", "unit", "symbol"]),
        quantity_amount=pydash.get(offer, ["quantity", "size", "amount", "max"]),
        quantity_standard_amount=pydash.get(
            offer, ["quantity", "size", "standard", "max"]
        ),
        context=offer["context"],
        subtitle=offer.get("subtitle"),
        title=offer["title"],
        valid_from=offer["validFrom"],
        valid_through=offer["validThrough"],
        value_unit=pydash.get(offer, ["value", "size", "unit", "symbol"]),
        value_amount=pydash.get(offer, ["value", "size", "amount", "max"]),
        value_standard_amount=pydash.get(offer, ["value", "size", "standard", "max"]),
        description=offer.get("description"),
        short_description=offer.get("short_description"),
        item_condition=offer.get("itemCondition"),
        mpn=offer.get("mpn"),
        upc=offer.get("upc"),
        ahref=offer.get("ahref"),
        is_partner=offer.get("isPartner"),
        market=offer["market"],
        is_promotion_restricted=offer.get("isPromoted"),
        scrape_batch_id=offer["scrapeBatchId"],
    )


def get_offer_price_object_from_processed_offer(
    offer: ProcessedMpnOffer, scrape_time: datetime
):
    uri = f"{offer['namespace']}:{offer['provenanceId']}"
    return {
        "uri": uri,
        "price": offer["pricing"]["price"],
        "recorded_at": scrape_time,
    }


def upsert_brands_postgres(offers: Sequence[ProcessedMpnOffer]):
    from sqlalchemy.dialects.postgresql import insert as pg_insert

    brand_entries = []
    brand_keys = set()

    for offer in offers:
        brand_title = offer.get("brand")
        brand_key = offer.get("brandKey")
        market = offer["market"]

        if brand_key and brand_key not in brand_keys:
            brand_keys.add(brand_key)
            brand_entries.append(
                {"key": brand_key, "title": brand_title, "market": market}
            )

    if len(brand_entries) == 0:
        return 0

    with Session(pg_engine) as session:
        try:
            # Prepare the insert statement with conflict handling
            stmt = pg_insert(BrandsTable.__table__).values(brand_entries)
            stmt = stmt.on_conflict_do_nothing(index_elements=["key", "market"])

            # Execute the statement
            session.execute(stmt)
            session.commit()
            print(f"Upserted {len(brand_entries)} brands")
        except Exception as e:
            session.rollback()
            print(f"An error occurred: {e}")

        return len(brand_entries)


def upsert_vendors_postgres(offers: Sequence[ProcessedMpnOffer]):
    from sqlalchemy.dialects.postgresql import insert as pg_insert

    vendor_entries = []
    vendor_keys = set()

    for offer in offers:
        vendor_title = offer.get("vendor")
        vendor_key = offer.get("vendorKey")
        market = offer["market"]

        if vendor_key and vendor_key not in vendor_keys:
            vendor_keys.add(vendor_key)
            vendor_entries.append(
                {"key": vendor_key, "title": vendor_title, "market": market}
            )

    if len(vendor_entries) == 0:
        return 0

    with Session(pg_engine) as session:
        try:
            # Prepare the insert statement with conflict handling
            stmt = pg_insert(VendorsTable.__table__).values(vendor_entries)
            stmt = stmt.on_conflict_do_nothing(index_elements=["key", "market"])

            # Execute the statement
            session.execute(stmt)
            session.commit()
            print(f"Upserted {len(vendor_entries)} vendors")
        except Exception as e:
            session.rollback()
            print(f"An error occurred: {e}")

        return len(vendor_entries)


def get_dealer_title(dealer: str) -> str:
    # Remove "www."
    dealer = re.sub(r"www\.", "", dealer)
    dealer = re.sub(r"www_", "", dealer)

    # Remove country code suffixes preceded by an underscore
    dealer = re.sub(r"_(no|se|de|dk|fi|us|uk|sg|th|nl|fr|es|it|pl|au)$", "", dealer)

    # Replace underscores with spaces
    dealer = dealer.replace("_", " ")

    # Capitalize each word
    return capwords(dealer)


def upsert_dealers_postgres(offers: Sequence[ProcessedMpnOffer]):
    from sqlalchemy.dialects.postgresql import insert as pg_insert

    dealer_entries = []
    dealer_keys = set()

    for offer in offers:
        dealer_key = slugify(offer["dealer"], separator="_")
        dealer_title = get_dealer_title(dealer_key)

        market = offer["market"]
        is_partner = offer.get("isPartner", False) or False

        if dealer_key and dealer_key not in dealer_keys:
            dealer_keys.add(dealer_key)
            dealer_entries.append(
                {
                    "key": dealer_key,
                    "title": dealer_title,
                    "market": market,
                    "is_partner": is_partner,
                }
            )

    with Session(pg_engine) as session:
        try:
            # Prepare the insert statement with conflict handling
            stmt = pg_insert(DealersTable.__table__).values(dealer_entries)
            stmt = stmt.on_conflict_do_update(
                index_elements=["key", "market"],
                set_={"is_partner": stmt.excluded.is_partner},
            )

            # Execute the statement
            session.execute(stmt)
            session.commit()
            print(f"Upserted {len(dealer_entries)} dealers")
        except Exception as e:
            session.rollback()
            print(f"An error occurred: {e}")

        return len(dealer_entries)


def upsert_offers_postgres(
    session: Session,
    offers: Sequence[ProcessedMpnOffer],
    offer_to_product_id: Dict[str, UUID],
) -> int:
    from sqlalchemy.dialects.postgresql import insert as pg_insert

    pg_offers = [processed_offer_to_pg_offer(offer) for offer in offers]

    # Prepare the insert statement with the list of offers
    stmt = pg_insert(OffersTable.__table__).values(
        [
            {**offer.model_dump(), "product_id": offer_to_product_id[offer.uri]}
            for offer in pg_offers
        ]
    )

    # Define the `ON CONFLICT` clause
    update_fields = {
        field: getattr(stmt.excluded, field)
        for field in PgOffer.model_fields.keys()
        if field != "uri"  # Exclude the primary key field
    }

    stmt = stmt.on_conflict_do_update(
        index_elements=["uri"],  # Columns to check for conflict
        set_=update_fields,
    )

    result = session.execute(stmt)
    print(f"Upserted {result.rowcount} offers")
    return result.rowcount


def upsert_offer_prices_batch(session: Session, offer_prices_batch):
    from sqlalchemy.dialects.postgresql import insert as pg_insert

    # Create the upsert (insert on conflict) statement
    stmt = (
        pg_insert(OfferPricesTable.__table__)
        .values(offer_prices_batch)
        .on_conflict_do_nothing(index_elements=["uri", "recorded_at"])
    )
    session.execute(stmt)

    logging.info(f"Upserted {len(offer_prices_batch)} offer prices")
