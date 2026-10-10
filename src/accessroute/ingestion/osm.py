import osmnx as ox
from sqlalchemy import text

from src.accessroute.database.db import engine


# Manchester city centre
CENTRE = (53.4808, -2.2426)
RADIUS_METRES = 3000


def normalise_value(value, default=None):
    if isinstance(value, list):
        return value[0] if value else default
    return value if value is not None else default


def ingest_osm_network():
    print("Downloading Manchester walking network from OpenStreetMap...")

    graph = ox.graph_from_point(
        CENTRE,
        dist=RADIUS_METRES,
        network_type="walk",
        simplify=True,
    )

    # Keep the main connected walking network.
    graph = ox.truncate.largest_component(
        graph,
        strongly=False,
    )

    print(
        f"Downloaded {graph.number_of_nodes()} nodes "
        f"and {graph.number_of_edges()} edges"
    )

    if graph.number_of_nodes() < 100:
        raise RuntimeError(
            "OSM download returned too few nodes. "
            "Expected a real Manchester street network."
        )

    with engine.begin() as connection:
        connection.execute(text("DELETE FROM route_edges"))
        connection.execute(text("DELETE FROM route_nodes"))

        for node_id, data in graph.nodes(data=True):
            latitude = float(data["y"])
            longitude = float(data["x"])

            name = normalise_value(
                data.get("name"),
                f"OSM node {node_id}",
            )

            connection.execute(
                text("""
                    INSERT INTO route_nodes (
                        id,
                        name,
                        latitude,
                        longitude,
                        location
                    )
                    VALUES (
                        :id,
                        :name,
                        :latitude,
                        :longitude,
                        ST_SetSRID(
                            ST_MakePoint(:longitude, :latitude),
                            4326
                        )::geography
                    )
                    ON CONFLICT (id) DO NOTHING
                """),
                {
                    "id": str(node_id),
                    "name": str(name),
                    "latitude": latitude,
                    "longitude": longitude,
                },
            )

        inserted_edges = 0

        for source, target, key, data in graph.edges(
            keys=True,
            data=True,
        ):
            highway = str(
                normalise_value(
                    data.get("highway"),
                    "unknown",
                )
            ).lower()

            surface = str(
                normalise_value(
                    data.get("surface"),
                    "unknown",
                )
            ).lower()

            wheelchair = str(
                normalise_value(
                    data.get("wheelchair"),
                    "unknown",
                )
            ).lower()

            distance_m = float(data.get("length", 1.0))

            has_stairs = highway == "steps"

            has_lift = highway == "elevator"

            wheelchair_accessible = (
                wheelchair != "no"
                and not has_stairs
            )

            connection.execute(
                text("""
                    INSERT INTO route_edges (
                        source,
                        target,
                        distance_m,
                        gradient,
                        has_stairs,
                        has_lift,
                        surface,
                        wheelchair_accessible
                    )
                    VALUES (
                        :source,
                        :target,
                        :distance_m,
                        0.0,
                        :has_stairs,
                        :has_lift,
                        :surface,
                        :wheelchair_accessible
                    )
                """),
                {
                    "source": str(source),
                    "target": str(target),
                    "distance_m": distance_m,
                    "has_stairs": has_stairs,
                    "has_lift": has_lift,
                    "surface": surface,
                    "wheelchair_accessible": wheelchair_accessible,
                },
            )

            inserted_edges += 1

    print("\nOpenStreetMap ingestion complete.")
    print("Nodes loaded:", graph.number_of_nodes())
    print("Edges loaded:", inserted_edges)


if __name__ == "__main__":
    ingest_osm_network()
