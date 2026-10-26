"""Offline tests for the historical dataset registry."""
import json
from pathlib import Path

from scripts.validate_dataset_registry import DEFAULT_REGISTRY, validate_registry


def test_curated_registry_is_structurally_valid() -> None:
    assert validate_registry(DEFAULT_REGISTRY) == []


def test_registry_contains_all_pdf_entries() -> None:
    document = json.loads(DEFAULT_REGISTRY.read_text(encoding="utf-8"))
    assert len(document["datasets"]) == 11
    assert len({item["id"] for item in document["datasets"]}) == 11


def test_stocktwits_is_not_mislabeled_as_x() -> None:
    document = json.loads(DEFAULT_REGISTRY.read_text(encoding="utf-8"))
    stocktwits = next(item for item in document["datasets"] if item["id"] == "stocktwits-nyu-2008-2022")
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
