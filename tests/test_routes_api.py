from fastapi.testclient import TestClient

from src.accessroute.main import app


client = TestClient(app)


def test_standard_route():
    response = client.post(
        "/routes",
        json={
            "origin": "piccadilly_gardens",
            "destination": "manchester_royal_infirmary",
            "profile": {
                "wheelchair": False,
                "avoid_stairs": False,
                "max_gradient": 0.08,
                "require_lift": False,
            },
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["route"] == [
        "piccadilly_gardens",
        "market_street",
        "manchester_royal_infirmary",
    ]

    assert data["distance_m"] == 1600


def test_wheelchair_route_avoids_stairs():
    response = client.post(
        "/routes",
        json={
            "origin": "piccadilly_gardens",
            "destination": "manchester_royal_infirmary",
            "profile": {
                "wheelchair": True,
                "avoid_stairs": True,
                "max_gradient": 0.05,
                "require_lift": False,
            },
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["route"] == [
        "piccadilly_gardens",
        "oxford_road",
        "manchester_royal_infirmary",
    ]

    assert data["distance_m"] == 2000


def test_unknown_location_returns_404():
    response = client.post(
        "/routes",
        json={
            "origin": "unknown_place",
            "destination": "manchester_royal_infirmary",
            "profile": {},
        },
    )

    assert response.status_code == 404


def test_no_accessible_route_returns_422():
    response = client.post(
        "/routes",
        json={
            "origin": "piccadilly_gardens",
            "destination": "manchester_royal_infirmary",
            "profile": {
                "wheelchair": True,
                "avoid_stairs": True,
                "max_gradient": 0.01,
                "require_lift": False,
            },
        },
    )

    assert response.status_code == 422


def test_invalid_gradient_returns_422():
    response = client.post(
        "/routes",
        json={
            "origin": "piccadilly_gardens",
            "destination": "manchester_royal_infirmary",
            "profile": {
                "max_gradient": 2.0
            },
        },
    )

    assert response.status_code == 422
