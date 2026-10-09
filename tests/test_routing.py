import pytest

from src.accessroute.graph import load_graph
from src.accessroute.models import AccessibilityProfile
from src.accessroute.routing import (
    NoAccessibleRouteError,
    find_route,
)


SAMPLE_FILE = "data/raw/manchester_sample.json"


def test_standard_user_gets_shorter_route():
    graph = load_graph(SAMPLE_FILE)

    profile = AccessibilityProfile(
        max_gradient=0.08
    )

    result = find_route(
        graph,
        "piccadilly_gardens",
        "manchester_royal_infirmary",
        profile,
    )

    assert result["path"] == [
        "piccadilly_gardens",
        "market_street",
        "manchester_royal_infirmary",
    ]

    assert result["distance_m"] == 1600


def test_wheelchair_user_avoids_inaccessible_route():
    graph = load_graph(SAMPLE_FILE)

    profile = AccessibilityProfile(
        wheelchair=True,
        avoid_stairs=True,
        max_gradient=0.05,
    )

    result = find_route(
        graph,
        "piccadilly_gardens",
        "manchester_royal_infirmary",
        profile,
    )

    assert result["path"] == [
        "piccadilly_gardens",
        "oxford_road",
        "manchester_royal_infirmary",
    ]

    assert result["distance_m"] == 2000


def test_unknown_origin_raises_error():
    graph = load_graph(SAMPLE_FILE)

    profile = AccessibilityProfile()

    with pytest.raises(ValueError):
        find_route(
            graph,
            "unknown_place",
            "manchester_royal_infirmary",
            profile,
        )


def test_no_accessible_route():
    graph = load_graph(SAMPLE_FILE)

    profile = AccessibilityProfile(
        wheelchair=True,
        avoid_stairs=True,
        max_gradient=0.01,
    )

    with pytest.raises(NoAccessibleRouteError):
        find_route(
            graph,
            "piccadilly_gardens",
            "manchester_royal_infirmary",
            profile,
        )
