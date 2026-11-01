"""Naive persistence baseline.

The baseline predicts the last completed close for every horizon, which is the
strongest "no information" comparison for a price series: it never needs fitting
and it never sees the future. It is the reference that a fitted model must beat
before any value can be claimed.
"""
from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from xsentiment.features.dataset import SupervisedRow
from xsentiment.models.forecasting import CloseForecaster

NAIVE_MODEL_NAME = "naive"


@dataclass(frozen=True, slots=True)
class NaivePersistenceModel:
    """Predict the last completed close for a horizon; ``None`` without history."""

    horizon: str
    name: str = NAIVE_MODEL_NAME

    def fit(self, rows: Sequence[SupervisedRow]) -> int:
        """Nothing is fitted; returns the number of rows seen for reporting."""
        return len(rows)

    @property
    def feature_names(self) -> tuple[str, ...]:
        return ()

    @property
    def training_samples(self) -> int:
        return 0

    @property
    def is_fitted(self) -> bool:
        return True

    def predict_close(self, row: SupervisedRow) -> float | None:
        return row.reference_close


__all__ = ["NAIVE_MODEL_NAME", "NaivePersistenceModel", "CloseForecaster"]
