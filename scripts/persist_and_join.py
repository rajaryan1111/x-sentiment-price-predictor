#!/usr/bin/env python3
"""Persist a price snapshot and optional normalized posts, then print a cutoff join.

This is a local, no-network utility. It never prints post text and never commits
data. The join uses only posts published and first observed by each cutoff plus the
last completed price bar before that cutoff.
"""
from __future__ import annotations

import argparse
import asyncio
import json
from datetime import date, timedelta
from pathlib import Path

from sqlalchemy.ext.asyncio import async_sessionmaker

from xsentiment.pipeline.forecast_run import load_candles, load_posts
from xsentiment.storage.database import build_engine
from xsentiment.storage.repositories import (
    create_schema,
    cutoff_post_price_join,
    upsert_posts,
    upsert_price_bars,
)


def _parse_date(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"{value!r} is not a YYYY-MM-DD date") from exc


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prices", type=Path, required=True, help="price snapshot JSON")
    parser.add_argument("--posts", type=Path, default=None, help="normalized posts JSONL")
    parser.add_argument(
        "--database-url",
        default="sqlite+aiosqlite:///./data/xsentiment.db",
        help="local database URL; keep the file under data/ (ignored by Git)",
    )
    parser.add_argument("--product", default="BTC-USD")
    parser.add_argument("--start", type=_parse_date, default=None, help="first cutoff date")
    parser.add_argument("--end", type=_parse_date, default=None, help="last cutoff date")
    parser.add_argument("--out", type=Path, default=None, help="optional JSON output path")
    return parser


async def _run(args: argparse.Namespace) -> dict[str, object]:
    candles = load_candles(args.prices)
    posts = load_posts(args.posts) if args.posts is not None else []
    engine = build_engine(args.database_url)
    try:
        await create_schema(engine)
        factory = async_sessionmaker(engine, expire_on_commit=False)
        async with factory() as session:
            await upsert_price_bars(session, candles, source_snapshot_id=args.prices.name)
            if posts:
                await upsert_posts(session, posts, source_snapshot_id=args.posts.name)
            await session.commit()

            dates = sorted({candle.timestamp.date() for candle in candles})
            start = args.start or (dates[0] + timedelta(days=1))
            end = args.end or dates[-1]
            joined = await cutoff_post_price_join(
                session, product_id=args.product, start=start, end=end
            )
    finally:
        await engine.dispose()

    return {
        "product": args.product,
        "database_url": args.database_url,
        "price_rows_input": len(candles),
        "post_rows_input": len(posts),
        "cutoff_start": start.isoformat(),
        "cutoff_end": end.isoformat(),
        "join_rows": [
            {
                "cutoff": row.cutoff.isoformat(),
                "previous_close": str(row.previous_close),
                "post_count": row.post_count,
                "scored_post_count": row.scored_post_count,
                "mean_sentiment": row.mean_sentiment,
            }
            for row in joined
        ],
        "note": (
            "Leakage-safe cutoff join. Posts are eligible only when published and first "
            "observed by the cutoff; no post text is printed. The run CLI does not yet "
            "consume this persisted path."
        ),
    }


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        result = asyncio.run(_run(args))
    except (OSError, ValueError, RuntimeError) as exc:
        parser.error(str(exc))
    text = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.out is not None:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
        print(f"wrote {args.out}")
    print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
