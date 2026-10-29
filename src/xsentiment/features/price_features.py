"""Price-derived features computed only from completed candles before the cutoff.

Every function here takes the candles that had *already completed* before the
forecast cutoff, ordered oldest to newest. The candle that starts at the cutoff is
never an input, so no target-period information can enter the feature matrix.

Values are ``None`` when the available history is shorter than the window needs.
Missing values are preserved; the model layer is responsible for any imputation,
and it must be fitted on training folds only.
"""
from __future__ import annotations

from collections.abc import Sequence
from statistics import fmean, pstdev

from xsentiment.ingestion.prices import PriceCandle

PRICE_FEATURE_NAMES: tuple[str, ...] = (
    "return_1d",
    "return_3d",
    "return_7d",
    "volatility_7d",
    "range_1d",
    "close_vs_sma_7d",
)

_RETURN_WINDOWS: tuple[tuple[str, int], ...] = (
    ("return_1d", 1),
    ("return_3d", 3),
    ("return_7d", 7),
)
_VOLATILITY_WINDOW = 7
_SMA_WINDOW = 7


def _closes(candles: Sequence[PriceCandle]) -> list[float]:
    return [float(candle.close) for candle in candles]


def _simple_return(closes: Sequence[float], lag: int) -> float | None:
    if len(closes) < lag + 1:
        return None
    previous = closes[-1 - lag]
    if previous == 0:  # pragma: no cover - OHLC validation rejects zero closes
        return None
    return closes[-1] / previous - 1.0


def daily_returns(closes: Sequence[float]) -> list[float]:
    """Simple close-to-close returns; empty when fewer than two closes exist."""
    return [
        closes[index] / closes[index - 1] - 1.0
        for index in range(1, len(closes))
        if closes[index - 1] != 0
    ]


def price_features(completed: Sequence[PriceCandle]) -> dict[str, float | None]:
    """Return the predeclared price feature group for a forecast cutoff.

    ``completed`` must end with the last candle that finished before the cutoff.
    """
    closes = _closes(completed)
    features: dict[str, float | None] = {}
    for name, lag in _RETURN_WINDOWS:
        features[name] = _simple_return(closes, lag)

    returns = daily_returns(closes)
    features["volatility_7d"] = (
        pstdev(returns[-_VOLATILITY_WINDOW:]) if len(returns) >= _VOLATILITY_WINDOW else None
    )

    if completed:
        last = completed[-1]
        close = float(last.close)
        features["range_1d"] = float(last.high - last.low) / close if close else None
    else:
        features["range_1d"] = None

    features["close_vs_sma_7d"] = (
        closes[-1] / fmean(closes[-_SMA_WINDOW:]) - 1.0
        if len(closes) >= _SMA_WINDOW and fmean(closes[-_SMA_WINDOW:]) != 0
        else None
    )
    return features
