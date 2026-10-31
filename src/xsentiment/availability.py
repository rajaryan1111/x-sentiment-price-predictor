"""Availability-basis contract for historical X posts.

The default ``observed`` basis is the leakage-safe rule: a post may enter a
forecast cutoff only when it was both published and first observed by that
cutoff. It protects the experiment from using information that did not exist
yet.

``archive_created_at`` is an explicitly opt-in retrospective basis for a
historical archive whose true first-observation times are unknowable. It uses
event time as a proxy for availability, requires a disclosure note, and must be
reported as a limitation: look-ahead bias cannot be excluded, so results from
this basis are retrospective, not a fully leakage-safe historical backtest.
"""
from __future__ import annotations

from typing import Literal

AvailabilityBasis = Literal["observed", "archive_created_at"]

OBSERVED_AVAILABILITY: AvailabilityBasis = "observed"
ARCHIVE_AVAILABILITY: AvailabilityBasis = "archive_created_at"
AVAILABILITY_BASES: tuple[AvailabilityBasis, ...] = (
    OBSERVED_AVAILABILITY,
    ARCHIVE_AVAILABILITY,
)

ARCHIVE_LIMITATION = (
    "Historical posts were collected after the event window. Their availability "
    "is assumed to equal their event time, so look-ahead bias cannot be excluded; "
    "results from this basis are retrospective and are not a fully leakage-safe "
    "historical backtest."
)


def validate_availability_basis(basis: str, note: str | None = None) -> None:
    """Fail closed on an unknown basis or an undisclosed archive assumption."""
    if basis not in AVAILABILITY_BASES:
        allowed = ", ".join(AVAILABILITY_BASES)
        raise ValueError(f"availability_basis must be one of: {allowed}")
    if basis == ARCHIVE_AVAILABILITY and not (note and note.strip()):
        raise ValueError(
            "availability_basis='archive_created_at' requires a non-empty "
            "availability_note describing the retrospective assumption"
        )
