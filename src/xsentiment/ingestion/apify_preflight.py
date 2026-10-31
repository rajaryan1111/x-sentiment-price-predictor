"""Offline preflight validation for an Apify X Actor input file.

The validator never constructs an HTTP client, never reads a token value, and
never launches a run. It checks the local JSON against the project's documented
contract: three query modes (ticker, cashtag, keyword), an explicit since/until
window of at most 180 days, a bounded item count, and no credential-shaped keys.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

_DATE_TOKEN = re.compile(r"\b(since|until):(\d{4}-\d{2}-\d{2})\b")
_FORBIDDEN_KEY_PARTS = (
    "token",
    "api_key",
    "apikey",
    "authorization",
    "cookie",
    "password",
    "secret",
)
_MAX_WINDOW_DAYS = 180
_MAX_ITEMS_CEILING = 1000


@dataclass(frozen=True, slots=True)
class PreflightReport:
    """Sanitized facts about a locally validated Actor input file."""

    query_modes: tuple[str, ...]
    window_start: date
    window_end: date
    window_days: int
    max_items: int | None
    warnings: tuple[str, ...]


def load_actor_input(path: str | Path) -> dict[str, Any]:
    """Read one Actor input JSON object; fail closed with a stable message."""
    try:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
    except OSError as exc:
        raise ValueError(f"could not read Actor input: {exc.__class__.__name__}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"Actor input is not valid JSON: {exc.msg}") from exc
    if not isinstance(payload, dict):
        raise ValueError("Actor input JSON root must be an object")
    return payload


def classify_query_modes(terms: list[str]) -> tuple[str, ...]:
    """Return the documented query modes present in the search terms."""
    joined = " ".join(terms).lower()
    modes: list[str] = []
    if re.search(r"(?<!\$)\bbtc\b", joined) or "btc-usd" in joined:
        modes.append("ticker")
    if "$btc" in joined:
        modes.append("cashtag")
    if "bitcoin" in joined:
        modes.append("keyword")
    return tuple(modes)


def validate_actor_input(
    actor_input: dict[str, Any],
    *,
    today: date | None = None,
    max_window_days: int = _MAX_WINDOW_DAYS,
) -> PreflightReport:
    """Validate the local contract without any network or credential access."""
    _reject_credential_keys(actor_input)
    terms = actor_input.get("searchTerms")
    if not isinstance(terms, list) or not terms:
        raise ValueError("Actor input must contain a non-empty searchTerms list")
    normalized: list[str] = []
    for index, term in enumerate(terms, start=1):
        if not isinstance(term, str) or not term.strip():
            raise ValueError(f"searchTerms[{index}] must be a non-empty string")
        normalized.append(term.strip())

    modes = classify_query_modes(normalized)
    missing = [mode for mode in ("ticker", "cashtag", "keyword") if mode not in modes]
    if missing:
        raise ValueError(
            "searchTerms must cover ticker, cashtag and keyword queries; missing: "
            + ", ".join(missing)
        )

    windows: list[tuple[date, date]] = []
    for index, term in enumerate(normalized, start=1):
        parsed = _DATE_TOKEN.findall(term)
        if len(parsed) != 2 or {name for name, _ in parsed} != {"since", "until"}:
            raise ValueError(
                f"searchTerms[{index}] must contain exactly one since:YYYY-MM-DD "
                "and one until:YYYY-MM-DD bound"
            )
        values = {name: date.fromisoformat(value) for name, value in parsed}
        start, end = values["since"], values["until"]
        if start >= end:
            raise ValueError(f"searchTerms[{index}] since must be earlier than until")
        window_days = (end - start).days
        if window_days > max_window_days:
            raise ValueError(
                f"searchTerms[{index}] window is {window_days} days; the maximum is "
                f"{max_window_days}"
            )
        windows.append((start, end))

    window_start = min(start for start, _ in windows)
    window_end = max(end for _, end in windows)
    if (window_end - window_start).days > max_window_days:
        raise ValueError(
            f"combined query window is {(window_end - window_start).days} days; "
            f"the maximum is {max_window_days}"
        )

    warnings: list[str] = []
    check_day = today or date.today()
    if window_end > check_day:
        warnings.append(
            "the query window ends after today; confirm the upper bound is the "
            "exclusive end of the intended completed-day window"
        )

    max_items = actor_input.get("maxItems")
    if max_items is not None:
        if isinstance(max_items, bool) or not isinstance(max_items, int):
            raise ValueError("maxItems must be an integer when present")
        if not 1 <= max_items <= _MAX_ITEMS_CEILING:
            raise ValueError(f"maxItems must be within 1..{_MAX_ITEMS_CEILING}")

    actor_id = actor_input.get("actorId")
    if isinstance(actor_id, str) and any(
        marker in actor_id.lower() for marker in ("example", "reviewed", "owner~")
    ):
        warnings.append("actorId looks like a placeholder; replace it with the reviewed Actor ID")

    return PreflightReport(
        query_modes=modes,
        window_start=window_start,
        window_end=window_end,
        window_days=(window_end - window_start).days,
        max_items=max_items,
        warnings=tuple(warnings),
    )


def _reject_credential_keys(value: object) -> None:
    """Refuse an input payload that contains credential-shaped keys anywhere."""
    if isinstance(value, dict):
        for key, child in value.items():
            normalized = str(key).lower().replace("-", "_")
            if any(part in normalized for part in _FORBIDDEN_KEY_PARTS):
                raise ValueError(
                    f"Actor input must not contain credential-shaped key {key!r}"
                )
            _reject_credential_keys(child)
    elif isinstance(value, list):
        for child in value:
            _reject_credential_keys(child)
