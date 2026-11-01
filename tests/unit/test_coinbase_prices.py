from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal

import pytest

from xsentiment.config.settings import Settings
from xsentiment.ingestion.prices import CoinbasePriceAdapter, PriceCandle


class FakeResponse:
    def __init__(self, text: str) -> None:
        self.text = text


class FakeHttpClient:
    def __init__(self, text: str = "[]") -> None:
        self.text = text
        self.urls: list[str] = []
        self.closed = False

    async def get(self, url: str, *, headers=None) -> FakeResponse:
        self.urls.append(url)
        return FakeResponse(self.text)

    async def aclose(self) -> None:
        self.closed = True


def configured_adapter(text: str = "[]") -> tuple[CoinbasePriceAdapter, FakeHttpClient]:
    client = FakeHttpClient(text)
    adapter = CoinbasePriceAdapter(http_client=client)  # type: ignore[arg-type]
    adapter.settings = Settings(price_provider="coinbase_exchange", asset_symbol="BTC-USD")
    return adapter, client


@pytest.mark.asyncio
async def test_fetch_daily_candles_sorts_rows_and_preserves_decimal_values() -> None:
    adapter, client = configured_adapter(
        '[ [1792886400, 98.1, 105.2, 100.0, 103.4, 12.5],'
        ' [1792800000, 90.0, 102.0, 95.0, 100.0, 9.25] ]'
    )
    start = datetime(2026, 10, 24, tzinfo=UTC)
    end = datetime(2026, 10, 26, tzinfo=UTC)

    candles = await adapter.fetch_daily_candles(start, end)

    assert [c.timestamp for c in candles] == sorted(c.timestamp for c in candles)
    assert candles[0].product_id == "BTC-USD"
    assert candles[0].close == Decimal("100.0")
    assert candles[0].volume == Decimal("9.25")
    assert "granularity=86400" in client.urls[0]
    assert "products/BTC-USD/candles" in client.urls[0]


@pytest.mark.asyncio
async def test_fetch_rejects_naive_dates() -> None:
    adapter, _ = configured_adapter()
    with pytest.raises(ValueError, match="start must be timezone-aware"):
        await adapter.fetch_daily_candles(
            datetime(2026, 10, 1), datetime(2026, 10, 2, tzinfo=UTC)
        )


@pytest.mark.asyncio
async def test_fetch_rejects_ranges_over_provider_limit() -> None:
    adapter, client = configured_adapter()
    with pytest.raises(ValueError, match="300-candle limit"):
        await adapter.fetch_daily_candles(
            datetime(2025, 1, 1, tzinfo=UTC), datetime(2025, 11, 1, tzinfo=UTC)
        )
    assert client.urls == []


@pytest.mark.asyncio
async def test_fetch_rejects_duplicate_timestamps() -> None:
    row = '[1792800000, 90, 102, 95, 100, 9]'
    adapter, _ = configured_adapter(f"[{row}, {row}]")
    with pytest.raises(ValueError, match="duplicate candle timestamps"):
        await adapter.fetch_daily_candles(
            datetime(2026, 10, 23, tzinfo=UTC), datetime(2026, 10, 26, tzinfo=UTC)
        )


@pytest.mark.asyncio
async def test_fetch_rejects_malformed_json_and_invalid_ohlc() -> None:
    adapter, _ = configured_adapter("not-json")
    with pytest.raises(ValueError, match="valid JSON"):
        await adapter.fetch_daily_candles(
            datetime(2026, 10, 23, tzinfo=UTC), datetime(2026, 10, 26, tzinfo=UTC)
        )

    adapter, _ = configured_adapter("[[1792800000, 110, 102, 95, 100, 9]]")
    with pytest.raises(ValueError, match="OHLC values are inconsistent"):
        await adapter.fetch_daily_candles(
            datetime(2026, 10, 23, tzinfo=UTC), datetime(2026, 10, 26, tzinfo=UTC)
        )


def test_price_candle_rejects_non_utc_timestamp() -> None:
    with pytest.raises(ValueError, match="normalized to UTC"):
        PriceCandle(
            "BTC-USD",
            datetime(2026, 10, 23, 5, tzinfo=timezone(timedelta(hours=5))),
            Decimal("90"),
            Decimal("102"),
            Decimal("95"),
            Decimal("100"),
            Decimal("9"),
        )
