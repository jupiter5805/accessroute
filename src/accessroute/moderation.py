"""Admin-only review of community accessibility reports."""
import hmac
import os
from typing import Literal

from fastapi import Header, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import text

from src.accessroute.database.db import engine

CLOSURE_TYPES = {"blocked_pavement", "construction"}
MAX_EDGE_DISTANCE_M = 25


class ReviewDecision(BaseModel):
    status: Literal["verified", "rejected"]
    edge_id: int | None = Field(default=None, ge=1)
    valid_hours: int = Field(default=168, ge=1, le=720)


def require_admin(x_admin_key: str | None = Header(default=None)):
    expected = os.getenv("ACCESSROUTE_ADMIN_KEY")
    if not expected:
        raise HTTPException(503, "Moderator authentication is not configured")
    if not x_admin_key or not hmac.compare_digest(x_admin_key, expected):
        raise HTTPException(401, "Invalid moderator credentials")


def validate_review(report_type: str, decision: ReviewDecision) -> bool:
    """Return whether a review activates a route closure."""
    closure = decision.status == "verified" and report_type in CLOSURE_TYPES
    if closure and decision.edge_id is None:
        raise HTTPException(422, "Choose a nearby edge before verifying a closure")
    if not closure and decision.edge_id is not None:
        raise HTTPException(422, "Edge selection is only valid for verified closures")
    return closure


def find_report_edges(report_id: int):
    """Suggest directed street edges within 25 m of a report.

    Because only OSM endpoint locations are stored, the geometry here is a
    straight-line approximation. A moderator must inspect the map before approval.
    """
    with engine.connect() as connection:
        exists = connection.execute(
            text("SELECT 1 FROM barrier_reports WHERE id = :id"),
            {"id": report_id},
        ).scalar_one_or_none()
        if exists is None:
            raise HTTPException(404, "Barrier report not found")

        rows = connection.execute(text("""
            SELECT e.id AS edge_id, e.source, e.target,
                   ROUND(ST_Distance(
                       r.location,
                       ST_MakeLine(s.location::geometry,
                                   t.location::geometry)::geography
                   )::numeric, 1) AS distance_m
            FROM barrier_reports AS r
            JOIN route_edges AS e ON TRUE
            JOIN route_nodes AS s ON s.id = e.source
            JOIN route_nodes AS t ON t.id = e.target
            WHERE r.id = :report_id
              AND ST_DWithin(
                  r.location,
                  ST_MakeLine(s.location::geometry,
                              t.location::geometry)::geography,
                  :max_distance
              )
            ORDER BY distance_m, e.id
            LIMIT 10
        """), {"report_id": report_id, "max_distance": MAX_EDGE_DISTANCE_M}).mappings().all()
        return [dict(row) for row in rows]


def review_barrier_report(report_id: int, decision: ReviewDecision):
    """Atomically change a pending report to verified/rejected."""
    with engine.begin() as connection:
        report = connection.execute(text("""
            SELECT id, report_type, status
            FROM barrier_reports
            WHERE id = :id
            FOR UPDATE
        """), {"id": report_id}).mappings().first()

        if report is None:
            raise HTTPException(404, "Barrier report not found")
        if report["status"] != "pending":
            raise HTTPException(409, "This report has already been reviewed")

        closure = validate_review(report["report_type"], decision)
        if closure:
            nearby = connection.execute(text("""
                SELECT EXISTS (
                    SELECT 1
                    FROM barrier_reports AS r
                    JOIN route_edges AS e ON e.id = :edge_id
                    JOIN route_nodes AS s ON s.id = e.source
                    JOIN route_nodes AS t ON t.id = e.target
                    WHERE r.id = :report_id
                      AND ST_DWithin(
                          r.location,
                          ST_MakeLine(s.location::geometry,
                                      t.location::geometry)::geography,
                          :max_distance
                      )
                )
            """), {
                "edge_id": decision.edge_id,
                "report_id": report_id,
                "max_distance": MAX_EDGE_DISTANCE_M,
            }).scalar_one()
            if nearby is not True:
                raise HTTPException(422, "Selected edge is more than 25 m away or does not exist")

        result = connection.execute(text("""
            UPDATE barrier_reports
            SET status = :status,
                edge_id = :edge_id,
                reviewed_at = NOW(),
                expires_at = CASE WHEN :closure
                    THEN NOW() + (:valid_hours * INTERVAL '1 hour')
                    ELSE NULL END
            WHERE id = :report_id
            RETURNING id, report_type, status, edge_id, reviewed_at, expires_at
        """), {
            "status": decision.status,
            "edge_id": decision.edge_id if closure else None,
            "closure": closure,
            "valid_hours": decision.valid_hours,
            "report_id": report_id,
        }).mappings().one()
        return dict(result)
