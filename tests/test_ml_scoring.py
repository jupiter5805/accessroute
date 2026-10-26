import numpy as np

from src.accessroute.ml.score_network import (
    normalise_scores,
)


def test_normalise_ml_scores():
    result = normalise_scores(
        np.array([1.0, 2.0, 3.0])
    )

    assert result[0] == 0
    assert result[1] == 50
    assert result[2] == 100


def test_equal_scores_return_zero():
    result = normalise_scores(
        np.array([5.0, 5.0, 5.0])
    )

    assert list(result) == [0, 0, 0]
