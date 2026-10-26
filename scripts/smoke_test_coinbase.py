"""Read-only Coinbase public API smoke test; writes no files and requires no API key."""
import asyncio
from datetime import UTC, datetime, timedelta

from xsentiment.ingestion.prices import CoinbasePriceAdapter, DAILY_GRANULARITY_SECONDS


async def run() -> int:
    end = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
    start = end - timedelta(days=7)
    async with CoinbasePriceAdapter() as adapter:
        if not adapter.is_configured():
            print(
                "Not configured. Set PRICE_PROVIDER=coinbase_exchange and "
                "ASSET_SYMBOL=BTC-USD in your local .env."
            )
            return 2
        candles = await adapter.fetch_daily_candles(start, end)

    expected = {
        start + timedelta(seconds=DAILY_GRANULARITY_SECONDS * offset)
        for offset in range(7)
    }
    observed = {candle.timestamp for candle in candles}
    missing = sorted(expected - observed)
    print(f"provider=coinbase_exchange product={candles[0].product_id if candles else 'BTC-USD'}")
    print(f"granularity_seconds={DAILY_GRANULARITY_SECONDS}")
    print(f"requested_start_utc={start.isoformat()} requested_end_utc_exclusive={end.isoformat()}")
    print(f"candle_count={len(candles)}")
    print(f"first_candle_utc={candles[0].timestamp.isoformat() if candles else 'none'}")
    print(f"last_candle_utc={candles[-1].timestamp.isoformat() if candles else 'none'}")
    print(f"missing_daily_bars={[value.isoformat() for value in missing]}")
    if missing or len(candles) != 7:
        print("RESULT=FAIL: recent daily candle coverage did not match the expected 7 complete bars")
        return 1
    print("RESULT=PASS: recent 7-bar read-only smoke test")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(run()))
