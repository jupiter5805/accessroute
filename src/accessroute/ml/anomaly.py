from pathlib import Path

import joblib

from src.accessroute.ml.features import (
    build_features,
    load_network_dataframe,
)


MODEL_PATH = Path(
    "models/accessibility_anomaly.joblib"
)


def get_network_anomalies(limit=50):
    limit = max(
        1,
        min(int(limit), 500),
    )

    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            "Accessibility ML model has not been "
            "trained yet."
        )

    model_data = joblib.load(MODEL_PATH)

    pipeline = model_data["pipeline"]

    df = load_network_dataframe()

    features = build_features(df)

    predictions = pipeline.predict(
        features
    )

    decision_scores = pipeline.decision_function(
        features
    )

    df = df.copy()

    df["is_anomaly"] = (
        predictions == -1
    )

    # Isolation Forest:
    # lower decision scores = more unusual.
    # Reverse it so larger numbers represent
    # stronger anomalies.
    df["anomaly_score"] = -decision_scores

    anomalies = (
        df[df["is_anomaly"]]
        .sort_values(
            "anomaly_score",
            ascending=False,
        )
        .head(limit)
    )

    results = []

    for _, row in anomalies.iterrows():

        signals = []

        if bool(row["has_stairs"]):
            signals.append("stairs")

        if not bool(
            row["wheelchair_accessible"]
        ):
            signals.append(
                "wheelchair restriction"
            )

        if (
            bool(row["gradient_reliable"])
            and float(row["gradient"]) > 0.08
        ):
            signals.append(
                "steep gradient"
            )

        if row["surface"] in {
            "cobblestone",
            "gravel",
            "unpaved",
        }:
            signals.append("rough surface")

        if not bool(
            row["gradient_reliable"]
        ):
            signals.append(
                "uncertain gradient data"
            )

        results.append(
            {
                "edge_id": int(row["id"]),
                "source": str(
                    row["source"]
                ),
                "target": str(
                    row["target"]
                ),
                "distance_m": round(
                    float(row["distance_m"]),
                    1,
                ),
                "anomaly_score": round(
                    float(
                        row["anomaly_score"]
                    ),
                    4,
                ),
                "signals": signals,
                "source_coordinate": {
                    "latitude": float(
                        row[
                            "source_latitude"
                        ]
                    ),
                    "longitude": float(
                        row[
                            "source_longitude"
                        ]
                    ),
                },
                "target_coordinate": {
                    "latitude": float(
                        row[
                            "target_latitude"
                        ]
                    ),
                    "longitude": float(
                        row[
                            "target_longitude"
                        ]
                    ),
                },
            }
        )

    return {
        "model": "IsolationForest",
        "training_rows": model_data[
            "training_rows"
        ],
        "total_network_edges": len(df),
        "anomalies": results,
    }
