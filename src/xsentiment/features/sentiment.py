"""Deterministic, versioned sentiment scoring for permitted X post text.

The default scorer is VADER (``vaderSentiment``, MIT), a rule-based lexicon model
designed for short social-media text. It is a documented, reproducible baseline:
it needs no network access, no model download and no GPU, and it returns a
compound score in [-1, 1].

Known limitations (see MODEL_PLAN.md and DECISIONS.md D-016): the lexicon is
English-oriented and not finance-specific, it does not resolve sarcasm or author
credibility, and it is not a substitute for a domain-tuned model such as FinBERT
or a crypto-specific lexicon. Replacing the scorer only requires another
``SentimentScorer`` implementation; nothing else in the pipeline changes.

Scoring never invents a value: text that is missing or blank yields ``None``,
which downstream code must keep as "unscored" rather than treating it as neutral.
"""
from __future__ import annotations

from collections.abc import Iterable
from dataclasses import replace
from importlib.metadata import PackageNotFoundError, version
from typing import Protocol, runtime_checkable

from xsentiment.ingestion.contracts import XPostRecord

DEFAULT_SCORER_NAME = "vader"
VADER_PACKAGE = "vaderSentiment"
MIN_SCORE = -1.0
MAX_SCORE = 1.0


@runtime_checkable
class SentimentScorer(Protocol):
    """Contract for a post-level sentiment scorer."""

    name: str
    version: str

    def score(self, text: str) -> float | None:
        """Return a score in [-1, 1], or None when the text cannot be scored."""


class ScorerUnavailableError(RuntimeError):
    """Raised when the configured sentiment scorer cannot be loaded."""


class VaderSentimentScorer:
    """VADER compound-score wrapper in the canonical [-1, 1] range."""

    name = DEFAULT_SCORER_NAME

    def __init__(self) -> None:
        try:
            from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
        except ImportError as exc:  # pragma: no cover - dependency is declared
            raise ScorerUnavailableError(
                f"{VADER_PACKAGE} is not installed; install the project dependencies "
                "before scoring posts"
            ) from exc
        self._analyzer = SentimentIntensityAnalyzer()

    @property
    def version(self) -> str:
        try:
            return version(VADER_PACKAGE)
        except PackageNotFoundError:  # pragma: no cover - defensive
            return "unknown"

    def score(self, text: str) -> float | None:
        if not isinstance(text, str):
            raise TypeError("sentiment scorer expects a string")
        if not text.strip():
            return None
        compound = float(self._analyzer.polarity_scores(text)["compound"])
        if not MIN_SCORE <= compound <= MAX_SCORE:  # pragma: no cover - defensive
            raise ValueError(f"sentiment scorer returned out-of-range value: {compound}")
        return compound


def score_posts(
    posts: Iterable[XPostRecord], scorer: SentimentScorer | None = None
) -> list[XPostRecord]:
    """Return copies of ``posts`` with ``sentiment_score`` filled by ``scorer``.

    Records whose text is unavailable keep a null score. Already-scored records are
    re-scored so one run always reflects exactly one documented scorer version.
    """
    active = scorer or VaderSentimentScorer()
    return [replace(post, sentiment_score=active.score(post.text)) for post in posts]


def scorer_identity(scorer: SentimentScorer) -> dict[str, str]:
    """Provenance for a run manifest: scorer name and exact installed version."""
    return {"scorer": scorer.name, "version": scorer.version}


def coverage(posts: Iterable[XPostRecord]) -> dict[str, int]:
    """Count posts and how many carry a usable score, without printing text."""
    total = 0
    scored = 0
    for post in posts:
        total += 1
        if post.sentiment_score is not None:
            scored += 1
    return {"posts": total, "scored_posts": scored, "unscored_posts": total - scored}
