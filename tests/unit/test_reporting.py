"""Rendering tests on a clearly labelled synthetic fixture, never provider data."""

import math
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from xsentiment.features.dataset import build_supervised_dataset, summarize
from xsentiment.ingestion.contracts import XPostRecord
from xsentiment.ingestion.prices import PriceCandle
from xsentiment.models.evaluation import evaluate_walk_forward
from xsentiment.reporting.charts import (
    EMPTY_SENTIMENT_MESSAGE,
    price_points,
    render_sentiment_price_chart,
    sentiment_points,
)
from xsentiment.reporting.outlook import build_outlook, render_outlook_markdown
from xsentiment.reporting.report import render_evaluation_report

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
    return [
        XPostRecord(
            post_id=f"p{index}",
            created_at=candle.timestamp - timedelta(hours=1),
            retrieved_at=candle.timestamp - timedelta(minutes=30),
            text=f"synthetic post {index}",
            sentiment_score=round(math.sin(index / 3.0), 4),
        )
        for index, candle in enumerate(candles[1:], start=1)
    ]


def test_price_and_sentiment_series_are_built_from_observations_only() -> None:
    candles = synthetic_candles(5)
    posts = synthetic_posts(candles)
    rows = build_supervised_dataset(candles, posts)

    assert len(price_points(candles)) == 5
    assert len(sentiment_points(rows)) == sum(row.has_sentiment for row in rows)
    assert sentiment_points(build_supervised_dataset(candles, [])) == ()


def test_chart_renders_both_panels_and_marks_an_empty_sentiment_panel(tmp_path) -> None:
    candles = synthetic_candles(10)
    with_sentiment = tmp_path / "with.svg"
    without_sentiment = tmp_path / "without.svg"

    render_sentiment_price_chart(
        candles, build_supervised_dataset(candles, synthetic_posts(candles)), with_sentiment
    )
    render_sentiment_price_chart(
        candles, build_supervised_dataset(candles, []), without_sentiment
    )

    rich = with_sentiment.read_text(encoding="utf-8")
    empty = without_sentiment.read_text(encoding="utf-8")

    assert rich.startswith("<svg") and rich.rstrip().endswith("</svg>")
    assert rich.count("<polyline") == 2
    assert EMPTY_SENTIMENT_MESSAGE not in rich
    assert empty.count("<polyline") == 1
    assert EMPTY_SENTIMENT_MESSAGE in empty


def test_outlook_reports_coverage_predictions_and_limitations() -> None:
    candles = synthetic_candles(90)
    posts = synthetic_posts(candles)
    rows = build_supervised_dataset(candles, posts)
    summary = summarize(rows, posts, candles=candles)

    outlook = build_outlook(
        rows,
        summary,
        asset="BTC-USD",
        as_of=START + timedelta(days=91),
        scorer={"scorer": "vader", "version": "3.3.2"},
        news_context=["Example headline (2026-01-30, https://example.invalid/a)"],
    )
    rendered = render_outlook_markdown(outlook)

    assert outlook.cutoff == rows[-1].cutoff
    assert {prediction.horizon for prediction in outlook.predictions} == {
        f"n+{index}" for index in range(6)
    }
    assert {prediction.model for prediction in outlook.predictions} == {
        "naive",
        "price_only",
        "sentiment_price",
    }
    assert "current sentiment outlook" in rendered
    assert "vader" in rendered
    assert "Example headline" in rendered
    assert "not investment advice" in rendered
    assert "Data coverage" in rendered


def test_outlook_states_that_sentiment_is_unavailable() -> None:
    candles = synthetic_candles(30)
    rows = build_supervised_dataset(candles, [])
    summary = summarize(rows, [], candles=candles)

    outlook = build_outlook(rows, summary, asset="BTC-USD", as_of=START + timedelta(days=31))
    rendered = render_outlook_markdown(outlook)

    assert "No scored post sentiment is available" in rendered
    assert "No recent-news context was supplied" in rendered


def test_report_contains_measured_tables_and_withheld_metric_reasons() -> None:
    candles = synthetic_candles(120)
    posts = synthetic_posts(candles)
    rows = build_supervised_dataset(candles, posts)
    summary = summarize(rows, posts, candles=candles)
    evaluation = evaluate_walk_forward(rows, min_train_samples=60, test_samples=20)
    outlook = build_outlook(rows, summary, asset="BTC-USD", as_of=START + timedelta(days=121))

    report = render_evaluation_report(
        asset="BTC-USD",
        dataset_summary=summary,
        evaluation=evaluation,
        outlook=outlook,
        provenance={"price_snapshot": "prices.json", "price_snapshot_sha256": "deadbeef"},
        generated_at=START + timedelta(days=121),
        limitations=["Post text comes from a labelled synthetic fixture in this test."],
    )

    assert "## Out-of-sample forecast metrics" in report
    assert "| Model | Horizon | Samples | MAE (USD) | RMSE (USD) | Mean error (USD) |" in report
    assert "## Trading strategy and risk metrics" in report
    assert "Risk metrics withheld" in report
    assert "zero dispersion" in report
    assert "## Data and provenance" in report
    assert "deadbeef" in report
    assert "labelled as such" in report
    assert "synthetic fixture" in report


def test_report_explains_why_no_metrics_exist_when_history_is_short() -> None:
    candles = synthetic_candles(40)
    rows = build_supervised_dataset(candles, [])
    summary = summarize(rows, [], candles=candles)
    evaluation = evaluate_walk_forward(rows, min_train_samples=60, test_samples=20)

    report = render_evaluation_report(
        asset="BTC-USD",
        dataset_summary=summary,
        evaluation=evaluation,
        outlook=None,
        provenance={},
    )

    assert "No out-of-sample metrics were produced" in report
    assert "cannot fill a first fold" in report
    assert "No provenance metadata was recorded" in report
