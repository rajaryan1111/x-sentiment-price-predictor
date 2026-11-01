"""Deterministic, provenance-preserving assembly of normalized X post batches."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from typing import Any

from xsentiment.ingestion.contracts import XPostRecord

MERGED_POSTS_SCHEMA = "x-posts-merge-v1"


@dataclass(frozen=True, slots=True)
class PostBatch:
    """One normalized posts snapshot and its sanitized ingestion manifest."""

    posts: tuple[XPostRecord, ...]
    posts_name: str
    posts_sha256: str
    run_manifest_name: str
    run_manifest_sha256: str
    run_manifest: dict[str, Any]


@dataclass(frozen=True, slots=True)
class MergedPostDataset:
    """Unique normalized posts plus a text-free query provenance sidecar."""

    posts: tuple[XPostRecord, ...]
    provenance: dict[str, Any]


def serialize_x_post(post: XPostRecord) -> dict[str, Any]:
    """Serialize the stable normalized record contract to JSON-compatible values."""
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


def _hash_query(query: str | None) -> str | None:
    if query is None:
        return None
    return hashlib.sha256(query.encode("utf-8")).hexdigest()


def _stable_record_key(post: XPostRecord) -> str:
    """Tie-break duplicate snapshots without depending on input file ordering."""
    return json.dumps(serialize_x_post(post), sort_keys=True, separators=(",", ":"))


def _validate_batch(batch: PostBatch) -> tuple[str, str]:
    manifest = batch.run_manifest
    if manifest.get("provider") != "apify":
        raise ValueError("run manifest provider must be 'apify'")
    query = manifest.get("query")
    if not isinstance(query, dict):
        raise ValueError("run manifest is missing query provenance")
    mode = query.get("mode")
    query_sha256 = query.get("sha256")
    if mode not in {"ticker", "cashtag", "keyword"}:
        raise ValueError("run manifest has an unsupported query mode")
    if not isinstance(query_sha256, str) or len(query_sha256) != 64:
        raise ValueError("run manifest has an invalid query hash")
    for post in batch.posts:
        if post.source_platform != "x":
            raise ValueError("post batch contains a record that is not labeled as X")
        if post.query_mode != mode or _hash_query(post.query) != query_sha256:
            raise ValueError("post query provenance does not match its run manifest")
    return mode, query_sha256


def merge_post_batches(batches: tuple[PostBatch, ...] | list[PostBatch]) -> MergedPostDataset:
    """Merge batches, failing on identity conflicts and retaining first observation.

    A duplicate is compatible when its immutable post ID, event time, text and
    platform agree. Mutable engagement values are taken from the earliest
    deterministic snapshot; every query origin is preserved in the sidecar.
    """
    if not batches:
        raise ValueError("at least one post batch is required")

    records: dict[str, list[tuple[int, XPostRecord]]] = {}
    sources: list[dict[str, Any]] = []
    for batch_index, batch in enumerate(batches):
        mode, query_sha256 = _validate_batch(batch)
        source_manifest = batch.run_manifest
        sources.append(
            {
                "batch_index": batch_index,
                "posts_file": batch.posts_name,
                "posts_sha256": batch.posts_sha256,
                "run_manifest_file": batch.run_manifest_name,
                "run_manifest_sha256": batch.run_manifest_sha256,
                "actor_id": source_manifest.get("actor_id"),
                "query_mode": mode,
                "query_sha256": query_sha256,
                "window": source_manifest.get("window"),
            }
        )
        for post in batch.posts:
            records.setdefault(post.post_id, []).append((batch_index, post))

    merged: list[XPostRecord] = []
    per_post_sources: list[dict[str, Any]] = []
    for post_id in sorted(records):
        candidates = records[post_id]
        canonical = candidates[0][1]
        for _, candidate in candidates[1:]:
            if (
                candidate.created_at != canonical.created_at
                or candidate.text != canonical.text
                or candidate.source_platform != canonical.source_platform
            ):
                raise ValueError(
                    "conflicting duplicate post ID has different event time, text, or platform"
                )
        ordered = sorted(
            candidates,
            key=lambda pair: (pair[1].retrieved_at, _stable_record_key(pair[1])),
        )
        earliest = ordered[0][1]
        earliest_retrieval = min(post.retrieved_at for _, post in candidates)
        merged.append(replace(earliest, retrieved_at=earliest_retrieval))

        matched: set[tuple[int, str | None]] = set()
        origins: list[dict[str, Any]] = []
        for batch_index, post in candidates:
            origin_key = (batch_index, post.source_record_hash)
            if origin_key in matched:
                continue
            matched.add(origin_key)
            batch_source = sources[batch_index]
            origins.append(
                {
                    "batch_index": batch_index,
                    "query_mode": batch_source["query_mode"],
                    "query_sha256": batch_source["query_sha256"],
                    "source_record_hash": post.source_record_hash,
                }
            )
        per_post_sources.append({"post_id": post_id, "sources": origins})

    merged.sort(key=lambda post: (post.created_at, post.post_id))
    total_input = sum(len(batch.posts) for batch in batches)
    return MergedPostDataset(
        posts=tuple(merged),
        provenance={
            "schema_version": MERGED_POSTS_SCHEMA,
            "generated_at": datetime.now(UTC).isoformat(),
            "input_batches": sources,
            "counts": {
                "input_records": total_input,
                "unique_posts": len(merged),
                "duplicate_records_removed": total_input - len(merged),
            },
            "per_post_sources": per_post_sources,
            "post_text_in_manifest": False,
            "credentials_in_manifest": False,
        },
    )
