# Verified barrier moderation (Phase 12)

A community barrier report starts as `pending`. Public users cannot verify it.

## Initialise schema

After bringing up PostgreSQL and initialising the core tables and Phase 11 reports:

```bash
python -m src.accessroute.database.setup_moderation
```

The migration is idempotent and preserves existing barrier reports. `edge_id` is a
foreign key with `ON DELETE SET NULL`, so re-ingesting OSM edges cannot leave a
report pointing at a reused edge ID.

## Moderator authentication

Start the API with a nontrivial `ACCESSROUTE_ADMIN_KEY` environment variable.
The key is supplied in an `X-Admin-Key` request header; it must never be added
to the public map JavaScript or checked into Git.

- `GET /barriers/reports/{id}/candidates` suggests directed edges within 25 m.
- `POST /barriers/reports/{id}/review` accepts `status`, `edge_id`, and `valid_hours`.
- Only `pending` reports can be reviewed; repeat reviews return 409.
- For `blocked_pavement` and `construction`, verification requires a nearby edge.
- Other verified reports remain informational, and rejected reports never close edges.

Review JSON example (replace `42` with an ID returned by `candidates`):

```json
{"status": "verified", "edge_id": 42, "valid_hours": 168}
```

## Routing behaviour and caveats

The graph loader filters **verified, unexpired, specific directed edge IDs** in SQL
before the shortest parallel edge is selected. All real PostgreSQL-backed route
endpoints use this loader, so subsequent requests see the new closures. Expiration
is checked by PostgreSQL using `NOW()` and does not need a background worker.

Only approximate straight segments between stored OSM end nodes are available;
this is not a full road/path geometry match. Moderators must confirm the right
segment and check directionality. A reverse-direction edge may require separate
review/reporting. The routing prototype is not a safety-certified navigation aid.

The sample-JSON `/routes` endpoint is intentionally unaffected by live closures.

## Phase 12 Integration Verification

Verified on 5 November 2026:
- All 45 automated tests passed
- PostgreSQL/PostGIS migration completed successfully
- Manchester routing graph loaded with 33,052 nodes and 85,997 edges
- Docker PostgreSQL and Airflow services running successfully
- Live moderation-to-rerouting integration test remains pending

## Phase 13 moderator dashboard

Open `http://127.0.0.1:8002/moderator` while running FastAPI on port 8002.
The dashboard provides a Leaflet map of report locations, status filtering,
nearby candidate street segments, and verify/reject controls. Candidate lines
use endpoint-to-endpoint approximations and must be checked manually.

Start the server with `ACCESSROUTE_ADMIN_KEY` set to a strong secret, then
enter that key into the dashboard. The key is kept in the current page's
JavaScript memory only; it is not embedded in the HTML, stored in browser
storage, or sent in query parameters. Moderator data and decisions are only
available through endpoints requiring the `X-Admin-Key` header.

For local testing:

```bash
export ACCESSROUTE_ADMIN_KEY="$(python -c 'import secrets; print(secrets.token_urlsafe(32))')"
uvicorn src.accessroute.main:app --reload --port 8002
```

A production deployment would require proper user authentication, TLS, audit
logs, and stronger safeguards before real users rely on the route results.

## Phase 14 — Transactional moderation audit history

Run the audit migration **before** approving or rejecting further reports:

```bash
python -m src.accessroute.database.setup_audit
```

Every successful review creates one `barrier_review_events` entry in the **same
PostgreSQL transaction** as the report update. A failed event insert causes the
review update to roll back. Historical entries preserve the report identifier,
decision, selected edge ID and closure duration; they do not establish an
individual moderator identity because the current local-only authentication
uses a shared secret.

- `GET /barriers/moderation/audit?limit=50&offset=0` is protected by
  `X-Admin-Key` and returns newest-first review decisions.
- In `/moderator`, enter the local moderation key and select **Load audit
  history** to view the 30 most recent entries.
- Decisions made **before Phase 14** are not backfilled; existing records have
  no trustworthy individual event timestamps beyond the report review time.

This is an application-level audit trail rather than tamper-proof logging.
Production deployment still requires per-moderator identities, structured
logging, access controls, TLS and operational monitoring.
