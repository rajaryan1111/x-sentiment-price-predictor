"""Run a small, explicitly bounded Apify X schema smoke test.

This command may incur charges. Run it only after reviewing the selected Actor's
current terms, input schema and pricing. It prints only aggregate/schema metadata,
never post text or credentials, and persists no raw records.

Use ``--validate-only`` first: it validates the local JSON contract and reports
whether credentials are configured without making any network call or launching a
paid run.
"""
from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path

from xsentiment.config.settings import get_settings
from xsentiment.ingestion.apify_preflight import load_actor_input, validate_actor_input
from xsentiment.ingestion.apify_x import ApifyXAdapter


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
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
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="validate the local input and credential presence; make no network call",
    )
    args = parser.parse_args(argv)
    if not args.input_json.is_file():
        parser.error(f"input file not found: {args.input_json}")
    return args


def _credential_status() -> dict[str, bool]:
    """Report presence only; never print or return a credential value."""
    settings = get_settings()
    token = settings.apify_api_token
    return {
        "APIFY_API_TOKEN": bool(token and token.get_secret_value().strip()),
        "APIFY_ACTOR_ID": bool(settings.apify_actor_id and settings.apify_actor_id.strip()),
    }


def _validate(args: argparse.Namespace) -> tuple[dict[str, object] | None, int]:
    try:
        actor_input = load_actor_input(args.input_json)
        report = validate_actor_input(actor_input)
    except (OSError, ValueError) as exc:
        print(f"ERROR: {exc}")
        return None, 2
    output = {
        "valid": True,
        "network_call_made": False,
        "paid_run_launched": False,
        "query_modes": list(report.query_modes),
        "window_start": report.window_start.isoformat(),
        "window_end": report.window_end.isoformat(),
        "window_days": report.window_days,
        "max_items": report.max_items,
        "credentials_configured": _credential_status(),
        "warnings": list(report.warnings),
    }
    return output, 0


async def run(args: argparse.Namespace) -> int:
    output, status = _validate(args)
    if output is None:
        return status
    if args.validate_only:
        print(json.dumps(output, indent=2))
        return 0

    if not all(_credential_status().values()):
        print("ERROR: Apify credentials are not configured; no run was launched")
        return 2

    try:
        actor_input = load_actor_input(args.input_json)
        async with ApifyXAdapter() as adapter:
            posts = await adapter.run_and_fetch(
                actor_input,
                max_items=args.max_items,
                max_total_charge_usd=args.max_total_charge_usd,
                timeout_seconds=args.timeout_seconds,
            )
    except (OSError, ValueError, RuntimeError) as exc:
        print(f"ERROR: {exc.__class__.__name__}: {exc}")
        return 1

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
