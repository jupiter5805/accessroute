"""Phase 14: authenticated audit access, filtering and transactional recording."""
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

from fastapi.testclient import TestClient
import src.accessroute.main as api
import src.accessroute.moderation as moderation
from src.accessroute.moderation import ReviewDecision

client = TestClient(api.app)


def test_audit_unavailable_without_key_configuration(monkeypatch):
    monkeypatch.delenv('ACCESSROUTE_ADMIN_KEY', raising=False)
    assert client.get('/barriers/moderation/audit').status_code == 503


def test_audit_rejects_incorrect_key(monkeypatch):
    monkeypatch.setenv('ACCESSROUTE_ADMIN_KEY', 'test-key')
    assert client.get('/barriers/moderation/audit', headers={
        'X-Admin-Key': 'wrong',
    }).status_code == 401


def test_audit_returns_auth_only_paginated_results(monkeypatch):
    monkeypatch.setenv('ACCESSROUTE_ADMIN_KEY', 'test-key')
    observed = []

    def fake_history(limit, offset):
        observed.append((limit, offset))
        return [{'id': 3, 'report_id': 7, 'decision': 'verified'}]

    monkeypatch.setattr(api, 'list_review_events', fake_history)
    response = client.get('/barriers/moderation/audit?limit=5&offset=10',
                          headers={'X-Admin-Key': 'test-key'})
    assert response.status_code == 200
    assert response.json()['events'][0]['report_id'] == 7
    assert response.headers['cache-control'] == 'no-store'
    assert observed == [(5, 10)]


def test_audit_validates_pagination(monkeypatch):
    monkeypatch.setenv('ACCESSROUTE_ADMIN_KEY', 'test-key')
    for query in ('limit=0', 'limit=201', 'offset=-1'):
        response = client.get('/barriers/moderation/audit?' + query,
                              headers={'X-Admin-Key': 'test-key'})
        assert response.status_code == 422


class FakeResult:
    def __init__(self, value):
        self.value = value

    def mappings(self):
        return self

    def first(self):
        return self.value

    def one(self):
        return self.value


class FakeConnection:
    def __init__(self):
        self.statements = []
        self.events = []

    def execute(self, statement, parameters):
        sql = str(statement)
        self.statements.append(sql)
        if 'SELECT id, report_type, status' in sql:
            return FakeResult({'id': 7, 'report_type': 'rough_surface',
                               'status': 'pending'})
        if 'UPDATE barrier_reports' in sql:
            return FakeResult({'id': 7, 'report_type': 'rough_surface',
                               'status': parameters['status'],
                               'edge_id': None, 'reviewed_at': datetime.now(timezone.utc),
                               'expires_at': None})
        if 'INSERT INTO barrier_review_events' in sql:
            self.events.append(parameters)
            return FakeResult(None)
        raise AssertionError(f'Unexpected SQL: {sql}')


class FakeEngine:
    def __init__(self, connection):
        self.connection = connection

    @contextmanager
    def begin(self):
        yield self.connection


def test_review_writes_event_in_same_transaction(monkeypatch):
    connection = FakeConnection()
    monkeypatch.setattr(moderation, 'engine', FakeEngine(connection))
    result = moderation.review_barrier_report(
        7, ReviewDecision(status='verified')
    )
    assert result['status'] == 'verified'
    assert len(connection.events) == 1
    assert connection.events[0] == {
        'report_id': 7, 'decision': 'verified',
        'edge_id': None, 'valid_hours': None,
    }
    assert 'UPDATE barrier_reports' in connection.statements[-2]
    assert 'INSERT INTO barrier_review_events' in connection.statements[-1]


def test_moderator_dashboard_has_audit_ui():
    html = Path('static/moderator.html').read_text()
    js = Path('static/moderator.js').read_text()
    assert 'id="loadAudit"' in html
    assert '/barriers/moderation/audit' in js
    assert 'localStorage' not in js
    assert 'innerHTML' not in js


def test_schema_is_idempotent_and_indexed():
    source = Path('src/accessroute/database/setup_audit.py').read_text()
    assert 'CREATE TABLE IF NOT EXISTS barrier_review_events' in source
    assert 'CREATE INDEX IF NOT EXISTS idx_barrier_review_events_recent' in source
    assert 'CREATE INDEX IF NOT EXISTS idx_barrier_review_events_report' in source
