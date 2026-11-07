"""Idempotent migration: record all moderation decisions in an append-only log."""
from sqlalchemy import text
from src.accessroute.database.db import engine


def setup_audit():
    with engine.begin() as connection:
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS barrier_review_events (
                id BIGSERIAL PRIMARY KEY,
                report_id BIGINT NOT NULL REFERENCES barrier_reports(id),
                decision VARCHAR(20) NOT NULL
                    CHECK (decision IN ('verified', 'rejected')),
                edge_id BIGINT,
                valid_hours INTEGER
                    CHECK (valid_hours BETWEEN 1 AND 720),
                recorded_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                CHECK (decision = 'verified' OR edge_id IS NULL)
            )
        """))
        connection.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_barrier_review_events_recent
            ON barrier_review_events (recorded_at DESC, id DESC)
        """))
        connection.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_barrier_review_events_report
            ON barrier_review_events (report_id, recorded_at DESC)
        """))
    print('AccessRoute moderation audit schema ready.')


if __name__ == '__main__':
    setup_audit()
