import asyncio
from datetime import UTC, datetime

import httpx
import pytest
from pydantic import SecretStr

from xsentiment.config.settings import Settings
from xsentiment.ingestion.apify_x import (
    ApifyXAdapter,
    normalize_apify_post,
)


def configured_settings() -> Settings:
    return Settings(
        apify_api_token=SecretStr("test-token"),
        apify_actor_id="sample~reviewed-x-actor",
        http_timeout_seconds=2,
        http_max_response_bytes=500_000,
    )


def test_normalize_apify_post_supports_common_schema_and_preserves_nulls() -> None:
    retrieved = datetime(2026, 10, 26, tzinfo=UTC)
    record = normalize_apify_post(
        {
            "id": "123",
            "text": "BTC price action is interesting",
            "createdAt": "2026-10-25T12:30:00.000Z",
            "likeCount": 12,
            "retweetCount": 3,
            "viewCount": 99,
            "author": {"followers_count": 500},
            "url": "https://x.com/example/status/123",
        },
        retrieved_at=retrieved,
    )
    assert record.post_id == "123"
    assert record.created_at == datetime(2026, 10, 25, 12, 30, tzinfo=UTC)
    assert record.retrieved_at == retrieved
    assert record.likes == 12
    assert record.reposts == 3
    assert record.views == 99
    assert record.author_followers == 500
    assert record.provenance_url == "https://x.com/example/status/123"
    assert record.sentiment_score is None


def test_normalize_apify_post_supports_rfc822_timestamp_and_missing_engagement() -> None:
    record = normalize_apify_post(
        {"tweet_id": "x-1", "full_text": "BTC", "created_at": "Sun Oct 25 12:30:00 +0000 2026"}
    )
    assert record.created_at == datetime(2026, 10, 25, 12, 30, tzinfo=UTC)
    assert record.likes is None
    assert record.reposts is None
    assert record.views is None
    assert record.author_followers is None


@pytest.mark.parametrize(
    "item, message",
    [
        ({"text": "missing ID", "createdAt": "2026-10-25T12:00:00Z"}, "stable post ID"),
        ({"id": "1", "createdAt": "2026-10-25T12:00:00Z"}, "missing post text"),
        ({"id": "1", "text": "x", "createdAt": "2026-10-25T12:00:00"}, "include a timezone"),
    ],
)
def test_normalizer_rejects_missing_required_or_invalid_time(item: dict, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        normalize_apify_post(item)


def test_apify_config_is_required_before_network_activity() -> None:
    calls: list[str] = []
    transport = httpx.MockTransport(lambda request: calls.append(str(request.url)) or httpx.Response(500))
    client = httpx.AsyncClient(transport=transport)
    adapter = ApifyXAdapter(
        settings=Settings(http_timeout_seconds=2),
        client=client,
    )
    assert not adapter.is_configured()

    async def run() -> None:
        with pytest.raises(RuntimeError, match="Apify is not configured"):
            await adapter.run_and_fetch({"searchTerms": ["BTC"]})
        assert calls == []
        await adapter.aclose()

    asyncio.run(run())


def test_apify_run_uses_bearer_auth_cost_and_item_caps_and_fetches_dataset() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if request.method == "POST" and "/acts/" in request.url.path:
            assert request.headers["Authorization"] == "Bearer test-token"
            return httpx.Response(
                201,
                json={"id": "run-1", "status": "SUCCEEDED", "exitCode": 0, "defaultDatasetId": "ds-1"},
            )
        if request.method == "GET" and "/datasets/" in request.url.path:
            return httpx.Response(
                200,
                json=[{"id": "p1", "text": "BTC", "createdAt": "2026-10-25T12:00:00Z"}],
            )
        return httpx.Response(404)

    async def run() -> list:
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            async with ApifyXAdapter(settings=configured_settings(), client=client) as adapter:
                return await adapter.run_and_fetch(
                    {"searchTerms": ["BTC after:2026-04-29 before:2026-10-26"]},
                    max_items=25,
                    max_total_charge_usd=0.75,
                    timeout_seconds=120,
                )

    import asyncio
    records = asyncio.run(run())
    launch = next(request for request in requests if request.method == "POST")
    assert "maxItems=25" in str(launch.url)
    assert "maxTotalChargeUsd=0.75" in str(launch.url)
    assert "timeout=120" in str(launch.url)
    assert "token=" not in str(launch.url)
    assert records[0].post_id == "p1"


def test_apify_rejects_bad_caps_before_network_activity() -> None:
    calls: list[str] = []
    client = httpx.AsyncClient(
        transport=httpx.MockTransport(lambda request: calls.append(str(request.url)) or httpx.Response(500))
    )
    adapter = ApifyXAdapter(settings=configured_settings(), client=client)

    async def run() -> None:
        with pytest.raises(ValueError, match="max_items"):
            await adapter.run_and_fetch({}, max_items=5000)
        with pytest.raises(ValueError, match="max_total_charge_usd"):
            await adapter.run_and_fetch({}, max_total_charge_usd=0)
        assert calls == []
        await adapter.aclose()

    import asyncio
    asyncio.run(run())
