"""Deterministic Phase 2 data-quality and point-in-time alignment primitives.

This module does not scrape X or infer sentiment. Provider adapters must supply
source timestamps, retrieval timestamps, and sentiment scores from a configured model.
"""
from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from statistics import fmean

from xsentiment.ingestion.prices import PriceCandle


@dataclass(frozen=True, slots=True)
class XPostRecord:
    """Normalized post with event time and system-availability time."""

    post_id: str
    created_at: datetime
    retrieved_at: datetime
    text: str
    sentiment_score: float | None = None
    likes: int | None = None
    reposts: int | None = None
    views: int | None = None
    author_followers: int | None = None

    def __post_init__(self) -> None:
        if not self.post_id.strip():
            raise ValueError("post_id must not be empty")
        for name, value in (("created_at", self.created_at), ("retrieved_at", self.retrieved_at)):
            if value.tzinfo is None or value.utcoffset() is None:
                raise ValueError(f"{name} must be timezone-aware")
        if not self.text.strip():
            raise ValueError("post text must not be empty")
        if self.sentiment_score is not None and not -1.0 <= self.sentiment_score <= 1.0:
            raise ValueError("sentiment_score must be between -1 and 1")
        for name in ("likes", "reposts", "views", "author_followers"):
            value = getattr(self, name)
            if value is not None and value < 0:
                raise ValueError(f"{name} must be non-negative")


@dataclass(frozen=True, slots=True)
class DailyFeatureRow:
    cutoff: datetime
    previous_close: Decimal | None
    previous_daily_return: float | None
    post_count_24h: int
    scored_post_count_24h: int
    mean_sentiment_24h: float | None
    positive_share_24h: float | None
    negative_share_24h: float | None


@dataclass(frozen=True, slots=True)
class PriceCoverageReport:
    product_id: str
    requested_start: datetime
    requested_end: datetime
    expected_daily_bars: int
    observed_daily_bars: int
    missing_utc_days: tuple[str, ...]
    duplicate_timestamps: tuple[str, ...]
    out_of_range_timestamps: tuple[str, ...]
    has_incomplete_current_day: bool

    @property
    def is_complete(self) -> bool:
        return (
            self.expected_daily_bars == self.observed_daily_bars
            and not self.missing_utc_days
            and not self.duplicate_timestamps
            and not self.out_of_range_timestamps
            and not self.has_incomplete_current_day
        )


def _utc(value: datetime, name: str) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value.astimezone(UTC)


