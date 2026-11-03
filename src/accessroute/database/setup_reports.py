from sqlalchemy import text

from src.accessroute.database.db import engine


def setup_reports():
    with engine.begin() as connection:
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS barrier_reports (
                id BIGSERIAL PRIMARY KEY,

                latitude DOUBLE PRECISION NOT NULL,
                longitude DOUBLE PRECISION NOT NULL,

                report_type VARCHAR(40) NOT NULL,
                description TEXT NOT NULL,

                status VARCHAR(20) NOT NULL
                    DEFAULT 'pending'
                    CHECK (
                        status IN (
                            'pending',
                            'verified',
                            'rejected'
                        )
                    ),

                location GEOGRAPHY(POINT, 4326)
                    NOT NULL,

                created_at TIMESTAMPTZ NOT NULL
                    DEFAULT NOW(),

                CHECK (latitude BETWEEN -90 AND 90),
                CHECK (longitude BETWEEN -180 AND 180)
            )
        """))

        connection.execute(text("""
            CREATE INDEX IF NOT EXISTS
                idx_barrier_reports_location
            ON barrier_reports
            USING GIST(location)
        """))

    print("AccessRoute barrier reporting database ready.")


if __name__ == "__main__":
    setup_reports()
