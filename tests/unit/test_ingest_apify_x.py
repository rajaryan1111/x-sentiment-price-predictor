"""Offline tests for the bounded Apify ingestion script; no network is used."""

from __future__ import annotations

import asyncio
import importlib.util
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

from xsentiment.ingestion.contracts import XPostRecord

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = REPO_ROOT / "scripts" / "ingest_apify_x.py"


def load_script():
    spec = importlib.util.spec_from_file_location("ingest_apify_x", SCRIPT_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def actor_input() -> dict[str, object]:
    return {
        "searchTerms": [
            "BTC since:2026-05-05 until:2026-11-01 lang:en -filter:retweets",
        ],
        "tweetLanguage": "en",
        "maxItems": 10,
    }


def posts() -> list[XPostRecord]:
    start = datetime(2026, 10, 20, 12, tzinfo=UTC)
    return [
        XPostRecord(
            post_id="p1",
            created_at=start,
            retrieved_at=start + timedelta(hours=1),
            text="synthetic post one",
            likes=5,
            reposts=2,
            views=100,
            author_followers=1_000,
            query_mode="ticker",
            query="BTC",
        ),
        XPostRecord(
            post_id="p2",
            created_at=start + timedelta(days=1),
            retrieved_at=start + timedelta(days=1, hours=1),
            text="synthetic post two",
            likes=None,
            reposts=0,
            query_mode="ticker",
            query="BTC",
        ),
    ]


class FakeAdapter:
    captured: dict[str, object] = {}

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return None

    async def run_and_fetch(self, actor_input, **kwargs):
        type(self).captured = kwargs
        return posts()


def test_manifest_is_sanitized_and_records_counts(tmp_path: Path) -> None:
    script = load_script()
    preflight = script.validate_actor_input(actor_input(), required_modes=("ticker",))
    manifest = script.build_manifest(
        posts(),
        preflight=preflight,
        query_mode="ticker",
        query="BTC",
        actor_id="apidojo/tweet-scraper",
        max_items=10,
        max_total_charge_usd=0.25,
        timeout_seconds=300,
        generated_at=datetime(2026, 11, 1, tzinfo=UTC),
    )
    encoded = json.dumps(manifest)
    assert manifest["counts"]["returned_records"] == 2
    assert manifest["counts"]["unique_post_ids"] == 2
    assert manifest["counts"]["records_with_likes"] == 1
    assert manifest["counts"]["records_with_author_followers"] == 1
    assert manifest["coverage"]["days_with_posts"] == 2
    assert manifest["query"]["raw_query_stored"] is False
    assert "synthetic post" not in encoded
    assert manifest["sanitization"]["post_text_in_manifest"] is False


def test_run_refuses_without_confirmation_and_constructs_no_adapter(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    script = load_script()

    class ExplodingAdapter:
        def __init__(self, *args, **kwargs):
            raise AssertionError("unconfirmed ingest must not construct the adapter")

    monkeypatch.setattr(script, "ApifyXAdapter", ExplodingAdapter)
    input_path = tmp_path / "input.json"
    input_path.write_text(json.dumps(actor_input()), encoding="utf-8")
    args = script.parse_args(
        [
            "--input-json",
            str(input_path),
            "--query-mode",
            "ticker",
            "--query",
            "BTC",
            "--posts-out",
            str(tmp_path / "posts.jsonl"),
            "--manifest-out",
            str(tmp_path / "manifest.json"),
        ]
    )

    assert asyncio.run(script.run(args)) == 2
    assert "ingest refused" in capsys.readouterr().err
    assert not (tmp_path / "posts.jsonl").exists()


def test_run_writes_jsonl_and_sanitized_manifest(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    script = load_script()
    monkeypatch.setattr(script, "ApifyXAdapter", FakeAdapter)
    monkeypatch.setattr(script, "_credentials_configured", lambda: True)
    input_path = tmp_path / "input.json"
    input_path.write_text(json.dumps(actor_input()), encoding="utf-8")
    posts_path = tmp_path / "posts.jsonl"
    manifest_path = tmp_path / "manifest.json"
    args = script.parse_args(
        [
            "--input-json",
            str(input_path),
            "--query-mode",
            "ticker",
            "--query",
            "BTC",
            "--posts-out",
            str(posts_path),
            "--manifest-out",
            str(manifest_path),
            "--confirm-paid-run",
            "--max-items",
            "10",
            "--max-total-charge-usd",
            "0.25",
            "--timeout-seconds",
            "300",
        ]
    )

    assert asyncio.run(script.run(args)) == 0
    lines = [json.loads(line) for line in posts_path.read_text().splitlines() if line.strip()]
    assert [line["post_id"] for line in lines] == ["p1", "p2"]
    assert lines[0]["query_mode"] == "ticker"
    assert "synthetic post one" in lines[0]["text"]

    manifest_text = manifest_path.read_text()
    manifest = json.loads(manifest_text)
    assert manifest["counts"]["returned_records"] == 2
    assert manifest["query"]["mode"] == "ticker"
    assert manifest["caps"]["max_items"] == 10
    assert "synthetic post" not in manifest_text
    assert FakeAdapter.captured["query_mode"] == "ticker"
    assert FakeAdapter.captured["max_items"] == 10
    assert "wrote 2 normalized posts" in capsys.readouterr().out


def test_run_refuses_without_credentials(tmp_path: Path, monkeypatch, capsys) -> None:
    script = load_script()
    monkeypatch.setattr(script, "_credentials_configured", lambda: False)
    input_path = tmp_path / "input.json"
    input_path.write_text(json.dumps(actor_input()), encoding="utf-8")
    args = script.parse_args(
        [
            "--input-json",
            str(input_path),
            "--query-mode",
            "ticker",
            "--query",
            "BTC",
            "--posts-out",
            str(tmp_path / "posts.jsonl"),
            "--manifest-out",
            str(tmp_path / "manifest.json"),
            "--confirm-paid-run",
        ]
    )

    assert asyncio.run(script.run(args)) == 2
    assert "not configured" in capsys.readouterr().err


def test_run_refuses_a_query_mode_missing_from_the_input(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    script = load_script()
    monkeypatch.setattr(script, "_credentials_configured", lambda: True)
    input_path = tmp_path / "input.json"
    input_path.write_text(
        json.dumps(
            {
                "searchTerms": [
                    "BTC since:2026-05-05 until:2026-11-01",
                ]
            }
        ),
        encoding="utf-8",
    )
    args = script.parse_args(
        [
            "--input-json",
            str(input_path),
            "--query-mode",
            "cashtag",
            "--query",
            "$BTC",
            "--posts-out",
            str(tmp_path / "posts.jsonl"),
            "--manifest-out",
            str(tmp_path / "manifest.json"),
            "--confirm-paid-run",
        ]
    )

    assert asyncio.run(script.run(args)) == 2
    assert "missing: cashtag" in capsys.readouterr().err
