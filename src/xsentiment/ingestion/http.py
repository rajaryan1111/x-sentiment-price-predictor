"""Shared async HTTP client with bounded concurrency, timeouts and response-size limits."""
import hashlib
from dataclasses import dataclass

import httpx

from xsentiment.config.settings import get_settings
from xsentiment.ingestion.retry import retry_async


@dataclass(frozen=True, slots=True)
class FetchResult:
    url: str
    status_code: int
    text: str
    content_hash: str
    headers: dict[str, str]


class AsyncHttpClient:
    """Single place for outbound HTTP, so adapters share safety and retry policy."""

    def __init__(self, *, client: httpx.AsyncClient | None = None) -> None:
        settings = get_settings()
        self._owns_client = client is None
        self._client = client or httpx.AsyncClient(
            timeout=settings.http_timeout_seconds,
            follow_redirects=True,
            headers={"User-Agent": "XSentimentPricePredictor/0.1 (+research; contact repository owner)"},
        )
        self._limit = settings.http_max_concurrency
        self._semaphore = __import__("asyncio").Semaphore(self._limit)
        self._max_bytes = settings.http_max_response_bytes
        self._attempts = settings.http_max_retries + 1

    async def get(self, url: str, *, headers: dict[str, str] | None = None) -> FetchResult:
        async def request() -> FetchResult:
            async with self._semaphore:
                async with self._client.stream("GET", url, headers=headers) as response:
                    response.raise_for_status()
                    chunks: list[bytes] = []
                    total = 0
                    async for chunk in response.aiter_bytes():
                        total += len(chunk)
                        if total > self._max_bytes:
                            from xsentiment.errors import PayloadTooLargeError
                            raise PayloadTooLargeError(f"Response exceeded {self._max_bytes} bytes")
                        chunks.append(chunk)
                    body = b"".join(chunks)
                    return FetchResult(
                        url=str(response.url),
                        status_code=response.status_code,
                        text=body.decode(response.encoding or "utf-8", errors="replace"),
                        content_hash=hashlib.sha256(body).hexdigest(),
                        headers=dict(response.headers),
                    )
        return await retry_async(request, attempts=self._attempts)

    async def aclose(self) -> None:
        if self._owns_client:
            await self._client.aclose()

    async def __aenter__(self) -> "AsyncHttpClient":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:  # noqa: ANN001
        await self.aclose()
