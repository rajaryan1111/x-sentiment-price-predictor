"""Forecast-error and risk metrics with explicit, documented conventions.

Forecast error and trading risk are different things. MAE/RMSE are computed on
predicted versus realised closes. Sharpe, Sortino and maximum drawdown are only
defined on a return series produced by a stated strategy, so they must never be
presented as evidence about forecast accuracy.

Conventions used here, and repeated in the evaluation report:

* returns are simple period returns, already net of any assumed costs,
* ``periods_per_year`` defaults to 365 because BTC-USD trades every day,
* the risk-free rate and the Sortino minimum acceptable return are annualised and
  converted to a per-period rate before use,
* sample standard deviation is used, so the Sharpe ratio needs at least two
  observations and returns ``None`` below that; the Sortino downside deviation is
  a root-mean-square and is defined for a single observation (the strategy's
  30-day gate withholds both ratios on short samples regardless),
* a degenerate series (zero dispersion) returns ``None`` instead of an infinite
  ratio.
"""
from __future__ import annotations

import math
from collections.abc import Sequence
from statistics import fmean, stdev

DEFAULT_PERIODS_PER_YEAR = 365


def _require_samples(values: Sequence[float], label: str) -> list[float]:
    if not values:
        raise ValueError(f"{label} requires at least one observation")
    cleaned = [float(value) for value in values]
    if any(not math.isfinite(value) for value in cleaned):
        raise ValueError(f"{label} observations must be finite")
    return cleaned


def mae(errors: Sequence[float]) -> float:
    """Mean absolute error of ``predicted - actual`` values."""
    return fmean(abs(value) for value in _require_samples(errors, "mae"))


def rmse(errors: Sequence[float]) -> float:
    """Root mean squared error of ``predicted - actual`` values."""
    cleaned = _require_samples(errors, "rmse")
    return math.sqrt(fmean(value * value for value in cleaned))


def mean_error(errors: Sequence[float]) -> float:
    """Signed mean error; negative values mean the model under-predicts."""
    return fmean(_require_samples(errors, "mean_error"))


def equity_curve(returns: Sequence[float], *, initial: float = 1.0) -> list[float]:
    """Compound a return series into an equity curve starting at ``initial``."""
    if initial <= 0:
        raise ValueError("initial equity must be positive")
    curve = [float(initial)]
    for value in _require_samples(returns, "equity_curve"):
        if value <= -1.0:
            raise ValueError("a return of -100% or less cannot be compounded")
        curve.append(curve[-1] * (1.0 + value))
    return curve


def max_drawdown(returns: Sequence[float]) -> float:
    """Largest peak-to-trough decline of the compounded equity curve.

    Returned as a non-negative fraction: 0.25 means a 25% drawdown.
    """
    curve = equity_curve(returns)
    peak = curve[0]
    worst = 0.0
    for value in curve:
        peak = max(peak, value)
        worst = max(worst, (peak - value) / peak)
    return worst


def sharpe_ratio(
    returns: Sequence[float],
    *,
    periods_per_year: int = DEFAULT_PERIODS_PER_YEAR,
    risk_free_rate: float = 0.0,
) -> float | None:
    """Annualised Sharpe ratio, or ``None`` when dispersion is zero."""
    if periods_per_year <= 0:
        raise ValueError("periods_per_year must be positive")
    cleaned = _require_samples(returns, "sharpe_ratio")
    if len(cleaned) < 2:
        return None
    excess = [value - risk_free_rate / periods_per_year for value in cleaned]
    spread = stdev(excess)
    if spread == 0:
        return None
    return fmean(excess) / spread * math.sqrt(periods_per_year)


def sortino_ratio(
    returns: Sequence[float],
    *,
    periods_per_year: int = DEFAULT_PERIODS_PER_YEAR,
    risk_free_rate: float = 0.0,
    minimum_acceptable_return: float = 0.0,
) -> float | None:
    """Annualised Sortino ratio using downside deviation about the MAR."""
    if periods_per_year <= 0:
        raise ValueError("periods_per_year must be positive")
    cleaned = _require_samples(returns, "sortino_ratio")
    period_mar = minimum_acceptable_return / periods_per_year
    downside = [min(value - period_mar, 0.0) for value in cleaned]
    deviation = math.sqrt(fmean(value * value for value in downside))
    if deviation == 0:
        return None
    mean_excess = fmean(cleaned) - risk_free_rate / periods_per_year
    return mean_excess / deviation * math.sqrt(periods_per_year)


def return_metrics(
    returns: Sequence[float],
    *,
    periods_per_year: int = DEFAULT_PERIODS_PER_YEAR,
    risk_free_rate: float = 0.0,
    minimum_acceptable_return: float = 0.0,
) -> dict[str, float | None]:
    """Bundle the reported return statistics; ``None`` where undefined."""
    cleaned = _require_samples(returns, "return_metrics")
    return {
        "periods": float(len(cleaned)),
        "mean_period_return": fmean(cleaned),
        "cumulative_return": equity_curve(cleaned)[-1] - 1.0,
        "annualised_volatility": (
            stdev(cleaned) * math.sqrt(periods_per_year) if len(cleaned) >= 2 else None
        ),
        "sharpe_ratio": sharpe_ratio(
            cleaned, periods_per_year=periods_per_year, risk_free_rate=risk_free_rate
        ),
        "sortino_ratio": sortino_ratio(
            cleaned,
            periods_per_year=periods_per_year,
            risk_free_rate=risk_free_rate,
            minimum_acceptable_return=minimum_acceptable_return,
        ),
        "max_drawdown": max_drawdown(cleaned),
    }
