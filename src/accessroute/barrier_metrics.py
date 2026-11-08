"""Read-only operational metrics for the community barrier moderation queue.

All calculations are performed by PostgreSQL, avoiding fetching report text,
coordinates or identities into Python. These metrics never influence routing.
"""
from sqlalchemy import text
from src.accessroute.database.db import engine


def format_metrics(summary, grouped):
    """Convert database aggregates into a stable, JSON-friendly response."""
    data = dict(summary)
    return {
        "total_reports": int(data["total_reports"]),
        "by_status": {
            "pending": int(data["pending_reports"]),
            "verified": int(data["verified_reports"]),
            "rejected": int(data["rejected_reports"]),
        },
        "pending_older_than_48h": int(data["pending_older_than_48h"]),
        "active_route_closures": int(data["active_route_closures"]),
        "expired_route_closures": int(data["expired_route_closures"]),
        "by_type": [
            {"report_type": row["report_type"], "count": int(row["count"])}
            for row in grouped
        ],
    }


def get_barrier_metrics():
    """Return counts from PostgreSQL. Requires the Phase 12 schema migration."""
    with engine.connect() as connection:
        summary = connection.execute(text("""
            SELECT
                COUNT(*) AS total_reports,
                COUNT(*) FILTER (WHERE status = 'pending') AS pending_reports,
                COUNT(*) FILTER (WHERE status = 'verified') AS verified_reports,
                COUNT(*) FILTER (WHERE status = 'rejected') AS rejected_reports,
                COUNT(*) FILTER (
                    WHERE status = 'pending'
                    AND created_at < NOW() - INTERVAL '48 hours'
                ) AS pending_older_than_48h,
                COUNT(*) FILTER (
                    WHERE status = 'verified'
                    AND report_type IN ('blocked_pavement', 'construction')
                    AND edge_id IS NOT NULL
                    AND expires_at > NOW()
                ) AS active_route_closures,
                COUNT(*) FILTER (
                    WHERE status = 'verified'
                    AND report_type IN ('blocked_pavement', 'construction')
                    AND edge_id IS NOT NULL
                    AND expires_at <= NOW()
                ) AS expired_route_closures
            FROM barrier_reports
        """)).mappings().one()

        grouped = connection.execute(text("""
            SELECT report_type, COUNT(*) AS count
            FROM barrier_reports
            GROUP BY report_type
            ORDER BY count DESC, report_type
        """)).mappings().all()

    return format_metrics(summary, grouped)
