"""Offline merge of normalized Apify X JSONL batches; makes no network requests."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from xsentiment.ingestion.post_dataset import (
    PostBatch,
    merge_post_batches,
    serialize_x_post,
)
from xsentiment.pipeline.forecast_run import load_posts, sha256_file


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--posts", action="append", type=Path, required=True)
    parser.add_argument("--run-manifest", action="append", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True, help="merged normalized posts JSONL")
    parser.add_argument(
        "--manifest-out", type=Path, required=True, help="text-free provenance sidecar JSON"
    )
    args = parser.parse_args(argv)
    if len(args.posts) != len(args.run_manifest):
        parser.error("provide one --run-manifest for each --posts input, in the same order")
    for path in (*args.posts, *args.run_manifest):
        if not path.is_file():
            parser.error(f"input file not found: {path}")
    return args


def _load_run_manifest(path: Path) -> dict[str, Any]:
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"run manifest is invalid JSON: {path.name}") from exc
    if not isinstance(manifest, dict):
        raise ValueError(f"run manifest must be a JSON object: {path.name}")
    return manifest


def merge_files(args: argparse.Namespace) -> tuple[int, int]:
    batches: list[PostBatch] = []
    for posts_path, manifest_path in zip(args.posts, args.run_manifest, strict=True):
        batches.append(
            PostBatch(
                posts=tuple(load_posts(posts_path)),
                posts_name=posts_path.name,
                posts_sha256=sha256_file(posts_path),
                run_manifest_name=manifest_path.name,
                run_manifest_sha256=sha256_file(manifest_path),
                run_manifest=_load_run_manifest(manifest_path),
            )
        )

    merged = merge_post_batches(batches)
    lines = [json.dumps(serialize_x_post(post), sort_keys=True) for post in merged.posts]
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
    merged.provenance["posts_sha256"] = sha256_file(args.out)
    args.manifest_out.parent.mkdir(parents=True, exist_ok=True)
    args.manifest_out.write_text(
        json.dumps(merged.provenance, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return sum(len(batch.posts) for batch in batches), len(merged.posts)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        input_count, unique_count = merge_files(args)
    except (OSError, ValueError, TypeError) as exc:
        print(f"merge failed: {exc}", file=sys.stderr)
        return 1
    print(
        f"wrote {unique_count} unique posts from {input_count} input records; "
        "post text remains only in the posts JSONL"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
