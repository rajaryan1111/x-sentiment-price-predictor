"""Deterministic chronological split generation for walk-forward evaluation.

This module only creates fold boundaries. Model fitting, preprocessing, and
metrics must be performed independently inside each fold by the caller.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class WalkForwardFold:
    """Positional row indices for one expanding-window fold."""

    fold_number: int
    train_indices: tuple[int, ...]
    test_indices: tuple[int, ...]


def expanding_window_splits(
    n_samples: int,
    *,
    min_train_size: int,
    test_size: int,
    step_size: int | None = None,
    gap: int = 0,
    max_splits: int | None = None,
) -> tuple[WalkForwardFold, ...]:
    """Return non-overlapping chronological test folds with expanding training data.

    The gap excludes rows immediately before each test window from training.
    For multi-step targets, callers should choose a gap large enough to prevent
    training labels from reaching into the test period (for example, at least
    the maximum target horizon when rows and horizons are daily).

    The function operates on row positions only. The caller must sort rows by
    forecast cutoff first and must fit all learned transforms on train rows only.
    """
    integer_values = {
        "n_samples": n_samples,
        "min_train_size": min_train_size,
        "test_size": test_size,
        "gap": gap,
    }
    if step_size is not None:
        integer_values["step_size"] = step_size
    if max_splits is not None:
        integer_values["max_splits"] = max_splits
    for name, value in integer_values.items():
        if isinstance(value, bool) or not isinstance(value, int):
            raise ValueError(f"{name} must be an integer")

    if n_samples < 1:
        raise ValueError("n_samples must be positive")
    if min_train_size < 1:
        raise ValueError("min_train_size must be positive")
    if test_size < 1:
        raise ValueError("test_size must be positive")
    if gap < 0:
        raise ValueError("gap must be non-negative")
    if max_splits is not None and max_splits < 1:
        raise ValueError("max_splits must be positive when provided")

    resolved_step = test_size if step_size is None else step_size
    if resolved_step < test_size:
        raise ValueError("step_size must be at least test_size to avoid overlapping test folds")
    if resolved_step < 1:
        raise ValueError("step_size must be positive")

    first_test_start = min_train_size + gap
    if first_test_start + test_size > n_samples:
        raise ValueError("not enough samples for the requested train, gap, and test sizes")

    folds: list[WalkForwardFold] = []
    test_start = first_test_start
    while test_start + test_size <= n_samples:
        train_end = test_start - gap
        folds.append(
            WalkForwardFold(
                fold_number=len(folds) + 1,
                train_indices=tuple(range(train_end)),
                test_indices=tuple(range(test_start, test_start + test_size)),
            )
        )
        if max_splits is not None and len(folds) >= max_splits:
            break
        test_start += resolved_step

    return tuple(folds)
