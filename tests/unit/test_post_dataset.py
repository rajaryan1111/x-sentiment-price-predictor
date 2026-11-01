"""Offline tests for multi-query normalized X post assembly."""

from __future__ import annotations

import hashlib
import importlib.util
import json
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from xsentiment.ingestion.apify_x import normalize_apify_post
from xsentiment.ingestion.post_dataset import PostBatch, merge_post_batches

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = REPO_ROOT / "scripts" / "merge_apify_x_posts.py"
CREATED = datetime(2026, 7, 1, 10, tzinfo=UTC)
RETRIEVED = datetime(2026, 7, 1, 11, tzinfo=UTC)
TEXT = "Synthetic test fixture: Bitcoin sentiment is optimistic."


def load_merge_script():
    spec = importlib.util.spec_from_file_location("merge_apify_x_posts", SCRIPT_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def make_post(*, mode: str, query: str, retrieved_at=RETRIEVED, text=TEXT):
    return normalize_apify_post(
        {
            "id": "fixture-post-1",
            "text": text,
            "createdAt": CREATED.isoformat(),
            "url": "https://x.com/test/status/fixture-post-1",
            "author": {"id": "fixture-author"},
        },
        retrieved_at=retrieved_at,
        query_mode=mode,
        query=query,
    )


def make_batch(mode: str, query: str, posts, index: int = 0) -> PostBatch:
    query_sha = hashlib.sha256(query.encode()).hexdigest()
    return PostBatch(
        posts=tuple(posts),
        posts_name=f"{mode}.jsonl",
        posts_sha256=f"{index + 1:064x}",
        run_manifest_name=f"{mode}-manifest.json",
        run_manifest_sha256=f"{index + 11:064x}",
        run_manifest={
            "provider": "apify",
            "actor_id": "apidojo/tweet-scraper",
            "query": {"mode": mode, "sha256": query_sha},
            "window": {"start": "2026-05-05", "end": "2026-11-01", "days": 180},
        },
    )


def test_merge_deduplicates_by_id_keeps_earliest_retrieval_and_all_origins() -> None:
    ticker_post = make_post(mode="ticker", query="BTC")
    cashtag_post = make_post(
        mode="cashtag", query="$BTC", retrieved_at=RETRIEVED + timedelta(hours=1)
    )

    merged = merge_post_batches(
        [
            make_batch("ticker", "BTC", [ticker_post]),
            make_batch("cashtag", "$BTC", [cashtag_post], index=1),
        ]
    )

    assert len(merged.posts) == 1
    assert merged.posts[0].created_at == CREATED
    assert merged.posts[0].retrieved_at == RETRIEVED
    assert merged.posts[0].query_mode == "ticker"
    origins = merged.provenance["per_post_sources"][0]["sources"]
    assert [source["query_mode"] for source in origins] == ["ticker", "cashtag"]
    encoded = json.dumps(merged.provenance)
    assert TEXT not in encoded
    assert merged.provenance["counts"] == {
        "input_records": 2,
        "unique_posts": 1,
        "duplicate_records_removed": 1,
    }


@pytest.mark.parametrize(
    "field,value",
    [
        ("text", "Different synthetic text"),
        ("created_at", CREATED + timedelta(seconds=1)),
    ],
)
def test_merge_fails_closed_on_conflicting_duplicate_identity(field, value) -> None:
    first = make_post(mode="ticker", query="BTC")
    conflicting = make_post(mode="cashtag", query="$BTC")
    conflicting = replace(conflicting, **{field: value})

    with pytest.raises(ValueError, match="conflicting duplicate post ID"):
        merge_post_batches(
            [make_batch("ticker", "BTC", [first]), make_batch("cashtag", "$BTC", [conflicting], 1)]
        )


def test_merge_rejects_query_provenance_that_disagrees_with_batch_manifest() -> None:
    post = make_post(mode="ticker", query="BTC")
    batch = make_batch("ticker", "$BTC", [post])

    with pytest.raises(ValueError, match="does not match its run manifest"):
        merge_post_batches([batch])


def test_merge_rejects_non_x_records() -> None:
    post = replace(make_post(mode="ticker", query="BTC"), source_platform="other-platform")

    with pytest.raises(ValueError, match="not labeled as X"):
        merge_post_batches([make_batch("ticker", "BTC", [post])])


def test_merge_cli_writes_hash_bound_text_free_manifest(tmp_path: Path) -> None:
    script = load_merge_script()
    paths = []
    for index, (mode, query) in enumerate((("ticker", "BTC"), ("cashtag", "$BTC"))):
        posts_path = tmp_path / f"{mode}.jsonl"
        post = make_post(mode=mode, query=query, retrieved_at=RETRIEVED + timedelta(minutes=index))
        from xsentiment.ingestion.post_dataset import serialize_x_post

        posts_path.write_text(json.dumps(serialize_x_post(post)) + "\n", encoding="utf-8")
        manifest_path = tmp_path / f"{mode}-manifest.json"
        manifest_path.write_text(
            json.dumps(make_batch(mode, query, []).run_manifest), encoding="utf-8"
        )
        paths.append((posts_path, manifest_path))

    out = tmp_path / "merged.jsonl"
    sidecar = tmp_path / "merged-manifest.json"
    result = script.main(
        [
            "--posts", str(paths[0][0]), "--run-manifest", str(paths[0][1]),
            "--posts", str(paths[1][0]), "--run-manifest", str(paths[1][1]),
            "--out", str(out), "--manifest-out", str(sidecar),
        ]
    )

    assert result == 0
    merged_rows = [json.loads(line) for line in out.read_text().splitlines()]
    manifest = json.loads(sidecar.read_text())
    assert len(merged_rows) == 1
    assert manifest["posts_sha256"] == hashlib.sha256(out.read_bytes()).hexdigest()
    assert manifest["counts"]["duplicate_records_removed"] == 1
    assert TEXT not in sidecar.read_text()
