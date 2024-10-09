from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
import json
from dateutil.parser import isoparse

from config.vars import POSTGRES_URL
from storage.postgres.postgres_tables import HandleConfigsTable
from util.mappings import get_offer_context_from_site_collection


def migrate_data(json_file_path, database_url):
    # Create the database engine
    engine = create_engine(database_url)

    # Read the JSON file
    with open(json_file_path, "r") as f:
        data = json.load(f)

    with Session(engine) as session:
        try:
            for item in data:
                created_at_raw = item.get("createdAt")
                if not created_at_raw:
                    created_at_raw = None
                elif type(created_at_raw) is dict:
                    created_at_raw = created_at_raw.get("$date")
                updated_at_raw = item.get("updatedAt")
                if not updated_at_raw:
                    updated_at_raw = None
                elif type(updated_at_raw) is dict:
                    updated_at_raw = updated_at_raw.get("$date")

                # Map the fields
                mongo_id = item["_id"]["$oid"]
                created_at = isoparse(created_at_raw) if created_at_raw else None
                updated_at = isoparse(updated_at_raw) if updated_at_raw else None
                provenance = item.get("provenance")
                additional_config = item.get("additionalConfig", {})
                field_mapping = item.get("fieldMapping")
                extract_quantity_fields = item.get("extractQuantityFields")
                context = get_offer_context_from_site_collection(
                    item.get("collection_name")
                )
                namespace = item.get("namespace")
                is_partner = item.get("is_partner", False)
                market = item.get("market")

                # Create the Spider instance
                config = HandleConfigsTable(
                    mongo_id=mongo_id,
                    created_at=created_at,
                    updated_at=updated_at,
                    provenance=provenance,
                    additional_config=additional_config,
                    extract_quantity_fields=extract_quantity_fields,
                    field_mapping=field_mapping,
                    context=context,
                    namespace=namespace,
                    is_partner=is_partner,
                    market=market,
                )

                # Add to session
                session.add(config)

            # Commit the session
            session.commit()
        except:
            session.rollback()
            raise


if __name__ == "__main__":
    json_file_path = Path(__file__).parent.parent / "strapi.handleconfigs.json"
    json_file = str(json_file_path)

    migrate_data(json_file, POSTGRES_URL)
