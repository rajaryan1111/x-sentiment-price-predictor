"""Chronological walk-forward validation with a purge/embargo gap.

Rows are ordered by forecast cutoff. Each fold trains on an expanding prefix of
history only, leaves an embargo gap, and then tests on the next untouched block.
The embargo defaults to the longest forecast horizon so that a label from the end
of the training block (which resolves up to ``MAX_HORIZON`` days later) can never
overlap the test block.

No random shuffling is available here on purpose: random splits are not a valid
primary evaluation for time series.
"""
from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from xsentiment.features.dataset import MAX_HORIZON


@dataclass(frozen=True, slots=True)
class WalkForwardFold:
    """Index ranges over the ordered eligible rows; all bounds are half-open."""

    index: int
    train_start: int
    train_end: int
    test_start: int
    test_end: int

    @property
    def train_indices(self) -> tuple[int, ...]:
        return tuple(range(self.train_start, self.train_end))

    @property
    def test_indices(self) -> tuple[int, ...]:
        return tuple(range(self.test_start, self.test_end))

    @property
    def embargo_samples(self) -> int:
        return self.test_start - self.train_end

    @property
    def overlaps(self) -> bool:
        return self.train_end > self.test_start


def expanding_walk_forward(
    n_samples: int,
    *,
    min_train_samples: int,
    test_samples: int,
    embargo_samples: int = MAX_HORIZON,
    max_folds: int | None = None,
) -> list[WalkForwardFold]:
    """Build expanding-window folds; returns an empty list when data is too short."""
    if n_samples < 0:
        raise ValueError("n_samples must be non-negative")
    if min_train_samples < 1:
        raise ValueError("min_train_samples must be at least 1")
    if test_samples < 1:
        raise ValueError("test_samples must be at least 1")
    if embargo_samples < 0:
        raise ValueError("embargo_samples must be non-negative")
    if max_folds is not None and max_folds < 1:
        raise ValueError("max_folds must be at least 1 when supplied")

    folds: list[WalkForwardFold] = []
    train_end = min_train_samples
    while True:
        test_start = train_end + embargo_samples
        test_end = test_start + test_samples
        if test_end > n_samples:
            break
        folds.append(
            WalkForwardFold(
                index=len(folds),
                train_start=0,
                train_end=train_end,
                test_start=test_start,
                test_end=test_end,
            )
        )
        if max_folds is not None and len(folds) >= max_folds:
            break
        train_end += test_samples
    return folds


def validate_folds(
    folds: Sequence[WalkForwardFold], n_samples: int, *, embargo_samples: int | None = None
) -> None:
    """Fail closed if any fold leaks, overlaps, or falls outside the sample range."""
    for fold in folds:
        if fold.overlaps:
            raise ValueError(f"fold {fold.index} trains on rows it also tests")
        if fold.train_start < 0 or fold.test_end > n_samples:
            raise ValueError(f"fold {fold.index} falls outside the labelled sample range")
        if fold.train_end <= fold.train_start or fold.test_end <= fold.test_start:
            raise ValueError(f"fold {fold.index} has an empty train or test block")
        if embargo_samples is not None and fold.embargo_samples < embargo_samples:
            raise ValueError(f"fold {fold.index} embeds too small a purge gap")
