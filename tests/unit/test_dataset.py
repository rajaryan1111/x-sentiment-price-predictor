from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from xsentiment.features.dataset import (
    HORIZON_LABELS,
    build_supervised_dataset,
    summarize,
)
from xsentiment.ingestion.contracts import XPostRecord
from xsentiment.ingestion.prices import PriceCandle


def make_candle(day: int, close: str, *, open_: str | None = None) -> PriceCandle:
    return PriceCandle(
        "BTC-USD",
        datetime(2026, 9, day, tzinfo=UTC),
        Decimal(close),
        Decimal(close),
        Decimal(open_ or close),
        Decimal(close),
        Decimal("5"),
    )


def candles_from(closes: list[str], *, start_day: int = 1) -> list[PriceCandle]:
    return [make_candle(start_day + index, close) for index, close in enumerate(closes)]


def make_post(
    post_id: str,
    created: datetime,
    retrieved: datetime,
    score: float | None,
) -> XPostRecord:
    return XPostRecord(
        post_id=post_id,
        created_at=created,
        retrieved_at=retrieved,
        text=f"post {post_id}",
        sentiment_score=score,
    )


def test_labels_exist_only_when_the_whole_forward_horizon_exists() -> None:
    rows = build_supervised_dataset(candles_from([str(100 + index) for index in range(8)]), [])

    assert len(rows) == 8
    assert set(rows[0].labels) == set(HORIZON_LABELS)
    assert rows[0].labels["n+0"] == 100.0
    assert rows[0].labels["n+5"] == 105.0
    assert rows[2].has_full_horizon
    assert rows[3].labels == {}
    assert rows[-1].labels == {}
    assert [row.cutoff for row in rows] == sorted(row.cutoff for row in rows)


def test_features_never_use_the_candle_that_starts_at_the_cutoff() -> None:
    rows = build_supervised_dataset(candles_from(["100", "101", "102", "200"]), [])
    last = rows[-1]

    assert last.reference_close == 102.0
    assert last.features["return_1d"] == pytest.approx(102 / 101 - 1)
    assert last.features["close_vs_sma_7d"] is None
    assert last.entry_open == 200.0
    assert last.labels == {}


def test_sentiment_features_use_only_posts_available_by_the_cutoff() -> None:
    candles = candles_from(["100", "101", "102", "103"])
    cutoff = datetime(2026, 9, 3, tzinfo=UTC)
    posts = [
        make_post("in_window", cutoff - timedelta(hours=1), cutoff - timedelta(minutes=1), 0.5),
        make_post("late", cutoff - timedelta(hours=2), cutoff + timedelta(seconds=1), -0.5),
        make_post("future", cutoff + timedelta(seconds=1), cutoff + timedelta(seconds=1), -1.0),
    ]

    row = {row.cutoff: row for row in build_supervised_dataset(candles, posts)}[cutoff]

    assert row.features["post_count_24h"] == 1.0
    assert row.features["scored_post_count_24h"] == 1.0
    assert row.features["mean_sentiment_24h"] == pytest.approx(0.5)
    assert row.has_sentiment


def test_missing_sentiment_stays_null_and_volume_still_counts() -> None:
    candles = candles_from(["100", "101"])
    cutoff = datetime(2026, 9, 2, tzinfo=UTC)
    posts = [make_post("unscored", cutoff - timedelta(hours=1), cutoff, None)]

    row = {row.cutoff: row for row in build_supervised_dataset(candles, posts)}[cutoff]

    assert row.features["post_count_24h"] == 1.0
    assert row.features["scored_post_count_24h"] == 0.0
    assert row.features["mean_sentiment_24h"] is None
    assert not row.has_sentiment

    empty_row = build_supervised_dataset(candles, [])[1]
    assert empty_row.features["mean_sentiment_24h"] is None
    assert empty_row.features["post_count_24h"] == 0.0


def test_unfinished_current_day_is_dropped_from_features_and_labels() -> None:
    candles = candles_from([str(100 + index) for index in range(5)])
    now = datetime(2026, 9, 5, 12, tzinfo=UTC)

    rows = build_supervised_dataset(candles, [], now=now)

    assert [row.cutoff for row in rows] == [
        datetime(2026, 9, day, tzinfo=UTC) for day in range(1, 5)
    ]
    assert all(row.labels == {} for row in rows)


def test_summarize_reports_counts_without_post_text() -> None:
    candles = candles_from([str(100 + index) for index in range(8)])
    now = datetime(2026, 9, 8, 6, tzinfo=UTC)
    cutoff = datetime(2026, 9, 7, tzinfo=UTC)
    posts = [make_post("scored", cutoff - timedelta(hours=1), cutoff, 0.25)]
    rows = build_supervised_dataset(candles, posts, now=now)

    summary = summarize(rows, posts, candles=candles, now=now)

    assert summary.rows == 7
    assert summary.rows_with_full_horizon == 2
    assert summary.rows_with_sentiment == 1
    assert summary.posts == 1
    assert summary.scored_posts == 1
    assert summary.unfinished_day_dropped
    assert summary.first_cutoff == datetime(2026, 9, 1, tzinfo=UTC)
    assert summary.last_cutoff == datetime(2026, 9, 7, tzinfo=UTC)
    assert summary.labels_available_from == datetime(2026, 9, 1, tzinfo=UTC)
