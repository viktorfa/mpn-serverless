import json
from pathlib import Path

from dateutil.parser import isoparse
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from config.vars import POSTGRES_URL
from storage.postgres.postgres_tables import SpiderConfigsTable


def migrate_data(json_file_path, database_url):
    # Create the database engine
    engine = create_engine(database_url)

    # Read the JSON file
    with open(json_file_path) as f:
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
                use_fargate = item.get("use_fargate", False)
                settings = item.get("settings", {})
                crawl_kwargs = item.get("crawl_kwargs")
                other_kwargs = item.get("other_kwargs")
                spider_name = item.get("spider_name")
                created_at = isoparse(created_at_raw) if created_at_raw else None
                updated_at = isoparse(updated_at_raw) if updated_at_raw else None
                rate = item.get("rate")
                cron = item.get("cron")
                region = item.get("region")
                enabled = item.get("enabled", False)

                # Create the Spider instance
                spider = SpiderConfigsTable(
                    mongo_id=mongo_id,
                    use_fargate=use_fargate,
                    settings=settings,
                    crawl_kwargs=crawl_kwargs,
                    other_kwargs=other_kwargs,
                    spider_name=spider_name,
                    created_at=created_at,
                    updated_at=updated_at,
                    rate=rate,
                    cron=cron,
                    region=region,
                    enabled=enabled,
                )

                # Add to session
                session.add(spider)

            # Commit the session
            session.commit()
        except:
            session.rollback()
            raise


if __name__ == "__main__":
    json_file_path = Path(__file__).parent.parent / "strapi.spiderconfigs.json"
    json_file = str(json_file_path)

    migrate_data(json_file, POSTGRES_URL)
