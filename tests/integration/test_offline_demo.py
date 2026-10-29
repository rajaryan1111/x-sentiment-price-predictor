"""Realistic offline end-to-end execution on clearly labelled synthetic fixtures.

The generator writes inputs, the application CLI consumes them, and every artefact
checked here is produced by the application itself. Nothing in this module is a
claim about real BTC prices, real X posts or live provider behaviour.
"""

import json
import math
import socket
import subprocess
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

import httpx
import pytest

from xsentiment import main as cli
from xsentiment.pipeline.forecast_run import load_price_snapshot_metadata
from xsentiment.reporting.outlook import check_outlook_page

ROOT = Path(__file__).resolve().parents[2]
GENERATOR = ROOT / "scripts" / "make_offline_demo.py"
GENERATED_AT = "2026-10-27T00:00:00+00:00"
HORIZONS = {f"n+{index}" for index in range(6)}
MODELS = {"naive", "price_only", "sentiment_price"}
ARTEFACTS = (
    "evaluation-report.md",
    "outlook.md",
    "sentiment-vs-price.svg",
    "manifest.json",
    "metrics.json",
    "predictions.jsonl",
)


def generate(tmp_path: Path) -> tuple[Path, Path, dict]:
    prices = tmp_path / "prices.json"
    posts = tmp_path / "posts.jsonl"
    completed = subprocess.run(
        [
            sys.executable,
            str(GENERATOR),
            "--out",
            str(prices),
            "--posts-out",
            str(posts),
            "--generated-at",
            GENERATED_AT,
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    return prices, posts, json.loads(prices.read_text(encoding="utf-8"))


def test_generator_is_deterministic_and_explicitly_labelled(tmp_path: Path) -> None:
    first_prices, first_posts, payload = generate(tmp_path)
    second = tmp_path / "second"
    second.mkdir()
    other_prices, other_posts, _ = generate(second)

    assert first_prices.read_bytes() == other_prices.read_bytes()
    assert first_posts.read_bytes() == other_posts.read_bytes()
    assert payload["synthetic"] is True
    assert payload["fetch_mode"] == "synthetic_offline_demo"
    assert payload["generator_seed"] == 20_261_027
    assert "not a provider retrieval time" in payload["retrieval_time_note"]
    assert len(payload["candles"]) == 210

    expected_start = datetime(2026, 1, 1, tzinfo=UTC)
    for index, candle in enumerate(payload["candles"]):
        assert candle["timestamp"] == (expected_start + timedelta(days=index)).isoformat()
        low, high = float(candle["low"]), float(candle["high"])
        open_, close = float(candle["open"]), float(candle["close"])
        assert low <= min(open_, close) <= max(open_, close) <= high
        assert float(candle["volume"]) > 0

    records = [json.loads(line) for line in first_posts.read_text().splitlines()]
    assert len(records) == 209
    assert {record["query_mode"] for record in records} == {"cashtag", "keyword", "ticker"}
    for index, record in enumerate(records, start=1):
        assert record["synthetic"] is True
        assert record["source_platform"] == "synthetic"
        assert record["source_name"] == "synthetic_offline_demo"
        assert record["warnings"] == ["synthetic demonstration record, not observed X data"]
        assert len(record["source_record_hash"]) == 64
        created = datetime.fromisoformat(record["created_at"])
        retrieved = datetime.fromisoformat(record["retrieved_at"])
        cutoff = expected_start + timedelta(days=index)
        assert created < retrieved < cutoff


def test_price_snapshot_metadata_loader_uses_an_allow_list(tmp_path: Path) -> None:
    path = tmp_path / "snapshot.json"
    path.write_text(
        json.dumps(
            {
                "fetched_at": "2026-10-27T01:02:03+00:00",
                "requested_start": "2026-01-01T00:00:00+00:00",
                "synthetic": True,
                "api_key": "must-never-be-copied-into-a-manifest",
                "candles": [{"close": "1"}],
            }
        ),
        encoding="utf-8",
    )

    metadata = load_price_snapshot_metadata(path)

    assert metadata["fetched_at"] == "2026-10-27T01:02:03+00:00"
    assert metadata["synthetic"] is True
    assert "api_key" not in metadata
    assert "candles" not in metadata
    assert "must-never" not in json.dumps(metadata)


def test_fetch_prices_cli_records_retrieval_time_with_mocked_download(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def fake_download(start, end, asset):
        return [
            {
                "product_id": asset,
                "timestamp": "2026-01-01T00:00:00+00:00",
                "low": "99",
                "high": "101",
                "open": "100",
                "close": "100.5",
                "volume": "3",
            },
            {
                "product_id": asset,
                "timestamp": "2026-01-02T00:00:00+00:00",
                "low": "100",
                "high": "102",
                "open": "100.5",
                "close": "101.5",
                "volume": "4",
            },
        ]

    monkeypatch.setattr(cli, "_download_candles", fake_download)
    out = tmp_path / "prices.json"

    assert (
        cli.main(
            [
                "fetch-prices",
                "--start",
                "2026-01-01",
                "--end",
                "2026-01-03",
                "--out",
                str(out),
            ]
        )
        == 0
    )

    payload = json.loads(out.read_text(encoding="utf-8"))
    fetched_at = datetime.fromisoformat(payload["fetched_at"])
    assert fetched_at.tzinfo is not None
    assert fetched_at.utcoffset() == timedelta(0)
    assert payload["fetch_mode"] == "public_no_credentials"
    assert payload["requested_end"] == "2026-01-03T00:00:00+00:00"
    assert len(payload["candles"]) == 2
    assert load_price_snapshot_metadata(out)["fetched_at"] == payload["fetched_at"]


def test_offline_demo_end_to_end_writes_real_application_artifacts(tmp_path: Path) -> None:
    prices, posts, snapshot = generate(tmp_path)
    now = snapshot["recommended_now"]
    output = tmp_path / "run"
    note = "synthetic offline demo from scripts/make_offline_demo.py"
    command = [
        "run",
        "--prices",
        str(prices),
        "--posts",
        str(posts),
        "--out",
        str(output),
        "--now",
        now,
        "--input-note",
        note,
    ]

    assert cli.main(command) == 0

    for name in ARTEFACTS:
        path = output / name
        assert path.exists() and path.stat().st_size > 0, name

    manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
    metrics = json.loads((output / "metrics.json").read_text(encoding="utf-8"))
    predictions = [
        json.loads(line)
        for line in (output / "predictions.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]

    assert manifest["asset"] == "BTC-USD"
    assert manifest["generated_at"] == now
    assert manifest["dataset"]["posts"] == 209
    assert manifest["dataset"]["rows_with_sentiment"] > 0
    assert len(manifest["evaluation"]["folds"]) >= 5
    assert manifest["evaluation"]["predictions"] == len(predictions) > 0
    assert set(manifest["evaluation"]["assumptions"]["horizons"]) == HORIZONS
    assert manifest["provenance"]["input_source"] == "file_snapshot"
    assert manifest["provenance"]["input_note"] == note
    assert len(manifest["provenance"]["price_snapshot_sha256"]) == 64
    assert len(manifest["provenance"]["posts_snapshot_sha256"]) == 64

    lineage = manifest["input_lineage"]
    assert lineage["input_source"] == "file_snapshot"
    assert lineage["price"]["synthetic"] is True
    assert lineage["price"]["bars"] == 210
    assert lineage["price"]["product_ids"] == ["BTC-USD"]
    assert lineage["price"]["retrieved_at"] is None
    assert "does not record a provider retrieval time" in lineage["price"]["retrieved_at_reason"]
    assert lineage["price"]["snapshot_metadata"]["fetch_mode"] == "synthetic_offline_demo"
    assert lineage["posts"]["count"] == 209
    assert lineage["posts"]["source_platforms"] == ["synthetic"]
    assert lineage["posts"]["schema_versions"] == ["x-post-v1"]
    assert lineage["posts"]["retrieved_at_first"] is not None
    assert lineage["queries"]["modes"] == ["cashtag", "keyword", "ticker"]
    assert lineage["queries"]["term_count"] == 3
    assert len(lineage["queries"]["terms_sha256"]) == 64
    assert "Bitcoin" not in json.dumps(lineage["queries"])

    assert len(metrics["forecast_metrics"]) == 18
    assert set(metrics["mean_mae_by_model"]) == MODELS
    assert set(metrics["strategies"]) == MODELS
    for row in metrics["forecast_metrics"]:
        assert row["horizon"] in HORIZONS and row["model"] in MODELS
        assert row["samples"] > 0
        assert math.isfinite(row["mae"]) and row["mae"] >= 0
        assert math.isfinite(row["rmse"]) and row["rmse"] >= 0
        assert math.isfinite(row["mean_error"])

    assert predictions
    for prediction in predictions:
        assert prediction["horizon"] in HORIZONS
        assert prediction["model"] in MODELS
        assert isinstance(prediction["fold"], int) and prediction["fold"] >= 0
        assert prediction["cutoff"].endswith("+00:00")
        datetime.fromisoformat(prediction["cutoff"])
        for field in ("predicted_close", "actual_close", "reference_close", "error"):
            assert math.isfinite(prediction[field])

    report = (output / "evaluation-report.md").read_text(encoding="utf-8")
    outlook = (output / "outlook.md").read_text(encoding="utf-8")
    chart = (output / "sentiment-vs-price.svg").read_text(encoding="utf-8")
    assert "Out-of-sample forecast metrics" in report
    assert "Trading strategy and risk metrics" in report
    assert "Sharpe" in report and "Sortino" in report and "Max drawdown" in report
    assert "labelled synthetic" in report
    assert "labelled synthetic or non-X" in report
    assert check_outlook_page(outlook) == []
    assert "labelled synthetic" in outlook
    assert "labelled synthetic or non-X" in outlook
    assert "No recent-news context was supplied" in outlook
    assert "<svg" in chart
    assert "Day-over-day change" in chart
    assert "No scored posts are available" not in chart

    repeated = tmp_path / "run-repeat"
    repeat_command = list(command)
    repeat_command[repeat_command.index("--out") + 1] = str(repeated)
    assert cli.main(repeat_command) == 0
    assert (output / "predictions.jsonl").read_bytes() == (
        repeated / "predictions.jsonl"
    ).read_bytes()
    assert (output / "metrics.json").read_bytes() == (repeated / "metrics.json").read_bytes()


def test_offline_demo_run_makes_no_network_connection(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    prices, posts, snapshot = generate(tmp_path)
    output = tmp_path / "run-no-network"
    now = snapshot["recommended_now"]

    def forbidden(*args: object, **kwargs: object) -> None:
        raise AssertionError("the offline run attempted a network connection")

    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(socket, "create_connection", forbidden)
    monkeypatch.setattr(socket, "getaddrinfo", forbidden)
    for client in (httpx.AsyncClient, httpx.Client):
        for method in ("request", "stream", "send"):
            monkeypatch.setattr(client, method, forbidden)

    assert (
        cli.main(
            [
                "run",
                "--prices",
                str(prices),
                "--posts",
                str(posts),
                "--out",
                str(output),
                "--now",
                now,
                "--input-note",
                "offline network-isolation regression",
            ]
        )
        == 0
    )
    assert (output / "manifest.json").stat().st_size > 0
