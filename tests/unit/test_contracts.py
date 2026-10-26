from datetime import datetime, timezone

import pytest

from xsentiment.ingestion.contracts import SourceRecord


def test_source_record_rejects_naive_event_time() -> None:
    now = datetime.now(timezone.utc)
    with pytest.raises(ValueError, match="event_time must be timezone-aware"):
        SourceRecord("test", "id-1", datetime(2025, 1, 1), now, {})


def test_source_record_rejects_naive_retrieval_time() -> None:
    with pytest.raises(ValueError, match="retrieved_at must be timezone-aware"):
        SourceRecord("test", "id-1", None, datetime(2025, 1, 1), {})


def test_source_record_accepts_timezone_aware_timestamps() -> None:
    now = datetime.now(timezone.utc)
    record = SourceRecord("test", "id-1", now, now, {"sentiment": 0.2})
    assert record.retrieved_at == now
