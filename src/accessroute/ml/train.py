from pathlib import Path

import joblib

from sklearn.ensemble import IsolationForest
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from src.accessroute.ml.features import (
    FEATURE_COLUMNS,
    build_features,
    load_network_dataframe,
)


MODEL_PATH = Path(
    "models/accessibility_anomaly.joblib"
)


def train_model():
    print("Loading Manchester route network...")

    df = load_network_dataframe()

    print(
        f"Training on {len(df):,} route segments..."
    )

    if len(df) < 100:
        raise RuntimeError(
            "Not enough route segments to train model."
        )

    features = build_features(df)

    pipeline = Pipeline(
        [
            (
                "scaler",
                StandardScaler(),
            ),
            (
                "model",
                IsolationForest(
                    n_estimators=300,
                    contamination=0.03,
                    random_state=42,
                    n_jobs=-1,
                ),
            ),
        ]
    )

    pipeline.fit(features)

    MODEL_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    joblib.dump(
        {
            "pipeline": pipeline,
            "feature_columns": FEATURE_COLUMNS,
            "training_rows": len(df),
        },
        MODEL_PATH,
    )

    predictions = pipeline.predict(features)

    anomaly_count = int(
        (predictions == -1).sum()
    )

    print()
    print("ACCESSROUTE ML TRAINING COMPLETE")
    print("--------------------------------")
    print(
        f"Training segments: {len(df):,}"
    )
    print(
        f"ML anomalies identified: {anomaly_count:,}"
    )
    print(
        f"Anomaly rate: "
        f"{anomaly_count / len(df) * 100:.2f}%"
    )
    print(
        f"Model saved to: {MODEL_PATH}"
    )


if __name__ == "__main__":
    train_model()
