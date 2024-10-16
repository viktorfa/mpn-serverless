from typing import Optional
from sqlalchemy import create_engine
from config.vars import POSTGRES_URL


# Create an engine and metadata
engine = create_engine(POSTGRES_URL, pool_pre_ping=True)


def get_pg_engine(db_url: Optional[str] = None):
    if db_url:
        return create_engine(db_url, pool_pre_ping=True)
    return engine


def execute_statement(stmt):
    with engine.connect() as connection:
        transaction = connection.begin()
        try:
            result = connection.execute(stmt)
            transaction.commit()
            return result
        except Exception as e:
            transaction.rollback()
            print(f"An error occurred: {e}")
            raise e
