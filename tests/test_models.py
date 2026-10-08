import pytest
from pydantic import ValidationError

from src.accessroute.models import AccessibilityProfile, RouteEdge


def test_route_edge_accepts_valid_data():
    edge = RouteEdge(
        source="a",
        target="b",
        distance_m=120,
        gradient=0.03,
        has_stairs=False,
        has_lift=False,
        surface="paved",
        wheelchair_accessible=True,
    )

    assert edge.distance_m == 120
    assert edge.wheelchair_accessible is True


def test_route_edge_rejects_negative_distance():
    with pytest.raises(ValidationError):
        RouteEdge(
            source="a",
            target="b",
            distance_m=-10,
            gradient=0.02,
            has_stairs=False,
            has_lift=False,
            surface="paved",
            wheelchair_accessible=True,
        )


def test_accessibility_profile_defaults():
    profile = AccessibilityProfile()

    assert profile.wheelchair is False
    assert profile.avoid_stairs is False
    assert profile.max_gradient == 0.08
    assert profile.require_lift is False


def test_accessibility_profile_rejects_invalid_gradient():
    with pytest.raises(ValidationError):
        AccessibilityProfile(max_gradient=1.5)
