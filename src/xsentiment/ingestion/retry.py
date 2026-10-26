"""Bounded asynchronous retry with exponential backoff and jitter."""
import asyncio
import random
from collections.abc import Awaitable, Callable
from typing import TypeVar

import httpx

T = TypeVar("T")


async def retry_async(
    operation: Callable[[], Awaitable[T]], *, attempts: int = 3, base_delay: float = 0.25,
    max_delay: float = 8.0, retry_statuses: tuple[int, ...] = (408, 429, 500, 502, 503, 504),
) -> T:
    """Retry transient transport/status failures; never retry ordinary 4xx failures."""
    if attempts < 1:
        raise ValueError("attempts must be at least 1")
    for attempt in range(attempts):
        try:
            return await operation()
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code not in retry_statuses or attempt == attempts - 1:
                raise
        except (httpx.TimeoutException, httpx.NetworkError):
            if attempt == attempts - 1:
                raise
        ceiling = min(max_delay, base_delay * (2 ** attempt))
        await asyncio.sleep(random.uniform(0.0, ceiling))
    raise RuntimeError("unreachable retry state")
