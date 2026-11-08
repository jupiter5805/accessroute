# Barrier moderation metrics

Phase 15 adds a **read-only, moderator-only operational analytics endpoint**.

`GET /barriers/moderation/metrics`

Set `ACCESSROUTE_ADMIN_KEY` on the FastAPI server and send the same value in
`X-Admin-Key`. Never hardcode or commit the key.

The JSON response contains:

- Total reports, and counts pending / verified / rejected.
- Reports still pending after 48 hours (moderation backlog).
- Active verified closures and expired verified closures. Closures apply only
  to blocked pavement and construction reports with an assigned street edge.
- Counts by report type.

The queries aggregate directly in PostgreSQL and do not expose report
coordinates or descriptions. They **do not change route availability**.

A verified non-closure report is counted as verified but not as a route closure.
Run `pytest -v` before pushing changes. This endpoint requires the Phase 12
`setup_moderation` migration to have been applied to your database.
