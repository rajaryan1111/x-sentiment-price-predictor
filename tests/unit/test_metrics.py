import pytest

from xsentiment.backtesting.metrics import (
    equity_curve,
    mae,
    max_drawdown,
    mean_error,
    return_metrics,
    rmse,
    sharpe_ratio,
    sortino_ratio,
)


def test_error_metrics_match_known_values() -> None:
    assert mae([1.0, -1.0]) == pytest.approx(1.0)
    assert rmse([3.0, 4.0]) == pytest.approx(12.5**0.5)
    assert mean_error([1.0, -3.0]) == pytest.approx(-1.0)
    with pytest.raises(ValueError, match="at least one"):
        mae([])


def test_equity_curve_and_max_drawdown_follow_a_known_path() -> None:
    returns = [0.1, -0.5, 0.1]

    assert equity_curve(returns) == pytest.approx([1.0, 1.1, 0.55, 0.605])
    assert max_drawdown(returns) == pytest.approx(0.5)
    assert max_drawdown([0.02, 0.03]) == 0.0
    with pytest.raises(ValueError, match="cannot be compounded"):
        equity_curve([-1.0])


def test_sharpe_ratio_matches_the_closed_form() -> None:
    value = sharpe_ratio([0.02, 0.0], periods_per_year=365)

    assert value == pytest.approx((1 / 2**0.5) * 365**0.5)
    assert sharpe_ratio([0.01]) is None
    assert sharpe_ratio([0.01, 0.01, 0.01]) is None


def test_sortino_ratio_uses_downside_deviation_and_the_mar() -> None:
    expected = (0.01 / (0.0001 / 2) ** 0.5) * 365**0.5

    assert sortino_ratio([-0.01, 0.03], periods_per_year=365) == pytest.approx(expected)
    assert sortino_ratio([0.01, 0.02], periods_per_year=365) is None
    assert sortino_ratio(
        [-0.01, 0.03], periods_per_year=365, minimum_acceptable_return=0.365
    ) != pytest.approx(expected)


def test_return_metrics_report_every_documented_field() -> None:
    metrics = return_metrics([0.02, -0.01, 0.03, 0.0], periods_per_year=365)

    assert metrics["periods"] == 4.0
    assert metrics["cumulative_return"] == pytest.approx(1.02 * 0.99 * 1.03 * 1.0 - 1)
    assert metrics["max_drawdown"] is not None and metrics["max_drawdown"] > 0
    assert metrics["sharpe_ratio"] is not None
    assert set(metrics) == {
        "periods",
        "mean_period_return",
        "cumulative_return",
        "annualised_volatility",
        "sharpe_ratio",
        "sortino_ratio",
        "max_drawdown",
    }


def test_invalid_inputs_fail_closed() -> None:
    with pytest.raises(ValueError, match="periods_per_year"):
        sharpe_ratio([0.01, 0.02], periods_per_year=0)
    with pytest.raises(ValueError, match="finite"):
        mae([float("inf")])
    with pytest.raises(ValueError, match="positive"):
        equity_curve([0.01], initial=0.0)
