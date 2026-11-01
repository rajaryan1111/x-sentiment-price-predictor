"""Exa adapter contract tests with a mock HTTP transport."""
from __future__ import annotations

import asyncio
import json
from datetime import UTC, date, datetime

import httpx
import pytest

from xsentiment.ingestion.exa_news import ExaNewsAdapter
from xsentiment.ingestion.tavily_news import NewsProviderError


def run_search(handler, **kwargs):
    async def execute():
        client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
        adapter = ExaNewsAdapter(api_key="exa-mock-key", client=client)
        try:
            result = await adapter.search(
                "Bitcoin market news",
                retrieved_at=datetime(2026, 11, 1, tzinfo=UTC),
                **kwargs,
            )
        finally:
            await adapter.aclose()
            await client.aclose()
        return result

    return asyncio.run(execute())


def test_exa_search_normalizes_results_and_sends_date_bounds() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url == "https://api.exa.ai/search"
        assert request.headers["x-api-key"] == "exa-mock-key"
        payload = json.loads(request.content)
        assert payload["type"] == "auto"
        assert payload["category"] == "news"
        assert payload["startPublishedDate"].startswith("2026-10-01T")
        assert payload["endPublishedDate"].startswith("2026-10-31T")
        return httpx.Response(
            200,
            json={
                "results": [
                    {
                        "title": "Bitcoin market update",
                        "url": "https://example.test/story?token=private&ref=7",
                        "publishedDate": "2026-10-30T12:30:00Z",
                        "author": "Example Desk",
                        "text": "ignored",
                    }
                ],
                "requestId": "ignored",
            },
        )

    (item,) = run_search(
        handler,
        start_date=date(2026, 10, 1),
        end_date=date(2026, 10, 31),
    ).items
    assert item.provider == "exa"
    assert item.published_at == datetime(2026, 10, 30, 12, 30, tzinfo=UTC)
    assert "token=%5BREDACTED%5D" in item.url
    assert "ref=7" in item.url


def test_exa_invalid_response_schema_is_a_bounded_provider_error() -> None:
    with pytest.raises(NewsProviderError, match="invalid results schema"):
        run_search(lambda _request: httpx.Response(200, json={"results": "not-a-list"}))


def test_exa_reversed_date_bounds_fail_before_http() -> None:
    def forbidden(_request: httpx.Request) -> httpx.Response:
        raise AssertionError("request should not be sent")

    with pytest.raises(NewsProviderError, match="start_date"):
        run_search(
            forbidden,
            start_date=date(2026, 10, 31),
            end_date=date(2026, 10, 1),
        )
