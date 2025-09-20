import json
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from config.vars import POSTGRES_URL
from storage.postgres.postgres_tables import CategoryMappingsTable


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
                context = item.get("context")
                dealer_key = item.get("dealer")
                source = item.get("source")
                target = item.get("target")

                # Create the Spider instance
                config = CategoryMappingsTable(
                    context=context,
                    dealer_key=dealer_key,
                    source=source,
                    target=target,
                )

                # Add to session
                session.add(config)

            # Commit the session
            session.commit()
        except:
            session.rollback()
            raise


if __name__ == "__main__":
    json_file_path = Path(__file__).parent.parent / "strapi.mpncategorymappings.json"
    json_file = str(json_file_path)

    migrate_data(json_file, POSTGRES_URL)
