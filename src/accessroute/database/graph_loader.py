import networkx as nx
from sqlalchemy import text

from src.accessroute.database.db import engine


def load_graph_from_postgres() -> nx.DiGraph:
    graph = nx.DiGraph()

    with engine.connect() as connection:
        nodes = connection.execute(
            text("""
                SELECT id, name, latitude, longitude
                FROM route_nodes
            """)
        )

        for row in nodes.mappings():
            graph.add_node(
                row["id"],
                name=row["name"],
                latitude=row["latitude"],
                longitude=row["longitude"],
            )

        edges = connection.execute(
            text("""
                SELECT
                    source,
                    target,
                    distance_m,
                    gradient,
                    has_stairs,
                    has_lift,
                    surface,
                    wheelchair_accessible
                FROM route_edges
                ORDER BY distance_m
            """)
        )

        for row in edges.mappings():
            source = row["source"]
            target = row["target"]

            # If OSM contains parallel edges between the same nodes,
            # keep the shortest one for this first routing version.
            if graph.has_edge(source, target):
                if graph[source][target]["distance_m"] <= row["distance_m"]:
                    continue

            graph.add_edge(
                source,
                target,
                distance_m=row["distance_m"],
                gradient=row["gradient"],
                has_stairs=row["has_stairs"],
                has_lift=row["has_lift"],
                surface=row["surface"],
                wheelchair_accessible=row["wheelchair_accessible"],
            )

    return graph


def find_nearest_node(latitude: float, longitude: float) -> str:
    with engine.connect() as connection:
        result = connection.execute(
            text("""
                SELECT id
                FROM route_nodes
                ORDER BY ST_Distance(
                    location,
                    ST_SetSRID(
                        ST_MakePoint(:longitude, :latitude),
                        4326
                    )::geography
                )
                LIMIT 1
            """),
            {
                "latitude": latitude,
                "longitude": longitude,
            },
        )

        node_id = result.scalar()

    if node_id is None:
        raise ValueError("No routing nodes available.")

    return str(node_id)
