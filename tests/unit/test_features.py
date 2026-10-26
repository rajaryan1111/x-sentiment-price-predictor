from datetime import UTC, datetime
from decimal import Decimal
from statistics import pstdev

import pytest

from xsentiment.features.price_features import PRICE_FEATURE_NAMES, price_features
from xsentiment.features.sentiment import (
    VaderSentimentScorer,
    coverage,
    score_posts,
    scorer_identity,
)
from xsentiment.ingestion.contracts import XPostRecord
from xsentiment.ingestion.prices import PriceCandle


def make_candle(
    day: int,
    close: str,
    *,
    low: str | None = None,
    high: str | None = None,
    open_: str | None = None,
) -> PriceCandle:
    return PriceCandle(
        "BTC-USD",
        datetime(2026, 9, day, tzinfo=UTC),
        Decimal(low or close),
        Decimal(high or close),
        Decimal(open_ or close),
        Decimal(close),
        Decimal("1"),
    )


def make_post(post_id: str, text: str) -> XPostRecord:
    timestamp = datetime(2026, 9, 10, tzinfo=UTC)
    return XPostRecord(
        post_id=post_id, created_at=timestamp, retrieved_at=timestamp, text=text
    )


def test_price_features_return_every_declared_name_even_when_history_is_short() -> None:
    features = price_features([make_candle(1, "100"), make_candle(2, "101")])
    assert set(features) == set(PRICE_FEATURE_NAMES)
    assert features["return_1d"] == pytest.approx(0.01)
    assert features["return_3d"] is None
    assert features["return_7d"] is None
    assert features["volatility_7d"] is None
    assert features["close_vs_sma_7d"] is None
    assert price_features([])["return_1d"] is None


def test_price_features_match_known_values() -> None:
    closes = ["100", "101", "102", "103", "104", "105", "106", "108"]
    candles = [make_candle(index + 1, close) for index, close in enumerate(closes)]
    features = price_features(candles)

    assert features["return_1d"] == pytest.approx(108 / 106 - 1)
    assert features["return_3d"] == pytest.approx(108 / 104 - 1)
    assert features["return_7d"] == pytest.approx(108 / 100 - 1)
    last_seven = [float(close) for close in closes[-7:]]
    assert features["close_vs_sma_7d"] == pytest.approx(108 / (sum(last_seven) / 7) - 1)

    daily_returns = [
        float(closes[index]) / float(closes[index - 1]) - 1
        for index in range(1, len(closes))
    ]
    assert features["volatility_7d"] == pytest.approx(pstdev(daily_returns[-7:]))


def test_range_feature_uses_high_low_and_close_of_last_completed_candle() -> None:
    features = price_features([make_candle(1, "100", low="90", high="110")])
    assert features["range_1d"] == pytest.approx(0.2)


def test_vader_scorer_is_bounded_signed_and_versioned() -> None:
    scorer = VaderSentimentScorer()
    positive = scorer.score("Bitcoin is breaking out, huge gains today!")
    negative = scorer.score("Bitcoin is crashing, this is a catastrophic dump")

    assert scorer.name == "vader"
    assert scorer.version
    assert positive is not None and 0.0 < positive <= 1.0
    assert negative is not None and -1.0 <= negative < 0.0
    assert scorer.score("   ") is None


def test_scorer_rejects_non_string_text_and_scores_unicode_without_crashing() -> None:
    scorer = VaderSentimentScorer()
    with pytest.raises(TypeError, match="string"):
        scorer.score(None)  # type: ignore[arg-type]

    emoji_text = scorer.score("🚀🚀 huge gains for Bitcoin holders today!! 🚀🚀")
    assert emoji_text is not None
    assert 0.0 < emoji_text <= 1.0
    # non-breaking space is unicode blank, too
    assert scorer.score("\n\t\u00a0 ") is None


def test_scorer_identity_records_the_installed_version() -> None:
    identity = scorer_identity(VaderSentimentScorer())

    assert identity["scorer"] == "vader"
    assert identity["version"] and identity["version"][0].isdigit()


def test_scored_posts_match_across_repeat_runs() -> None:
    posts = [
        make_post("a", "Bitcoin to the moon, huge bull run"),
        make_post("c", "This crash is terrible news for holders"),
    ]

    first = score_posts(posts)
    second = score_posts(posts)

    assert [(post.post_id, post.sentiment_score) for post in first] == [
        (post.post_id, post.sentiment_score) for post in second
    ]


def test_score_posts_fills_scores_and_reports_coverage() -> None:
    posts = [
        make_post("a", "Bitcoin to the moon, huge bull run"),
        make_post("b", "This crash is terrible news for holders"),
    ]
    scored = score_posts(posts)

    assert scored[0].sentiment_score is not None and scored[0].sentiment_score > 0
    assert scored[1].sentiment_score is not None and scored[1].sentiment_score < 0
    assert scored[0].post_id == "a"
    assert coverage(scored) == {"posts": 2, "scored_posts": 2, "unscored_posts": 0}
    assert coverage([]) == {"posts": 0, "scored_posts": 0, "unscored_posts": 0}
