import networkx as nx

from src.accessroute.ml_compare import (
    compare_ml_routes,
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
        ml_anomaly=risk >= 70,
    )


def test_ml_route_comparison():
    graph = nx.Graph()

    # Shorter but risky
    add_edge(
        graph,
        "A",
        "B",
        100,
        80,
    )

    add_edge(
        graph,
        "B",
        "C",
        100,
        80,
    )

    # Slightly longer but safer
    add_edge(
        graph,
        "A",
        "D",
        130,
        10,
    )

    add_edge(
        graph,
        "D",
        "C",
        130,
        10,
    )

    profile = AccessibilityProfile(
        wheelchair=True,
        avoid_stairs=True,
        max_gradient=0.08,
        require_lift=False,
    )

    result = compare_ml_routes(
        graph=graph,
        origin="A",
        destination="C",
        profile=profile,
        risk_weight=5,
    )

    assert (
        result["accessible_route"]["path"]
        == ["A", "B", "C"]
    )

    assert (
        result["ml_aware_route"]["path"]
        == ["A", "D", "C"]
    )

    assert (
        result["tradeoff"]["extra_distance_m"]
        == 60
    )

    assert (
        result["tradeoff"][
            "risk_reduction_percent"
        ]
        > 0
    )
