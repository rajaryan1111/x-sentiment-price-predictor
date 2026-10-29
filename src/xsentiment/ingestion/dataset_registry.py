"""Validate the curated historical social-text dataset registry offline."""
from __future__ import annotations

import json
import re
from datetime import date
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
ALLOWED_PLATFORMS = {"X/Twitter", "StockTwits"}
ALLOWED_TEXT_AVAILABILITY = {
    "full-post-text-reported",
    "full-tweet-text-reported",
    "cleaned-english-tweets-reported",
    "cleaned-tweets-reported",
    "tweet-text-reported",
    "tweet-text-and-metadata-reported",
    "sentiment-labelled-tweets-reported",
    "ids-only",
}
VERIFICATION_STATUSES = {"not-reverified", "partially-reverified", "reverified"}
_DATE_RE = re.compile(r"^\d{4}(?:-\d{2}(?:-\d{2})?)?$")


def _date_key(value: str) -> tuple[int, int, int]:
    parts = [int(part) for part in value.split("-")]
    return (parts[0], parts[1] if len(parts) > 1 else 0, parts[2] if len(parts) > 2 else 0)


def validate_registry(path: Path = DEFAULT_REGISTRY) -> list[str]:
    """Return validation errors; an empty list means the registry is structurally valid."""
    try:
        document: Any = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"Cannot read valid JSON from {path}: {exc}"]

    errors: list[str] = []
    if not isinstance(document, dict):
        return ["Registry root must be a JSON object."]

    verification = document.get("independent_verification")
    if not isinstance(verification, dict):
        errors.append(
            "'independent_verification' must be an object recording registry-wide "
            "review status."
        )
    else:
        status = verification.get("status")
        if status not in VERIFICATION_STATUSES:
            errors.append(
                "'independent_verification.status' must be one of: "
                + ", ".join(sorted(VERIFICATION_STATUSES))
            )
        checked = verification.get("checked_date")
        if not isinstance(checked, str):
            errors.append("'independent_verification.checked_date' must be an ISO date.")
        else:
            try:
                date.fromisoformat(checked)
            except ValueError:
                errors.append("'independent_verification.checked_date' must be an ISO date.")

    datasets = document.get("datasets")
    if not isinstance(datasets, list) or not datasets:
        errors.append("'datasets' must be a non-empty list.")
        return errors

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

        for field_name in ("name", "topic", "format", "license_access", "relevance"):
            value = dataset[field_name]
            if not isinstance(value, str) or not value.strip():
                errors.append(f"{prefix}.{field_name} must be a non-empty string.")
        if dataset["platform"] not in ALLOWED_PLATFORMS:
            errors.append(
                f"{prefix}.platform must be one of: {', '.join(sorted(ALLOWED_PLATFORMS))}"
            )
        if dataset["text_availability"] not in ALLOWED_TEXT_AVAILABILITY:
            errors.append(
                f"{prefix}.text_availability must be one of: "
                f"{', '.join(sorted(ALLOWED_TEXT_AVAILABILITY))}"
            )
        verified_date = dataset["source_verified_date"]
        if not isinstance(verified_date, str):
            errors.append(f"{prefix}.source_verified_date must be an ISO date.")
        else:
            try:
                date.fromisoformat(verified_date)
            except ValueError:
                errors.append(f"{prefix}.source_verified_date must be an ISO date.")

        if not isinstance(dataset["limitations"], list) or not all(
            isinstance(item, str) and item.strip() for item in dataset["limitations"]
        ):
            errors.append(f"{prefix}.limitations must be a list of non-empty strings.")
        if not isinstance(dataset["recommended_for_initial_run"], bool):
            errors.append(f"{prefix}.recommended_for_initial_run must be boolean.")
        elif dataset["recommended_for_initial_run"] and (
            dataset["platform"] != "X/Twitter"
            or dataset["text_availability"] == "ids-only"
        ):
            errors.append(
                f"{prefix} cannot be recommended without X/Twitter post text."
            )

        date_values: dict[str, tuple[int, int, int]] = {}
        for field_name in ("date_start", "date_end"):
            value = dataset[field_name]
            if value is None:
                joined = " ".join(dataset["limitations"]).lower()
                if "coverage" not in joined and "cutoff" not in joined:
                    errors.append(
                        f"{prefix}.{field_name} is null but the limitations do not warn that "
                        "coverage is unverified"
                    )
            elif not isinstance(value, str) or not _DATE_RE.fullmatch(value):
                errors.append(
                    f"{prefix}.{field_name} must be YYYY, YYYY-MM or YYYY-MM-DD, or null "
                    "accompanied by a coverage limitation"
                )
            else:
                date_values[field_name] = _date_key(value)
        if len(date_values) == 2 and date_values["date_start"] > date_values["date_end"]:
            errors.append(f"{prefix}.date_start must not be later than date_end.")

        records = dataset.get("approximate_records")
        if records is not None and (
            isinstance(records, bool) or not isinstance(records, int) or records <= 0
        ):
            errors.append(f"{prefix}.approximate_records must be a positive integer or null.")

        if dataset["text_availability"] == "ids-only" and not any(
            word in " ".join(dataset["limitations"]).lower()
            for word in ("id", "hydration")
        ):
            errors.append(f"{prefix} is ID-only but lacks a hydration limitation.")

    if len(seen_ids) != len(datasets):
        errors.append("Dataset IDs must all be present and unique.")
    return errors
