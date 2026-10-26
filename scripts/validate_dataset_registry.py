"""Validate the curated historical social-text dataset registry without network access."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REGISTRY = ROOT / "data" / "registry" / "historical_twitter_x_datasets.json"
REQUIRED_FIELDS = {
    "id",
    "name",
    "platform",
    "topic",
    "date_start",
    "date_end",
    "text_availability",
    "license_access",
    "source_url",
    "source_verified_date",
    "limitations",
    "recommended_for_initial_run",
}


def validate_registry(path: Path) -> list[str]:
    """Return validation errors; an empty list means the registry is structurally valid."""
    try:
        document: Any = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"Cannot read valid JSON from {path}: {exc}"]

    errors: list[str] = []
    if not isinstance(document, dict):
        return ["Registry root must be a JSON object."]

    datasets = document.get("datasets")
    if not isinstance(datasets, list) or not datasets:
        return ["'datasets' must be a non-empty list."]

    seen_ids: set[str] = set()
    seen_urls: set[str] = set()
    for index, dataset in enumerate(datasets):
        prefix = f"datasets[{index}]"
        if not isinstance(dataset, dict):
            errors.append(f"{prefix} must be an object.")
            continue

        missing = sorted(REQUIRED_FIELDS - dataset.keys())
        if missing:
            errors.append(f"{prefix} is missing fields: {', '.join(missing)}")
            continue

        dataset_id = dataset["id"]
        if not isinstance(dataset_id, str) or not dataset_id.strip():
            errors.append(f"{prefix}.id must be a non-empty string.")
        elif dataset_id in seen_ids:
            errors.append(f"Duplicate dataset id: {dataset_id}")
        else:
            seen_ids.add(dataset_id)

        url = dataset["source_url"]
        if not isinstance(url, str) or not url.startswith("https://"):
            errors.append(f"{prefix}.source_url must be an HTTPS URL.")
        elif url in seen_urls:
            errors.append(f"Duplicate source URL: {url}")
        else:
            seen_urls.add(url)

        if not isinstance(dataset["limitations"], list) or not all(
            isinstance(item, str) and item.strip() for item in dataset["limitations"]
        ):
            errors.append(f"{prefix}.limitations must be a list of non-empty strings.")
        if not isinstance(dataset["recommended_for_initial_run"], bool):
            errors.append(f"{prefix}.recommended_for_initial_run must be boolean.")
        if dataset["text_availability"] == "ids-only" and not any(
            word in " ".join(dataset["limitations"]).lower()
            for word in ("id", "hydration")
        ):
            errors.append(f"{prefix} is ID-only but lacks a hydration limitation.")

    if len(seen_ids) != len(datasets):
        errors.append("Dataset IDs must all be present and unique.")
    return errors


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
