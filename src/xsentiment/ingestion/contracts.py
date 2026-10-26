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
