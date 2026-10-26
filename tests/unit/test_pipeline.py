"""Pipeline tests use an explicitly synthetic fixture; no network call is made."""

import json
import math
import subprocess
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from xsentiment.main import main
from xsentiment.pipeline import forecast_run
from xsentiment.pipeline.forecast_run import (
    _code_revision,
    load_candles,
    load_news_context,
    load_posts,
    run_forecast_pipeline,
    sha256_file,
)


def repo_root() -> Path:
    return forecast_run._REPO_ROOT

START = datetime(2026, 1, 1, tzinfo=UTC)


def snapshot_candles(days: int) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for index in range(days):
        close = 100.0 + 6.0 * math.sin(index / 4.0) + 0.4 * index
        value = f"{round(close, 6)}"
        rows.append(
            {
                "product_id": "BTC-USD",
                "timestamp": (START + timedelta(days=index)).isoformat(),
                "low": value,
                "high": value,
                "open": value,
                "close": value,
                "volume": "3",
            }
        )
    return rows


def write_prices(path: Path, days: int) -> Path:
    path.write_text(json.dumps({"product_id": "BTC-USD", "candles": snapshot_candles(days)}))
    return path


def write_posts(path: Path, candles: list[dict[str, str]]) -> Path:
    lines = []
    for index, candle in enumerate(candles[1:], start=1):
        moment = datetime.fromisoformat(candle["timestamp"])
        lines.append(
            json.dumps(
                {
                    "post_id": f"p{index}",
                    "created_at": (moment - timedelta(hours=1)).isoformat(),
                    "retrieved_at": (moment - timedelta(minutes=30)).isoformat(),
                    "text": f"synthetic post {index}",
                    "sentiment_score": round(math.sin(index / 3.0), 4),
                    "likes": index,
                }
            )
        )
    path.write_text("\n".join(lines) + "\n")
    return path


def test_candles_round_trip_and_invalid_rows_fail_closed(tmp_path: Path) -> None:
    path = write_prices(tmp_path / "prices.json", 5)

    candles = load_candles(path)

    assert len(candles) == 5
    assert candles[0].timestamp == START
    assert candles[0].product_id == "BTC-USD"

    broken = tmp_path / "broken.json"
    broken.write_text(json.dumps({"candles": [{"product_id": "BTC-USD"}]}))
    with pytest.raises(ValueError, match="missing"):
        load_candles(broken)

    empty = tmp_path / "empty.json"
    empty.write_text(json.dumps({"candles": []}))
    with pytest.raises(ValueError, match="non-empty"):
        load_candles(empty)


def test_posts_loader_reports_the_offending_line(tmp_path: Path) -> None:
    good = write_posts(tmp_path / "posts.jsonl", snapshot_candles(3))
    assert len(load_posts(good)) == 2

    bad = tmp_path / "bad.jsonl"
    bad.write_text('{"post_id": "a", "created_at": "2026-01-02T00:00:00+00:00"}\n')
    with pytest.raises(ValueError, match="posts line 1 is missing"):
        load_posts(bad)

    naive = tmp_path / "naive.jsonl"
    naive.write_text(
        json.dumps(
            {
                "post_id": "a",
                "created_at": "2026-01-02T00:00:00",
                "retrieved_at": "2026-01-02T00:00:00+00:00",
                "text": "x",
            }
        )
        + "\n"
    )
    with pytest.raises(ValueError, match="must include a timezone"):
        load_posts(naive)


def test_posts_loader_preserves_utc_provenance_and_warnings(tmp_path: Path) -> None:
    path = tmp_path / "provenance.jsonl"
    path.write_text(
        json.dumps(
            {
                "post_id": "p1",
                "created_at": "2026-01-01T07:30:00-05:00",
                "retrieved_at": "2026-01-01T13:00:00+00:00",
                "text": "synthetic post",
                "source_name": "apify_x",
                "source_platform": "x",
                "source_created_at_raw": "2026-01-01T07:30:00-05:00",
                "source_utc_offset": "-05:00",
                "author_id": "author-1",
                "query_mode": "cashtag",
                "query": "$BTC",
                "source_record_hash": "a" * 64,
                "warnings": ["engagement counts were not available"],
            }
        )
        + "\n",
        encoding="utf-8",
    )

    record = load_posts(path)[0]

    assert record.created_at == datetime(2026, 1, 1, 12, 30, tzinfo=UTC)
    assert record.source_created_at_raw == "2026-01-01T07:30:00-05:00"
    assert record.source_utc_offset == "-05:00"
    assert record.author_id == "author-1"
    assert record.query_mode == "cashtag"
    assert record.query == "$BTC"
    assert record.source_record_hash == "a" * 64
    assert record.warnings == ("engagement counts were not available",)


def test_news_context_is_optional_and_validated(tmp_path: Path) -> None:
    path = tmp_path / "news.jsonl"
    path.write_text(
        json.dumps(
            {
                "title": "BTC steady",
                "url": "https://example.invalid/n",
                "published_at": "2026-01-05",
            }
        )
        + "\n"
    )
    assert load_news_context(path) == ["BTC steady (2026-01-05 — https://example.invalid/n)"]

    empty_title = tmp_path / "bad_news.jsonl"
    empty_title.write_text('{"url": "https://example.invalid/n"}\n')
    with pytest.raises(ValueError, match="missing a title"):
        load_news_context(empty_title)


