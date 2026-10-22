import networkx as nx

from src.accessroute.accessibility import analyse_route
from src.accessroute.models import AccessibilityProfile


def build_test_graph():
    graph = nx.Graph()

    graph.add_edge(
        "a",
        "b",
        distance_m=100,
        gradient=0.03,
        gradient_reliable=True,
        has_stairs=False,
        surface="paved",
        wheelchair_accessible=True,
    )

    graph.add_edge(
        "b",
        "c",
        distance_m=100,
        gradient=0.04,
        gradient_reliable=False,
        has_stairs=False,
        surface="unknown",
        wheelchair_accessible=True,
    )

    return graph


def test_accessibility_analysis():
    graph = build_test_graph()

    profile = AccessibilityProfile(
        wheelchair=True,
        avoid_stairs=True,
        max_gradient=0.08,
        require_lift=False,
    )

    result = analyse_route(
        graph,
        ["a", "b", "c"],
        profile,
    )

    assert result["barriers"]["stairs"] == 0
    assert result["barriers"]["steep_segments"] == 0

    assert (
        result["confidence"]
        ["reliable_gradient_coverage_percent"]
        == 50.0
    )

    assert result["confidence"]["level"] == "low"

    assert len(result["reasons"]) > 0
