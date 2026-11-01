"""Offline tests for the historical dataset registry."""
import json
from pathlib import Path

from xsentiment.ingestion.dataset_registry import DEFAULT_REGISTRY, validate_registry


def test_curated_registry_is_structurally_valid() -> None:
    assert validate_registry() == []


def test_registry_contains_all_pdf_entries() -> None:
    document = json.loads(DEFAULT_REGISTRY.read_text(encoding="utf-8"))
    assert len(document["datasets"]) == 12
    assert len({item["id"] for item in document["datasets"]}) == 12


def test_stocktwits_is_not_mislabeled_as_x() -> None:
    document = json.loads(DEFAULT_REGISTRY.read_text(encoding="utf-8"))
    stocktwits = next(
        item for item in document["datasets"] if item["id"] == "stocktwits-nyu-2008-2022"
    )
    assert stocktwits["platform"] == "StockTwits"
    assert stocktwits["recommended_for_initial_run"] is False


def test_id_only_sources_are_explicitly_marked() -> None:
    document = json.loads(DEFAULT_REGISTRY.read_text(encoding="utf-8"))
    id_only = [item for item in document["datasets"] if item["text_availability"] == "ids-only"]
    assert len(id_only) == 3
    assert all(item["limitations"] for item in id_only)


def test_sentiment140_license_is_not_assumed() -> None:
    document = json.loads(DEFAULT_REGISTRY.read_text(encoding="utf-8"))
    dataset = next(item for item in document["datasets"] if item["id"] == "sentiment140")
    assert dataset["license_identifier"] is None
    assert "Other" in dataset["license_access"]


def test_validator_reports_duplicate_ids(tmp_path: Path) -> None:
    document = json.loads(DEFAULT_REGISTRY.read_text(encoding="utf-8"))
    document["datasets"][1]["id"] = document["datasets"][0]["id"]
    registry_path = tmp_path / "registry.json"
    registry_path.write_text(json.dumps(document), encoding="utf-8")
    assert any("Duplicate dataset id" in error for error in validate_registry(registry_path))


def test_rolling_source_without_coverage_end_requires_a_limitation(tmp_path: Path) -> None:
    document = json.loads(DEFAULT_REGISTRY.read_text(encoding="utf-8"))
    dataset = next(
        item for item in document["datasets"] if item["id"] == "bitcoin-tweets-2021-onward"
    )
    assert dataset["date_end"] is None
    dataset["limitations"] = ["Count from the provider card."]
    registry_path = tmp_path / "registry.json"
    registry_path.write_text(json.dumps(document), encoding="utf-8")

    errors = validate_registry(registry_path)

    assert any("coverage is unverified" in error for error in errors)


def test_registry_records_independent_verification_state() -> None:
    document = json.loads(DEFAULT_REGISTRY.read_text(encoding="utf-8"))
    verification = document["independent_verification"]
    assert verification["status"] == "partially-reverified"
    assert verification["checked_date"] == "2026-10-29"
    assert "Hugging Face" in verification["scope"]
    assert "row-level coverage" in verification["scope"]


def test_validator_rejects_unknown_verification_and_recommended_id_only_source(
    tmp_path: Path,
) -> None:
    document = json.loads(DEFAULT_REGISTRY.read_text(encoding="utf-8"))
    document["independent_verification"]["status"] = "assumed"
    document["datasets"][0]["recommended_for_initial_run"] = True
    registry_path = tmp_path / "registry.json"
    registry_path.write_text(json.dumps(document), encoding="utf-8")

    errors = validate_registry(registry_path)

    assert any("independent_verification.status" in error for error in errors)
    assert any("cannot be recommended" in error for error in errors)


def test_validator_rejects_invalid_dates_and_date_order(tmp_path: Path) -> None:
    document = json.loads(DEFAULT_REGISTRY.read_text(encoding="utf-8"))
    dataset = next(
        item for item in document["datasets"] if item["id"] == "top-companies-tweets-2015-2020"
    )
    dataset["date_start"] = "2021"
    dataset["date_end"] = "2020"
    dataset["source_verified_date"] = "21-10-2026"
    registry_path = tmp_path / "registry.json"
    registry_path.write_text(json.dumps(document), encoding="utf-8")

    errors = validate_registry(registry_path)

    assert any("date_start must not be later" in error for error in errors)
    assert any("source_verified_date must be an ISO date" in error for error in errors)


def test_source_pdf_count_mismatch_is_flagged() -> None:
    document = json.loads(DEFAULT_REGISTRY.read_text(encoding="utf-8"))
    dataset = next(item for item in document["datasets"] if item["id"] == "crypto-stock-tweets-hf")
    assert dataset["approximate_records"] == 8_020_000
    assert any("conflicts with its component counts" in item for item in dataset["limitations"])
