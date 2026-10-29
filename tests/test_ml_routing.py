import networkx as nx

from src.accessroute.ml_routing import (
    find_ml_aware_route,
)
from src.accessroute.models import (
    AccessibilityProfile,
)


def add_edge(
    graph,
    source,
    target,
    distance,
    risk,
):
    graph.add_edge(
        source,
        target,
        distance_m=distance,
        gradient=0.01,
        has_stairs=False,
        has_lift=False,
        surface="paved",
        wheelchair_accessible=True,
        ml_risk_score=risk,
        ml_anomaly=risk > 70,
    )


def test_ml_routing_prefers_lower_risk_route():
    graph = nx.Graph()

    # Short but high-risk route
    add_edge(
        graph,
        "A",
        "B",
        100,
        90,
    )

    add_edge(
        graph,
        "B",
        "C",
        100,
        90,
    )

    # Longer but low-risk route
    add_edge(
        graph,
        "A",
        "D",
        130,
        5,
    )

    add_edge(
        graph,
        "D",
        "C",
        130,
        5,
    )

    profile = AccessibilityProfile(
        wheelchair=True,
        avoid_stairs=True,
        max_gradient=0.08,
        require_lift=False,
    )

    result = find_ml_aware_route(
        graph,
        "A",
        "C",
        profile,
        risk_weight=5,
    )

    assert result["path"] == [
        "A",
        "D",
        "C",
    ]

    assert result["distance_m"] == 260

    assert (
        result["ml"]["average_risk_score"]
        == 5
    )
