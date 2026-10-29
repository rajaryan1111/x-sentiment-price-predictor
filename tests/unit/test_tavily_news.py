"""Tavily adapter tests on an in-process mock transport; no network, no real key."""

import asyncio
import json
import os
import time
from datetime import UTC, datetime
from urllib.parse import quote

import httpx
import pytest

from xsentiment.errors import PayloadTooLargeError
from xsentiment.ingestion.tavily_news import (
    NewsCredentialsMissingError,
    NewsProviderError,
    TavilyNewsAdapter,
    sanitize_news_text,
    sanitize_news_url,
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


@pytest.mark.parametrize(
    ("timestamp", "expected", "note"),
    [
        ("2026-10-25T10:00:00Z", "2026-10-25T10:00:00+00:00", None),
        ("2026-10-25T10:00:00-04:00", "2026-10-25T14:00:00+00:00", None),
        ("2026-10-25T10:00:00", None, "publication timestamp has no timezone; timestamp withheld"),
        ("yesterday", None, "publication timestamp malformed; timestamp withheld"),
        (None, None, "publication date not supplied by the provider"),
        ("yesterday;token=private", None, "publication timestamp malformed; timestamp withheld"),
    ],
)
def test_publication_timestamp_normalization_and_missing_reason(
    timestamp: str | None, expected: str | None, note: str | None
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "results": [
                    {
                        "title": "t",
                        "url": "https://e.com/date",
                        "published_date": timestamp,
                    }
                ]
            },
        )

    (item,) = run_search(handler).items

    actual = item.published_at.isoformat() if item.published_at is not None else None
    assert actual == expected
    assert item.published_at_note == note


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


def test_naive_publication_timestamp_is_withheld_independent_of_host_timezone(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "results": [
                    {
                        "title": "t",
                        "url": "https://e.com/naive",
                        "published_date": "2026-10-25T10:00:00",
                    }
                ]
            },
        )

    previous_tz = os.environ.get("TZ")
    if hasattr(time, "tzset"):
        monkeypatch.setenv("TZ", "Pacific/Honolulu")
        time.tzset()
    try:
        (item,) = run_search(handler).items
    finally:
        if previous_tz is None:
            monkeypatch.delenv("TZ", raising=False)
        else:
            monkeypatch.setenv("TZ", previous_tz)
        if hasattr(time, "tzset"):
            time.tzset()

    assert item.published_at is None
    assert item.published_at_raw == "2026-10-25T10:00:00"
    assert item.published_at_note == "publication timestamp has no timezone; timestamp withheld"
    assert "timestamp withheld" in item.context_line()


def test_sensitive_url_query_values_and_userinfo_are_redacted() -> None:
    raw_url = (
        "https://user:password@example.com/story?token=abc123&"
        "API-Key=secret-value&id=42&campaign=spring#access_token=fragment-secret"
    )

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"results": [{"title": "t", "url": raw_url}]})

    result = run_search(handler)
    (item,) = result.items

    assert item.url == (
        "https://example.com/story?token=%5BREDACTED%5D&"
        "API-Key=%5BREDACTED%5D&id=42&campaign=spring"
    )
    for secret in ("password", "abc123", "secret-value", "fragment-secret", "user:"):
        assert secret not in item.url
        assert secret not in item.context_line()
        assert secret not in json.dumps(
            {
                field: getattr(item, field)
                for field in item.__dataclass_fields__
            },
            default=str,
        )
        assert secret not in json.dumps([item.context_line(), *result.excluded])
    assert "id=42" in item.url
    assert "campaign=spring" in item.url


def test_encoded_auth_parameter_names_and_auth_aliases_are_redacted() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "results": [
                    {
                        "title": "t",
                        "url": (
                            "https://e.com/story?%61pi%5Fkey=encoded-secret&"
                            "X-Amz-Security-Token=aws-secret;OAuth_Authorization=oauth-secret&"
                            "sig=signature-secret&article=42&code=oauth-code&nonce=nonce-secret"
                        ),
                    },
                    {"title": "t", "url": "javascript:alert(1)"},
                    {"title": "t", "url": "https://e.com:invalid/story"},
                ]
            },
        )

    result = run_search(handler)

    assert len(result.items) == 1
    sanitized = result.items[0].url
    assert sanitized == (
        "https://e.com/story?api_key=%5BREDACTED%5D&"
        "X-Amz-Security-Token=%5BREDACTED%5D&"
        "OAuth_Authorization=%5BREDACTED%5D&sig=%5BREDACTED%5D&article=42&"
        "code=%5BREDACTED%5D&nonce=%5BREDACTED%5D"
    )
    for secret in (
        "encoded-secret",
        "aws-secret",
        "oauth-secret",
        "signature-secret",
        "oauth-code",
        "nonce-secret",
    ):
        assert secret not in sanitized
        assert secret not in result.items[0].context_line()
    assert "article=42" in sanitized
    assert result.excluded == (
        "result 1: invalid url excluded",
        "result 2: invalid url excluded",
    )


