"""Run one bounded, explicitly confirmed Apify X query.

This command can incur charges. It refuses to launch without
``--confirm-paid-run``, a valid local input file, configured credentials and
explicit item/USD/time caps. Post text is written only to the caller-supplied
local JSONL path; the manifest is sanitized and contains no post text.

Use one invocation per ticker, cashtag or keyword query so provenance is exact.
The output JSONL is accepted by ``xsentiment persist --posts`` and
``xsentiment run --posts``.
"""
from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import sys
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from xsentiment.config.settings import get_settings
from xsentiment.ingestion.apify_preflight import (
    PreflightReport,
    load_actor_input,
    validate_actor_input,
)
from xsentiment.ingestion.apify_x import ApifyXAdapter
from xsentiment.ingestion.contracts import XPostRecord

QUERY_MODES = ("ticker", "cashtag", "keyword")
MAX_QUERY_CHARS = 400


def _query(value: str) -> str:
    query = " ".join(value.split())
    if not query:
        raise argparse.ArgumentTypeError("--query must not be empty")
    if len(query) > MAX_QUERY_CHARS:
        raise argparse.ArgumentTypeError(f"--query must not exceed {MAX_QUERY_CHARS} characters")
    return query


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input-json",
        type=Path,
        required=True,
        help="local JSON matching the reviewed Actor's exact input schema",
    )
    parser.add_argument("--query-mode", choices=QUERY_MODES, required=True)
    parser.add_argument(
        "--query", type=_query, required=True, help="exact query label for provenance"
    )
    parser.add_argument(
        "--posts-out", type=Path, required=True, help="ignored local JSONL output"
    )
    parser.add_argument(
        "--manifest-out", type=Path, required=True, help="sanitized manifest JSON output"
    )
    parser.add_argument("--max-items", type=int, default=500)
    parser.add_argument("--max-total-charge-usd", type=float, default=0.5)
    parser.add_argument("--timeout-seconds", type=int, default=600)
    parser.add_argument(
        "--confirm-paid-run",
        action="store_true",
        help="required acknowledgement that this command may launch a paid Actor run",
    )
    args = parser.parse_args(argv)
    if not args.input_json.is_file():
        parser.error(f"input file not found: {args.input_json}")
    if not 1 <= args.max_items <= 1000:
        parser.error("--max-items must be within 1..1000")
    if not 0 < args.max_total_charge_usd <= 50:
        parser.error("--max-total-charge-usd must be > 0 and <= 50")
    if not 60 <= args.timeout_seconds <= 3600:
        parser.error("--timeout-seconds must be within 60..3600")
    return args


def _credentials_configured() -> bool:
    settings = get_settings()
    token = settings.apify_api_token
    return bool(
        token
        and token.get_secret_value().strip()
        and settings.apify_actor_id
        and settings.apify_actor_id.strip()
    )


def _serialize(post: XPostRecord) -> dict[str, Any]:
    return {
        "post_id": post.post_id,
        "created_at": post.created_at.isoformat(),
        "retrieved_at": post.retrieved_at.isoformat(),
        "text": post.text,
        "sentiment_score": post.sentiment_score,
        "likes": post.likes,
        "reposts": post.reposts,
        "views": post.views,
        "author_followers": post.author_followers,
        "provenance_url": post.provenance_url,
        "source_name": post.source_name,
        "source_platform": post.source_platform,
        "source_created_at_raw": post.source_created_at_raw,
        "source_utc_offset": post.source_utc_offset,
        "author_id": post.author_id,
        "query_mode": post.query_mode,
        "query": post.query,
        "source_record_hash": post.source_record_hash,
        "schema_version": post.schema_version,
        "warnings": list(post.warnings),
    }


