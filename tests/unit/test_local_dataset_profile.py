from __future__ import annotations

import csv
import json
from argparse import Namespace
from datetime import UTC, datetime
from pathlib import Path

import pytest

from xsentiment.ingestion.local_dataset_profile import parse_timestamp, profile


def test_parse_timestamp_requires_timezone_and_normalizes_offsets() -> None:
    assert parse_timestamp("2026-10-25T12:00:00Z") is not None
    assert parse_timestamp("2026-10-25T12:00:00") is None
    assert parse_timestamp("not-a-date") is None
    assert parse_timestamp("2026-10-25T07:30:00-05:00") == datetime(
        2026, 10, 25, 12, 30, tzinfo=UTC
    )
    assert parse_timestamp("Sun Oct 25 12:30:00 +0000 2026") == datetime(
        2026, 10, 25, 12, 30, tzinfo=UTC
    )


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
            file=path,
            days=180,
            id_column=None,
            text_column=None,
            timestamp_column=None,
            as_of=datetime(2026, 10, 26, tzinfo=UTC),
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
                file=path,
                days=180,
                id_column=None,
                text_column=None,
                timestamp_column=None,
                as_of=datetime(2026, 10, 26, tzinfo=UTC),
            )
        )

    result = profile(
        Namespace(
            file=path,
            days=180,
            id_column="post_id",
            text_column="body",
            timestamp_column="event",
            as_of=datetime(2026, 10, 26, tzinfo=UTC),
        )
    )
    assert result["row_count"] == 1
    assert result["rows_in_last_window"] == 1
    assert result["point_in_time_backtest_ready"] is False


def test_profile_reports_daily_gaps_and_rejects_invalid_counts(tmp_path: Path) -> None:
    path = tmp_path / "coverage.jsonl"
    rows = [
        {
            "id": "1",
            "text": "BTC day one",
            "created_at": "2026-10-24T12:00:00Z",
            "likes": "-1",
            "views": "not-a-number",
        },
        {
            "id": "2",
            "text": "BTC day three",
            "created_at": "2026-10-26T12:00:00Z",
            "likes": "5",
            "views": "10",
        },
    ]
    path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")

    result = profile(
        Namespace(
            file=path,
            days=2,
            id_column=None,
            text_column=None,
            timestamp_column=None,
            as_of=datetime(2026, 10, 26, 12, tzinfo=UTC),
        )
    )

    assert result["coverage"]["expected_utc_days"] == 3
    assert result["coverage"]["observed_utc_days"] == 2
    assert result["coverage"]["missing_utc_days"] == ["2026-10-25"]
    assert result["coverage"]["coverage_complete"] is False
    assert result["coverage"]["per_day_counts"]["2026-10-25"] == 0
    assert result["invalid_engagement_counts"]["likes"] == 1
    assert result["invalid_engagement_counts"]["views"] == 1
    assert result["rows_with_engagement"]["likes"] == 1
    assert result["rows_with_any_quality_issue"] == 1
    assert result["schema_compatibility"]["schema_drift_rows"] == 0


def test_profile_is_deterministic_for_a_fixed_reference_time(tmp_path: Path) -> None:
    path = tmp_path / "deterministic.csv"
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["id", "text", "created_at"])
        writer.writeheader()
        writer.writerow(
            {"id": "1", "text": "BTC", "created_at": "2026-10-24T00:00:00Z"}
        )
        writer.writerow(
            {"id": "2", "text": "ETH", "created_at": "2026-10-26T00:00:00Z"}
        )
    args = Namespace(
        file=path,
        days=180,
        id_column=None,
        text_column=None,
        timestamp_column=None,
        as_of=datetime(2026, 10, 26, tzinfo=UTC),
    )

    first = profile(args)
    second = profile(args)

    assert first["coverage"] == second["coverage"]
    assert first["rows_in_last_window"] == second["rows_in_last_window"]
    assert first["earliest_valid_timestamp_utc"] == second["earliest_valid_timestamp_utc"]
    assert first["point_in_time_backtest_ready"] is False


def test_profile_reports_retrieval_timestamp_coverage(tmp_path: Path) -> None:
    path = tmp_path / "retrieval.jsonl"
    rows = [
        {
            "id": "1",
            "text": "BTC",
            "created_at": "2026-10-25T12:00:00Z",
            "retrieved_at": "2026-10-26T12:00:00Z",
        },
        {
            "id": "2",
            "text": "BTC",
            "created_at": "2026-10-25T13:00:00Z",
            "retrieved_at": "",
        },
        {
            "id": "3",
            "text": "BTC",
            "created_at": "2026-10-25T14:00:00Z",
            "retrieved_at": "2026-10-25T13:00:00Z",
        },
    ]
    path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")

    result = profile(
        Namespace(
            file=path,
            days=180,
            id_column=None,
            text_column=None,
            timestamp_column=None,
            retrieved_column=None,
            as_of=datetime(2026, 10, 26, tzinfo=UTC),
        )
    )

    retrieval = result["retrieval_timestamp"]
    assert result["detected_columns"]["retrieved_at"] == "retrieved_at"
    assert retrieval["column_present"] is True
    assert retrieval["valid_rows"] == 2
    assert retrieval["missing_rows"] == 1
    assert retrieval["retrieval_before_event_rows"] == 1
    assert result["historical_retrieval_time_known"] is False


def test_profile_flags_jsonl_schema_drift(tmp_path: Path) -> None:
    path = tmp_path / "drift.jsonl"
    path.write_text(
        json.dumps(
            {"id": "1", "text": "BTC", "created_at": "2026-10-25T00:00:00Z"}
        )
        + "\n"
        + json.dumps(
            {
                "id": "2",
                "text": "BTC",
                "created_at": "2026-10-25T01:00:00Z",
                "unexpected_field": "x",
            }
        )
        + "\n",
        encoding="utf-8",
    )

    result = profile(
        Namespace(
            file=path,
            days=180,
            id_column=None,
            text_column=None,
            timestamp_column=None,
            as_of=datetime(2026, 10, 26, tzinfo=UTC),
        )
    )

    assert result["schema_compatibility"]["schema_drift_rows"] == 1
    assert result["schema_compatibility"]["extra_fields_seen"] == ["unexpected_field"]
    assert result["coverage"]["coverage_complete"] is False
