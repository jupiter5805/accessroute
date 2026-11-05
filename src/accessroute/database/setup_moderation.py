"""Idempotent schema update for verified accessibility barriers."""
from sqlalchemy import text
from src.accessroute.database.db import engine


def setup_moderation():
    with engine.begin() as connection:
        connection.execute(text("""
            ALTER TABLE barrier_reports
            ADD COLUMN IF NOT EXISTS edge_id BIGINT
            REFERENCES route_edges(id) ON DELETE SET NULL
        """))
        connection.execute(text("""
            ALTER TABLE barrier_reports
            ADD COLUMN IF NOT EXISTS reviewed_at TIMESTAMPTZ
        """))
        connection.execute(text("""
            ALTER TABLE barrier_reports
            ADD COLUMN IF NOT EXISTS expires_at TIMESTAMPTZ
        """))
        connection.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_barrier_active_edge
            ON barrier_reports (edge_id, expires_at)
            WHERE status = 'verified'
              AND report_type IN ('blocked_pavement', 'construction')
        """))
    print("AccessRoute barrier moderation database ready.")


if __name__ == "__main__":
    setup_moderation()
