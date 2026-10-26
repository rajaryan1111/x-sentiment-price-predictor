from decimal import Decimal

import pytest

from xsentiment.models.baseline import persistence_forecast


def test_persistence_forecast_returns_all_six_horizons_in_order() -> None:
    forecast = persistence_forecast(Decimal("67123.45"))

    assert list(forecast) == [f"n+{horizon}" for horizon in range(6)]
    assert list(forecast.values()) == [Decimal("67123.45")] * 6


@pytest.mark.parametrize(
    "price",
    [Decimal("0"), Decimal("-1"), Decimal("NaN"), Decimal("Infinity")],
)
def test_persistence_forecast_rejects_invalid_prices(price: Decimal) -> None:
    with pytest.raises(ValueError, match="finite positive price"):
        persistence_forecast(price)


def test_persistence_forecast_requires_decimal_input() -> None:
    with pytest.raises(ValueError, match="must be a Decimal"):
        persistence_forecast(100.0)  # type: ignore[arg-type]
