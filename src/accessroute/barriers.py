from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field
from sqlalchemy import text

from src.accessroute.database.db import engine


BarrierType = Literal[
    "blocked_pavement",
    "broken_lift",
    "missing_dropped_kerb",
    "construction",
    "stairs",
    "rough_surface",
    "other",
]


class BarrierReportIn(BaseModel):
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    report_type: BarrierType
    description: str = Field(min_length=10, max_length=500)


class BarrierReportOut(BarrierReportIn):
    id: int
    status: Literal["pending", "verified", "rejected"]
    created_at: datetime


def create_barrier_report(report: BarrierReportIn):
    query = text("""
        INSERT INTO barrier_reports (
            latitude,
            longitude,
            report_type,
            description,
            location
        )
        VALUES (
            :latitude,
            :longitude,
            :report_type,
            :description,
            ST_SetSRID(
                ST_MakePoint(:longitude, :latitude),
                4326
            )::geography
        )
        RETURNING
            id,
            latitude,
            longitude,
            report_type,
            description,
            status,
            created_at
    """)

    with engine.begin() as connection:
        result = connection.execute(
            query,
            report.model_dump(),
        ).mappings().one()

    return dict(result)


def list_barrier_reports(limit: int = 50):
    query = text("""
        SELECT
            id,
            latitude,
            longitude,
            report_type,
            description,
            status,
            created_at
        FROM barrier_reports
        ORDER BY created_at DESC, id DESC
        LIMIT :limit
    """)

    with engine.connect() as connection:
        rows = connection.execute(
            query,
            {"limit": limit},
        ).mappings().all()

    return [dict(row) for row in rows]
