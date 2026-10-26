"""Validate the curated historical social-text dataset registry without network access."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from xsentiment.ingestion.dataset_registry import DEFAULT_REGISTRY, validate_registry


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    args = parser.parse_args()
    errors = validate_registry(args.registry)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1

    document = json.loads(args.registry.read_text(encoding="utf-8"))
    print(f"OK: validated {len(document['datasets'])} dataset records in {args.registry}")
    print("Note: structural validation does not verify URLs, licenses, downloads, or data quality.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
