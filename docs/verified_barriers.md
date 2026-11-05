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
