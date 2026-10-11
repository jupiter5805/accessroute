from src.accessroute.ingestion.elevation import (
    calculate_gradient,
)


def test_gradient_calculation():
    gradient = calculate_gradient(
        source_elevation=40,
        target_elevation=45,
        distance_m=100,
    )

    assert gradient == 0.05


def test_downhill_gradient_is_absolute():
    gradient = calculate_gradient(
        source_elevation=50,
        target_elevation=40,
        distance_m=100,
    )

    assert gradient == 0.10


def test_zero_distance_returns_zero():
    gradient = calculate_gradient(
        source_elevation=50,
        target_elevation=60,
        distance_m=0,
    )

    assert gradient == 0.0
