"""Phase 12: authorization, review rules, and routing query safeguards."""
import inspect

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

import src.accessroute.main as api
from src.accessroute.database.graph_loader import load_graph_from_postgres
from src.accessroute.moderation import ReviewDecision, validate_review

client = TestClient(api.app)


def test_cannot_access_moderation_without_config(monkeypatch):
    monkeypatch.delenv('ACCESSROUTE_ADMIN_KEY', raising=False)
    response = client.get('/barriers/reports/1/candidates')
    assert response.status_code == 503


def test_wrong_admin_key_rejected(monkeypatch):
    monkeypatch.setenv('ACCESSROUTE_ADMIN_KEY', 'test-only-secret')
    response = client.get('/barriers/reports/1/candidates',
                          headers={'X-Admin-Key': 'wrong'})
    assert response.status_code == 401


def test_wrong_admin_key_cannot_approve(monkeypatch):
    monkeypatch.setenv('ACCESSROUTE_ADMIN_KEY', 'test-only-secret')
    response = client.post('/barriers/reports/1/review',
                           headers={'X-Admin-Key': 'wrong'},
                           json={'status': 'verified', 'edge_id': 42})
    assert response.status_code == 401


def test_authenticated_candidate_lookup(monkeypatch):
    monkeypatch.setenv('ACCESSROUTE_ADMIN_KEY', 'test-only-secret')
    monkeypatch.setattr(api, 'find_report_edges',
                        lambda rid: [{'edge_id': 42, 'distance_m': 4.5}])
    response = client.get('/barriers/reports/1/candidates',
                          headers={'X-Admin-Key': 'test-only-secret'})
    assert response.status_code == 200
    assert response.json()['candidates'][0]['edge_id'] == 42


def test_closure_requires_selected_edge():
    with pytest.raises(HTTPException) as error:
        validate_review('blocked_pavement', ReviewDecision(status='verified'))
    assert error.value.status_code == 422


def test_rejection_cannot_close_edge():
    with pytest.raises(HTTPException) as error:
        validate_review('construction',
                        ReviewDecision(status='rejected', edge_id=42))
    assert error.value.status_code == 422


def test_nonclosure_verified_without_edge():
    assert validate_review('rough_surface',
                           ReviewDecision(status='verified')) is False


def test_expiration_duration_validated():
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        ReviewDecision(status='verified', edge_id=42, valid_hours=721)


def test_routing_filters_only_verified_unexpired_edge_ids():
    loader_source = inspect.getsource(load_graph_from_postgres)
    assert 'WHERE NOT EXISTS' in loader_source
    assert "r.status = 'verified'" in loader_source
    assert 'r.expires_at > NOW()' in loader_source
    assert 'r.edge_id = e.id' in loader_source
    assert 'edge_id=row["edge_id"]' in loader_source
