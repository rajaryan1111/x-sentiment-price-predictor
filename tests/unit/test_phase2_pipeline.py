from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from xsentiment.ingestion.prices import PriceCandle
from xsentiment.pipeline.phase2 import (
    XPostRecord,
    build_close_targets,
    build_point_in_time_features,
    deduplicate_posts,
    profile_daily_price_coverage,
)


def candle(day: int, close: str) -> PriceCandle:
    return PriceCandle(
        "BTC-USD", datetime(2026, 10, day, tzinfo=UTC),
        Decimal(close) - Decimal("1"), Decimal(close) + Decimal("1"),
        Decimal(close), Decimal(close), Decimal("10"),
    )


def post(post_id: str, created: datetime, retrieved: datetime, score: float | None = 0.5) -> XPostRecord:
    return XPostRecord(
        post_id=post_id, created_at=created, retrieved_at=retrieved,
        text=f"post {post_id}", sentiment_score=score, likes=10,
    )


def test_post_rejects_naive_timestamp_and_invalid_sentiment() -> None:
    with pytest.raises(ValueError, match="created_at must be timezone-aware"):
        post("a", datetime(2026, 10, 20), datetime(2026, 10, 20, tzinfo=UTC))
    with pytest.raises(ValueError, match="between -1 and 1"):
        post("b", datetime(2026, 10, 20, tzinfo=UTC), datetime(2026, 10, 20, tzinfo=UTC), 2)


def test_deduplicate_posts_rejects_conflicting_duplicate_ids() -> None:
    timestamp = datetime(2026, 10, 20, tzinfo=UTC)
    with pytest.raises(ValueError, match="conflicting duplicate"):
        deduplicate_posts([post("same", timestamp, timestamp), post("same", timestamp, timestamp, -0.5)])


def test_point_in_time_features_exclude_late_arriving_and_future_posts() -> None:
    candles = [candle(20, "100"), candle(21, "110"), candle(22, "99")]
    cutoff = datetime(2026, 10, 21, tzinfo=UTC)
    posts = [
        post("available", cutoff - timedelta(hours=1), cutoff - timedelta(minutes=1), 0.8),
        post("late", cutoff - timedelta(hours=2), cutoff + timedelta(minutes=1), -0.9),
        post("future", cutoff + timedelta(minutes=1), cutoff + timedelta(minutes=1), -1.0),
    ]
    rows = build_point_in_time_features(candles, posts)
    assert rows[1].post_count_24h == 1
    assert rows[1].mean_sentiment_24h == pytest.approx(0.8)
    assert rows[1].previous_close == Decimal("100")
    assert rows[2].previous_close == Decimal("110")
    assert rows[2].previous_daily_return == pytest.approx(0.1)


def test_features_do_not_treat_unscored_posts_as_zero_sentiment() -> None:
    candles = [candle(20, "100"), candle(21, "110")]
    cutoff = datetime(2026, 10, 21, tzinfo=UTC)
    rows = build_point_in_time_features(candles, [post("unscored", cutoff - timedelta(hours=1), cutoff, None)])
    assert rows[1].post_count_24h == 1
    assert rows[1].scored_post_count_24h == 0
    assert rows[1].mean_sentiment_24h is None


def test_close_targets_include_n0_through_n5_and_omit_incomplete_tail() -> None:
    candles = [candle(day, str(100 + day)) for day in range(1, 9)]
    targets = build_close_targets(candles, max_horizon=5)
    first = targets[datetime(2026, 10, 1, tzinfo=UTC)]
    assert list(first) == [f"n+{i}" for i in range(6)]
    assert first["n+0"] == Decimal("101")
    assert first["n+5"] == Decimal("106")
    assert datetime(2026, 10, 4, tzinfo=UTC) not in targets


def test_price_coverage_reports_missing_days_without_filling_them() -> None:
    start, end = datetime(2026, 10, 20, tzinfo=UTC), datetime(2026, 10, 23, tzinfo=UTC)
    report = profile_daily_price_coverage(
        [candle(20, "100"), candle(22, "102")], start, end,
        now=datetime(2026, 10, 26, tzinfo=UTC),
    )
    assert report.expected_daily_bars == 3
    assert report.observed_daily_bars == 2
    assert report.missing_utc_days == ("2026-10-21",)
    assert not report.is_complete
