"""Provider-neutral records preserving provenance and event time."""
from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

_QUERY_MODES = frozenset({"ticker", "cashtag", "keyword", "mixed"})
_HASH_RE = re.compile(r"^[0-9a-f]{64}$")


@dataclass(frozen=True, slots=True)
class DiscoveredItem:
    source_id: str
    url: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class SourceRecord:
    source_name: str
    source_id: str
    event_time: datetime | None
    retrieved_at: datetime
    payload: dict[str, Any]
    provenance_url: str | None = None
    content_hash: str | None = None

    def __post_init__(self) -> None:
        if not self.source_name.strip():
            raise ValueError("source_name must not be empty")
        if not self.source_id.strip():
            raise ValueError("source_id must not be empty")
        if self.event_time is not None:
            _require_aware(self.event_time, "event_time")
        _require_aware(self.retrieved_at, "retrieved_at")


@dataclass(frozen=True, slots=True)
class XPostRecord:
    """Normalized X post with separate event/retrieval times and provenance.

    Timestamps are normalized to UTC. The original provider timestamp string and
    UTC offset, when available, are retained for audit. ``retrieved_at`` is the
    first time this system observed the record and must never be backdated.
    """

    post_id: str
    created_at: datetime
    retrieved_at: datetime
    text: str
    sentiment_score: float | None = None
    likes: int | None = None
    reposts: int | None = None
    views: int | None = None
    author_followers: int | None = None
    provenance_url: str | None = None
    source_name: str = "apify_x"
    source_platform: str = "x"
    source_created_at_raw: str | None = None
    source_utc_offset: str | None = None
    author_id: str | None = None
    query_mode: str | None = None
    query: str | None = None
    source_record_hash: str | None = None
    schema_version: str = "x-post-v1"
    warnings: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.post_id, str) or not self.post_id.strip():
            raise ValueError("post_id must not be empty")
        if not isinstance(self.text, str) or not self.text.strip():
            raise ValueError("post text must not be empty")
        if not isinstance(self.source_name, str) or not self.source_name.strip():
            raise ValueError("source_name must not be empty")
        if not isinstance(self.source_platform, str) or not self.source_platform.strip():
            raise ValueError("source_platform must not be empty")
        if not isinstance(self.schema_version, str) or not self.schema_version.strip():
            raise ValueError("schema_version must not be empty")

        created_at = _require_aware(self.created_at, "created_at")
        retrieved_at = _require_aware(self.retrieved_at, "retrieved_at")
        if retrieved_at < created_at:
            raise ValueError("retrieved_at must not precede created_at")

        object.__setattr__(self, "post_id", self.post_id.strip())
        object.__setattr__(self, "created_at", created_at)
        object.__setattr__(self, "retrieved_at", retrieved_at)
        object.__setattr__(self, "source_name", self.source_name.strip())
        object.__setattr__(self, "source_platform", self.source_platform.strip().lower())
        object.__setattr__(self, "schema_version", self.schema_version.strip())

        if self.sentiment_score is not None:
            if isinstance(self.sentiment_score, bool) or not isinstance(
                self.sentiment_score, (int, float)
            ):
                raise ValueError("sentiment_score must be numeric or null")
            score = float(self.sentiment_score)
            if not math.isfinite(score) or not -1.0 <= score <= 1.0:
                raise ValueError("sentiment_score must be between -1 and 1")
            object.__setattr__(self, "sentiment_score", score)

        for name in ("likes", "reposts", "views", "author_followers"):
            value = getattr(self, name)
            if value is not None and (
                isinstance(value, bool) or not isinstance(value, int) or value < 0
            ):
                raise ValueError(f"{name} must be a non-negative integer or null")

        query_mode = self.query_mode.strip().lower() if self.query_mode else None
        if query_mode == "":
            query_mode = None
        if query_mode is not None and query_mode not in _QUERY_MODES:
            raise ValueError(
                "query_mode must be one of ticker, cashtag, keyword, mixed, or null"
            )
        object.__setattr__(self, "query_mode", query_mode)

        if self.source_record_hash is not None:
            if not isinstance(self.source_record_hash, str) or not _HASH_RE.fullmatch(
                self.source_record_hash.lower()
            ):
                raise ValueError("source_record_hash must be a 64-character hex SHA-256")
            object.__setattr__(self, "source_record_hash", self.source_record_hash.lower())

        if isinstance(self.warnings, str):
            raise ValueError("warnings must be a tuple/list of strings, not a string")
        if self.warnings:
            warnings = tuple(self.warnings)
            if any(not isinstance(item, str) or not item.strip() for item in warnings):
                raise ValueError("warnings must contain non-empty strings")
            object.__setattr__(self, "warnings", warnings)
        else:
            object.__setattr__(self, "warnings", ())

        for name in ("source_created_at_raw", "source_utc_offset", "author_id", "query"):
            value = getattr(self, name)
            if value is not None and not isinstance(value, str):
                raise ValueError(f"{name} must be a string or null")
            if isinstance(value, str) and not value.strip():
                object.__setattr__(self, name, None)


def _require_aware(value: datetime, name: str) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value.astimezone(UTC)
