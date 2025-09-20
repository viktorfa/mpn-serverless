from sqlalchemy.orm import Session
from storage.postgres.common import get_pg_engine
from storage.postgres.postgres_tables import SpiderConfigsTable

pg_engine = get_pg_engine()


def get_spider_config_by_id(config_id: str):
    """Get a spider config by its ID."""
    with Session(pg_engine) as session:
        try:
            result = session.query(SpiderConfigsTable).filter(
                SpiderConfigsTable.id == config_id
            ).one_or_none()
            return result
        except Exception as e:
            print(f"An error occurred: {e}")
            raise e


def get_spider_config_by_mongo_id(mongo_id: str):
    """Get a spider config by its original MongoDB ID."""
    with Session(pg_engine) as session:
        try:
            result = session.query(SpiderConfigsTable).filter(
                SpiderConfigsTable.mongo_id == mongo_id
            ).one_or_none()
            return result
        except Exception as e:
            print(f"An error occurred: {e}")
            raise e