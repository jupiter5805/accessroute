"""Phase 13 dashboard: protected data, UI serving, and basic input rules."""
from pathlib import Path

from fastapi.testclient import TestClient
import src.accessroute.main as api

client = TestClient(api.app)


def test_admin_listing_unavailable_without_config(monkeypatch):
    monkeypatch.delenv("ACCESSROUTE_ADMIN_KEY", raising=False)
    response = client.get("/barriers/moderation/reports")
    assert response.status_code == 503


def test_admin_listing_rejects_wrong_key(monkeypatch):
    monkeypatch.setenv("ACCESSROUTE_ADMIN_KEY", "local-test-key")
    response = client.get(
        "/barriers/moderation/reports",
        headers={"X-Admin-Key": "wrong"},
    )
    assert response.status_code == 401


def test_admin_listing_with_valid_key(monkeypatch):
    monkeypatch.setenv("ACCESSROUTE_ADMIN_KEY", "local-test-key")
    monkeypatch.setattr(
        api, "list_reports_for_review",
        lambda status, limit: [{"id": 7, "status": status}],
    )
    response = client.get(
        "/barriers/moderation/reports?status=verified&limit=4",
        headers={"X-Admin-Key": "local-test-key"},
    )
    assert response.status_code == 200
    assert response.json() == {"reports": [{"id": 7, "status": "verified"}]}
    assert response.headers["cache-control"] == "no-store"


def test_admin_listing_validates_filters(monkeypatch):
    monkeypatch.setenv("ACCESSROUTE_ADMIN_KEY", "local-test-key")
    for query in ("status=not-a-status", "limit=201", "limit=0"):
        response = client.get(
            f"/barriers/moderation/reports?{query}",
            headers={"X-Admin-Key": "local-test-key"},
        )
        assert response.status_code == 422


def test_dashboard_shell_and_js_available_without_key():
    page = client.get("/moderator")
    script = client.get("/moderator.js")
    assert page.status_code == 200
    assert script.status_code == 200
    assert "Moderator Dashboard" in page.text
    assert "javascript" in script.headers["content-type"]
    assert page.headers["cache-control"] == "no-store"
    assert "X-Admin-Key" in script.text


def test_dashboard_does_not_persist_credentials():
    js = Path("static/moderator.js").read_text()
    assert "localStorage" not in js
    assert "sessionStorage" not in js
    assert "document.cookie" not in js
    assert "innerHTML" not in js
