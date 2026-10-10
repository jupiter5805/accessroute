from sqlalchemy import text

from src.accessroute.database.db import engine


def initialise_database():
    with engine.begin() as connection:
        connection.execute(
            text("CREATE EXTENSION IF NOT EXISTS postgis")
        )

        connection.execute(
            text("""
                CREATE TABLE IF NOT EXISTS route_nodes (
                    id VARCHAR PRIMARY KEY,
                    name VARCHAR NOT NULL,
                    latitude DOUBLE PRECISION NOT NULL,
                    longitude DOUBLE PRECISION NOT NULL,
                    location GEOGRAPHY(POINT, 4326) NOT NULL
                )
            """)
        )

        connection.execute(
            text("""
                CREATE TABLE IF NOT EXISTS route_edges (
                    id BIGSERIAL PRIMARY KEY,
                    source VARCHAR NOT NULL REFERENCES route_nodes(id),
                    target VARCHAR NOT NULL REFERENCES route_nodes(id),
                    distance_m DOUBLE PRECISION NOT NULL,
                    gradient DOUBLE PRECISION NOT NULL,
                    has_stairs BOOLEAN NOT NULL,
                    has_lift BOOLEAN NOT NULL,
                    surface VARCHAR NOT NULL,
                    wheelchair_accessible BOOLEAN NOT NULL
                )
            """)
        )


if __name__ == "__main__":
    initialise_database()
    print("AccessRoute database initialised.")
