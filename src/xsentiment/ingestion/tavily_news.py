"""Optional Tavily news adapter: explicit credentials, bounded calls, context only.

News is contextual information for the outlook. It never becomes a model
feature (D-005) and never passes through the pipeline automatically: the
separate ``xsentiment fetch-news --confirm-live-call`` command is the only live
trigger, and a later ``run --news-file`` consumes the resulting JSONL. A missing
key is an explicit, graceful condition rather than a silent no-op.

The adapter enforces the project's safety policy (NFR4):

* one bounded POST with the configured timeout and response ceiling, never
  automatically retried;
* every normalized item keeps headline, URL, publication time when the
  provider actually carries one, retrieval time, source identity and a payload
  hash; nothing is invented, and malformed items are excluded with a reason;
* credential values and query parameters with secrets are never logged or
  included in error messages.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

import httpx

from xsentiment.config.settings import get_settings
from xsentiment.errors import PayloadTooLargeError

_SEARCH_URL = "https://api.tavily.com/search"
MAX_QUERY_CHARS = 400
MAX_RESULTS_CEILING = 20


class NewsCredentialsMissingError(ValueError):
    """Raised when news was requested but no provider key is configured."""


class NewsProviderError(RuntimeError):
    """Raised for bounded provider failures (HTTP, timeout, malformed body)."""


@dataclass(frozen=True, slots=True)
class NormalizedNewsItem:
    """One contextual news observation with explicit availability boundaries."""

    headline: str
    url: str
    published_at: datetime | None
    retrieved_at: datetime
    source: str
    provider: str
    payload_sha256: str

    def context_line(self) -> str:
        published = (
            self.published_at.date().isoformat()
            if self.published_at is not None
            else "publication date not supplied by the provider"
        )
        return f"{self.headline} ({published}, {self.url})"


@dataclass(frozen=True, slots=True)
class NewsResult:
    query: str
    retrieved_at: datetime
    items: tuple[NormalizedNewsItem, ...]
    excluded: tuple[str, ...]


def _parse_published(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        return datetime.fromisoformat(value.strip().replace("Z", "+00:00")).astimezone(UTC)
    except ValueError:
        return None


def _payload_hash(raw: Any) -> str:
    return hashlib.sha256(
        json.dumps(raw, sort_keys=True, default=str).encode("utf-8")
    ).hexdigest()


def _extract_text(item: dict[str, Any], *keys: str) -> str | None:
    for key in keys:
        value = item.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


class TavilyNewsAdapter:
    """Bounded search against the documented Tavily `/search` endpoint."""

    def __init__(
        self,
        *,
        api_key: str | None = None,
        client: httpx.AsyncClient | None = None,
        max_results: int = 5,
        max_body_bytes: int | None = None,
    ) -> None:
        settings = get_settings()
        key = api_key
        if key is None and settings.tavily_api_key is not None:
            key = settings.tavily_api_key.get_secret_value()
        self._api_key = (key or "").strip() or None
        self._owns_client = client is None
        self._client = client or httpx.AsyncClient(
            timeout=settings.http_timeout_seconds,
            follow_redirects=False,
            headers={
                "User-Agent": "XSentimentPricePredictor/0.1 (+research; contact repository owner)",
                "Accept": "application/json",
            },
        )
        if not 1 <= max_results <= MAX_RESULTS_CEILING:
            raise NewsProviderError(f"max_results must be within 1..{MAX_RESULTS_CEILING}")
        self._max_results = max_results
        self._max_body_bytes = max_body_bytes or settings.http_max_response_bytes

    async def aclose(self) -> None:
        if self._owns_client:
            await self._client.aclose()

    async def __aenter__(self) -> TavilyNewsAdapter:
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:  # noqa: ANN001
        await self.aclose()

    async def search(
        self,
        query: str,
        *,
        retrieved_at: datetime | None = None,
    ) -> NewsResult:
        """One bounded search; read-only, so it is never silently retried."""
        if not self._api_key:
            raise NewsCredentialsMissingError(
                "no Tavily API key is configured; set TAVILY_API_KEY in the environment "
                "or supply one to the adapter"
            )
        if not isinstance(query, str) or not query.strip():
            raise NewsProviderError("a non-empty search query is required")
        if len(query) > MAX_QUERY_CHARS:
            raise NewsProviderError(f"search query must not exceed {MAX_QUERY_CHARS} characters")
        moment = (retrieved_at or datetime.now(UTC)).astimezone(UTC)

        body = await self._post(query)
        raw_items = body.get("results") if isinstance(body, dict) else None
        if not isinstance(raw_items, list):
            raise NewsProviderError("tavily response body has no results list")

        items: list[NormalizedNewsItem] = []
        excluded: list[str] = []
        seen_urls: set[str] = set()
        for index, raw in enumerate(raw_items[: self._max_results]):
            if not isinstance(raw, dict):
                excluded.append(f"result {index}: not an object")
                continue
            headline = _extract_text(raw, "title", "headline")
            url = _extract_text(raw, "url", "link")
            if headline is None or url is None:
                excluded.append(
                    f"result {index}: missing " + ("headline" if headline is None else "url")
                )
                continue
            if url in seen_urls:
                excluded.append(f"result {index}: duplicate url excluded")
                continue
            seen_urls.add(url)
            items.append(
                NormalizedNewsItem(
                    headline=headline,
                    url=url,
                    published_at=_parse_published(raw.get("published_date")),
                    retrieved_at=moment,
                    source=_extract_text(raw, "source") or "tavily",
                    provider="tavily",
                    payload_sha256=_payload_hash(raw),
                )
            )
        return NewsResult(
            query=query,
            retrieved_at=moment,
            items=tuple(items),
            excluded=tuple(excluded),
        )

    async def _post(self, query: str) -> dict[str, Any]:
        try:
            # One bounded POST: news search is contextual, read-only and passed
            # to the provider as sent, so it is never automatically retried.
            response = await self._client.post(
                _SEARCH_URL,
                json={
                    "query": query,
                    "max_results": self._max_results,
                    "search_depth": "basic",
                },
                headers={"Authorization": f"Bearer {self._api_key}"},
            )
        except httpx.TimeoutException as exc:
            raise NewsProviderError(
                "tavily request timed out within the configured boundary"
            ) from exc
        except httpx.HTTPError as exc:
            raise NewsProviderError(
                f"tavily request failed with HTTP transport error {exc.__class__.__name__}"
            ) from exc
        if response.status_code != 200:
            raise NewsProviderError(f"tavily returned HTTP {response.status_code}")
        if len(response.content) > self._max_body_bytes:
            raise PayloadTooLargeError(
                f"tavily response exceeded the configured ceiling of "
                f"{self._max_body_bytes} bytes"
            )
        try:
            body = response.json()
        except (json.JSONDecodeError, ValueError) as exc:
            raise NewsProviderError("tavily response body is not valid JSON") from exc
        if not isinstance(body, dict):
            raise NewsProviderError("tavily response body is not a JSON object")
        return body
