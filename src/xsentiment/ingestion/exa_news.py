"""Opt-in, bounded Exa search adapter for contextual news observations."""
from __future__ import annotations

import json
from datetime import UTC, date, datetime, time
from typing import Any

import httpx
from pydantic import BaseModel, ConfigDict, ValidationError

from xsentiment.config.settings import get_settings
from xsentiment.errors import PayloadTooLargeError
from xsentiment.ingestion.tavily_news import (
    MAX_QUERY_CHARS,
    NewsCredentialsMissingError,
    NewsProviderError,
    NewsResult,
    NormalizedNewsItem,
    _extract_text,
    _parse_published,
    _payload_hash,
    _publication_note,
    _safe_raw_publication,
    sanitize_news_text,
    sanitize_news_url,
)

_SEARCH_URL = "https://api.exa.ai/search"


class ExaSearchResultModel(BaseModel):
    """Fields consumed from an Exa search result; other documented fields are ignored."""

    model_config = ConfigDict(extra="ignore")
    title: str | None = None
    url: str
    publishedDate: str | None = None
    author: str | None = None


class ExaSearchResponseModel(BaseModel):
    """Typed envelope for Exa's documented /search response."""

    model_config = ConfigDict(extra="ignore")
    results: list[ExaSearchResultModel]


class ExaNewsAdapter:
    """One bounded Exa /search POST; no automatic retries or synthesized answers."""

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
        if key is None and settings.exa_api_key is not None:
            key = settings.exa_api_key.get_secret_value()
        self._api_key = (key or "").strip() or None
        self._owns_client = client is None
        self._client = client or httpx.AsyncClient(
            timeout=settings.http_timeout_seconds,
            follow_redirects=False,
            headers={"Accept": "application/json", "User-Agent": "XSentimentPricePredictor/0.1"},
        )
        if not 1 <= max_results <= 20:
            raise NewsProviderError("max_results must be within 1..20")
        self._max_results = max_results
        self._max_body_bytes = max_body_bytes or settings.http_max_response_bytes

    async def aclose(self) -> None:
        if self._owns_client:
            await self._client.aclose()

    async def __aenter__(self) -> ExaNewsAdapter:
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:  # noqa: ANN001
        await self.aclose()

    async def search(
        self,
        query: str,
        *,
        retrieved_at: datetime | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> NewsResult:
        if not self._api_key:
            raise NewsCredentialsMissingError(
                "no Exa API key is configured; set EXA_API_KEY in the environment "
                "or a local .env file"
            )
        if not isinstance(query, str) or not query.strip() or len(query) > MAX_QUERY_CHARS:
            raise NewsProviderError(f"query must contain 1..{MAX_QUERY_CHARS} characters")
        if start_date is not None and end_date is not None and start_date > end_date:
            raise NewsProviderError("start_date must be on or before end_date")
        moment = retrieved_at or datetime.now(UTC)
        if moment.tzinfo is None or moment.utcoffset() is None:
            raise NewsProviderError("retrieval timestamp must be timezone-aware")
        body = await self._post(query, start_date=start_date, end_date=end_date)
        try:
            envelope = ExaSearchResponseModel.model_validate(body)
        except ValidationError as exc:
            raise NewsProviderError("exa response body has an invalid results schema") from exc

        items: list[NormalizedNewsItem] = []
        excluded: list[str] = []
        seen: set[str] = set()
        for index, result in enumerate(envelope.results[: self._max_results]):
            raw: dict[str, Any] = result.model_dump(by_alias=True)
            headline = _extract_text(raw, "title")
            url = _extract_text(raw, "url")
            if headline is None or url is None:
                excluded.append(f"result {index}: missing headline or url")
                continue
            headline = sanitize_news_text(headline)
            url = sanitize_news_url(url)
            if not url:
                excluded.append(f"result {index}: invalid url excluded")
                continue
            if url in seen:
                excluded.append(f"result {index}: duplicate url excluded")
                continue
            seen.add(url)
            raw_published = raw.get("publishedDate")
            published_at = _parse_published(raw_published)
            items.append(
                NormalizedNewsItem(
                    headline=headline,
                    url=url,
                    published_at=published_at,
                    retrieved_at=moment.astimezone(UTC),
                    source=sanitize_news_text(_extract_text(raw, "author") or "exa"),
                    provider="exa",
                    payload_sha256=_payload_hash(raw),
                    published_at_raw=_safe_raw_publication(raw_published),
                    published_at_note=_publication_note(raw_published, published_at),
                )
            )
        return NewsResult(
            query=query,
            retrieved_at=moment.astimezone(UTC),
            items=tuple(items),
            excluded=tuple(excluded),
        )

    async def _post(
        self, query: str, *, start_date: date | None, end_date: date | None
    ) -> dict[str, Any]:
        payload: dict[str, object] = {
            "query": query,
            "type": "auto",
            "numResults": self._max_results,
            "category": "news",
        }
        if start_date is not None:
            payload["startPublishedDate"] = datetime.combine(start_date, time.min, UTC).isoformat()
        if end_date is not None:
            payload["endPublishedDate"] = datetime.combine(end_date, time.max, UTC).isoformat()
        try:
            async with self._client.stream(
                "POST", _SEARCH_URL, json=payload, headers={"x-api-key": self._api_key or ""}
            ) as response:
                if response.status_code != 200:
                    raise NewsProviderError(f"exa returned HTTP {response.status_code}")
                chunks: list[bytes] = []
                total = 0
                async for chunk in response.aiter_bytes():
                    total += len(chunk)
                    if total > self._max_body_bytes:
                        raise PayloadTooLargeError(
                            f"exa response exceeded the configured ceiling of "
                            f"{self._max_body_bytes} bytes"
                        )
                    chunks.append(chunk)
        except httpx.TimeoutException as exc:
            raise NewsProviderError("exa request timed out within the configured boundary") from exc
        except httpx.HTTPError as exc:
            raise NewsProviderError(
                f"exa request failed with HTTP transport error {exc.__class__.__name__}"
            ) from exc
        try:
            body = json.loads(b"".join(chunks).decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
            raise NewsProviderError("exa response body is not valid JSON") from exc
        if not isinstance(body, dict):
            raise NewsProviderError("exa response body is not a JSON object")
        return body
