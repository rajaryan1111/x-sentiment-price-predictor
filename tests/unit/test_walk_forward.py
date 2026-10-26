from __future__ import annotations

import pytest

from xsentiment.validation.walk_forward import expanding_window_splits


def test_expanding_window_splits_are_chronological_and_non_overlapping() -> None:
    folds = expanding_window_splits(n_samples=12, min_train_size=4, test_size=2)

    assert len(folds) == 4
    assert folds[0].train_indices == (0, 1, 2, 3)
    assert folds[0].test_indices == (4, 5)
    assert folds[1].train_indices == (0, 1, 2, 3, 4, 5)
    assert folds[1].test_indices == (6, 7)
    assert folds[-1].test_indices == (10, 11)
    for fold in folds:
        assert max(fold.train_indices) < min(fold.test_indices)


def test_gap_excludes_rows_before_each_test_window_from_training() -> None:
    folds = expanding_window_splits(
        n_samples=15, min_train_size=5, test_size=2, gap=3
    )

    assert folds[0].train_indices == (0, 1, 2, 3, 4)
    assert folds[0].test_indices == (8, 9)
    assert folds[1].train_indices == (0, 1, 2, 3, 4, 5, 6)
    assert folds[1].test_indices == (10, 11)
    for fold in folds:
        assert set(fold.train_indices).isdisjoint(fold.test_indices)


def test_step_size_can_skip_test_windows_but_cannot_overlap_them() -> None:
    folds = expanding_window_splits(
        n_samples=20, min_train_size=4, test_size=2, step_size=4, max_splits=2
    )

    assert [fold.test_indices for fold in folds] == [(4, 5), (8, 9)]


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"n_samples": 0, "min_train_size": 1, "test_size": 1}, "n_samples"),
        ({"n_samples": 5, "min_train_size": 0, "test_size": 1}, "min_train_size"),
        ({"n_samples": 5, "min_train_size": 2, "test_size": 0}, "test_size"),
        ({"n_samples": 5, "min_train_size": 2, "test_size": 1, "gap": -1}, "gap"),
        (
            {"n_samples": 10, "min_train_size": 2, "test_size": 3, "step_size": 2},
            "step_size",
        ),
        (
            {"n_samples": 5, "min_train_size": 3, "test_size": 2, "gap": 1},
            "not enough samples",
        ),
    ],
)
def test_invalid_split_configuration_fails_closed(
    kwargs: dict[str, int], message: str
) -> None:
    with pytest.raises(ValueError, match=message):
        expanding_window_splits(**kwargs)