def build_manifest(
    posts: list[XPostRecord],
    *,
    preflight: PreflightReport,
    query_mode: str,
    query: str,
    actor_id: str | None,
    max_items: int,
    max_total_charge_usd: float,
    timeout_seconds: int,
    generated_at: datetime,
) -> dict[str, Any]:
    """Sanitized run manifest: counts, coverage and caps, never post text."""
    event_times = sorted(post.created_at for post in posts)
    retrieved_times = sorted(post.retrieved_at for post in posts)
    daily = Counter(post.created_at.date().isoformat() for post in posts)
    ids = {post.post_id for post in posts}
    return {
        "generated_at": generated_at.isoformat(),
        "provider": "apify",
        "actor_id": actor_id,
        "query": {
            "mode": query_mode,
            "sha256": hashlib.sha256(query.encode("utf-8")).hexdigest(),
            "raw_query_stored": False,
        },
        "window": {
            "start": preflight.window_start.isoformat(),
            "end": preflight.window_end.isoformat(),
            "days": preflight.window_days,
        },
        "caps": {
            "max_items": max_items,
            "max_total_charge_usd": max_total_charge_usd,
            "timeout_seconds": timeout_seconds,
        },
        "counts": {
            "returned_records": len(posts),
            "unique_post_ids": len(ids),
            "duplicate_post_ids": len(posts) - len(ids),
            "records_with_text": sum(bool(post.text) for post in posts),
            "records_with_event_time": sum(post.created_at is not None for post in posts),
            "records_with_provenance_url": sum(bool(post.provenance_url) for post in posts),
            "records_with_likes": sum(post.likes is not None for post in posts),
            "records_with_reposts": sum(post.reposts is not None for post in posts),
            "records_with_views": sum(post.views is not None for post in posts),
            "records_with_author_followers": sum(
                post.author_followers is not None for post in posts
            ),
        },
        "coverage": {
            "event_time_first": event_times[0].isoformat() if event_times else None,
            "event_time_last": event_times[-1].isoformat() if event_times else None,
            "retrieved_at_first": retrieved_times[0].isoformat() if retrieved_times else None,
            "retrieved_at_last": retrieved_times[-1].isoformat() if retrieved_times else None,
            "days_with_posts": len(daily),
            "per_day_counts": dict(sorted(daily.items())),
        },
        "sanitization": {
            "post_text_in_manifest": False,
            "credentials_in_manifest": False,
        },
    }


async def run(args: argparse.Namespace) -> int:
    if not args.confirm_paid_run:
        print(
            "ingest refused: this command may launch a paid Actor run; rerun with "
            "--confirm-paid-run only after the source, cap and credentials are approved",
            file=sys.stderr,
        )
        return 2
    if not _credentials_configured():
        print(
            "ingest failed: APIFY_API_TOKEN and APIFY_ACTOR_ID are not configured",
            file=sys.stderr,
        )
        return 2
    try:
        actor_input = load_actor_input(args.input_json)
        preflight = validate_actor_input(actor_input, required_modes=(args.query_mode,))
    except (OSError, ValueError) as exc:
        print(f"ingest failed: {exc}", file=sys.stderr)
        return 2
    try:
        async with ApifyXAdapter() as adapter:
            posts = await adapter.run_and_fetch(
                actor_input,
                max_items=args.max_items,
                max_total_charge_usd=args.max_total_charge_usd,
                timeout_seconds=args.timeout_seconds,
                query_mode=args.query_mode,
                query=args.query,
            )
    except (OSError, ValueError, RuntimeError) as exc:
        print(f"ingest failed: {exc.__class__.__name__}: {exc}", file=sys.stderr)
        return 1

    lines = [json.dumps(_serialize(post), sort_keys=True) for post in posts]
    try:
        args.posts_out.parent.mkdir(parents=True, exist_ok=True)
        args.posts_out.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
        manifest = build_manifest(
            posts,
            preflight=preflight,
            query_mode=args.query_mode,
            query=args.query,
            actor_id=get_settings().apify_actor_id,
            max_items=args.max_items,
            max_total_charge_usd=args.max_total_charge_usd,
            timeout_seconds=args.timeout_seconds,
            generated_at=datetime.now(UTC),
        )
        args.manifest_out.parent.mkdir(parents=True, exist_ok=True)
        args.manifest_out.write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
    except OSError as exc:
        print(f"ingest failed: could not write output: {exc}", file=sys.stderr)
        return 1

    print(
        f"wrote {len(posts)} normalized posts to {args.posts_out} and a sanitized "
        f"manifest to {args.manifest_out}"
    )
    print(
        f"query_mode={args.query_mode} unique_post_ids={len({p.post_id for p in posts})} "
        f"raw_post_text_saved_only_locally=true"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(run(parse_args())))
