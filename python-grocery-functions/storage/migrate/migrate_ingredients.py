import json
from pathlib import Path

from dateutil.parser import isoparse
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from config.vars import POSTGRES_URL
from storage.postgres.postgres_tables import IngredientsTable


def migrate_data(json_file_path, database_url):
    # Create the database engine
    engine = create_engine(database_url)

    # Read the JSON file
    with open(json_file_path) as f:
        data = json.load(f)

    with Session(engine) as session:
        try:
            for item in data:
                # Map the fields
                created_at_raw = item.get("createdAt", {}).get("$date")
                created_at = isoparse(created_at_raw) if created_at_raw else None
                updated_at_raw = item.get("updatedAt", {}).get("$date")
                updated_at = isoparse(updated_at_raw) if updated_at_raw else None
                title = item.get("name")
                patterns = item.get("patterns", [])
                e_number = item.get("eNumber")
                short_description = item.get("shortDescription")
                processed_value = item.get("processedValue", 0)

                # Create the Spider instance
                config = IngredientsTable(
                    created_at=created_at,
                    updated_at=updated_at,
                    title=title,
                    patterns=patterns,
                    e_number=e_number,
                    short_description=short_description,
                    processed_value=processed_value,
                )

                # Add to session
                session.add(config)

            # Commit the session
            session.commit()
        except:
            session.rollback()
            raise


if __name__ == "__main__":
    json_file_path = Path(__file__).parent.parent / "strapi.ingredients.json"
    json_file = str(json_file_path)

    migrate_data(json_file, POSTGRES_URL)
