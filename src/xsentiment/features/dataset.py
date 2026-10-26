"""Leakage-safe supervised dataset assembly for the BTC-USD daily horizons.

Each row is anchored at one UTC forecast cutoff (the start of day ``n``) and holds:

* price features computed from candles that completed strictly before the cutoff,
* sentiment features aggregated over the trailing ``(cutoff - 24h, cutoff]`` window
  using only posts published *and* first observed by the cutoff,
* close labels for horizons ``n+0`` through ``n+5`` when the whole forward horizon
  exists, and no labels at all otherwise.

Labels are never an input to a feature. The unfinished current UTC day is dropped
whenever ``now`` is supplied, so a partial intraday close cannot become a feature
or a label.
"""
from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime

from xsentiment.features.price_features import PRICE_FEATURE_NAMES, price_features
from xsentiment.features.sentiment import coverage
from xsentiment.ingestion.contracts import XPostRecord
from xsentiment.ingestion.prices import PriceCandle
from xsentiment.pipeline.phase2 import (
    build_close_targets,
    build_point_in_time_features,
    completed_candles,
    deduplicate_posts,
)

MAX_HORIZON = 5
HORIZON_LABELS: tuple[str, ...] = tuple(f"n+{horizon}" for horizon in range(MAX_HORIZON + 1))

SENTIMENT_FEATURE_NAMES: tuple[str, ...] = (
    "post_count_24h",
    "scored_post_count_24h",
    "mean_sentiment_24h",
    "positive_share_24h",
    "negative_share_24h",
)

FEATURE_GROUPS: dict[str, tuple[str, ...]] = {
    "price_only": PRICE_FEATURE_NAMES,
    "sentiment_price": PRICE_FEATURE_NAMES + SENTIMENT_FEATURE_NAMES,
}


@dataclass(frozen=True, slots=True)
class SupervisedRow:
    """One forecast cutoff with its features and (possibly empty) horizon labels."""

    cutoff: datetime
    reference_close: float | None
    entry_open: float | None
    features: dict[str, float | None]
    labels: dict[str, float]

    @property
    def has_full_horizon(self) -> bool:
        return all(label in self.labels for label in HORIZON_LABELS)

    @property
    def has_sentiment(self) -> bool:
        return self.features.get("mean_sentiment_24h") is not None


@dataclass(frozen=True, slots=True)
class DatasetSummary:
    rows: int
    rows_with_full_horizon: int
    rows_with_sentiment: int
    first_cutoff: datetime | None
    last_cutoff: datetime | None
    labels_available_from: datetime | None
    posts: int
    scored_posts: int
    unfinished_day_dropped: bool
    max_horizon: int


def _unfinished_day_dropped(candles: Sequence[PriceCandle], now: datetime | None) -> bool:
    if now is None:
        return False
    day_start = now.astimezone(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
    return any(candle.timestamp.astimezone(UTC) >= day_start for candle in candles)


def build_supervised_dataset(
    candles: Sequence[PriceCandle],
    posts: Iterable[XPostRecord],
    *,
    max_horizon: int = MAX_HORIZON,
    now: datetime | None = None,
) -> list[SupervisedRow]:
    """Assemble point-in-time rows for evaluation and for the current outlook.

    Pass already-scored posts (see ``xsentiment.features.sentiment.score_posts``);
    unscored posts still contribute to post volume but never to sentiment means.
    """
    if max_horizon < 0:
        raise ValueError("max_horizon must be non-negative")
    ordered = sorted(completed_candles(candles, now), key=lambda candle: candle.timestamp)
    deduped_posts = deduplicate_posts(posts)
    feature_rows = build_point_in_time_features(ordered, deduped_posts)
    targets = build_close_targets(ordered, max_horizon=max_horizon)
    if len(feature_rows) != len(ordered):  # pragma: no cover - defensive alignment guard
        raise ValueError("feature rows and completed candles are misaligned")

    rows: list[SupervisedRow] = []
    for index, candle in enumerate(ordered):
        cutoff = candle.timestamp.astimezone(UTC)
        feature_row = feature_rows[index]
        if feature_row.cutoff != cutoff:  # pragma: no cover - defensive alignment guard
            raise ValueError("feature row cutoff does not match its candle")
        features: dict[str, float | None] = price_features(ordered[:index])
        features["post_count_24h"] = float(feature_row.post_count_24h)
        features["scored_post_count_24h"] = float(feature_row.scored_post_count_24h)
        features["mean_sentiment_24h"] = feature_row.mean_sentiment_24h
        features["positive_share_24h"] = feature_row.positive_share_24h
        features["negative_share_24h"] = feature_row.negative_share_24h
        rows.append(
            SupervisedRow(
                cutoff=cutoff,
                reference_close=(
                    float(feature_row.previous_close)
                    if feature_row.previous_close is not None
                    else None
                ),
                entry_open=float(candle.open),
                features=features,
                labels={
                    label: float(value) for label, value in targets.get(cutoff, {}).items()
                },
            )
        )
    return rows


def summarize(
    rows: Sequence[SupervisedRow],
    posts: Iterable[XPostRecord],
    *,
    candles: Sequence[PriceCandle] = (),
    max_horizon: int = MAX_HORIZON,
    now: datetime | None = None,
) -> DatasetSummary:
    """Sanitized dataset profile for run manifests and reports (never post text)."""
    post_counts = coverage(posts)
    labelled = [row for row in rows if row.has_full_horizon]
    return DatasetSummary(
        rows=len(rows),
        rows_with_full_horizon=len(labelled),
        rows_with_sentiment=sum(row.has_sentiment for row in rows),
        first_cutoff=rows[0].cutoff if rows else None,
        last_cutoff=rows[-1].cutoff if rows else None,
        labels_available_from=labelled[0].cutoff if labelled else None,
        posts=post_counts["posts"],
        scored_posts=post_counts["scored_posts"],
        unfinished_day_dropped=_unfinished_day_dropped(candles, now),
        max_horizon=max_horizon,
    )
