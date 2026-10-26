"""Leakage-safe forecast baselines."""

from __future__ import annotations

from decimal import Decimal


def persistence_forecast(last_completed_close: Decimal) -> dict[str, Decimal]:
    """Predict every requested horizon with the last completed close.

    This is a deliberately simple reference baseline, not a trained model.
    The input must be the most recent completed close available at the issue
    cutoff; a current/incomplete candle close must never be passed here.
    """
    if not isinstance(last_completed_close, Decimal):
        raise ValueError("last_completed_close must be a Decimal")
    if not last_completed_close.is_finite() or last_completed_close <= 0:
        raise ValueError("last_completed_close must be a finite positive price")

    return {f"n+{horizon}": last_completed_close for horizon in range(6)}
