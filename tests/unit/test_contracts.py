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


def test_blank_optional_provider_credentials_are_not_configured(monkeypatch) -> None:
    from xsentiment.config.settings import Settings

    monkeypatch.delenv("APIFY_API_TOKEN", raising=False)
    monkeypatch.delenv("APIFY_ACTOR_ID", raising=False)
    settings = Settings(apify_api_token="", apify_actor_id="  ", tavily_api_key="")
    assert settings.apify_api_token is None
    assert settings.apify_actor_id is None
    assert settings.tavily_api_key is None
