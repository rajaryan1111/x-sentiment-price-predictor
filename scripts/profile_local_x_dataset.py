#!/usr/bin/env python3
"""Profile a local CSV or JSONL social-text file without printing or storing post text.

This is a schema/coverage diagnostic, not a licensing check and not proof of
point-in-time availability. Keep source files outside Git and review source terms.
"""
from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Iterable

ALIASES = {
    "id": ("post_id", "tweet_id", "id", "id_str", "status_id"),
    "text": ("text", "full_text", "tweet", "content", "post_text"),
    "timestamp": ("created_at", "createdAt", "timestamp", "date", "datetime", "created_at_utc"),
    "likes": ("likes", "like_count", "favorite_count", "favoriteCount"),
    "reposts": ("reposts", "retweets", "retweet_count", "retweetCount"),
    "views": ("views", "view_count", "viewCount", "impression_count"),
    "followers": ("author_followers", "followers_count", "followersCount", "user_followers"),
}


def parse_timestamp(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    raw = value.strip()
    try:
        # ISO timestamps are preferred; support common trailing Z notation.
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        for fmt in ("%a %b %d %H:%M:%S %z %Y", "%Y-%m-%d %H:%M:%S%z"):
            try:
                parsed = datetime.strptime(raw, fmt)
                break
            except ValueError:
                continue
        else:
            return None
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        return None
    return parsed.astimezone(UTC)


def pick_field(fields: Iterable[str], explicit: str | None, kind: str) -> str | None:
    available = set(fields)
    if explicit:
        if explicit not in available:
            raise ValueError(f"requested {kind} column {explicit!r} not found")
        return explicit
    return next((name for name in ALIASES[kind] if name in available), None)


def read_rows(path: Path) -> tuple[list[str], Iterable[dict[str, Any]]]:
    if path.suffix.lower() in {".jsonl", ".ndjson"}:
        def jsonl_rows():
            with path.open("r", encoding="utf-8-sig") as handle:
                for line in handle:
                    if not line.strip():
                        continue
                    item = json.loads(line)
                    if not isinstance(item, dict):
                        raise ValueError("each JSONL line must be a JSON object")
                    yield item
        with path.open("r", encoding="utf-8-sig") as handle:
            first = next((line for line in handle if line.strip()), None)
        if first is None:
            return [], iter(())
        parsed = json.loads(first)
        if not isinstance(parsed, dict):
            raise ValueError("each JSONL line must be a JSON object")
        return list(parsed.keys()), jsonl_rows()

    if path.suffix.lower() != ".csv":
        raise ValueError("supported formats are .csv, .jsonl, and .ndjson")

    handle = path.open("r", encoding="utf-8-sig", newline="")
    reader = csv.DictReader(handle)
    fields = reader.fieldnames or []

    def csv_rows():
        try:
            yield from reader
        finally:
            handle.close()

    return fields, csv_rows()


def profile(args: argparse.Namespace) -> dict[str, Any]:
    path: Path = args.file
    if not path.is_file():
        raise ValueError(f"input file not found: {path}")
    fields, rows = read_rows(path)
    if not fields:
        raise ValueError("input file is empty or has no header/fields")

    id_col = pick_field(fields, args.id_column, "id")
    text_col = pick_field(fields, args.text_column, "text")
    time_col = pick_field(fields, args.timestamp_column, "timestamp")
    if not time_col:
        raise ValueError(
            "could not identify a timestamp column; pass --timestamp-column explicitly"
        )

    now = datetime.now(UTC)
    window_start = now - timedelta(days=args.days)
    seen_ids: set[str] = set()
    counts: Counter[str] = Counter()
    min_time: datetime | None = None
    max_time: datetime | None = None
    in_window_min: datetime | None = None
    in_window_max: datetime | None = None

    for row in rows:
        counts["rows"] += 1
        identifier = str(row.get(id_col, "")).strip() if id_col else ""
        text = row.get(text_col) if text_col else None
        stamp = parse_timestamp(row.get(time_col))
        if not identifier:
            counts["missing_id"] += 1
        elif identifier in seen_ids:
            counts["duplicate_id_rows"] += 1
        else:
            seen_ids.add(identifier)
        if not isinstance(text, str) or not text.strip():
            counts["missing_text"] += 1
        if stamp is None:
            counts["missing_or_invalid_timestamp"] += 1
            continue
        min_time = stamp if min_time is None or stamp < min_time else min_time
        max_time = stamp if max_time is None or stamp > max_time else max_time
        if window_start <= stamp <= now:
            counts["rows_in_last_window"] += 1
            if in_window_min is None or stamp < in_window_min:
                in_window_min = stamp
            if in_window_max is None or stamp > in_window_max:
                in_window_max = stamp
        elif stamp > now:
            counts["future_timestamp_rows"] += 1
        else:
            counts["rows_older_than_window"] += 1

        engagement_aliases = (
            ("likes", ALIASES["likes"]),
            ("reposts", ALIASES["reposts"]),
            ("views", ALIASES["views"]),
            ("followers", ALIASES["followers"]),
        )
        for field_name, aliases in engagement_aliases:
            actual = next((alias for alias in aliases if alias in row), None)
            if actual and row.get(actual) not in (None, ""):
                counts[f"rows_with_{field_name}"] += 1

    return {
        "file_name": path.name,
        "format": path.suffix.lower().lstrip("."),
        "profiled_at_utc": now.isoformat(),
        "requested_lookback_days": args.days,
        "window_start_utc": window_start.isoformat(),
        "window_end_utc_inclusive": now.isoformat(),
        "columns": fields,
        "detected_columns": {"id": id_col, "text": text_col, "timestamp": time_col},
        "row_count": counts["rows"],
        "unique_nonempty_ids": len(seen_ids),
        "duplicate_id_rows": counts["duplicate_id_rows"],
        "missing_id_rows": counts["missing_id"],
        "missing_text_rows": counts["missing_text"],
        "missing_or_invalid_timestamp_rows": counts["missing_or_invalid_timestamp"],
        "future_timestamp_rows": counts["future_timestamp_rows"],
        "rows_older_than_window": counts["rows_older_than_window"],
        "rows_in_last_window": counts["rows_in_last_window"],
        "earliest_valid_timestamp_utc": min_time.isoformat() if min_time else None,
        "latest_valid_timestamp_utc": max_time.isoformat() if max_time else None,
        "earliest_timestamp_in_window_utc": in_window_min.isoformat() if in_window_min else None,
        "latest_timestamp_in_window_utc": in_window_max.isoformat() if in_window_max else None,
        "rows_with_engagement": {
            key: counts[f"rows_with_{key}"] for key in ("likes", "reposts", "views", "followers")
        },
        "historical_retrieval_time_known": False,
        "point_in_time_backtest_ready": False,
        "raw_text_printed": False,
        "note": (
            "Profile only. This script does not verify license/terms, infer retrieval time, "
            "download/hydrate posts, or certify 180-day coverage."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "file", type=Path, help="Local CSV or JSONL/NDJSON file; keep it outside Git"
    )
    parser.add_argument(
        "--days", type=int, default=180, help="Lookback window in days (default: 180)"
    )
    parser.add_argument("--id-column")
    parser.add_argument("--text-column")
    parser.add_argument("--timestamp-column")
    args = parser.parse_args()
    if args.days < 1 or args.days > 3650:
        parser.error("--days must be between 1 and 3650")
    try:
        result = profile(args)
    except (OSError, UnicodeError, json.JSONDecodeError, csv.Error, ValueError) as exc:
        parser.error(str(exc))
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