def test_pipeline_writes_every_documented_artefact(tmp_path: Path) -> None:
    prices = write_prices(tmp_path / "prices.json", 120)
    posts = write_posts(tmp_path / "posts.jsonl", snapshot_candles(120))

    artifacts = run_forecast_pipeline(
        candles=load_candles(prices),
        posts=load_posts(posts),
        output_dir=tmp_path / "run",
        now=START + timedelta(days=121),
        provenance={
            "price_snapshot": str(prices),
            "price_snapshot_sha256": sha256_file(prices),
        },
    )

    for path in (
        artifacts.report_path,
        artifacts.outlook_path,
        artifacts.chart_path,
        artifacts.manifest_path,
        artifacts.predictions_path,
        artifacts.metrics_path,
    ):
        assert path.exists() and path.stat().st_size > 0

    manifest = json.loads(artifacts.manifest_path.read_text())
    metrics = json.loads(artifacts.metrics_path.read_text())

    assert manifest["asset"] == "BTC-USD"
    assert manifest["dataset"]["rows_with_sentiment"] > 0
    assert manifest["evaluation"]["folds"]
    assert manifest["provenance"]["price_snapshot_sha256"] == sha256_file(prices)
    assert manifest["provenance"]["sentiment_scorer"].startswith("vader ")
    assert set(metrics["mean_mae_by_model"]) == {"naive", "price_only", "sentiment_price"}
    assert metrics["strategies"]["price_only"]["assumptions"]["fee_rate"] == 0.001


def test_run_manifest_records_the_actual_checkout_revision(tmp_path: Path) -> None:
    """NFR1: the revision comes from the real repository, never an inference."""
    prices = write_prices(tmp_path / "prices.json", 90)

    artifacts = run_forecast_pipeline(
        candles=load_candles(prices),
        output_dir=tmp_path / "run",
        now=START + timedelta(days=91),
    )
    manifest = json.loads(artifacts.manifest_path.read_text())
    expected = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        cwd=repo_root(),
        check=True,
    ).stdout.strip()

    assert manifest["provenance"]["code_revision"] == expected
    assert set(manifest["provenance"]["code_revision"]) <= set("0123456789abcdef")
    assert "code_revision_reason" not in manifest["provenance"]


def test_code_revision_fails_closed_outside_a_repository(tmp_path: Path) -> None:
    result = _code_revision(root=tmp_path)

    assert result == {
        "code_revision": "unavailable",
        "code_revision_reason": "not a git repository (source archive or imported install)",
    }


def test_code_revision_reports_a_missing_git_executable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def explode(*args: object, **kwargs: object) -> object:
        raise FileNotFoundError("no git on this host")

    monkeypatch.setattr(forecast_run.subprocess, "run", explode)

    assert _code_revision(root=tmp_path) == {
        "code_revision": "unavailable",
        "code_revision_reason": "git executable is not available",
    }


def test_caller_supplied_revision_is_never_silently_overwritten(tmp_path: Path) -> None:
    prices = write_prices(tmp_path / "prices.json", 90)

    artifacts = run_forecast_pipeline(
        candles=load_candles(prices),
        output_dir=tmp_path / "run",
        now=START + timedelta(days=91),
        provenance={"code_revision": "explicitly-supplied"},
    )
    manifest = json.loads(artifacts.manifest_path.read_text())

    assert manifest["provenance"]["code_revision"] == "explicitly-supplied"


def test_pipeline_report_and_manifest_content(tmp_path: Path) -> None:
    prices = write_prices(tmp_path / "prices.json", 120)
    posts = write_posts(tmp_path / "posts.jsonl", snapshot_candles(120))

    artifacts = run_forecast_pipeline(
        candles=load_candles(prices),
        posts=load_posts(posts),
        output_dir=tmp_path / "run",
        now=START + timedelta(days=121),
    )
    manifest = json.loads(artifacts.manifest_path.read_text())
    predictions = [
        line for line in artifacts.predictions_path.read_text().splitlines() if line.strip()
    ]

    assert len(predictions) == manifest["evaluation"]["predictions"]
    assert "Out-of-sample forecast metrics" in artifacts.report_path.read_text()
    assert "current sentiment outlook" in artifacts.outlook_path.read_text()
    assert "<svg" in artifacts.chart_path.read_text()


def test_pipeline_runs_without_any_posts_and_marks_sentiment_unavailable(tmp_path: Path) -> None:
    prices = write_prices(tmp_path / "prices.json", 120)

    artifacts = run_forecast_pipeline(
        candles=load_candles(prices),
        output_dir=tmp_path / "run",
        now=START + timedelta(days=121),
    )

    manifest = json.loads(artifacts.manifest_path.read_text())
    metrics = json.loads(artifacts.metrics_path.read_text())

    assert manifest["dataset"]["posts"] == 0
    assert manifest["dataset"]["rows_with_sentiment"] == 0
    assert metrics["warnings"]
    assert "scored-post sentiment" in " ".join(metrics["warnings"])
    assert "not identifiable" in " ".join(metrics["warnings"])
    assert metrics["mean_mae_by_model"]["price_only"] >= 0


def test_cli_run_command_produces_a_report_and_reports_input_errors(tmp_path: Path) -> None:
    prices = write_prices(tmp_path / "prices.json", 120)
    output = tmp_path / "cli-run"

    exit_code = main(
        [
            "run",
            "--prices",
            str(prices),
            "--out",
            str(output),
            "--now",
            (START + timedelta(days=121)).isoformat(),
        ]
    )

    assert exit_code == 0
    assert (output / "evaluation-report.md").exists()
    assert (output / "manifest.json").exists()
    assert main(["run", "--prices", str(tmp_path / "missing.json"), "--out", str(output)]) == 1


def test_hash_helper_is_stable_for_the_same_content(tmp_path: Path) -> None:
    path = tmp_path / "prices.json"
    write_prices(path, 3)
    assert sha256_file(path) == sha256_file(path)
    path.write_text("[]")
    assert sha256_file(path) != ""
