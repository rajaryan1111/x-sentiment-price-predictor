#!/usr/bin/env python3
"""Profile a local CSV or JSONL social-text file without printing or storing post text.

This is a schema/coverage/quality diagnostic, not a licensing check and not proof
of point-in-time availability. Keep source files outside Git and review source terms.
"""
from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from collections.abc import Iterable
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any

PROFILE_VERSION = "1.1.0"
ALIASES = {
    "id": ("post_id", "tweet_id", "id", "id_str", "status_id"),
    "text": ("text", "full_text", "tweet", "content", "post_text"),
    "timestamp": ("created_at", "createdAt", "timestamp", "date", "datetime", "created_at_utc"),
    "retrieved": (
        "retrieved_at",
        "retrievedAt",
        "observed_at",
        "collected_at",
        "collection_time",
    ),
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


def _valid_count(value: Any) -> bool:
    if value is None or isinstance(value, bool):
        return False
    try:
        integer = int(str(value))
    except (TypeError, ValueError, OverflowError):
        return False
    if not isinstance(value, int) and str(integer) != str(value).strip():
        return False
    return integer >= 0


def _engagement_column(row: dict[str, Any], kind: str) -> str | None:
    return next((alias for alias in ALIASES[kind] if alias in row), None)


def _resolve_reference_time(value: datetime | str | None) -> datetime:
    if value is None:
        return datetime.now(UTC)
    if isinstance(value, str):
        try:
            parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
        except ValueError as exc:
            raise ValueError("reference time must be an ISO-8601 timestamp") from exc
    else:
        parsed = value
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("reference time must include a UTC offset")
    return parsed.astimezone(UTC)


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
    retrieval_col = pick_field(fields, getattr(args, "retrieved_column", None), "retrieved")
    if not time_col:
        raise ValueError(
            "could not identify a timestamp column; pass --timestamp-column explicitly"
        )

    now = _resolve_reference_time(getattr(args, "as_of", None))
    window_start = now - timedelta(days=args.days)
    seen_ids: set[str] = set()
    counts: Counter[str] = Counter()
    invalid_engagement: Counter[str] = Counter()
    missing_engagement: Counter[str] = Counter()
    rows_with_engagement: Counter[str] = Counter()
    daily_counts: Counter[date] = Counter()
    extra_fields: set[str] = set()
    schema_drift_rows = 0
    quality_issue_rows = 0
    min_time: datetime | None = None
    max_time: datetime | None = None
    in_window_min: datetime | None = None
    in_window_max: datetime | None = None
    retrieval_present = 0
    retrieval_missing = 0
    retrieval_invalid = 0
    retrieval_before_event = 0
    base_fields = set(fields)

    for row in rows:
        counts["rows"] += 1
        row_has_issue = False
        extra = {str(key) for key in row if key is not None and str(key) not in base_fields}
        if extra:
            schema_drift_rows += 1
            extra_fields.update(extra)

        identifier = str(row.get(id_col, "")).strip() if id_col else ""
        text = row.get(text_col) if text_col else None
        raw_stamp = row.get(time_col) if time_col else None
        if not identifier:
            counts["missing_id"] += 1
            row_has_issue = True
        elif identifier in seen_ids:
            counts["duplicate_id_rows"] += 1
            row_has_issue = True
        else:
            seen_ids.add(identifier)
        if not isinstance(text, str) or not text.strip():
            counts["missing_text"] += 1
            row_has_issue = True

        if raw_stamp is None or not str(raw_stamp).strip():
            counts["missing_timestamp"] += 1
            row_has_issue = True
            stamp = None
        else:
            stamp = parse_timestamp(raw_stamp)
            if stamp is None:
                counts["invalid_timestamp"] += 1
                row_has_issue = True

        for field_name in ("likes", "reposts", "views", "followers"):
            actual = _engagement_column(row, field_name)
            value = row.get(actual) if actual else None
            if value is None or str(value).strip() == "":
                missing_engagement[field_name] += 1
            elif not _valid_count(value):
                invalid_engagement[field_name] += 1
                row_has_issue = True
            else:
                rows_with_engagement[field_name] += 1

        if retrieval_col:
            raw_retrieval = row.get(retrieval_col)
            if raw_retrieval is None or not str(raw_retrieval).strip():
                retrieval_missing += 1
                row_has_issue = True
            else:
                retrieval = parse_timestamp(raw_retrieval)
                if retrieval is None:
                    retrieval_invalid += 1
                    row_has_issue = True
                else:
                    retrieval_present += 1
                    if stamp is not None and retrieval < stamp:
                        retrieval_before_event += 1
                        row_has_issue = True

        if stamp is not None:
            counts["valid_timestamp_rows"] += 1
            min_time = stamp if min_time is None or stamp < min_time else min_time
            max_time = stamp if max_time is None or stamp > max_time else max_time
            if window_start <= stamp <= now:
                counts["rows_in_last_window"] += 1
                daily_counts[stamp.date()] += 1
                if in_window_min is None or stamp < in_window_min:
                    in_window_min = stamp
                if in_window_max is None or stamp > in_window_max:
                    in_window_max = stamp
            elif stamp > now:
                counts["future_timestamp_rows"] += 1
            else:
                counts["rows_older_than_window"] += 1

        if row_has_issue:
            quality_issue_rows += 1

    expected_dates = {
        (window_start + timedelta(days=offset)).date()
        for offset in range((now.date() - window_start.date()).days + 1)
    }
    observed_dates = set(daily_counts)
    missing_dates = sorted(expected_dates - observed_dates)
    per_day_counts = {
        day.isoformat(): daily_counts.get(day, 0) for day in sorted(expected_dates)
    }
    missing_required = [
        name
        for name, column in (("id", id_col), ("text", text_col), ("timestamp", time_col))
        if column is None
    ]

    return {
        "profile_version": PROFILE_VERSION,
        "file_name": path.name,
        "format": path.suffix.lower().lstrip("."),
        "profiled_at_utc": datetime.now(UTC).isoformat(),
        "reference_time_utc": now.isoformat(),
        "requested_lookback_days": args.days,
        "window_start_utc": window_start.isoformat(),
        "window_end_utc_inclusive": now.isoformat(),
        "columns": fields,
        "detected_columns": {
            "id": id_col,
            "text": text_col,
            "timestamp": time_col,
            "retrieved_at": retrieval_col,
        },
        "schema_compatibility": {
            "required_columns_present": not missing_required,
            "missing_required_columns": missing_required,
            "engagement_columns": {
                field_name: _engagement_column_from_fields(fields, field_name)
                for field_name in ("likes", "reposts", "views", "followers")
            },
            "extra_fields_seen": sorted(extra_fields),
            "schema_drift_rows": schema_drift_rows,
        },
        "row_count": counts["rows"],
        "unique_nonempty_ids": len(seen_ids),
        "duplicate_id_rows": counts["duplicate_id_rows"],
        "missing_id_rows": counts["missing_id"],
        "missing_text_rows": counts["missing_text"],
        "missing_timestamp_rows": counts["missing_timestamp"],
        "invalid_timestamp_rows": counts["invalid_timestamp"],
        "missing_or_invalid_timestamp_rows": (
            counts["missing_timestamp"] + counts["invalid_timestamp"]
        ),
        "future_timestamp_rows": counts["future_timestamp_rows"],
        "rows_older_than_window": counts["rows_older_than_window"],
        "rows_in_last_window": counts["rows_in_last_window"],
        "earliest_valid_timestamp_utc": min_time.isoformat() if min_time else None,
        "latest_valid_timestamp_utc": max_time.isoformat() if max_time else None,
        "earliest_timestamp_in_window_utc": in_window_min.isoformat()
        if in_window_min
        else None,
        "latest_timestamp_in_window_utc": in_window_max.isoformat()
        if in_window_max
        else None,
        "coverage": {
            "expected_utc_days": len(expected_dates),
            "observed_utc_days": len(observed_dates),
            "missing_utc_days": [day.isoformat() for day in missing_dates],
            "coverage_complete": not missing_dates and bool(expected_dates),
            "per_day_counts": per_day_counts,
        },
        "rows_with_engagement": {
            key: rows_with_engagement[key] for key in ("likes", "reposts", "views", "followers")
        },
        "missing_engagement_counts": {
            key: missing_engagement[key] for key in ("likes", "reposts", "views", "followers")
        },
        "invalid_engagement_counts": {
            key: invalid_engagement[key] for key in ("likes", "reposts", "views", "followers")
        },
        "rows_with_any_quality_issue": quality_issue_rows,
        "retrieval_timestamp": {
            "column_present": retrieval_col is not None,
            "valid_rows": retrieval_present,
            "missing_rows": retrieval_missing,
            "invalid_rows": retrieval_invalid,
            "retrieval_before_event_rows": retrieval_before_event,
        },
        "historical_retrieval_time_known": False,
        "point_in_time_backtest_ready": False,
        "raw_text_printed": False,
        "note": (
            "Profile only. This script does not verify license/terms, infer retrieval time, "
            "download/hydrate posts, or certify 180-day coverage."
        ),
    }


def _engagement_column_from_fields(fields: Iterable[str], kind: str) -> str | None:
    available = set(fields)
    return next((alias for alias in ALIASES[kind] if alias in available), None)


def _parse_reference_time(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            f"{value!r} is not an ISO-8601 timestamp"
        ) from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise argparse.ArgumentTypeError("reference time must include a UTC offset")
    return parsed.astimezone(UTC)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "file", type=Path, help="Local CSV or JSONL/NDJSON file; keep it outside Git"
    )
    parser.add_argument(
        "--days", type=int, default=180, help="Lookback window in days (default: 180)"
    )
    parser.add_argument(
        "--as-of",
        type=_parse_reference_time,
        default=None,
        help="Reference time for a reproducible window; defaults to the current UTC time",
    )
    parser.add_argument("--id-column")
    parser.add_argument("--text-column")
    parser.add_argument("--timestamp-column")
    parser.add_argument(
        "--retrieved-column",
        help="Optional first-observed/retrieval timestamp column for coverage reporting",
    )
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
