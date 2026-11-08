"""Phase 15: metrics formatting and authentication, without requiring Docker."""
from fastapi.testclient import TestClient
import src.accessroute.main as api
from src.accessroute.barrier_metrics import format_metrics

client = TestClient(api.app)


SAMPLE = {
    "total_reports": 10,
    "pending_reports": 5,
    "verified_reports": 3,
    "rejected_reports": 2,
    "pending_older_than_48h": 2,
    "active_route_closures": 1,
    "expired_route_closures": 1,
}


def test_metrics_formats_database_counts():
    result = format_metrics(SAMPLE, [
        {"report_type": "construction", "count": 6},
        {"report_type": "other", "count": 4},
    ])
    assert result["total_reports"] == 10
    assert result["by_status"] == {"pending": 5, "verified": 3, "rejected": 2}
    assert result["active_route_closures"] == 1
    assert result["expired_route_closures"] == 1
    assert result["by_type"][0] == {"report_type": "construction", "count": 6}


def test_zero_reports_has_predictable_structure():
    result = format_metrics({key: 0 for key in SAMPLE}, [])
    assert result["total_reports"] == 0
    assert result["by_status"] == {"pending": 0, "verified": 0, "rejected": 0}
    assert result["by_type"] == []


def test_metrics_rejects_unconfigured_auth(monkeypatch):
    monkeypatch.delenv("ACCESSROUTE_ADMIN_KEY", raising=False)
    assert client.get("/barriers/moderation/metrics").status_code == 503


def test_metrics_rejects_missing_key(monkeypatch):
    monkeypatch.setenv("ACCESSROUTE_ADMIN_KEY", "sample-dev-key")
    assert client.get("/barriers/moderation/metrics").status_code == 401


def test_metrics_rejects_invalid_key(monkeypatch):
    monkeypatch.setenv("ACCESSROUTE_ADMIN_KEY", "sample-dev-key")
    result = client.get(
        "/barriers/moderation/metrics",
        headers={"X-Admin-Key": "incorrect"},
    )
    assert result.status_code == 401


def test_metrics_is_protected_and_not_cached(monkeypatch):
    monkeypatch.setenv("ACCESSROUTE_ADMIN_KEY", "sample-dev-key")
    monkeypatch.setattr(api, "load_barrier_metrics", lambda: format_metrics(SAMPLE, []))
    result = client.get(
        "/barriers/moderation/metrics",
        headers={"X-Admin-Key": "sample-dev-key"},
    )
    assert result.status_code == 200
    assert result.json()["pending_older_than_48h"] == 2
    assert result.headers["cache-control"] == "no-store"
