import networkx as nx
from sqlalchemy import text

from src.accessroute.database.db import engine
from src.accessroute.routing import (
    NoAccessibleRouteError,
    build_accessible_graph,
)


def attach_ml_scores(graph):
    """
    Attach persisted ML risk scores to the NetworkX graph.

    For parallel OSM edges, use the shortest edge to match
    the behaviour of the PostgreSQL graph loader.
    """

    query = text("""
        SELECT DISTINCT ON (
            e.source,
            e.target
        )
            e.source,
            e.target,
            scores.ml_risk_score,
            scores.is_anomaly

        FROM route_edges e

        JOIN route_edge_ml_scores scores
            ON scores.edge_id = e.id

        ORDER BY
            e.source,
            e.target,
            e.distance_m ASC
    """)

    with engine.connect() as connection:
        rows = connection.execute(
            query
        ).mappings().all()

    attached = 0

    for row in rows:
        source = str(row["source"])
        target = str(row["target"])

        if graph.has_edge(source, target):
            graph[source][target]["ml_risk_score"] = float(
                row["ml_risk_score"]
            )

            graph[source][target]["ml_anomaly"] = bool(
                row["is_anomaly"]
            )

            attached += 1

    return attached


def find_ml_aware_route(
    graph,
    origin,
    destination,
    profile,
    risk_weight=5.0,
):
    """
    Find an accessible route while also penalising
    segments identified as higher risk by the ML model.

    risk_weight represents how many metres of routing
    cost one ML risk point contributes.
    """

    accessible_graph = build_accessible_graph(
        graph,
        profile,
    )

    for _, _, edge in accessible_graph.edges(
        data=True
    ):
        base_cost = float(
            edge.get(
                "routing_cost",
                edge.get("distance_m", 0),
            )
        )

        ml_risk = float(
            edge.get(
                "ml_risk_score",
                0,
            )
            or 0
        )

        edge["ml_routing_cost"] = (
            base_cost
            + (ml_risk * risk_weight)
        )

    try:
        path = nx.shortest_path(
            accessible_graph,
            origin,
            destination,
            weight="ml_routing_cost",
        )

    except nx.NetworkXNoPath as exc:
        raise NoAccessibleRouteError(
            f"No ML-aware accessible route exists "
            f"between {origin} and {destination}."
        ) from exc

    total_distance = 0.0
    weighted_risk = 0.0
    max_risk = 0.0
    anomaly_segments = 0

    for u, v in zip(
        path,
        path[1:],
    ):
        edge = accessible_graph[u][v]

        distance = float(
            edge["distance_m"]
        )

        risk = float(
            edge.get("ml_risk_score", 0)
            or 0
        )

        total_distance += distance
        weighted_risk += risk * distance

        max_risk = max(
            max_risk,
            risk,
        )

        if edge.get(
            "ml_anomaly",
            False,
        ):
            anomaly_segments += 1

    average_risk = (
        weighted_risk / total_distance
        if total_distance
        else 0
    )

    return {
        "origin": origin,
        "destination": destination,
        "path": path,
        "distance_m": round(
            total_distance,
            1,
        ),
        "ml": {
            "risk_weight": risk_weight,
            "average_risk_score": round(
                average_risk,
                2,
            ),
            "maximum_risk_score": round(
                max_risk,
                2,
            ),
            "anomaly_segments": anomaly_segments,
        },
    }
