"""Provider-neutral records preserving provenance and event time."""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


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
        if self.event_time is not None and self.event_time.tzinfo is None:
            raise ValueError("event_time must be timezone-aware")
        if self.retrieved_at.tzinfo is None:
            raise ValueError("retrieved_at must be timezone-aware")


@dataclass(frozen=True, slots=True)
class XPostRecord:
    """Normalized X post while preserving event time and retrieval/availability time."""

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

    def __post_init__(self) -> None:
        if not self.post_id.strip():
            raise ValueError("post_id must not be empty")
        for name, value in (
            ("created_at", self.created_at),
            ("retrieved_at", self.retrieved_at),
        ):
            if value.tzinfo is None or value.utcoffset() is None:
                raise ValueError(f"{name} must be timezone-aware")
        if not self.text.strip():
            raise ValueError("post text must not be empty")
        if self.sentiment_score is not None and not -1.0 <= self.sentiment_score <= 1.0:
            raise ValueError("sentiment_score must be between -1 and 1")
        for name in ("likes", "reposts", "views", "author_followers"):
            value = getattr(self, name)
            if value is not None and (isinstance(value, bool) or value < 0):
                raise ValueError(f"{name} must be non-negative")
