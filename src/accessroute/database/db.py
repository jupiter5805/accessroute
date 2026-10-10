import os

from sqlalchemy import create_engine, text


DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://accessroute:accessroute_dev@localhost:5434/accessroute",
)

engine = create_engine(DATABASE_URL)


def check_database_connection() -> bool:
    with engine.connect() as connection:
        result = connection.execute(text("SELECT 1"))
        return result.scalar() == 1


def check_postgis() -> str:
    with engine.connect() as connection:
        result = connection.execute(text("SELECT PostGIS_Version()"))
        return result.scalar()
