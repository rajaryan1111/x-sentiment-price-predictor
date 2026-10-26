import httpx
import pytest

from xsentiment.ingestion.retry import retry_async


@pytest.mark.asyncio
async def test_retry_does_not_retry_non_transient_status() -> None:
    calls = 0

    async def operation() -> None:
        nonlocal calls
        calls += 1
        request = httpx.Request("GET", "https://example.com")
        response = httpx.Response(400, request=request)
        raise httpx.HTTPStatusError("bad request", request=request, response=response)

    with pytest.raises(httpx.HTTPStatusError):
        await retry_async(operation, attempts=3)
    assert calls == 1
