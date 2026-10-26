from __future__ import annotations

import csv
import json
from argparse import Namespace
from pathlib import Path

import pytest

from xsentiment.ingestion.local_dataset_profile import parse_timestamp, profile


def test_parse_timestamp_requires_timezone() -> None:
    assert parse_timestamp("2026-10-25T12:00:00Z") is not None
    assert parse_timestamp("2026-10-25T12:00:00") is None
    assert parse_timestamp("not-a-date") is None


def test_profile_csv_counts_rows_duplicates_and_window(tmp_path: Path) -> None:
    path = tmp_path / "sample.csv"
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["id", "text", "created_at", "likes", "retweet_count"],
        )
        writer.writeheader()
        writer.writerow({
            "id": "1", "text": "BTC is moving", "created_at": "2026-10-25T12:00:00Z",
            "likes": "4", "retweet_count": "2",
        })
        writer.writerow({
            "id": "1", "text": "duplicate", "created_at": "2026-10-24T12:00:00Z",
            "likes": "", "retweet_count": "",
        })
        writer.writerow({
            "id": "", "text": "", "created_at": "invalid", "likes": "", "retweet_count": "",
        })

    result = profile(
        Namespace(
            file=path, days=180, id_column=None, text_column=None, timestamp_column=None
        )
    )

    assert result["row_count"] == 3
    assert result["unique_nonempty_ids"] == 1
    assert result["duplicate_id_rows"] == 1
    assert result["missing_id_rows"] == 1
    assert result["missing_text_rows"] == 1
    assert result["missing_or_invalid_timestamp_rows"] == 1
    assert result["rows_in_last_window"] == 2
    assert result["rows_with_engagement"]["likes"] == 1
    assert result["point_in_time_backtest_ready"] is False
    assert result["raw_text_printed"] is False


def test_profile_jsonl_requires_explicit_timestamp_when_no_alias(tmp_path: Path) -> None:
    path = tmp_path / "sample.jsonl"
    path.write_text(
        json.dumps({"post_id": "a", "body": "BTC", "event": "2026-10-25T12:00:00Z"}) + "\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="timestamp column"):
        profile(
            Namespace(
                file=path, days=180, id_column=None, text_column=None, timestamp_column=None
            )
        )

    result = profile(
        Namespace(
            file=path,
            days=180,
            id_column="post_id",
            text_column="body",
            timestamp_column="event",
        )
    )
    assert result["row_count"] == 1
    assert result["rows_in_last_window"] == 1
    assert result["point_in_time_backtest_ready"] is False
