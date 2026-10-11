from sqlalchemy import text

from src.accessroute.database.db import engine


def get_count(connection, query: str) -> int:
    return int(connection.execute(text(query)).scalar() or 0)


def run_quality_checks():
    with engine.connect() as connection:
        metrics = {
            "nodes": get_count(
                connection,
                "SELECT COUNT(*) FROM route_nodes",
            ),
            "edges": get_count(
                connection,
                "SELECT COUNT(*) FROM route_edges",
            ),
            "missing_elevation": get_count(
                connection,
                """
                SELECT COUNT(*)
                FROM route_nodes
                WHERE elevation_m IS NULL
                """,
            ),
            "invalid_coordinates": get_count(
                connection,
                """
                SELECT COUNT(*)
                FROM route_nodes
                WHERE latitude NOT BETWEEN -90 AND 90
                   OR longitude NOT BETWEEN -180 AND 180
                """,
            ),
            "invalid_distance": get_count(
                connection,
                """
                SELECT COUNT(*)
                FROM route_edges
                WHERE distance_m <= 0
                """,
            ),
            "orphan_edges": get_count(
                connection,
                """
                SELECT COUNT(*)
                FROM route_edges e
                LEFT JOIN route_nodes s
                    ON e.source = s.id
                LEFT JOIN route_nodes t
                    ON e.target = t.id
                WHERE s.id IS NULL OR t.id IS NULL
                """,
            ),
            "extreme_used_gradients": get_count(
                connection,
                """
                SELECT COUNT(*)
                FROM route_edges
                WHERE gradient > 0.35
                """,
            ),
            "reliable_gradients": get_count(
                connection,
                """
                SELECT COUNT(*)
                FROM route_edges
                WHERE gradient_reliable = TRUE
                """,
            ),
        }

    reliable_ratio = (
        metrics["reliable_gradients"] / metrics["edges"]
        if metrics["edges"]
        else 0
    )

    with engine.connect() as connection:
        distance_row = connection.execute(
            text("""
                SELECT
                    COALESCE(SUM(distance_m), 0) AS total_distance,
                    COALESCE(
                        SUM(distance_m)
                        FILTER (WHERE gradient_reliable = TRUE),
                        0
                    ) AS reliable_distance
                FROM route_edges
            """)
        ).mappings().one()

    total_distance = float(distance_row["total_distance"])
    reliable_distance = float(distance_row["reliable_distance"])

    reliable_distance_ratio = (
        reliable_distance / total_distance
        if total_distance
        else 0
    )

    checks = {
        "network_has_nodes": metrics["nodes"] > 1000,
        "network_has_edges": metrics["edges"] > 2000,
        "all_nodes_have_elevation":
            metrics["missing_elevation"] == 0,
        "coordinates_valid":
            metrics["invalid_coordinates"] == 0,
        "edge_distances_valid":
            metrics["invalid_distance"] == 0,
        "no_orphan_edges":
            metrics["orphan_edges"] == 0,
        "no_extreme_used_gradients":
            metrics["extreme_used_gradients"] == 0,
        "gradient_distance_coverage_above_70_percent":
            reliable_distance_ratio >= 0.70,
    }

    print("\nACCESSROUTE DATA QUALITY")
    print("=" * 60)

    print(f"Nodes: {metrics['nodes']:,}")
    print(f"Edges: {metrics['edges']:,}")
    print(
        f"Reliable gradient edges: "
        f"{metrics['reliable_gradients']:,} "
        f"({reliable_ratio:.1%})"
    )

    print(
        f"Reliable gradient distance: "
        f"{reliable_distance / 1000:,.1f} km "
        f"({reliable_distance_ratio:.1%})"
    )

    print()

    for name, passed in checks.items():
        status = "PASS" if passed else "FAIL"
        print(f"{name}: {status}")

    failed = [
        name
        for name, passed in checks.items()
        if not passed
    ]

    if failed:
        raise RuntimeError(
            "Data quality failed: "
            + ", ".join(failed)
        )

    print("\nAll data-quality checks passed.")


if __name__ == "__main__":
    run_quality_checks()