def profile_daily_price_coverage(
    candles: Sequence[PriceCandle], start: datetime, end: datetime, *, now: datetime
) -> PriceCoverageReport:
    """Profile half-open [start, end) daily coverage without filling missing bars."""
    start_utc, end_utc, now_utc = _utc(start, "start"), _utc(end, "end"), _utc(now, "now")
    if start_utc >= end_utc:
        raise ValueError("start must be earlier than end")
    if any(
        value.hour or value.minute or value.second or value.microsecond
        for value in (start_utc, end_utc)
    ):
        raise ValueError("daily coverage bounds must be UTC midnight")
    if candles and any(c.product_id != candles[0].product_id for c in candles):
        raise ValueError("all candles must use the same product")
    expected = int((end_utc - start_utc).total_seconds() // 86400)
    in_range = [c for c in candles if start_utc <= c.timestamp < end_utc]
    timestamps = [c.timestamp for c in in_range]
    unique = set(timestamps)
    expected_days = {start_utc + timedelta(days=i) for i in range(expected)}
    observed_days = {stamp for stamp in unique if stamp in expected_days}
    missing = tuple(stamp.date().isoformat() for stamp in sorted(expected_days - observed_days))
    duplicate = tuple(sorted(stamp.isoformat() for stamp in unique if timestamps.count(stamp) > 1))
    outside = tuple(
        sorted(
            c.timestamp.isoformat()
            for c in candles
            if not start_utc <= c.timestamp < end_utc
        )
    )
    current_day_start = now_utc.replace(hour=0, minute=0, second=0, microsecond=0)
    incomplete = any(c.timestamp >= current_day_start for c in candles)
    return PriceCoverageReport(
        product_id=candles[0].product_id if candles else "",
        requested_start=start_utc,
        requested_end=end_utc,
        expected_daily_bars=expected,
        observed_daily_bars=len(observed_days),
        missing_utc_days=missing,
        duplicate_timestamps=duplicate,
        out_of_range_timestamps=outside,
        has_incomplete_current_day=incomplete,
    )


def deduplicate_posts(posts: Iterable[XPostRecord]) -> list[XPostRecord]:
    """Deduplicate by stable source ID; fail closed on conflicting duplicate IDs."""
    by_id: dict[str, XPostRecord] = {}
    for post in posts:
        prior = by_id.get(post.post_id)
        if prior is not None and prior != post:
            raise ValueError(f"conflicting duplicate post_id: {post.post_id}")
        by_id[post.post_id] = post
    return sorted(
        by_id.values(),
        key=lambda post: (_utc(post.created_at, "created_at"), post.post_id),
    )


def build_point_in_time_features(
    candles: Sequence[PriceCandle], posts: Iterable[XPostRecord]
) -> list[DailyFeatureRow]:
    """Build features at each UTC candle start using only information available by cutoff.

    Price features use prior completed candles only. Sentiment features aggregate
    posts in (cutoff-24h, cutoff] that were published and retrieved by cutoff.
    Current engagement counts are deliberately excluded as historical features.
    """
    normalized_posts = deduplicate_posts(posts)
    rows: list[DailyFeatureRow] = []
    prior_close: Decimal | None = None
    prior_prior_close: Decimal | None = None
    for candle in sorted(candles, key=lambda item: item.timestamp):
        cutoff = _utc(candle.timestamp, "candle.timestamp")
        window_start = cutoff - timedelta(days=1)
        available = [
            post for post in normalized_posts
            if window_start < _utc(post.created_at, "created_at") <= cutoff
            and _utc(post.retrieved_at, "retrieved_at") <= cutoff
        ]
        scores = [post.sentiment_score for post in available if post.sentiment_score is not None]
        mean_score = fmean(scores) if scores else None
        positive_share = sum(score > 0 for score in scores) / len(scores) if scores else None
        negative_share = sum(score < 0 for score in scores) / len(scores) if scores else None
        daily_return = (
            float(prior_close / prior_prior_close - Decimal("1"))
            if prior_close is not None and prior_prior_close not in (None, Decimal("0"))
            else None
        )
        rows.append(DailyFeatureRow(
            cutoff=cutoff,
            previous_close=prior_close,
            previous_daily_return=daily_return,
            post_count_24h=len(available),
            scored_post_count_24h=len(scores),
            mean_sentiment_24h=mean_score,
            positive_share_24h=positive_share,
            negative_share_24h=negative_share,
        ))
        prior_prior_close, prior_close = prior_close, candle.close
    return rows


def build_close_targets(
    candles: Sequence[PriceCandle], *, max_horizon: int = 5
) -> dict[datetime, dict[str, Decimal]]:
    """Build n+0 through n+max_horizon labels; omit incomplete forward horizons."""
    if max_horizon < 0:
        raise ValueError("max_horizon must be non-negative")
    ordered = sorted(candles, key=lambda candle: candle.timestamp)
    result: dict[datetime, dict[str, Decimal]] = {}
    for index, candle in enumerate(ordered):
        if index + max_horizon >= len(ordered):
            continue
        horizon = ordered[index : index + max_horizon + 1]
        timestamps = [_utc(item.timestamp, "candle.timestamp") for item in horizon]
        if any(
            later - earlier != timedelta(days=1)
            for earlier, later in zip(timestamps, timestamps[1:])
        ):
            continue
        result[_utc(candle.timestamp, "candle.timestamp")] = {
            f"n+{offset}": ordered[index + offset].close
            for offset in range(max_horizon + 1)
        }
    return result
