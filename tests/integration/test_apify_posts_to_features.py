"""Synthetic offline exercise from Apify-shaped records to sentiment features."""

from __future__ import annotations

import hashlib
import importlib.util
import json
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from pathlib import Path

from xsentiment import main as cli
from xsentiment.features.dataset import build_supervised_dataset
from xsentiment.features.sentiment import VaderSentimentScorer, score_posts
from xsentiment.ingestion.apify_x import normalize_apify_post
from xsentiment.ingestion.post_dataset import PostBatch, merge_post_batches, serialize_x_post
from xsentiment.pipeline.forecast_run import load_candles, load_posts, sha256_file

DEMO_SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "make_offline_demo.py"
_DEMO_SPEC = importlib.util.spec_from_file_location("offline_demo_generator", DEMO_SCRIPT)
assert _DEMO_SPEC is not None and _DEMO_SPEC.loader is not None
_DEMO_MODULE = importlib.util.module_from_spec(_DEMO_SPEC)
_DEMO_SPEC.loader.exec_module(_DEMO_MODULE)
build_price_snapshot = _DEMO_MODULE.build_price_snapshot

AS_OF = datetime(2026, 8, 1, tzinfo=UTC)
START = datetime(2026, 1, 1, tzinfo=UTC)


def _manifest(mode: str, query: str) -> dict[str, object]:
    return {
        "provider": "apify",
        "actor_id": "fixture/actor",
        "query": {"mode": mode, "sha256": hashlib.sha256(query.encode()).hexdigest()},
        "window": {"start": "2026-01-01", "end": "2026-08-01", "days": 212},
    }


def _record(post_id: str, created_at: datetime, retrieved_at: datetime, mode: str, query: str):
    record = normalize_apify_post(
        {
            "id": post_id,
            "text": "Synthetic fixture: Bitcoin sentiment is strongly optimistic.",
            "createdAt": created_at.isoformat(),
            "url": f"https://x.com/fixture/status/{post_id}",
        },
        retrieved_at=retrieved_at,
        query_mode=mode,
        query=query,
    )
    return replace(
        record,
        source_name="synthetic_test_fixture",
        warnings=("synthetic fixture; not observed X data",),
    )


def test_synthetic_apify_batches_reach_point_in_time_sentiment_features(tmp_path: Path) -> None:
    prices_path = tmp_path / "prices.json"
    prices = build_price_snapshot(
        asset="BTCUSDT",
        start=START,
        days=210,
        seed=20261101,
        generated_at=AS_OF,
    )
    prices_path.write_text(json.dumps(prices), encoding="utf-8")

    batches: list[PostBatch] = []
    queries = (("ticker", "BTC"), ("cashtag", "$BTC"), ("keyword", "Bitcoin"))
    for index, (mode, query) in enumerate(queries):
        rows = []
        if mode == "ticker":
            rows.append(
                _record(
                    "fixture-duplicate",
                    START + timedelta(hours=12),
                    START + timedelta(hours=13),
                    mode,
                    query,
                )
            )
            for day in range(10, 31):
                created = START + timedelta(days=day, hours=12)
                rows.append(
                    _record(
                        f"fixture-{day}", created, created + timedelta(minutes=5), mode, query
                    )
                )
        elif mode == "cashtag":
            rows.append(
                _record(
                    "fixture-duplicate",
                    START + timedelta(hours=12),
                    START + timedelta(hours=15),
                    mode,
                    query,
                )
            )
            late_created = START + timedelta(days=3, hours=12)
            rows.append(
                _record(
                    "fixture-late",
                    late_created,
                    START + timedelta(days=5, hours=12),
                    mode,
                    query,
                )
            )
        else:
            future_created = START + timedelta(days=5, hours=2)
            rows.append(
                _record(
                    "fixture-future",
                    future_created,
                    future_created + timedelta(minutes=5),
                    mode,
                    query,
                )
            )

        posts_path = tmp_path / f"{mode}.jsonl"
        posts_path.write_text(
            "\n".join(json.dumps(serialize_x_post(row), sort_keys=True) for row in rows) + "\n",
            encoding="utf-8",
        )
        batch_manifest = _manifest(mode, query)
        run_manifest_path = tmp_path / f"{mode}-run-manifest.json"
        run_manifest_path.write_text(json.dumps(batch_manifest), encoding="utf-8")
        batches.append(
            PostBatch(
                posts=tuple(rows),
                posts_name=posts_path.name,
                posts_sha256=sha256_file(posts_path),
                run_manifest_name=run_manifest_path.name,
                run_manifest_sha256=sha256_file(run_manifest_path),
                run_manifest=batch_manifest,
            )
        )

    merged = merge_post_batches(batches)
    posts_path = tmp_path / "merged-posts.jsonl"
    posts_path.write_text(
        "\n".join(json.dumps(serialize_x_post(post), sort_keys=True) for post in merged.posts)
        + "\n",
        encoding="utf-8",
    )
    sidecar_path = tmp_path / "merged-provenance.json"
    merged.provenance["posts_sha256"] = sha256_file(posts_path)
    sidecar_path.write_text(json.dumps(merged.provenance, sort_keys=True), encoding="utf-8")

    candles = load_candles(prices_path)
    posts = load_posts(posts_path)
    scored_posts = score_posts(posts, VaderSentimentScorer())
    rows = build_supervised_dataset(candles, scored_posts, now=AS_OF)
    row_by_cutoff = {row.cutoff: row for row in rows}
    duplicate_cutoff = START + timedelta(days=1)
    late_cutoff = START + timedelta(days=4)
    assert row_by_cutoff[duplicate_cutoff].features["post_count_24h"] == 1.0
    assert row_by_cutoff[duplicate_cutoff].features["mean_sentiment_24h"] is not None
    assert row_by_cutoff[late_cutoff].features["post_count_24h"] == 0.0
    assert merged.provenance["counts"]["duplicate_records_removed"] == 1

    out = tmp_path / "run"
    result = cli.main(
        [
            "run",
            "--prices", str(prices_path),
            "--posts", str(posts_path),
            "--posts-provenance", str(sidecar_path),
            "--out", str(out),
            "--now", AS_OF.isoformat(),
        ]
    )

    assert result == 0
    run_manifest = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
    assert run_manifest["dataset"]["posts"] == len(merged.posts)
    assert run_manifest["dataset"]["rows_with_sentiment"] > 0
    assert run_manifest["provenance"]["posts_provenance_snapshot_sha256"] == sha256_file(
        sidecar_path
    )
    assert run_manifest["provenance"]["posts_snapshot_sha256"] == sha256_file(posts_path)


def test_run_rejects_a_posts_provenance_sidecar_for_another_snapshot(tmp_path: Path) -> None:
    prices_path = tmp_path / "prices.json"
    prices = build_price_snapshot(
        asset="BTCUSDT", start=START, days=2, seed=7, generated_at=AS_OF
    )
    prices_path.write_text(json.dumps(prices), encoding="utf-8")
    posts_path = tmp_path / "posts.jsonl"
    posts_path.write_text("", encoding="utf-8")
    sidecar_path = tmp_path / "provenance.json"
    sidecar_path.write_text(
        json.dumps({"schema_version": "x-posts-merge-v1", "posts_sha256": "0" * 64}),
        encoding="utf-8",
    )

    result = cli.main(
        [
            "run", "--prices", str(prices_path), "--posts", str(posts_path),
            "--posts-provenance", str(sidecar_path), "--out", str(tmp_path / "bad-run"),
        ]
    )

    assert result == 1
    assert not (tmp_path / "bad-run").exists()
