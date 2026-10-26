"""Validate the curated historical social-text dataset registry offline."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

DEFAULT_REGISTRY = (
    Path(__file__).resolve().parents[3]
    / "data"
    / "registry"
    / "historical_twitter_x_datasets.json"
)
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


def validate_registry(path: Path = DEFAULT_REGISTRY) -> list[str]:
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
        for field_name in ("date_start", "date_end"):
            value = dataset[field_name]
            if value is None:
                joined = " ".join(dataset["limitations"]).lower()
                if "coverage" not in joined and "cutoff" not in joined:
                    errors.append(
                        f"{prefix}.{field_name} is null but the limitations do not warn that "
                        "coverage is unverified"
                    )
            elif not isinstance(value, str) or not value.strip():
                errors.append(
                    f"{prefix}.{field_name} must be a date string, or null accompanied by a "
                    "coverage limitation"
                )

        if dataset["text_availability"] == "ids-only" and not any(
            word in " ".join(dataset["limitations"]).lower()
            for word in ("id", "hydration")
        ):
            errors.append(f"{prefix} is ID-only but lacks a hydration limitation.")

    if len(seen_ids) != len(datasets):
        errors.append("Dataset IDs must all be present and unique.")
    return errors
