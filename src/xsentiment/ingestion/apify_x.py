"""Configurable Apify X Actor adapter with explicit bounds and normalized output.

Actor input schemas differ. This adapter accepts a caller-supplied input JSON object
and does not initiate a run unless run_and_fetch is explicitly called. Set an Actor
that you have reviewed for current terms, output schema, historical reach, and costs.
"""
from __future__ import annotations

import asyncio
import json
import time
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from typing import Any
from urllib.parse import quote

import httpx

from xsentiment.config.settings import Settings, get_settings
from xsentiment.ingestion.contracts import XPostRecord

APIFY_API_BASE = "https://api.apify.com/v2"
TERMINAL_STATUSES = {"SUCCEEDED", "FAILED", "ABORTED", "TIMED-OUT"}


class ApifyRunError(RuntimeError):
    """Raised when an Apify run fails or returns an invalid response."""


class ApifyXAdapter:
    """Run a reviewed Apify Actor within explicit item, time and spend caps."""

    def __init__(
        self,
        settings: Settings | None = None,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self._owns_client = client is None
        self._client = client or httpx.AsyncClient(
            timeout=self.settings.http_timeout_seconds,
            follow_redirects=False,
            headers={"User-Agent": "XSentimentPricePredictor/0.1"},
        )

    def is_configured(self) -> bool:
        token = self.settings.apify_api_token
        return bool(
            token
            and token.get_secret_value().strip()
            and self.settings.apify_actor_id
            and self.settings.apify_actor_id.strip()
        )

    async def run_and_fetch(
        self,
        actor_input: dict[str, Any],
        *,
        max_items: int = 100,
        max_total_charge_usd: float = 1.0,
        timeout_seconds: int = 900,
    ) -> list[XPostRecord]:
        """Start one Actor run and fetch its default dataset under caller-approved caps.

        No automatic retry is used for the initial POST: retrying an ambiguous
        timeout could launch and bill a second Actor run.
        """
        if not self.is_configured():
            raise RuntimeError("Apify is not configured; set APIFY_API_TOKEN and APIFY_ACTOR_ID")
        if not isinstance(actor_input, dict):
            raise ValueError("actor_input must be a JSON object matching the selected Actor schema")
        if not 1 <= max_items <= 1000:
            raise ValueError("max_items must be between 1 and 1000")
        if not 0 < max_total_charge_usd <= 50:
            raise ValueError("max_total_charge_usd must be > 0 and <= 50 USD")
        if not 60 <= timeout_seconds <= 3600:
            raise ValueError("timeout_seconds must be between 60 and 3600")

        actor_id = quote(self.settings.apify_actor_id.strip(), safe="~")
        launch_url = (
            f"{APIFY_API_BASE}/acts/{actor_id}/runs"
            f"?waitForFinish=60&maxItems={max_items}"
            f"&maxTotalChargeUsd={max_total_charge_usd:g}&timeout={timeout_seconds}"
        )
        headers = self._auth_headers()
        run = await self._request_json("POST", launch_url, headers=headers, json_body=actor_input)
        if not isinstance(run, dict):
            raise ApifyRunError("Apify returned an invalid run object")
        run_id = run.get("id")
        status = run.get("status")
        deadline = time.monotonic() + timeout_seconds + 120
        while status not in TERMINAL_STATUSES:
            if not isinstance(run_id, str) or not run_id:
                raise ApifyRunError("Apify run response is missing its run ID")
            if time.monotonic() >= deadline:
                raise ApifyRunError("Apify run did not finish before the local wait deadline")
            await asyncio.sleep(1)
            run_url = f"{APIFY_API_BASE}/actor-runs/{quote(run_id, safe='')}?waitForFinish=60"
            run = await self._request_json("GET", run_url, headers=headers)
            if not isinstance(run, dict):
                raise ApifyRunError("Apify returned an invalid run status object")
            status = run.get("status")

        if status != "SUCCEEDED" or run.get("exitCode", 0) not in (None, 0):
            raise ApifyRunError(f"Apify run did not succeed (status={status!r})")
        dataset_id = run.get("defaultDatasetId")
        if not isinstance(dataset_id, str) or not dataset_id:
            raise ApifyRunError("Apify run did not return a default dataset ID")
        dataset_url = (
            f"{APIFY_API_BASE}/datasets/{quote(dataset_id, safe='')}/items"
            f"?format=json&clean=true&limit={max_items}"
        )
        items = await self._request_json("GET", dataset_url, headers=headers)
        if not isinstance(items, list):
            raise ApifyRunError("Apify dataset response must be a JSON array")
        if len(items) > max_items:
            raise ApifyRunError("Apify returned more items than the configured result cap")
        retrieved_at = datetime.now(UTC)
        records = [normalize_apify_post(item, retrieved_at=retrieved_at) for item in items]
        seen: dict[str, XPostRecord] = {}
        for record in records:
            existing = seen.get(record.post_id)
            if existing is not None and existing != record:
                raise ApifyRunError(
                    f"Actor returned conflicting duplicate post ID: {record.post_id}"
                )
            seen[record.post_id] = record
        return sorted(seen.values(), key=lambda record: (record.created_at, record.post_id))

    def _auth_headers(self) -> dict[str, str]:
        token = self.settings.apify_api_token
        if token is None:
            raise RuntimeError("Apify token is missing")
        return {"Authorization": f"Bearer {token.get_secret_value()}"}

    async def _request_json(
        self,
        method: str,
        url: str,
        *,
        headers: dict[str, str],
        json_body: dict[str, Any] | None = None,
    ) -> Any:
        """Read a bounded JSON response; bearer tokens never appear in URLs."""
        chunks: list[bytes] = []
        size = 0
        try:
            async with self._client.stream(
                method, url, headers=headers, json=json_body
            ) as response:
                response.raise_for_status()
                async for chunk in response.aiter_bytes():
                    size += len(chunk)
                    if size > self.settings.http_max_response_bytes:
                        raise ApifyRunError("Apify response exceeded configured size limit")
                    chunks.append(chunk)
        except httpx.HTTPStatusError as exc:
            raise ApifyRunError(
                f"Apify API returned HTTP {exc.response.status_code} for {method} request"
            ) from exc
        except httpx.RequestError as exc:
            if method == "POST":
                raise ApifyRunError(
                    "Apify launch request failed; run outcome may be unknown. "
                    "Check the Apify console before retrying to avoid duplicate charges."
                ) from exc
            raise ApifyRunError(f"Apify API request failed for {method}") from exc
        try:
            return json.loads(b"".join(chunks).decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ApifyRunError("Apify API response was not valid UTF-8 JSON") from exc

    async def aclose(self) -> None:
        if self._owns_client:
            await self._client.aclose()

    async def __aenter__(self) -> ApifyXAdapter:
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:  # noqa: ANN001
        await self.aclose()


def normalize_apify_post(
    item: object, *, retrieved_at: datetime | None = None
) -> XPostRecord:
    """Normalize common tweet fields without fabricating missing IDs, text or event time."""
    if not isinstance(item, dict):
        raise ValueError("Apify dataset item must be a JSON object")
    post_id = _first_text(item, ("id", "tweet_id", "tweetId", "post_id", "postId"))
    text = _first_text(item, ("text", "full_text", "fullText"))
    created_raw = _first_value(item, ("createdAt", "created_at", "created_at_datetime", "date"))
    if post_id is None:
        raise ValueError("Apify item is missing a stable post ID")
    if text is None:
        raise ValueError(f"Apify item {post_id!r} is missing post text")
    created_at = _parse_datetime(created_raw)
    author = item.get("author")
    if not isinstance(author, dict):
        author = {}
    return XPostRecord(
        post_id=post_id,
        created_at=created_at,
        retrieved_at=retrieved_at or datetime.now(UTC),
        text=text,
        likes=_optional_count(item, ("likeCount", "like_count", "favorite_count", "likesCount")),
        reposts=_optional_count(
            item, ("retweetCount", "retweet_count", "repostCount", "reposts")
        ),
        views=_optional_count(item, ("viewCount", "view_count", "viewsCount", "views")),
        author_followers=_optional_count(
            item,
            ("authorFollowers", "author_followers", "followersCount", "followers_count"),
            fallback=author,
        ),
        provenance_url=_first_text(item, ("url", "twitterUrl", "tweetUrl", "permalink")),
        sentiment_score=None,
        source_name="apify_x",
    )


def _first_value(item: dict[str, Any], keys: tuple[str, ...]) -> Any:
    for key in keys:
        if key in item and item[key] is not None:
            return item[key]
    return None


def _first_text(item: dict[str, Any], keys: tuple[str, ...]) -> str | None:
    value = _first_value(item, keys)
    if not isinstance(value, (str, int)) or isinstance(value, bool):
        return None
    normalized = str(value).strip()
    return normalized or None


def _parse_datetime(value: Any) -> datetime:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("Apify item is missing a valid creation timestamp")
    text = value.strip()
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        try:
            parsed = parsedate_to_datetime(text)
        except (TypeError, ValueError, OverflowError) as exc:
            raise ValueError("Apify item has an unrecognized creation timestamp") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("Apify creation timestamp must include a timezone")
    return parsed.astimezone(UTC)


def _optional_count(
    item: dict[str, Any],
    keys: tuple[str, ...],
    *,
    fallback: dict[str, Any] | None = None,
) -> int | None:
    value = _first_value(item, keys)
    if value is None and fallback is not None:
        value = _first_value(fallback, keys)
    if value is None:
        return None
    if isinstance(value, bool):
        raise ValueError("Apify engagement counts must be non-negative integers")
    try:
        integer = int(value)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError("Apify engagement counts must be non-negative integers") from exc
    if str(integer) != str(value) and not isinstance(value, int):
        raise ValueError("Apify engagement counts must be whole numbers")
    if integer < 0:
        raise ValueError("Apify engagement counts must be non-negative integers")
    return integer
