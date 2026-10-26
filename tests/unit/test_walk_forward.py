import pytest

from xsentiment.features.dataset import MAX_HORIZON
from xsentiment.validation.walk_forward import (
    expanding_walk_forward,
    validate_folds,
)


def test_expanding_folds_move_forward_with_a_purge_gap() -> None:
    folds = expanding_walk_forward(100, min_train_samples=40, test_samples=20, embargo_samples=5)

    assert [fold.index for fold in folds] == [0, 1]
    assert folds[0].train_indices == tuple(range(40))
    assert folds[0].test_indices == tuple(range(45, 65))
    assert folds[1].train_indices == tuple(range(60))
    assert folds[1].test_indices == tuple(range(65, 85))
    assert all(fold.embargo_samples == 5 for fold in folds)
    assert not any(fold.overlaps for fold in folds)
    validate_folds(folds, 100, embargo_samples=5)


def test_embargo_defaults_to_the_longest_horizon() -> None:
    folds = expanding_walk_forward(60, min_train_samples=30, test_samples=10)
    assert folds[0].embargo_samples == MAX_HORIZON


def test_no_folds_when_history_is_too_short() -> None:
    assert expanding_walk_forward(50, min_train_samples=60, test_samples=20) == []
    assert expanding_walk_forward(0, min_train_samples=1, test_samples=1, embargo_samples=0) == []


def test_max_folds_limits_the_number_of_folds() -> None:
    folds = expanding_walk_forward(
        200, min_train_samples=20, test_samples=20, embargo_samples=5, max_folds=3
    )
    assert len(folds) == 3
    assert [fold.train_end for fold in folds] == [20, 40, 60]


def test_train_and_test_blocks_never_overlap_in_time_order() -> None:
    folds = expanding_walk_forward(90, min_train_samples=30, test_samples=15, embargo_samples=6)
    for fold in folds:
        assert max(fold.train_indices) < min(fold.test_indices)
        assert fold.test_start - fold.train_end == 6
        assert fold.test_end <= 90


def test_invalid_configuration_fails_closed() -> None:
    with pytest.raises(ValueError, match="min_train_samples"):
        expanding_walk_forward(10, min_train_samples=0, test_samples=1)
    with pytest.raises(ValueError, match="test_samples"):
        expanding_walk_forward(10, min_train_samples=1, test_samples=0)
    with pytest.raises(ValueError, match="embargo_samples"):
        expanding_walk_forward(10, min_train_samples=1, test_samples=1, embargo_samples=-1)
    with pytest.raises(ValueError, match="max_folds"):
        expanding_walk_forward(10, min_train_samples=1, test_samples=1, max_folds=0)


def test_validate_folds_rejects_a_leaking_fold() -> None:
    folds = expanding_walk_forward(60, min_train_samples=30, test_samples=10, embargo_samples=0)
    validate_folds(folds, 60)
    with pytest.raises(ValueError, match="purge gap"):
        validate_folds(folds, 60, embargo_samples=5)
