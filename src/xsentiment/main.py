"""Command-line entry points.

Two commands are provided:

* ``fetch-prices`` downloads bounded, public Coinbase Exchange BTC-USD daily candles
  into a JSON snapshot. It uses no credentials, costs nothing and never trades.
* ``run`` executes the whole offline pipeline on a price snapshot plus optional
  JSONL posts and writes the evaluation report, outlook, chart and manifest.

Neither command launches a paid provider run. X ingestion requires an approved
Apify Actor and an explicit spend decision, so it stays a separate opt-in step.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from collections.abc import Sequence
from datetime import UTC, datetime, timedelta
from pathlib import Path

from xsentiment.backtesting.strategy import StrategyAssumptions
from xsentiment.config.settings import get_settings
from xsentiment.ingestion.prices import MAX_CANDLES_PER_REQUEST, CoinbasePriceAdapter
from xsentiment.pipeline.forecast_run import (
    load_candles,
    load_news_context,
    load_posts,
    run_forecast_pipeline,
    sha256_file,
)


def _parse_day(value: str) -> datetime:
    try:
        parsed = datetime.strptime(value, "%Y-%m-%d").replace(tzinfo=UTC)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            f"{value!r} is not a YYYY-MM-DD UTC date"
        ) from exc
    return parsed


def _parse_moment(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"{value!r} is not an ISO-8601 timestamp") from exc
    if parsed.tzinfo is None:
        raise argparse.ArgumentTypeError("timestamp must include a UTC offset")
    return parsed.astimezone(UTC)


def _configure_price_source(asset: str) -> None:
    """Default the public Coinbase source without overriding an existing .env."""
    os.environ.setdefault("PRICE_PROVIDER", "coinbase_exchange")
    os.environ.setdefault("ASSET_SYMBOL", asset)
    get_settings.cache_clear()


async def _download_candles(start: datetime, end: datetime, asset: str) -> list[dict[str, str]]:
    """Fetch the half-open [start, end) range in chunks inside the provider limit."""
    chunk_days = MAX_CANDLES_PER_REQUEST - 1
    rows: list[dict[str, str]] = []
    cursor = start
    async with CoinbasePriceAdapter() as adapter:
        while cursor < end:
            chunk_end = min(cursor + timedelta(days=chunk_days), end)
            for candle in await adapter.fetch_daily_candles(cursor, chunk_end):
                rows.append(
                    {
                        "product_id": candle.product_id,
                        "timestamp": candle.timestamp.isoformat(),
                        "low": str(candle.low),
                        "high": str(candle.high),
                        "open": str(candle.open),
                        "close": str(candle.close),
                        "volume": str(candle.volume),
                    }
                )
            cursor = chunk_end
    rows.sort(key=lambda row: row["timestamp"])
    if len({row["timestamp"] for row in rows}) != len(rows):
        raise RuntimeError("price download produced duplicate timestamps")
    return rows


def _command_fetch_prices(args: argparse.Namespace) -> int:
    _configure_price_source(args.asset)
    try:
        rows = asyncio.run(_download_candles(args.start, args.end, args.asset))
    except (RuntimeError, ValueError) as exc:
        print(f"price download failed: {exc}", file=sys.stderr)
        return 1
    destination = Path(args.out)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(
            {
                "product_id": args.asset,
                "granularity_seconds": 86_400,
                "requested_start": args.start.isoformat(),
                "requested_end": args.end.isoformat(),
                "fetch_mode": "public_no_credentials",
                "candles": rows,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"wrote {len(rows)} candles to {destination}")
    return 0


def _command_run(args: argparse.Namespace) -> int:
    try:
        provenance: dict[str, object] = {
            "price_snapshot": str(args.prices),
            "price_snapshot_sha256": sha256_file(args.prices),
        }
        if args.posts is not None:
            provenance["posts_snapshot"] = str(args.posts)
            provenance["posts_snapshot_sha256"] = sha256_file(args.posts)
        if args.news_file is not None:
            provenance["news_snapshot"] = str(args.news_file)
        candles = load_candles(args.prices)
        posts = load_posts(args.posts) if args.posts is not None else []
        news = load_news_context(args.news_file) if args.news_file is not None else []
        artifacts = run_forecast_pipeline(
            candles=candles,
            posts=posts,
            output_dir=args.out,
            asset=args.asset,
            now=args.now,
            min_train_samples=args.min_train,
            test_samples=args.test_size,
            embargo_samples=args.embargo,
            ridge_lambda=args.ridge_lambda,
            strategy_assumptions=StrategyAssumptions(fee_rate=args.fee_rate),
            news_context=news,
            provenance=provenance,
            limitations=[
                "Post text comes from the supplied snapshot only; no live X collection "
                "was performed for this run.",
                "Trading metrics describe a simple long/flat research strategy, not a "
                "deployable trading system.",
            ],
        )
    except (OSError, ValueError, RuntimeError) as exc:
        print(f"run failed: {exc}", file=sys.stderr)
        return 1

    metrics = json.loads(artifacts.metrics_path.read_text(encoding="utf-8"))
    print(f"run directory: {artifacts.output_dir}")
    print(f"forecast MAE by model (mean across horizons): {metrics['mean_mae_by_model']}")
    for model, strategy in metrics["strategies"].items():
        print(
            f"strategy[{model}]: long_days={strategy['long_days']} "
            f"cumulative_return={strategy['metrics'].get('cumulative_return')} "
            f"sharpe={strategy['metrics'].get('sharpe_ratio')} "
            f"sortino={strategy['metrics'].get('sortino_ratio')} "
            f"max_drawdown={strategy['metrics'].get('max_drawdown')}"
        )
    if metrics["unavailable"]:
        print(f"unavailable: {metrics['unavailable']}")
    print(f"report: {artifacts.report_path}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="xsentiment",
        description="Point-in-time X sentiment and BTC-USD forecast pipeline.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    fetch = subparsers.add_parser(
        "fetch-prices", help="download public Coinbase daily candles to a JSON snapshot"
    )
    fetch.add_argument("--start", type=_parse_day, required=True, help="inclusive UTC date")
    fetch.add_argument("--end", type=_parse_day, required=True, help="exclusive UTC date")
    fetch.add_argument("--asset", default="BTC-USD")
    fetch.add_argument("--out", required=True, help="destination JSON snapshot")
    fetch.set_defaults(handler=_command_fetch_prices)

    run = subparsers.add_parser("run", help="run the offline evaluation pipeline")
    run.add_argument("--prices", required=True, help="price snapshot from fetch-prices")
    run.add_argument("--posts", default=None, help="optional JSONL of normalized posts")
    run.add_argument("--news-file", default=None, help="optional JSONL of news context")
    run.add_argument("--out", required=True, help="output directory for artefacts")
    run.add_argument("--asset", default="BTC-USD")
    run.add_argument("--now", type=_parse_moment, default=None, help="override the as-of time")
    run.add_argument("--min-train", type=int, default=60, help="minimum training rows per fold")
    run.add_argument("--test-size", type=int, default=20, help="test rows per fold")
    run.add_argument("--embargo", type=int, default=5, help="purge rows between train and test")
    run.add_argument("--ridge-lambda", type=float, default=1.0, help="ridge penalty")
    run.add_argument("--fee-rate", type=float, default=0.001, help="per-side trading fee")
    run.set_defaults(handler=_command_run)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.handler(args))


if __name__ == "__main__":  # pragma: no cover - module entry point
    raise SystemExit(main())
