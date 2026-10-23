import numpy as np
import pandas as pd
from sqlalchemy import text

from src.accessroute.database.db import engine


FEATURE_COLUMNS = [
    "log_distance",
    "gradient",
    "gradient_reliable",
    "has_stairs",
    "wheelchair_inaccessible",
    "rough_surface",
    "unknown_surface",
]


def load_network_dataframe():
    query = text("""
        SELECT
            e.id,
            e.source,
            e.target,
            e.distance_m,
            COALESCE(e.gradient, 0) AS gradient,
            COALESCE(e.gradient_reliable, FALSE) AS gradient_reliable,
            COALESCE(e.has_stairs, FALSE) AS has_stairs,
            COALESCE(e.wheelchair_accessible, TRUE) AS wheelchair_accessible,
            LOWER(COALESCE(e.surface, '')) AS surface,

            ST_Y(s.location::geometry) AS source_latitude,
            ST_X(s.location::geometry) AS source_longitude,

            ST_Y(t.location::geometry) AS target_latitude,
            ST_X(t.location::geometry) AS target_longitude

        FROM route_edges e

        JOIN route_nodes s
            ON s.id = e.source

        JOIN route_nodes t
            ON t.id = e.target
    """)

    with engine.connect() as connection:
        return pd.read_sql(query, connection)


def build_features(df):
    features = pd.DataFrame(index=df.index)

    distance = pd.to_numeric(
        df["distance_m"],
        errors="coerce",
    ).fillna(0)

    gradient = pd.to_numeric(
        df["gradient"],
        errors="coerce",
    ).fillna(0)

    gradient_reliable = (
        df["gradient_reliable"]
        .fillna(False)
        .astype(bool)
    )

    # Do not allow unreliable SRTM gradient estimates
    # to dominate the ML model.
    reliable_gradient = gradient.where(
        gradient_reliable,
        0,
    )

    surface = (
        df["surface"]
        .fillna("")
        .astype(str)
        .str.lower()
    )

    features["log_distance"] = np.log1p(
        distance.clip(lower=0)
    )

    features["gradient"] = reliable_gradient.clip(
        lower=0,
        upper=0.35,
    )

    features["gradient_reliable"] = (
        gradient_reliable.astype(int)
    )

    features["has_stairs"] = (
        df["has_stairs"]
        .fillna(False)
        .astype(bool)
        .astype(int)
    )

    features["wheelchair_inaccessible"] = (
        ~df["wheelchair_accessible"]
        .fillna(True)
        .astype(bool)
    ).astype(int)

    features["rough_surface"] = surface.isin(
        {
            "cobblestone",
            "gravel",
            "unpaved",
        }
    ).astype(int)

    features["unknown_surface"] = surface.isin(
        {
            "",
            "unknown",
            "none",
        }
    ).astype(int)

    return features[FEATURE_COLUMNS]
