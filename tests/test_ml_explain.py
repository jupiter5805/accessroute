import networkx as nx

from src.accessroute.ml_explain import (
    classify_risk,
    explain_route,
)

from src.accessroute.models import (
    AccessibilityProfile,
)


def test_risk_classification():
    assert classify_risk(10) == "low"
    assert classify_risk(50) == "medium"
    assert classify_risk(90) == "high"


def test_route_explanation():
    graph = nx.Graph()

    graph.add_node(
        "A",
        latitude=53.48,
        longitude=-2.24,
    )

    graph.add_node(
        "B",
        latitude=53.481,
        longitude=-2.241,
    )

    graph.add_edge(
        "A",
        "B",
        distance_m=100,
        gradient=0.04,
        gradient_reliable=True,
        has_stairs=False,
        surface="cobblestone",
        wheelchair_accessible=True,
        ml_risk_score=82,
        ml_anomaly=True,
    )

    profile = AccessibilityProfile(
        wheelchair=True,
        avoid_stairs=True,
        max_gradient=0.08,
        require_lift=False,
    )

    result = explain_route(
        graph,
        ["A", "B"],
        profile,
    )

    assert result[
        "high_risk_segments"
    ] == 1

    segment = result["segments"][0]

    assert (
        segment["risk_level"]
        == "high"
    )

    assert (
        "ML anomaly detected"
        in segment["reasons"]
    )

    assert (
        "rough surface: cobblestone"
        in segment["reasons"]
    )
