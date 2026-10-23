import pandas as pd

from src.accessroute.ml.features import (
    FEATURE_COLUMNS,
    build_features,
)


def test_ml_feature_generation():
    df = pd.DataFrame(
        [
            {
                "distance_m": 100,
                "gradient": 0.05,
                "gradient_reliable": True,
                "has_stairs": False,
                "wheelchair_accessible": True,
                "surface": "paved",
            },
            {
                "distance_m": 20,
                "gradient": 4.5,
                "gradient_reliable": False,
                "has_stairs": True,
                "wheelchair_accessible": False,
                "surface": "cobblestone",
            },
        ]
    )

    features = build_features(df)

    assert list(features.columns) == FEATURE_COLUMNS

    assert len(features) == 2

    assert features.iloc[0]["gradient"] == 0.05

    # Unreliable extreme gradients must not
    # be fed directly into the ML model.
    assert features.iloc[1]["gradient"] == 0

    assert (
        features.iloc[1]["has_stairs"]
        == 1
    )

    assert (
        features.iloc[1][
            "wheelchair_inaccessible"
        ]
        == 1
    )

    assert (
        features.iloc[1]["rough_surface"]
        == 1
    )
