"""Read-only 180-day Coinbase daily-candle coverage profile; saves no raw data."""
from __future__ import annotations

import asyncio
import json
from datetime import UTC, datetime, timedelta

from xsentiment.config.settings import get_settings
from xsentiment.ingestion.prices import CoinbasePriceAdapter
from xsentiment.pipeline.phase2 import profile_daily_price_coverage


async def main() -> int:
    settings = get_settings()
    end = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
    start = end - timedelta(days=180)
    async with CoinbasePriceAdapter() as adapter:
        candles = await adapter.fetch_daily_candles(start, end)
    report = profile_daily_price_coverage(candles, start, end, now=datetime.now(UTC))
    payload = {
        "provider": "coinbase_exchange",
        "product_id": report.product_id or settings.asset_symbol,
        "granularity_seconds": 86400,
        "requested_start_utc": report.requested_start.isoformat(),
        "requested_end_utc_exclusive": report.requested_end.isoformat(),
        "expected_daily_bars": report.expected_daily_bars,
        "observed_daily_bars": report.observed_daily_bars,
        "missing_utc_days": list(report.missing_utc_days),
        "duplicate_timestamps": list(report.duplicate_timestamps),
        "out_of_range_timestamps": list(report.out_of_range_timestamps),
        "has_incomplete_current_day": report.has_incomplete_current_day,
        "coverage_complete": report.is_complete,
        "raw_data_saved": False,
    }
    print(json.dumps(payload, indent=2))
    return 0 if report.is_complete else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
