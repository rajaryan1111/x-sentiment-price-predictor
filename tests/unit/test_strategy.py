from datetime import UTC, datetime, timedelta

import pytest

from xsentiment.backtesting.strategy import (
    StrategyAssumptions,
    simulate_long_flat,
    strategy_specification,
)
from xsentiment.features.dataset import SupervisedRow


def make_signal(
    index: int,
    *,
    reference: float,
    entry: float,
    exit_price: float,
    predicted: float,
) -> tuple[SupervisedRow, float]:
    row = SupervisedRow(
        cutoff=datetime(2026, 1, 1, tzinfo=UTC) + timedelta(days=index),
        reference_close=reference,
        entry_open=entry,
        features={},
        labels={"n+0": entry, "n+1": exit_price},
    )
    return (row, predicted)


def test_long_days_pay_round_trip_fees_and_flat_days_earn_nothing() -> None:
    result = simulate_long_flat(
        [
            make_signal(0, reference=100.0, entry=100.0, exit_price=110.0, predicted=120.0),
            make_signal(1, reference=100.0, entry=100.0, exit_price=110.0, predicted=100.05),
        ],
        model="price_only",
    )

    assert result.long_days == 1
    assert result.metrics["exposure"] == pytest.approx(0.5)
    assert result.returns == pytest.approx((0.098, 0.0))
    assert result.benchmark_returns == pytest.approx((0.098, 0.098))
    assert result.metrics["hit_rate"] == pytest.approx(1.0)


def test_risk_metrics_are_withheld_until_enough_out_of_sample_days_exist() -> None:
    signals = [
        make_signal(index, reference=100.0, entry=100.0, exit_price=101.0, predicted=110.0)
        for index in range(5)
    ]

    result = simulate_long_flat(signals, model="price_only")

    assert result.metrics["sharpe_ratio"] is None
    assert result.metrics["sortino_ratio"] is None
    assert result.metrics["max_drawdown"] is None
    assert result.risk_metrics_unavailable_reason is not None
    assert "at least 30" in result.risk_metrics_unavailable_reason
    assert result.metrics["cumulative_return"] is not None


def test_a_never_trading_signal_reports_zero_dispersion_instead_of_a_ratio() -> None:
    signals = [
        make_signal(
            index,
            reference=100.0,
            entry=100.0 + index,
            exit_price=101.0 + index,
            predicted=100.0,
        )
        for index in range(40)
    ]

    result = simulate_long_flat(signals, model="naive", assumptions=StrategyAssumptions())

    assert result.long_days == 0
    assert all(value == 0.0 for value in result.returns)
    assert result.metrics["sharpe_ratio"] is None
    assert "zero dispersion" in (result.risk_metrics_unavailable_reason or "")


def test_costs_reduce_returns_and_assumptions_are_validated() -> None:
    signal = [make_signal(0, reference=100.0, entry=100.0, exit_price=110.0, predicted=120.0)]

    free = simulate_long_flat(signal, model="m", assumptions=StrategyAssumptions(fee_rate=0.0))
    costly = simulate_long_flat(
        signal, model="m", assumptions=StrategyAssumptions(fee_rate=0.005)
    )

    assert free.returns[0] == pytest.approx(0.10)
    assert free.returns[0] > costly.returns[0]
    with pytest.raises(ValueError, match="fee_rate"):
        StrategyAssumptions(fee_rate=-0.1)
    with pytest.raises(ValueError, match="min_returns_for_risk_metrics"):
        StrategyAssumptions(min_returns_for_risk_metrics=1)


def test_empty_signal_set_fails_closed() -> None:
    with pytest.raises(ValueError, match="at least one row"):
        simulate_long_flat([], model="m")


def test_specification_discloses_timing_costs_and_annualisation() -> None:
    disclosure = " ".join(strategy_specification())

    assert "00:00 UTC" in disclosure
    assert "close(n+1)/close(n)" in disclosure
    assert "365" in disclosure
    assert "no leverage" in disclosure
    assert "Benchmark" in disclosure
