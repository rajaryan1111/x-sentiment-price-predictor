from datetime import UTC, datetime, timedelta, timezone

import pytest

from xsentiment.ingestion.contracts import SourceRecord, XPostRecord


def test_source_record_rejects_naive_event_time() -> None:
    now = datetime.now(UTC)
    with pytest.raises(ValueError, match="event_time must be timezone-aware"):
        SourceRecord("test", "id-1", datetime(2025, 1, 1), now, {})


def test_source_record_rejects_naive_retrieval_time() -> None:
    with pytest.raises(ValueError, match="retrieved_at must be timezone-aware"):
        SourceRecord("test", "id-1", None, datetime(2025, 1, 1), {})


def test_source_record_accepts_timezone_aware_timestamps() -> None:
    now = datetime.now(UTC)
    record = SourceRecord("test", "id-1", now, now, {"sentiment": 0.2})
    assert record.retrieved_at == now


def test_blank_optional_provider_credentials_are_not_configured() -> None:
    from xsentiment.config.settings import Settings

    settings = Settings(apify_api_token="", apify_actor_id="  ", tavily_api_key="")
    assert settings.apify_api_token is None
    assert settings.apify_actor_id is None
    assert settings.tavily_api_key is None


def test_x_post_normalizes_offsets_and_preserves_raw_provenance() -> None:
    created = datetime(2026, 10, 25, 12, 30, tzinfo=timezone(timedelta(hours=-5)))
    record = XPostRecord(
        post_id=" 123 ",
        created_at=created,
        retrieved_at=created + timedelta(minutes=5),
        text="BTC",
        source_created_at_raw="2026-10-25T12:30:00-05:00",
        source_utc_offset="-05:00",
        author_id="author-1",
        query_mode="cashtag",
        query="$BTC",
    )

    assert record.post_id == "123"
    assert record.created_at == datetime(2026, 10, 25, 17, 30, tzinfo=UTC)
    assert record.retrieved_at == datetime(2026, 10, 25, 17, 35, tzinfo=UTC)
    assert record.source_created_at_raw == "2026-10-25T12:30:00-05:00"
    assert record.source_utc_offset == "-05:00"
    assert record.author_id == "author-1"
    assert record.query_mode == "cashtag"
    assert record.query == "$BTC"
    assert record.schema_version == "x-post-v1"


def test_x_post_rejects_backdated_retrieval_and_invalid_counts() -> None:
    now = datetime(2026, 10, 25, tzinfo=UTC)
    with pytest.raises(ValueError, match="retrieved_at must not precede"):
        XPostRecord("1", now, now - timedelta(seconds=1), "BTC")
    with pytest.raises(ValueError, match="likes must be"):
        XPostRecord("1", now, now, "BTC", likes=True)
    with pytest.raises(ValueError, match="views must be"):
        XPostRecord("1", now, now, "BTC", views=1.5)  # type: ignore[arg-type]


def test_x_post_rejects_invalid_query_mode_hash_and_warnings() -> None:
    now = datetime(2026, 10, 25, tzinfo=UTC)
    with pytest.raises(ValueError, match="query_mode"):
        XPostRecord("1", now, now, "BTC", query_mode="hashtag")
    with pytest.raises(ValueError, match="source_record_hash"):
        XPostRecord("1", now, now, "BTC", source_record_hash="not-a-hash")
    with pytest.raises(ValueError, match="warnings"):
        XPostRecord("1", now, now, "BTC", warnings=("",))  # type: ignore[arg-type]
