"""Offline tests for the Apify Actor input preflight; no network is used."""

from __future__ import annotations

import asyncio
import importlib.util
import json
from datetime import date
from pathlib import Path

import pytest

from xsentiment.ingestion.apify_preflight import (
    classify_query_modes,
    load_actor_input,
    validate_actor_input,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = REPO_ROOT / "scripts" / "smoke_test_apify_x.py"
EXAMPLE_PATH = REPO_ROOT / "config" / "apify_actor_input.example.json"


def valid_input() -> dict[str, object]:
    return {
        "searchTerms": [
            "BTC since:2026-05-05 until:2026-11-01 lang:en -filter:retweets",
            "$BTC since:2026-05-05 until:2026-11-01 lang:en -filter:retweets",
            "Bitcoin since:2026-05-05 until:2026-11-01 lang:en -filter:retweets",
        ],
        "tweetLanguage": "en",
        "sort": "Latest",
        "maxItems": 500,
    }


def load_script():
    spec = importlib.util.spec_from_file_location("smoke_test_apify_x", SCRIPT_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_example_input_is_valid_and_covers_all_three_query_modes() -> None:
    payload = load_actor_input(EXAMPLE_PATH)
    report = validate_actor_input(payload, today=date(2026, 11, 1))

    assert report.query_modes == ("ticker", "cashtag", "keyword")
    assert report.window_start == date(2026, 5, 5)
    assert report.window_end == date(2026, 11, 1)
    assert report.window_days == 180
    assert report.max_items == 500
    assert report.warnings == ()


def test_missing_cashtag_query_fails_closed() -> None:
    payload = valid_input()
    payload["searchTerms"] = [
        "BTC since:2026-05-05 until:2026-11-01",
        "Bitcoin since:2026-05-05 until:2026-11-01",
    ]
    with pytest.raises(ValueError, match="missing: cashtag"):
        validate_actor_input(payload)


def test_missing_or_reversed_date_bounds_fail_closed() -> None:
    payload = valid_input()
    payload["searchTerms"] = [
        "BTC lang:en",
        "$BTC lang:en",
        "Bitcoin lang:en",
    ]
    with pytest.raises(ValueError, match="since:YYYY-MM-DD"):
        validate_actor_input(payload)

    payload = valid_input()
    payload["searchTerms"] = [
        "BTC since:2026-11-01 until:2026-05-05",
        "$BTC since:2026-11-01 until:2026-05-05",
        "Bitcoin since:2026-11-01 until:2026-05-05",
    ]
    with pytest.raises(ValueError, match="since must be earlier than until"):
        validate_actor_input(payload)


def test_window_longer_than_180_days_fails_closed() -> None:
    payload = valid_input()
    payload["searchTerms"] = [
        "BTC since:2026-01-01 until:2026-11-01",
        "$BTC since:2026-01-01 until:2026-11-01",
        "Bitcoin since:2026-01-01 until:2026-11-01",
    ]
    with pytest.raises(ValueError, match="maximum is 180"):
        validate_actor_input(payload)


def test_credential_shaped_keys_are_rejected_without_reading_them() -> None:
    payload = valid_input()
    payload["apiToken"] = "must-not-be-accepted"
    with pytest.raises(ValueError, match="credential-shaped key"):
        validate_actor_input(payload)

    nested = valid_input()
    nested["filters"] = {"authorization": "Bearer must-not-be-accepted"}
    with pytest.raises(ValueError, match="credential-shaped key"):
        validate_actor_input(nested)


def test_max_items_must_be_a_bounded_integer() -> None:
    payload = valid_input()
    payload["maxItems"] = True
    with pytest.raises(ValueError, match="maxItems must be an integer"):
        validate_actor_input(payload)

    payload["maxItems"] = 10_000
    with pytest.raises(ValueError, match="within 1..1000"):
        validate_actor_input(payload)


def test_future_window_end_is_warned_about_not_silently_accepted() -> None:
    report = validate_actor_input(valid_input(), today=date(2026, 10, 1))
    assert any("ends after today" in warning for warning in report.warnings)


def test_classify_query_modes_does_not_treat_cashtag_as_ticker() -> None:
    assert classify_query_modes(["$BTC"]) == ("cashtag",)
    assert classify_query_modes(["BTC"]) == ("ticker",)
    assert classify_query_modes(["Bitcoin"]) == ("keyword",)


def test_validate_only_makes_no_network_call_or_paid_run(
    tmp_path: Path, capsys, monkeypatch
) -> None:
    script = load_script()

    class ExplodingAdapter:
        def __init__(self, *args, **kwargs):
            raise AssertionError("validate-only must not construct the Apify adapter")

    monkeypatch.setattr(script, "ApifyXAdapter", ExplodingAdapter)
    path = tmp_path / "actor-input.json"
    path.write_text(json.dumps(valid_input()), encoding="utf-8")

    args = script.parse_args(["--input-json", str(path), "--validate-only"])
    assert asyncio.run(script.run(args)) == 0

    output = json.loads(capsys.readouterr().out)
    assert output["valid"] is True
    assert output["network_call_made"] is False
    assert output["paid_run_launched"] is False
    assert output["query_modes"] == ["ticker", "cashtag", "keyword"]
    assert set(output["credentials_configured"]) == {"APIFY_API_TOKEN", "APIFY_ACTOR_ID"}
    assert all(isinstance(value, bool) for value in output["credentials_configured"].values())


def test_invalid_input_exits_before_constructing_the_adapter(
    tmp_path: Path, capsys, monkeypatch
) -> None:
    script = load_script()

    class ExplodingAdapter:
        def __init__(self, *args, **kwargs):
            raise AssertionError("invalid input must not reach the Apify adapter")

    monkeypatch.setattr(script, "ApifyXAdapter", ExplodingAdapter)
    path = tmp_path / "bad-input.json"
    path.write_text(json.dumps({"searchTerms": ["BTC"]}), encoding="utf-8")

    args = script.parse_args(["--input-json", str(path), "--validate-only"])
    assert asyncio.run(script.run(args)) == 2
    assert "ERROR:" in capsys.readouterr().out
