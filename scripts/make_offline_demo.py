"""Generate a deterministic, explicitly synthetic offline demonstration dataset.

This script exists so a reviewer can exercise the whole CLI without credentials,
network access or an accepted X corpus. Its output is **not** observed market or
social data. Every generated file carries a ``synthetic`` label and provenance;
metrics produced from it must never be presented as real-data results.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

PHRASES = (
    "Bitcoin rallies strongly; traders are optimistic and happy",
    "BTC falls sharply; traders are fearful and worried",
    "Bitcoin trades quietly; volume is calm and sentiment is neutral",
    "Bitcoin momentum improves and buyers are confident",
    "BTC weakens as sellers dominate and uncertainty rises",
    "Bitcoin recovers; long-term holders are optimistic",
)
QUERIES = (
    ("keyword", "Bitcoin"),
    ("ticker", "BTC"),
    ("cashtag", "$BTC"),
)


def _parse_day(value: str) -> datetime:
    try:
        return datetime.strptime(value, "%Y-%m-%d").replace(tzinfo=UTC)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"{value!r} is not a YYYY-MM-DD UTC date") from exc


def _hash_record(record: dict[str, object]) -> str:
    stable = json.dumps(record, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(stable).hexdigest()


def build_price_snapshot(
    *, asset: str, start: datetime, days: int, seed: int, generated_at: datetime
) -> dict[str, object]:
    """Return deterministic daily OHLCV candles with no gaps or duplicates."""
    rng = random.Random(seed)
    candles: list[dict[str, str]] = []
    close = 60_000.0
    for index in range(days):
        previous = close
        drift = 0.00035 + 0.0035 * math.sin(index / 9.0)
        shock = rng.uniform(-0.0025, 0.0025)
        close = max(1_000.0, previous * (1.0 + drift + shock))
        open_price = previous * (1.0 + rng.uniform(-0.0008, 0.0008))
        high = max(open_price, close) * (1.0 + rng.uniform(0.0004, 0.0025))
        low = min(open_price, close) * (1.0 - rng.uniform(0.0004, 0.0025))
        volume = 900.0 + 40.0 * math.cos(index / 7.0) + rng.uniform(0.0, 25.0)
        candles.append(
            {
                "product_id": asset,
                "timestamp": (start + timedelta(days=index)).isoformat(),
                "low": f"{low:.2f}",
                "high": f"{high:.2f}",
                "open": f"{open_price:.2f}",
                "close": f"{close:.2f}",
                "volume": f"{volume:.4f}",
            }
        )
    end_exclusive = start + timedelta(days=days)
    return {
        "product_id": asset,
        "granularity_seconds": 86_400,
        "requested_start": start.isoformat(),
        "requested_end": end_exclusive.isoformat(),
        "generated_at": generated_at.isoformat(),
        "fetch_mode": "synthetic_offline_demo",
        "synthetic": True,
        "generator": "scripts/make_offline_demo.py",
        "generator_seed": seed,
        "retrieval_time_note": (
            "generated_at is the local generation time, not a provider retrieval time; "
            "this snapshot contains no observed market data"
        ),
        "recommended_now": end_exclusive.isoformat(),
        "candles": candles,
    }


def build_post_records(
    *, start: datetime, days: int, generated_at: datetime
) -> list[dict[str, object]]:
    """Return clearly labelled synthetic posts available before each daily cutoff."""
    records: list[dict[str, object]] = []
    for index in range(1, days):
        cutoff = start + timedelta(days=index)
        created = cutoff - timedelta(hours=6)
        retrieved = cutoff - timedelta(hours=5)
        mode, query = QUERIES[index % len(QUERIES)]
        text = PHRASES[index % len(PHRASES)]
        stable = {
            "post_id": f"synthetic-demo-{index:04d}",
            "created_at": created.isoformat(),
            "retrieved_at": retrieved.isoformat(),
            "text": text,
        }
        record: dict[str, object] = {
            **stable,
            "sentiment_score": None,
            "likes": 10 + index,
            "reposts": None if index % 7 == 0 else index % 5,
            "views": 100 + index * 3,
            "author_followers": None if index % 11 == 0 else 500 + index,
            "provenance_url": None,
            "source_name": "synthetic_offline_demo",
            "source_platform": "synthetic",
            "source_created_at_raw": created.isoformat(),
            "source_utc_offset": "+00:00",
            "author_id": f"synthetic-author-{index % 7}",
            "query_mode": mode,
            "query": query,
            "schema_version": "x-post-v1",
            "synthetic": True,
            "dataset_label": "synthetic offline demo",
            "generated_at": generated_at.isoformat(),
            "warnings": ["synthetic demonstration record, not observed X data"],
            "source_record_hash": _hash_record(stable),
        }
        records.append(record)
    return records


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Write deterministic synthetic price/post snapshots for an offline demo.",
    )
    parser.add_argument("--out", type=Path, required=True, help="price snapshot JSON path")
    parser.add_argument(
        "--posts-out", type=Path, default=None, help="optional synthetic posts JSONL path"
    )
    parser.add_argument("--start", type=_parse_day, default=datetime(2026, 1, 1, tzinfo=UTC))
    parser.add_argument("--days", type=int, default=210, help="daily bars, at least 30")
    parser.add_argument("--seed", type=int, default=20_261_027)
    parser.add_argument("--asset", default="BTC-USD")
    parser.add_argument(
        "--generated-at",
        type=datetime.fromisoformat,
        default=None,
        help="fixed ISO-8601 generation time for byte-identical fixtures",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.days < 30:
        print("error: --days must be at least 30", file=sys.stderr)
        return 2
    generated_at = args.generated_at or datetime.now(UTC)
    if generated_at.tzinfo is None:
        generated_at = generated_at.replace(tzinfo=UTC)
    generated_at = generated_at.astimezone(UTC)

    snapshot = build_price_snapshot(
        asset=args.asset,
        start=args.start,
        days=args.days,
        seed=args.seed,
        generated_at=generated_at,
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(snapshot, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    post_count = 0
    if args.posts_out is not None:
        posts = build_post_records(
            start=args.start, days=args.days, generated_at=generated_at
        )
        args.posts_out.parent.mkdir(parents=True, exist_ok=True)
        args.posts_out.write_text(
            "\n".join(json.dumps(record, sort_keys=True) for record in posts) + "\n",
            encoding="utf-8",
        )
        post_count = len(posts)

    print(
        f"wrote {args.days} SYNTHETIC daily bars to {args.out} and {post_count} "
        f"SYNTHETIC posts to {args.posts_out or '(not requested)'}"
    )
    print(f"recommended --now: {snapshot['recommended_now']}")
    print("These files are labelled synthetic; never report their metrics as real data.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
