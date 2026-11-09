from datetime import datetime, timezone

from fastapi.testclient import TestClient

import src.accessroute.main as api


client = TestClient(api.app)


PAYLOAD = {
    "latitude": 53.4808,
    "longitude": -2.2426,
    "report_type": "blocked_pavement",
    "description": "Pavement blocked by construction barriers.",
}


def test_submit_barrier_report(monkeypatch):
    def fake_create(report):
        return {
            "id": 1,
            **report.model_dump(),
            "status": "pending",
            "created_at": datetime.now(timezone.utc),
        }

    monkeypatch.setattr(
        api,
        "create_barrier_report",
        fake_create,
    )

    response = client.post(
        "/barriers/reports",
        json=PAYLOAD,
    )

    assert response.status_code == 201
    assert response.json()["status"] == "pending"
    assert response.json()["id"] == 1


def test_invalid_report_rejected():
    response = client.post(
        "/barriers/reports",
        json={
            **PAYLOAD,
            "description": "Too short",
        },
    )

    assert response.status_code == 422


def test_barrier_report_listing(monkeypatch):
    monkeypatch.setattr(
        api,
        "list_barrier_reports",
        lambda limit: [],
    )

    response = client.get("/barriers/reports")

    assert response.status_code == 200
    assert response.json() == []


def test_barrier_ui_available():
    response = client.get("/barriers-ui.js")

    assert response.status_code == 200
    assert "javascript" in response.headers["content-type"]


def test_invalid_barrier_coordinates_are_rejected():
    invalid_locations = [
        (91.0, -2.2426),
        (-91.0, -2.2426),
        (53.4808, 181.0),
        (53.4808, -181.0),
    ]

    for latitude, longitude in invalid_locations:
        response = client.post(
            "/barriers/reports",
            json={
                **PAYLOAD,
                "latitude": latitude,
                "longitude": longitude,
            },
        )

        assert response.status_code == 422
