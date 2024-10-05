from sqlalchemy import create_engine
from config.vars import POSTGRES_URL


# Create an engine and metadata
engine = create_engine(POSTGRES_URL)


def get_pg_engine():
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
