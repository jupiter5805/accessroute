from pathlib import Path

import joblib
import numpy as np
from sqlalchemy import text

from src.accessroute.database.db import engine
from src.accessroute.ml.features import (
    build_features,
    load_network_dataframe,
)


MODEL_PATH = Path(
    "models/accessibility_anomaly.joblib"
)


def normalise_scores(scores):
    scores = np.asarray(scores, dtype=float)

    if len(scores) == 0:
        return scores

    minimum = scores.min()
    maximum = scores.max()

    if maximum == minimum:
        return np.zeros(len(scores))

    return (
        (scores - minimum)
        / (maximum - minimum)
        * 100
    )


def score_network():
    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            "ML model has not been trained yet."
        )

    print("Loading trained AccessRoute model...")

    model_data = joblib.load(MODEL_PATH)
    pipeline = model_data["pipeline"]

    print("Loading Manchester route network...")

    df = load_network_dataframe()
    features = build_features(df)

    print(
        f"Scoring {len(df):,} route segments..."
    )

    predictions = pipeline.predict(features)

    raw_scores = -pipeline.decision_function(
        features
    )

    risk_scores = normalise_scores(
        raw_scores
    )

    df = df.copy()

    df["is_anomaly"] = predictions == -1
    df["ml_risk_score"] = risk_scores

    create_table = text("""
        CREATE TABLE IF NOT EXISTS route_edge_ml_scores (
            edge_id BIGINT PRIMARY KEY
                REFERENCES route_edges(id)
                ON DELETE CASCADE,

            ml_risk_score DOUBLE PRECISION
                NOT NULL,

            is_anomaly BOOLEAN
                NOT NULL,

            scored_at TIMESTAMPTZ
                NOT NULL DEFAULT NOW()
        )
    """)

    clear_scores = text("""
        DELETE FROM route_edge_ml_scores
    """)

    insert_score = text("""
        INSERT INTO route_edge_ml_scores (
            edge_id,
            ml_risk_score,
            is_anomaly
        )
        VALUES (
            :edge_id,
            :ml_risk_score,
            :is_anomaly
        )
    """)

    records = [
        {
            "edge_id": int(row.id),
            "ml_risk_score": round(
                float(row.ml_risk_score),
                4,
            ),
            "is_anomaly": bool(
                row.is_anomaly
            ),
        }
        for row in df.itertuples()
    ]

    with engine.begin() as connection:
        connection.execute(create_table)
        connection.execute(clear_scores)
        connection.execute(
            insert_score,
            records,
        )

    anomaly_count = int(
        df["is_anomaly"].sum()
    )

    print()
    print("ACCESSROUTE NETWORK ML SCORING")
    print("------------------------------")
    print(
        f"Segments scored: {len(df):,}"
    )
    print(
        f"Anomalies: {anomaly_count:,}"
    )
    print(
        f"Average ML risk: "
        f"{df['ml_risk_score'].mean():.2f}/100"
    )
    print(
        f"Highest ML risk: "
        f"{df['ml_risk_score'].max():.2f}/100"
    )


if __name__ == "__main__":
    score_network()