def test_encoded_nested_urls_with_credentials_are_redacted() -> None:
    nested = (
        "https://user:inner-password@news.example/story?"
        "api_key=nested-secret&article=8#token=fragment-secret"
    )
    raw_url = "https://redirect.example/?next=" + quote(nested, safe="")

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"results": [{"title": "t", "url": raw_url}]})

    (item,) = run_search(handler).items

    for secret in ("inner-password", "nested-secret", "fragment-secret"):
        assert secret not in item.url
        assert secret not in item.context_line()
    assert "article%3D8" in item.url


@pytest.mark.parametrize(
    ("path", "expected_path"),
    [
        ("/oauth/token/secret-path", "/oauth/token/[REDACTED]"),
        ("/oauth/token", "/oauth/token"),
        ("/api_key/secret-path", "/api_key/[REDACTED]"),
        ("/api_key", "/api_key"),
    ],
)
def test_sensitive_path_segments_and_token_like_jwt_are_redacted(
    path: str, expected_path: str
) -> None:
    raw_url = (
        f"https://e.com{path}?next=ok/eyJhbGciOiJIUzI1NiJ9.abcdefghijk.klmnopqrst&"
        "signed=eyJhbGciOiJIUzI1NiJ9.abcdefghijk.klmnopqrst"
    )

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"results": [{"title": "t", "url": raw_url}]})

    (item,) = run_search(handler).items

    assert item.url == (
        f"https://e.com{expected_path}?next=%5BREDACTED%5D&signed=%5BREDACTED%5D"
    )
    assert "secret-path" not in item.context_line()
    assert "eyJhbGciOiJIUzI1NiJ9" not in item.context_line()


def test_provider_text_fields_redact_credentials_and_sanitize_embedded_urls() -> None:
    title = "Bearer top-secret-token from https://user:pw@news.example/item?api_key=embedded-secret"
    source = "source token=source-secret (https://source.example/?access_token=source-url-secret)"

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "results": [
                    {
                        "title": title,
                        "url": "https://news.example/story?id=42",
                        "source": source,
                    }
                ]
            },
        )

    (item,) = run_search(handler).items
    serialized = json.dumps(item.__dict__ if hasattr(item, "__dict__") else {
        field: getattr(item, field) for field in item.__dataclass_fields__
    }, default=str)

    for secret in (
        "top-secret-token",
        "pw",
        "embedded-secret",
        "source-secret",
        "source-url-secret",
    ):
        assert secret not in serialized
        assert secret not in item.context_line()
    assert "id=42" in item.url
    assert "[REDACTED]" in item.headline
    assert "[REDACTED]" in item.source


def test_text_sanitizer_keeps_nonsecret_text_and_removes_labelled_credentials() -> None:
    text = (
        "BTC wire: api_key=private123, article=42; Bearer bearer-secret "
        "and https://x.example/story?campaign=spring&token=link-secret."
    )
    sanitized = sanitize_news_text(text)

    assert "private123" not in sanitized
    assert "bearer-secret" not in sanitized
    assert "link-secret" not in sanitized
    assert "article=42" in sanitized
    assert "campaign=spring" in sanitized


def test_news_url_sanitizer_is_safe_for_user_supplied_jsonl() -> None:
    safe = sanitize_news_url(
        "https://user:private@news.example/a?Signature=private-sig&article=3#private-fragment"
    )

    assert safe == "https://news.example/a?Signature=%5BREDACTED%5D&article=3"
    for secret in ("private", "private-sig", "private-fragment"):
        assert secret not in safe


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


def test_response_ceiling_stops_streaming_before_the_whole_body_is_buffered() -> None:
    class ChunkedBody(httpx.AsyncByteStream):
        def __init__(self) -> None:
            self.chunks_yielded = 0

        async def __aiter__(self):
            for _ in range(5):
                self.chunks_yielded += 1
                yield b"x" * 400

        async def aclose(self) -> None:
            return None

    body = ChunkedBody()

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            stream=body,
            headers={"content-type": "application/json"},
        )

    with pytest.raises(PayloadTooLargeError, match="ceiling"):
        run_search(handler, max_results=1, max_body_bytes=512)

    assert body.chunks_yielded < 5


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
