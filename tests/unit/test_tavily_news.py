"""Tavily adapter tests on an in-process mock transport; no network, no real key."""

import asyncio
import json
from datetime import UTC, datetime

import httpx
import pytest

from xsentiment.errors import PayloadTooLargeError
from xsentiment.ingestion.tavily_news import (
    NewsCredentialsMissingError,
    NewsProviderError,
    TavilyNewsAdapter,
)

RETRIEVED = datetime(2026, 10, 26, tzinfo=UTC)


def transporting(handler) -> httpx.AsyncClient:
    return httpx.AsyncClient(transport=httpx.MockTransport(handler), follow_redirects=False)


def success_handler(request: httpx.Request) -> httpx.Response:
    payload = json.loads(request.content)
    assert "query" in payload and "max_results" in payload
    return httpx.Response(
        200,
        json={
            "results": [
                {
                    "title": "Bitcoin steadies after weekly range break",
                    "url": "https://example.com/a",
                    "published_date": "2026-10-25T10:00:00+00:00",
                    "source": "Example Wire",
                },
                {
                    "title": "Exchange inflows cool, ETF flows tick up",
                    "url": "https://example.com/b",
                },
                {
                    "title": "Bitcoin steadies after weekly range break",
                    "url": "https://example.com/a",
                },
            ]
        },
    )


def run_search(handler, query="BTC sentiment", **kwargs) -> object:
    async def execute():
        adapter = TavilyNewsAdapter(api_key="tvly-test-key", client=transporting(handler), **kwargs)
        try:
            result = await adapter.search(query, retrieved_at=RETRIEVED)
        except BaseException:
            await adapter.aclose()
            raise
        await adapter.aclose()
        return result

    return asyncio.run(execute())


def test_successful_response_is_normalized_with_explicit_availability() -> None:
    result = run_search(success_handler)

    assert [item.headline for item in result.items] == [
        "Bitcoin steadies after weekly range break",
        "Exchange inflows cool, ETF flows tick up",
    ]
    first, second = result.items
    assert first.published_at == datetime(2026, 10, 25, 10, tzinfo=UTC)
    assert first.source == "Example Wire"
    # publication time is genuinely absent in the provider payload -> stays absent
    assert second.published_at is None
    for item in result.items:
        assert item.provider == "tavily"
        assert item.retrieved_at == RETRIEVED
        assert item.payload_sha256 and len(item.payload_sha256) == 64
    assert result.excluded == ("result 2: duplicate url excluded",)
    assert "(2026-10-25," in first.context_line()
    assert "publication date not supplied" in second.context_line()


def test_duplicate_urls_are_excluded_exactly_once() -> None:
    result = run_search(success_handler)

    assert len(result.items) == 2
    assert "result 2: duplicate url excluded" in result.excluded


def test_missing_headline_is_excluded_with_a_reason_not_fabricated() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={"results": [{"url": "https://example.com/x"}, {"title": "ok", "url": "https://e.com/y"}]},
        )

    result = run_search(handler)

    assert [item.headline for item in result.items] == ["ok"]
    assert result.excluded == ("result 0: missing headline",)


def test_unparseable_publication_date_keeps_the_item_with_null_time() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={"results": [
                {"title": "t", "url": "https://e.com/z", "published_date": "yesterday"}
            ]},
        )

    (item,) = run_search(handler).items

    assert item.published_at is None


def test_empty_result_list_is_a_valid_outcome() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"results": []})

    result = run_search(handler)

    assert result.items == ()
    assert result.excluded == ()


def test_http_error_fails_bounded_without_exposing_the_key() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"error": "unauthorized"})

    with pytest.raises(NewsProviderError, match="HTTP 401") as excinfo:
        run_search(handler)

    assert "tvly-test-key" not in str(excinfo.value)


def test_timeout_maps_to_a_bounded_provider_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectTimeout("closing")

    with pytest.raises(NewsProviderError, match="timed out"):
        run_search(handler)


def test_malformed_json_body_fails_closed() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text="{not json")

    with pytest.raises(NewsProviderError, match="not valid JSON"):
        run_search(handler)


def test_response_body_without_a_results_list_fails_closed() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"detail": "weird"})

    with pytest.raises(NewsProviderError, match="no results list"):
        run_search(handler)


def test_oversized_response_hits_the_configured_ceiling() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={"results": [{"title": "t", "url": "https://e.com/1", "note": "x" * 4096}]},
        )

    with pytest.raises(PayloadTooLargeError, match="ceiling"):
        run_search(handler, max_results=1, max_body_bytes=1024)


def test_missing_credentials_is_an_explicit_condition() -> None:
    async def execute() -> None:
        adapter = TavilyNewsAdapter(api_key=None, client=transporting(success_handler))
        try:
            await adapter.search("BTC", retrieved_at=RETRIEVED)
        finally:
            await adapter.aclose()

    with pytest.raises(NewsCredentialsMissingError, match="no Tavily API key"):
        asyncio.run(execute())


def test_invalid_query_and_max_results_fail_closed() -> None:
    with pytest.raises(NewsProviderError, match="non-empty"):
        run_search(success_handler, query="   ")
    with pytest.raises(NewsProviderError, match="max_results"):
        run_search(success_handler, max_results=0)
