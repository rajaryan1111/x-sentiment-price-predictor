"""The predeclared long/flat strategy used for Sharpe, Sortino and drawdown.

The rule is fixed before any result is inspected, and it uses only information
available at the decision time:

* **Decision** at the UTC forecast cutoff ``t`` (00:00 UTC at the start of day ``n``)
  using the model's ``n+1`` close prediction and the last *completed* close
  ``close(t-1)``, which is the only close known at ``t``.
* **Signal**: go long when the predicted ``n+1`` close exceeds
  ``close(t-1) * (1 + 2 * fee_rate)``, i.e. only when the expected two-day move is
  larger than the round-trip cost. Otherwise stay flat.
* **Execution**: enter at ``close(t)`` (the first close observed after the decision)
  and exit at ``close(t+1)``, the predicted target itself. Consecutive decisions
  therefore chain without overlapping positions: the exit of the day-``t`` trade is
  the entry of the day-``t+1`` trade.
* **Net return** of a long day: ``close(t+1) / close(t) - 1 - 2 * fee_rate``.
  Flat days contribute exactly zero.
* **Benchmark**: the same windows held long unconditionally, charged the same
  round-trip fee, so the comparison is like-for-like.
* No shorting, no leverage, no position sizing, and no compounding inside a trade.

The signal compares a two-day predicted move with a one-day holding period; that is
deliberate and conservative — the rule only trades when the model's expected move
clears costs, and the realised return quoted is the return actually held.
"""
from __future__ import annotations

import math
from collections.abc import Iterable, Sequence
from dataclasses import dataclass

from xsentiment.backtesting.metrics import DEFAULT_PERIODS_PER_YEAR, return_metrics
from xsentiment.features.dataset import SupervisedRow

SIGNAL_HORIZON = "n+1"
ENTRY_LABEL = "n+0"
EXIT_LABEL = "n+1"
DEFAULT_FEE_RATE = 0.001  # 10 basis points per side
DEFAULT_MIN_RETURNS = 30


@dataclass(frozen=True, slots=True)
class StrategyAssumptions:
    """Every assumption needed to reproduce the risk metrics."""

    fee_rate: float = DEFAULT_FEE_RATE
    periods_per_year: int = DEFAULT_PERIODS_PER_YEAR
    risk_free_rate: float = 0.0
    minimum_acceptable_return: float = 0.0
    min_returns_for_risk_metrics: int = DEFAULT_MIN_RETURNS

    def __post_init__(self) -> None:
        if self.fee_rate < 0:
            raise ValueError("fee_rate must be non-negative")
        if self.periods_per_year <= 0:
            raise ValueError("periods_per_year must be positive")
        if self.min_returns_for_risk_metrics < 2:
            raise ValueError("min_returns_for_risk_metrics must be at least 2")


@dataclass(frozen=True, slots=True)
class StrategyResult:
    """Net return series and metrics for one model under the stated assumptions."""

    model: str
    assumptions: StrategyAssumptions
    returns: tuple[float, ...]
    benchmark_returns: tuple[float, ...]
    long_days: int
    metrics: dict[str, float | None]
    benchmark_metrics: dict[str, float | None]
    risk_metrics_unavailable_reason: str | None


def simulate_long_flat(
    predictions: Iterable[tuple[SupervisedRow, float]],
    *,
    model: str,
    assumptions: StrategyAssumptions | None = None,
) -> StrategyResult:
    """Simulate the rule on out-of-sample (row, predicted close) pairs only."""
    active = assumptions or StrategyAssumptions()
    round_trip = 2.0 * active.fee_rate

    ordered = sorted(predictions, key=lambda item: item[0].cutoff)
    returns: list[float] = []
    benchmark: list[float] = []
    long_days = 0
    for row, predicted_close in ordered:
        entry = row.labels.get(ENTRY_LABEL)
        exit_price = row.labels.get(EXIT_LABEL)
        reference = row.reference_close
        if entry is None or exit_price is None or entry <= 0:
            continue
        if not math.isfinite(predicted_close) or not math.isfinite(exit_price):
            continue
        held = exit_price / entry - 1.0 - round_trip
        benchmark.append(held)
        is_long = reference is not None and reference > 0 and predicted_close > (
            reference * (1.0 + round_trip)
        )
        if is_long:
            long_days += 1
            returns.append(held)
        else:
            returns.append(0.0)

    if not returns:
        raise ValueError("strategy requires at least one row with n+0 and n+1 labels")

    metrics = return_metrics(
        returns,
        periods_per_year=active.periods_per_year,
        risk_free_rate=active.risk_free_rate,
        minimum_acceptable_return=active.minimum_acceptable_return,
    )
    benchmark_metrics = return_metrics(
        benchmark,
        periods_per_year=active.periods_per_year,
        risk_free_rate=active.risk_free_rate,
        minimum_acceptable_return=active.minimum_acceptable_return,
    )
    metrics["exposure"] = long_days / len(returns)
    metrics["long_days"] = float(long_days)
    gains = [value for value in returns if value > 0]
    metrics["hit_rate"] = (len(gains) / long_days) if long_days else None

    reason: str | None = None
    if len(returns) < active.min_returns_for_risk_metrics:
        reason = (
            f"only {len(returns)} out-of-sample days are available; at least "
            f"{active.min_returns_for_risk_metrics} are required before Sharpe, Sortino "
            "and drawdown are reported"
        )
        metrics["sharpe_ratio"] = None
        metrics["sortino_ratio"] = None
        metrics["max_drawdown"] = None
    elif metrics["sharpe_ratio"] is None or metrics["sortino_ratio"] is None:
        reason = (
            "the strategy return series has zero dispersion over this sample, so the "
            "risk ratios are undefined"
        )
    return StrategyResult(
        model=model,
        assumptions=active,
        returns=tuple(returns),
        benchmark_returns=tuple(benchmark),
        long_days=long_days,
        metrics=metrics,
        benchmark_metrics=benchmark_metrics,
        risk_metrics_unavailable_reason=reason,
    )


def strategy_specification(assumptions: StrategyAssumptions | None = None) -> Sequence[str]:
    """Human-readable disclosure lines reused by the evaluation report."""
    active = assumptions or StrategyAssumptions()
    return (
        "Decision at 00:00 UTC at the start of day n, using the last completed close "
        f"close(n-1) and the model's {SIGNAL_HORIZON} close prediction.",
        f"Long only when predicted {SIGNAL_HORIZON} close > close(n-1) * "
        f"(1 + 2 x {active.fee_rate:g} fees); otherwise flat.",
        f"Entry at close(n), exit at close(n+1); net return = close(n+1)/close(n) - 1 - "
        f"2 x {active.fee_rate:g}.",
        f"Annualisation uses {active.periods_per_year} periods per year; risk-free rate "
        f"{active.risk_free_rate:g} and Sortino MAR {active.minimum_acceptable_return:g} "
        "are annualised before conversion.",
        "No shorting, no leverage, no position sizing; flat days contribute zero return.",
        "Benchmark: the same windows held long unconditionally with the same fees.",
    )
