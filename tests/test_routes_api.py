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


def test_coordinate_route(monkeypatch):
    import src.accessroute.main as main_module

    # Use our small sample graph instead of the real PostGIS database.
    monkeypatch.setattr(
        main_module,
        "load_graph_from_postgres",
        lambda: main_module.sample_graph,
    )

    # Pretend PostGIS snapped the two coordinates to these nodes.
    nearest_nodes = iter(
        [
            "piccadilly_gardens",
            "manchester_royal_infirmary",
        ]
    )

    monkeypatch.setattr(
        main_module,
        "find_nearest_node",
        lambda latitude, longitude: next(nearest_nodes),
    )

    response = client.post(
        "/routes/coordinates",
        json={
            "origin": {
                "latitude": 53.4810,
                "longitude": -2.2370,
            },
            "destination": {
                "latitude": 53.4631,
                "longitude": -2.2278,
            },
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

    assert data["snapped_origin_node"] == "piccadilly_gardens"
    assert data["snapped_destination_node"] == "manchester_royal_infirmary"

    assert data["route"][0]["node_id"] == "piccadilly_gardens"
    assert data["route"][-1]["node_id"] == "manchester_royal_infirmary"

    assert data["distance_m"] > 0
    assert len(data["route"]) >= 2


def test_place_search(monkeypatch):
    import src.accessroute.main as main_module

    async def fake_search_places(query):
        return [
            {
                "name": "Manchester Piccadilly",
                "latitude": 53.4774,
                "longitude": -2.2308,
                "type": "station",
                "category": "railway",
            }
        ]

    monkeypatch.setattr(
        main_module,
        "search_places",
        fake_search_places,
    )

    response = client.get(
        "/places/search",
        params={"q": "Manchester Piccadilly"},
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data["results"]) == 1
    assert data["results"][0]["name"] == "Manchester Piccadilly"
    assert data["results"][0]["latitude"] == 53.4774
