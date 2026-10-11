import srtm
from sqlalchemy import text

from src.accessroute.database.db import engine


CACHE_DIR = ".cache/srtm"


def calculate_gradient(
    source_elevation: float,
    target_elevation: float,
    distance_m: float,
) -> float:
    if distance_m <= 0:
        return 0.0

    return abs(target_elevation - source_elevation) / distance_m


def ensure_elevation_columns():
    with engine.begin() as connection:
        connection.execute(
            text("""
                ALTER TABLE route_nodes
                ADD COLUMN IF NOT EXISTS elevation_m
                DOUBLE PRECISION
            """)
        )

        connection.execute(
            text("""
                ALTER TABLE route_nodes
                ADD COLUMN IF NOT EXISTS elevation_source
                VARCHAR
            """)
        )

        connection.execute(
            text("""
                ALTER TABLE route_edges
                ADD COLUMN IF NOT EXISTS raw_gradient
                DOUBLE PRECISION
            """)
        )

        connection.execute(
            text("""
                ALTER TABLE route_edges
                ADD COLUMN IF NOT EXISTS gradient_reliable
                BOOLEAN DEFAULT TRUE
            """)
        )

        connection.execute(
            text("""
                ALTER TABLE route_edges
                ADD COLUMN IF NOT EXISTS gradient_source
                VARCHAR
            """)
        )


def fetch_nodes():
    with engine.connect() as connection:
        rows = connection.execute(
            text("""
                SELECT id, latitude, longitude
                FROM route_nodes
                ORDER BY id
            """)
        )

        return [dict(row) for row in rows.mappings()]


def write_batch(records):
    with engine.begin() as connection:
        connection.execute(
            text("""
                UPDATE route_nodes
                SET
                    elevation_m = :elevation,
                    elevation_source = :source
                WHERE id = :id
            """),
            records,
        )


def update_elevations():
    elevation_data = srtm.get_data(
        local_cache_dir=CACHE_DIR
    )

    nodes = fetch_nodes()

    print(
        f"Calculating SRTM elevation for "
        f"{len(nodes)} nodes..."
    )

    batch = []

    for index, node in enumerate(nodes, start=1):
        elevation = elevation_data.get_elevation(
            node["latitude"],
            node["longitude"],
        )

        if elevation is None:
            continue

        batch.append(
            {
                "id": node["id"],
                "elevation": float(elevation),
                "source": "NASA_SRTM",
            }
        )

        if len(batch) >= 1000:
            write_batch(batch)
            batch = []

            print(
                f"Elevation progress: "
                f"{index}/{len(nodes)}"
            )

    if batch:
        write_batch(batch)

    print(
        f"Elevation progress: "
        f"{len(nodes)}/{len(nodes)}"
    )


def update_edge_gradients():
    print("Calculating street gradients...")

    with engine.begin() as connection:
        connection.execute(
            text("""
                WITH grades AS (
                    SELECT
                        e.id,
                        e.distance_m,
                        ABS(
                            target.elevation_m
                            - source.elevation_m
                        ) / NULLIF(e.distance_m, 0)
                        AS raw_grade

                    FROM route_edges e

                    JOIN route_nodes source
                        ON e.source = source.id

                    JOIN route_nodes target
                        ON e.target = target.id

                    WHERE
                        source.elevation_m IS NOT NULL
                        AND target.elevation_m IS NOT NULL
                )

                UPDATE route_edges e

                SET
                    raw_gradient = grades.raw_grade,

                    gradient =
                        CASE
                            WHEN grades.distance_m >= 30
                            AND grades.raw_grade <= 0.35
                            THEN grades.raw_grade
                            ELSE 0
                        END,

                    gradient_reliable =
                        CASE
                            WHEN grades.distance_m >= 30
                            AND grades.raw_grade <= 0.35
                            THEN TRUE
                            ELSE FALSE
                        END,

                    gradient_source =
                        CASE
                            WHEN grades.distance_m < 30
                            THEN 'SRTM_UNRELIABLE_SHORT_EDGE'

                            WHEN grades.raw_grade > 0.35
                            THEN 'SRTM_OUTLIER'

                            ELSE 'NASA_SRTM'
                        END

                FROM grades

                WHERE e.id = grades.id
            """)
        )


def ingest_elevation():
    ensure_elevation_columns()

    update_elevations()

    update_edge_gradients()

    print(
        "SRTM elevation and gradient "
        "pipeline complete."
    )


if __name__ == "__main__":
    ingest_elevation()
