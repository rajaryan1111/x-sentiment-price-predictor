"""Run a small, explicitly bounded Apify X schema smoke test.

This command may incur charges. Run it only after reviewing the selected Actor's
current terms, input schema and pricing. It prints only aggregate/schema metadata,
never post text or credentials, and persists no raw records.
"""
from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path

from xsentiment.ingestion.apify_x import ApifyXAdapter


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input-json",
        type=Path,
        required=True,
        help="Local JSON file matching the reviewed Actor's exact input schema",
    )
    parser.add_argument("--max-items", type=int, default=10)
    parser.add_argument("--max-total-charge-usd", type=float, default=0.25)
    parser.add_argument("--timeout-seconds", type=int, default=300)
    args = parser.parse_args()
    if not args.input_json.is_file():
        parser.error(f"input file not found: {args.input_json}")
    return args


async def run(args: argparse.Namespace) -> int:
    try:
        actor_input = json.loads(args.input_json.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: could not read valid JSON input: {exc.__class__.__name__}")
        return 2
    if not isinstance(actor_input, dict):
        print("ERROR: Actor input JSON root must be an object")
        return 2

    async with ApifyXAdapter() as adapter:
        posts = await adapter.run_and_fetch(
            actor_input,
            max_items=args.max_items,
            max_total_charge_usd=args.max_total_charge_usd,
            timeout_seconds=args.timeout_seconds,
        )

    ids = {post.post_id for post in posts}
    output = {
        "provider": "apify",
        "actor_id": adapter.settings.apify_actor_id,
        "returned_records": len(posts),
        "unique_post_ids": len(ids),
        "records_with_text": sum(bool(post.text) for post in posts),
        "records_with_event_time": sum(bool(post.created_at) for post in posts),
        "records_with_provenance_url": sum(bool(post.provenance_url) for post in posts),
        "records_with_likes": sum(post.likes is not None for post in posts),
        "records_with_reposts": sum(post.reposts is not None for post in posts),
        "records_with_views": sum(post.views is not None for post in posts),
        "records_with_author_followers": sum(
            post.author_followers is not None for post in posts
        ),
        "records_with_sentiment_score": sum(
            post.sentiment_score is not None for post in posts
        ),
        "raw_posts_saved": False,
    }
    print(json.dumps(output, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(run(parse_args())))
