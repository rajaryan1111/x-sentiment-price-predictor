"""Coinbase Exchange public daily-candle ingestion with strict parsing and UTC semantics."""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from urllib.parse import urlencode

from xsentiment.config.settings import get_settings
from xsentiment.ingestion.http import AsyncHttpClient

EXCHANGE_API_BASE = "https://api.exchange.coinbase.com"
DAILY_GRANULARITY_SECONDS = 86_400
MAX_CANDLES_PER_REQUEST = 300


@dataclass(frozen=True, slots=True)
class PriceCandle:
    """A validated UTC candle; timestamp is the start of its daily UTC bucket."""

    product_id: str
    timestamp: datetime
    low: Decimal
    high: Decimal
    open: Decimal
    close: Decimal
    volume: Decimal

    def __post_init__(self) -> None:
        if self.timestamp.tzinfo is None:
            raise ValueError("candle timestamp must be timezone-aware")
        if self.timestamp.utcoffset() is None:
            raise ValueError("candle timestamp must be timezone-aware")
        if self.timestamp.utcoffset() != UTC.utcoffset(self.timestamp):
            raise ValueError("candle timestamp must be normalized to UTC")
        if min(self.low, self.high, self.open, self.close) <= 0:
            raise ValueError("OHLC prices must be positive")
        if self.volume < 0:
            raise ValueError("volume must be non-negative")
        if self.low > self.high or not self.low <= self.open <= self.high:
            raise ValueError("OHLC values are inconsistent")
        if not self.low <= self.close <= self.high:
            raise ValueError("OHLC values are inconsistent")


class CoinbasePriceAdapter:
    """Fetch Coinbase Exchange candles without API credentials or paid side effects.

    The caller owns the 180-day scope and must exclude incomplete current-day bars
    before treating their close as an observed value.
    """

    def __init__(self, http_client: AsyncHttpClient | None = None) -> None:
        self.settings = get_settings()
        self._owns_client = http_client is None
        self.http_client = http_client or AsyncHttpClient()

    def is_configured(self) -> bool:
        return (
            self.settings.price_provider == "coinbase_exchange"
            and bool(self.settings.asset_symbol)
        )

    async def fetch_daily_candles(
        self, start: datetime, end: datetime
    ) -> list[PriceCandle]:
        """Fetch daily candles for [start, end], where both bounds are UTC-aware."""
        start_utc = self._as_utc(start, "start")
        end_utc = self._as_utc(end, "end")
        if start_utc >= end_utc:
            raise ValueError("start must be earlier than end")
        if (end_utc.date() - start_utc.date()).days > MAX_CANDLES_PER_REQUEST - 1:
            raise ValueError(
                f"requested range exceeds Coinbase's {MAX_CANDLES_PER_REQUEST}-candle limit"
            )
        if not self.is_configured():
            raise RuntimeError(
                "price adapter is not configured; set PRICE_PROVIDER=coinbase_exchange "
                "and ASSET_SYMBOL (expected BTC-USD)"
            )

        product_id = self.settings.asset_symbol
        query = urlencode(
            {
                "granularity": DAILY_GRANULARITY_SECONDS,
                "start": start_utc.isoformat().replace("+00:00", "Z"),
                "end": end_utc.isoformat().replace("+00:00", "Z"),
            }
        )
        url = (
            f"{EXCHANGE_API_BASE}/products/{product_id}/candles?{query}"
        )
        response = await self.http_client.get(url)
        try:
            rows = json.loads(response.text)
        except json.JSONDecodeError as exc:
            raise ValueError("Coinbase candle response was not valid JSON") from exc
        if not isinstance(rows, list):
            raise ValueError("Coinbase candle response must be a list")
        candles = [self._parse_row(product_id, row) for row in rows]
        # Coinbase may include candles preceding the requested start; enforce our
        # UTC [start, end) convention locally and exclude the end-boundary candle.
        candles = [
            candle for candle in candles if start_utc <= candle.timestamp < end_utc
        ]
        candles.sort(key=lambda candle: candle.timestamp)

        timestamps = [candle.timestamp for candle in candles]
        if len(timestamps) != len(set(timestamps)):
            raise ValueError("Coinbase response contains duplicate candle timestamps")
        return candles

    @staticmethod
    def _as_utc(value: datetime, field_name: str) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError(f"{field_name} must be timezone-aware")
        return value.astimezone(UTC)

    @staticmethod
    def _parse_row(product_id: str, row: object) -> PriceCandle:
        # Coinbase Exchange candle rows are [time, low, high, open, close, volume].
        if not isinstance(row, list) or len(row) != 6:
            raise ValueError("Coinbase candle row must contain exactly six values")
        try:
            timestamp_raw = row[0]
            if isinstance(timestamp_raw, bool):
                raise ValueError("timestamp must be an integer Unix timestamp")
            timestamp_seconds = int(timestamp_raw)
            if str(timestamp_seconds) != str(timestamp_raw):
                raise ValueError("timestamp must be an integer Unix timestamp")
            timestamp = datetime.fromtimestamp(timestamp_seconds, tz=UTC)
            values = [Decimal(str(value)) for value in row[1:]]
        except (TypeError, ValueError, OverflowError, InvalidOperation) as exc:
            raise ValueError("Coinbase candle row contains invalid numeric values") from exc
        if any(not value.is_finite() for value in values):
            raise ValueError("Coinbase candle values must be finite")
        return PriceCandle(
            product_id=product_id,
            timestamp=timestamp,
            low=values[0],
            high=values[1],
            open=values[2],
            close=values[3],
            volume=values[4],
        )

    async def aclose(self) -> None:
        if self._owns_client:
            await self.http_client.aclose()

    async def __aenter__(self) -> CoinbasePriceAdapter:
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:  # noqa: ANN001
        await self.aclose()
