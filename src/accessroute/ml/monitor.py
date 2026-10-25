from pathlib import Path

import joblib

from src.accessroute.ml.features import (
    build_features,
    load_network_dataframe,
)


MODEL_PATH = Path(
    "models/accessibility_anomaly.joblib"
)


def check_model_drift():
    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            "Accessibility ML model has not been trained yet."
        )

    model_data = joblib.load(MODEL_PATH)
    pipeline = model_data["pipeline"]

    df = load_network_dataframe()
    features = build_features(df)

    predictions = pipeline.predict(features)

    current_anomalies = int(
        (predictions == -1).sum()
    )

    current_rate = (
        current_anomalies / len(features)
        if len(features)
        else 0
    )

    expected_rate = 0.03
    difference = abs(current_rate - expected_rate)

    if difference <= 0.02:
        status = "stable"
    elif difference <= 0.05:
        status = "warning"
    else:
        status = "drift_detected"

    return {
        "model": "IsolationForest",
        "training_rows": model_data["training_rows"],
        "current_rows": len(features),
        "expected_anomaly_rate_percent": round(
            expected_rate * 100,
            2,
        ),
        "current_anomaly_rate_percent": round(
            current_rate * 100,
            2,
        ),
        "anomaly_rate_change_percent": round(
            difference * 100,
            2,
        ),
        "current_anomalies": current_anomalies,
        "status": status,
    }


if __name__ == "__main__":
    report = check_model_drift()

    print()
    print("ACCESSROUTE ML MONITORING")
    print("-------------------------")

    for key, value in report.items():
        print(f"{key}: {value}")
