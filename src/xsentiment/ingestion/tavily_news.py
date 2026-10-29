"""Optional Tavily news adapter: explicit credentials, bounded calls, context only.

Provider headlines and source labels are untrusted content. URLs are sanitized
before output, and the offline JSONL loader repeats this policy for caller-supplied
files before those strings reach reports.

News is contextual information for the outlook. It never becomes a model
feature (D-005) and never passes through the pipeline automatically: the
separate ``xsentiment fetch-news --confirm-live-call`` command is the only live
trigger, and a later ``run --news-file`` consumes the resulting JSONL. A missing
key is an explicit, graceful condition rather than a silent no-op.

The adapter enforces the project's safety policy (NFR4):

* one bounded POST with the configured timeout and a streaming response
  ceiling enforced while chunks arrive, never automatically retried;
* every normalized item keeps headline, URL, publication time when the
  provider actually carries one, retrieval time, source identity and a payload
  hash; nothing is invented, and malformed items are excluded with a reason;
* credential values and query parameters with secrets are never logged or
  included in error messages.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any
from urllib.parse import parse_qsl, quote, unquote, urlencode, urlsplit, urlunsplit

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
    published_at_raw: str | None = None
    published_at_note: str | None = None

    def context_line(self) -> str:
        published = (
            self.published_at.date().isoformat()
            if self.published_at is not None
            else self.published_at_note or "publication timestamp unavailable"
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
        parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        # Do not reinterpret provider-local wall-clock time using the host timezone.
        return None
    return parsed.astimezone(UTC)


def _safe_raw_publication(value: Any) -> str | None:
    """Keep bounded ISO-like source timestamps, but never persist arbitrary text."""
    if not isinstance(value, str) or not value.strip() or len(value) > 128:
        return None
    try:
        datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError:
        return None
    return value.strip()


def _publication_note(value: Any, parsed: datetime | None) -> str | None:
    """Describe why a publication time is absent without inventing an offset."""
    if parsed is not None:
        return None
    if not isinstance(value, str) or not value.strip():
        return "publication date not supplied by the provider"
    try:
        candidate = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError:
        return "publication timestamp malformed; timestamp withheld"
    if candidate.tzinfo is None or candidate.utcoffset() is None:
        return "publication timestamp has no timezone; timestamp withheld"
    return "publication timestamp unavailable"


_SENSITIVE_QUERY_KEYS = frozenset(
    {
        "accesskey",
        "access_token",
        "api_key",
        "apikey",
        "auth",
        "authorization",
        "bearer",
        "code",
        "credential",
        "credentials",
        "hmac",
        "googleaccessid",
        "oauth",
        "key",
        "keypairid",
        "jwt",
        "nonce",
        "password",
        "policy",
        "secret",
        "session",
        "sessionid",
        "sharedsecret",
        "state",
        "sig",
        "signature",
        "ticket",
        "token",
        "verifier",
    }
)
_SENSITIVE_QUERY_SUFFIXES = (
    "accesskey",
    "accesskeyid",
    "apikey",
    "authorization",
    "bearer",
    "code",
    "credential",
    "jwt",
    "nonce",
    "password",
    "secret",
    "session",
    "ticket",
    "signature",
    "token",
    "verifier",
)


def _is_sensitive_query_key(value: str) -> bool:
    """Match common auth parameter spellings without hiding unrelated attribution."""
    normalized = re.sub(r"[^a-z0-9]", "", value.casefold())
    return normalized in _SENSITIVE_QUERY_KEYS or normalized.endswith(_SENSITIVE_QUERY_SUFFIXES)


def sanitize_news_text(value: str) -> str:
    """Sanitize URLs and explicitly labelled credentials in provider text."""
    text = re.sub(
        r"(?i)(https?://[^\s<>\"']+)",
        lambda match: _sanitize_url(match.group(1)),
        value,
    )
    text = re.sub(
        r"(?i)\b((?:[a-z0-9_-]*(?:access[_-]?key(?:id)?|api[_-]?key|authorization|"
        r"client[_-]?secret|credential|jwt|nonce|oauth|password|secret|session|"
        r"signature|sig|ticket|token|verifier)[a-z0-9_-]*)\s*[:=]\s*)"
        r"[^&?#\s,;)]+",
        r"\1[REDACTED]",
        text,
    )
    text = re.sub(r"(?i)\bbearer\s+\[REDACTED\]", "[REDACTED]", text)
    text = re.sub(r"(?i)\b(bearer\s+)[A-Za-z0-9._~+/-]+=*", r"\1[REDACTED]", text)
    return re.sub(
        r"[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}",
        "[REDACTED]",
        text,
    )


def sanitize_news_url(value: str) -> str:
    """Return the centralized safe form of a provider-supplied URL."""
    return _sanitize_url(value)


def _contains_jwt(value: str) -> bool:
    return bool(
        re.search(
            r"[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}",
            value,
        )
    )


def _sanitize_parameter_value(key: str, value: str, *, depth: int) -> str:
    if _is_sensitive_query_key(key) or _contains_jwt(value):
        return "[REDACTED]"
    if depth < 2:
        candidate = unquote(value)
        try:
            nested = urlsplit(candidate)
            if nested.scheme.casefold() in {"http", "https"} and nested.hostname:
                return _sanitize_url(candidate, _depth=depth + 1)
        except ValueError:
            pass
    return value


def _sanitize_url(value: str, *, _depth: int = 0) -> str:
    """Remove URL user-info/fragments and redact credential-like query values.

    Non-sensitive query parameters (for example article IDs and campaign
    attribution) are preserved. Fragments are dropped because their contents
    are client-side and may contain opaque bearer/session tokens.
    """
    try:
        parts = urlsplit(value.strip())
        if parts.scheme.casefold() not in {"http", "https"} or not parts.hostname:
            return ""
        query = [
            (key, _sanitize_parameter_value(key, item, depth=_depth))
            for key, item in parse_qsl(parts.query.replace(";", "&"), keep_blank_values=True)
        ]
        path = parts.path
        original_segments = path.split("/")
        path_segments = original_segments.copy()
        decoded_segments = [unquote(segment) for segment in original_segments]
        for index, segment in enumerate(decoded_segments):
            # Preserve the conventional /oauth/token endpoint while redacting a
            # credential value after a sensitive path key such as /api_key/<value>.
            oauth_token_route = segment.casefold() == "token" and index > 0 and (
                decoded_segments[index - 1].casefold() == "oauth"
            )
            if index and _is_sensitive_query_key(decoded_segments[index - 1]):
                if not oauth_token_route:
                    path_segments[index] = "[REDACTED]"
                    continue
            if _contains_jwt(segment):
                path_segments[index] = "[REDACTED]"
                continue
            if "=" in segment:
                key, separator, _item = segment.partition("=")
                if separator and _is_sensitive_query_key(key):
                    path_segments[index] = quote(f"{key}=[REDACTED]", safe="[]=_-")
        path = "/".join(path_segments)
        # User-info is never needed to display an article link.
        host = parts.hostname
        if ":" in host:  # Preserve brackets around IPv6 literals in the authority.
            host = f"[{host}]"
        if parts.port is not None:
            host = f"{host}:{parts.port}"
        return urlunsplit((parts.scheme.casefold(), host, path, urlencode(query), ""))
    except ValueError:
        # A malformed provider URL must not make the error path echo its raw value.
        return ""


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
        moment = retrieved_at or datetime.now(UTC)
        if moment.tzinfo is None or moment.utcoffset() is None:
            raise NewsProviderError("retrieval timestamp must be timezone-aware")
        moment = moment.astimezone(UTC)

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
            headline = sanitize_news_text(headline)
            url = sanitize_news_url(url)
            if not url:
                excluded.append(f"result {index}: invalid url excluded")
                continue
            if url in seen_urls:
                excluded.append(f"result {index}: duplicate url excluded")
                continue
            seen_urls.add(url)
            raw_published = raw.get("published_date")
            published_at = _parse_published(raw_published)
            items.append(
                NormalizedNewsItem(
                    headline=headline,
                    url=url,
                    published_at=published_at,
                    retrieved_at=moment,
                    source=sanitize_news_text(_extract_text(raw, "source") or "tavily"),
                    provider="tavily",
                    payload_sha256=_payload_hash(raw),
                    published_at_raw=_safe_raw_publication(raw_published),
                    published_at_note=_publication_note(raw_published, published_at),
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
            # Stream the body so an oversized response is rejected before the
            # whole payload is buffered in memory.
            async with self._client.stream(
                "POST",
                _SEARCH_URL,
                json={
                    "query": query,
                    "max_results": self._max_results,
                    "search_depth": "basic",
                },
                headers={"Authorization": f"Bearer {self._api_key}"},
            ) as response:
                if response.status_code != 200:
                    raise NewsProviderError(f"tavily returned HTTP {response.status_code}")
                chunks: list[bytes] = []
                total = 0
                async for chunk in response.aiter_bytes():
                    total += len(chunk)
                    if total > self._max_body_bytes:
                        raise PayloadTooLargeError(
                            f"tavily response exceeded the configured ceiling of "
                            f"{self._max_body_bytes} bytes"
                        )
                    chunks.append(chunk)
                body_bytes = b"".join(chunks)
        except httpx.TimeoutException as exc:
            raise NewsProviderError(
                "tavily request timed out within the configured boundary"
            ) from exc
        except httpx.HTTPError as exc:
            raise NewsProviderError(
                f"tavily request failed with HTTP transport error {exc.__class__.__name__}"
            ) from exc
        try:
            body = json.loads(body_bytes.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
            raise NewsProviderError("tavily response body is not valid JSON") from exc
        if not isinstance(body, dict):
            raise NewsProviderError("tavily response body is not a JSON object")
        return body
