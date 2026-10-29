"""These tests use a clearly labelled synthetic fixture, never provider data."""

import math
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from xsentiment.features.dataset import SupervisedRow, build_supervised_dataset
from xsentiment.ingestion.contracts import XPostRecord
from xsentiment.ingestion.prices import PriceCandle
from xsentiment.models.evaluation import (
    eligible_rows,
    evaluate_walk_forward,
    mean_mae_by_model,
)

START = datetime(2026, 1, 1, tzinfo=UTC)


def synthetic_candles(days: int) -> list[PriceCandle]:
    candles: list[PriceCandle] = []
    for index in range(days):
        close = 100.0 + 6.0 * math.sin(index / 4.0) + 0.4 * index
        value = Decimal(str(round(close, 6)))
        candles.append(
            PriceCandle(
                product_id="BTC-USD",
                timestamp=START + timedelta(days=index),
                low=value * Decimal("0.99"),
                high=value * Decimal("1.01"),
                open=value,
                close=value,
                volume=Decimal("3"),
            )
        )
    return candles


def synthetic_posts(candles: list[PriceCandle]) -> list[XPostRecord]:
    posts: list[XPostRecord] = []
    for index, candle in enumerate(candles[1:], start=1):
        posts.append(
            XPostRecord(
                post_id=f"p{index}",
                created_at=candle.timestamp - timedelta(hours=1),
                retrieved_at=candle.timestamp - timedelta(minutes=30),
                text=f"synthetic post {index}",
                sentiment_score=round(math.sin(index / 3.0), 4),
            )
        )
    return posts


def test_every_model_is_scored_on_identical_folds_and_rows() -> None:
    candles = synthetic_candles(120)
    rows = build_supervised_dataset(candles, synthetic_posts(candles))

    result = evaluate_walk_forward(rows, min_train_samples=60, test_samples=20)

    assert result.folds
    expected_samples = sum(len(fold.test_indices) for fold in result.folds)
    assert {metrics.model for metrics in result.metrics} == {
        "naive",
        "price_only",
        "sentiment_price",
    }
    assert {metrics.horizon for metrics in result.metrics} == {f"n+{index}" for index in range(6)}
    for metrics in result.metrics:
        assert metrics.samples == expected_samples
        assert metrics.mae >= 0
        assert metrics.rmse >= metrics.mae - 1e-9
    assert result.assumptions["eligible_rows_with_sentiment"] > 0
    assert result.warnings == ()


def test_folds_keep_a_purge_gap_between_training_and_testing() -> None:
    candles = synthetic_candles(120)
    rows = build_supervised_dataset(candles, [])
    eligible = eligible_rows(rows)

    result = evaluate_walk_forward(rows, min_train_samples=60, test_samples=20, embargo_samples=5)

    for fold in result.folds:
        train_last = eligible[fold.train_indices[-1]].cutoff
        first_test = eligible[fold.test_indices[0]].cutoff
        assert (first_test - train_last).days == 6


def test_predictions_are_deterministic_and_never_come_from_a_training_block() -> None:
    candles = synthetic_candles(120)
    rows = build_supervised_dataset(candles, synthetic_posts(candles))

    first = evaluate_walk_forward(rows, min_train_samples=60, test_samples=20)
    second = evaluate_walk_forward(rows, min_train_samples=60, test_samples=20)

    assert first.predictions == second.predictions
    eligible = eligible_rows(rows)
    for fold in first.folds:
        train_cutoffs = {eligible[index].cutoff for index in fold.train_indices}
        test_cutoffs = {eligible[index].cutoff for index in fold.test_indices}
        assert not train_cutoffs & test_cutoffs
        predicted_in_fold = {
            prediction.cutoff for prediction in first.predictions if prediction.fold == fold.index
        }
        assert predicted_in_fold
        assert predicted_in_fold <= test_cutoffs


def test_candidate_model_is_flagged_when_no_scored_posts_exist() -> None:
    candles = synthetic_candles(120)
    rows = build_supervised_dataset(candles, [])

    result = evaluate_walk_forward(rows, min_train_samples=60, test_samples=20)

    assert result.assumptions["eligible_rows_with_sentiment"] == 0
    assert any("not identifiable" in warning for warning in result.warnings)
    assert result.predictions
    assert any(metrics.model == "price_only" for metrics in result.metrics)


def test_strategies_are_derived_only_from_out_of_sample_signal_predictions() -> None:
    candles = synthetic_candles(120)
    rows = build_supervised_dataset(candles, synthetic_posts(candles))

    result = evaluate_walk_forward(rows, min_train_samples=60, test_samples=20)
    expected_days = sum(len(fold.test_indices) for fold in result.folds)

    assert set(result.strategies) == {"naive", "price_only", "sentiment_price"}
    for strategy in result.strategies.values():
        assert len(strategy.returns) == expected_days
        assert len(strategy.benchmark_returns) == expected_days
        assert strategy.metrics["periods"] == float(expected_days)


def test_short_history_reports_why_evaluation_cannot_run() -> None:
    candles = synthetic_candles(40)
    rows = build_supervised_dataset(candles, [])

    result = evaluate_walk_forward(rows, min_train_samples=60, test_samples=20)

    assert result.folds == ()
    assert not result.has_predictions
    assert result.metrics == ()
    assert "walk_forward" in result.unavailable


def test_mean_mae_by_model_covers_every_model() -> None:
    candles = synthetic_candles(120)
    rows = build_supervised_dataset(candles, [])

    summary = mean_mae_by_model(evaluate_walk_forward(rows, min_train_samples=60, test_samples=20))

    assert set(summary) == {"naive", "price_only", "sentiment_price"}
    assert all(value >= 0 for value in summary.values())


def test_duplicate_cutoffs_fail_closed() -> None:
    row = SupervisedRow(
        cutoff=START,
        reference_close=100.0,
        entry_open=100.0,
        features={},
        labels={f"n+{index}": 100.0 for index in range(6)},
    )
    with pytest.raises(ValueError, match="duplicate forecast cutoffs"):
        eligible_rows([row, row])
