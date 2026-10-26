"""Command-line entry points.

Three commands are provided:

* ``fetch-prices`` downloads bounded, public Coinbase Exchange BTC-USD daily candles
  into a JSON snapshot. It uses no credentials, costs nothing and never trades.
* ``persist`` upserts snapshot inputs into the local storage database so the same
  rows feed every later run; re-running the same snapshots is idempotent.
* ``run`` executes the whole offline pipeline on a price snapshot plus optional
  JSONL posts, or on the persisted storage rows via ``--database-url``, and writes
  the evaluation report, outlook, chart and manifest.

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
    run_forecast_pipeline,
    sha256_file,
)
from xsentiment.pipeline.forecast_run import (
    load_posts as load_posts_jsonl,
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


def _storage_stack():
    """Import the optional storage stack on demand for persisted-input paths.

    Returns ``(OperationalError, database, repositories)``: the error class needed
    to map a missing-table failure, the lazily loaded engine module and the
    repository helpers. The offline pipeline never needs the database, so
    ``pip install -e .`` keeps working without the storage extras; a persisted run
    imports them here and fails with the setup command instead of a stack trace.
    """
    try:
        from sqlalchemy.exc import OperationalError

        from xsentiment.storage import database, repositories
    except ImportError as exc:
        raise RuntimeError(
            "the persisted-input path needs the storage extras; install them with: "
            "pip install -e '.[storage]'"
        ) from exc
    return OperationalError, database, repositories


async def _persist_inputs(args: argparse.Namespace) -> dict[str, int]:
    """Upsert the supplied snapshots into the local storage database."""
    _, database, repositories = _storage_stack()
    candles = load_candles(args.prices)
    posts = load_posts_jsonl(args.posts) if args.posts is not None else []
    engine = database.build_engine(args.database_url)
    try:
        await repositories.create_schema(engine)
        factory = repositories.session_factory(engine)
        async with factory() as session:
            price_rows = await repositories.upsert_price_bars(
                session, candles, source_snapshot_id=args.prices.name
            )
            post_rows = 0
            if posts:
                post_rows = await repositories.upsert_posts(
                    session, posts, source_snapshot_id=args.posts.name
                )
            await session.commit()
    finally:
        await engine.dispose()
    return {"price_rows": price_rows, "post_rows": post_rows}


async def _load_persisted_inputs(args: argparse.Namespace):
    """Read candles and posts from the local storage database for a run."""
    OperationalError, database, repositories = _storage_stack()
    engine = database.build_engine(args.database_url)
    try:
        factory = repositories.session_factory(engine)
        async with factory() as session:
            try:
                candles = await repositories.load_price_candles(
                    session, product_id=args.asset
                )
                posts = await repositories.load_posts(session)
                snapshot_ids = await repositories.storage_snapshot_ids(session)
            except OperationalError as exc:
                raise RuntimeError(
                    f"database {args.database_url} has no xsentiment tables yet; "
                    "populate it first with xsentiment persist --prices ..."
                ) from exc
    finally:
        await engine.dispose()
    if not candles:
        raise ValueError(
            f"no candle rows for {args.asset} in {args.database_url}; "
            "populate the database first with xsentiment persist --prices ..."
        )
    return candles, posts, snapshot_ids


def _command_persist(args: argparse.Namespace) -> int:
    try:
        counts = asyncio.run(_persist_inputs(args))
    except (OSError, ValueError, RuntimeError) as exc:
        print(f"persist failed: {exc}", file=sys.stderr)
        return 1
    if counts["post_rows"]:
        print(
            f"upserted {counts['price_rows']} price bars and {counts['post_rows']} posts "
            f"into {args.database_url}; repeating this command is idempotent"
        )
    else:
        print(
            f"upserted {counts['price_rows']} price bars into {args.database_url}; "
            "repeating this command is idempotent"
        )
    return 0


def _command_run(args: argparse.Namespace) -> int:
    try:
        provenance: dict[str, object] = {}
        if args.database_url is not None:
            if args.prices is not None or args.posts is not None:
                raise ValueError("--database-url cannot be combined with --prices/--posts")
            candles, posts, snapshot_ids = asyncio.run(_load_persisted_inputs(args))
            provenance["input_source"] = "persisted_storage"
            provenance["database_url"] = args.database_url
            provenance["storage_snapshot_ids"] = snapshot_ids
        else:
            if args.prices is None:
                raise ValueError("usage: xsentiment run --prices SNAPSHOT or --database-url URL")
            provenance["input_source"] = "file_snapshot"
            provenance["price_snapshot"] = str(args.prices)
            provenance["price_snapshot_sha256"] = sha256_file(args.prices)
            if args.posts is not None:
                provenance["posts_snapshot"] = str(args.posts)
                provenance["posts_snapshot_sha256"] = sha256_file(args.posts)
            candles = load_candles(args.prices)
            posts = load_posts_jsonl(args.posts) if args.posts is not None else []
        news = load_news_context(args.news_file) if args.news_file is not None else []
        if args.news_file is not None:
            provenance["news_snapshot"] = str(args.news_file)
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

    persist = subparsers.add_parser(
        "persist", help="upsert snapshot inputs into the local storage database"
    )
    persist.add_argument(
        "--prices", type=Path, required=True, help="price snapshot from fetch-prices"
    )
    persist.add_argument(
        "--posts", type=Path, default=None, help="optional JSONL of normalized posts"
    )
    persist.add_argument(
        "--database-url",
        required=True,
        help="local database URL, e.g. sqlite+aiosqlite:///./data/xsentiment.db",
    )
    persist.set_defaults(handler=_command_persist)

    run = subparsers.add_parser("run", help="run the offline evaluation pipeline")
    run.add_argument("--prices", type=Path, default=None, help="price snapshot from fetch-prices")
    run.add_argument("--posts", default=None, help="optional JSONL of normalized posts")
    run.add_argument(
        "--database-url",
        default=None,
        help="read inputs from a persisted storage database instead of snapshots",
    )
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
