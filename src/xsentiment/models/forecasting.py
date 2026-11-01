"""Deterministic ridge regression used for the price-only and candidate models.

No third-party numerical dependency is used: the system size is tiny (a handful of
predeclared features), so a direct normal-equation solve is fast, deterministic and
runs inside the project's default test environment.

Every transform is fitted on the training fold only:

* missing feature values are imputed with the training-fold mean of that feature,
* features are standardized using training-fold statistics,
* the ridge penalty is applied to the slope only, never to the intercept.

The regression target is the horizon price ratio ``close(cutoff + h) / reference``
rather than the raw price level, so a prediction is directly comparable with the
naive persistence baseline and cannot drift outside plausible price ranges.
"""
from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass
from statistics import fmean, pstdev
from typing import Protocol, runtime_checkable

from xsentiment.features.dataset import FEATURE_GROUPS, SupervisedRow

DEFAULT_RIDGE_LAMBDA = 1.0
_SINGULAR_TOLERANCE = 1e-12


@runtime_checkable
class CloseForecaster(Protocol):
    """Contract for anything that can predict a horizon close at a cutoff."""

    name: str
    horizon: str

    def fit(self, rows: Sequence[SupervisedRow]) -> int:
        """Fit using training rows only; returns the number of usable rows."""

    @property
    def feature_names(self) -> tuple[str, ...]: ...

    def predict_close(self, row: SupervisedRow) -> float | None: ...


@dataclass(frozen=True, slots=True)
class ModelSpec:
    """A named model variant and the feature group it is allowed to see."""

    name: str
    feature_group: str


PRICE_ONLY_SPEC = ModelSpec(name="price_only", feature_group="price_only")
SENTIMENT_PRICE_SPEC = ModelSpec(name="sentiment_price", feature_group="sentiment_price")
CANDIDATE_MODEL_SPECS: tuple[ModelSpec, ...] = (PRICE_ONLY_SPEC, SENTIMENT_PRICE_SPEC)


def _solve_linear_system(matrix: list[list[float]], vector: list[float]) -> list[float]:
    """Gaussian elimination with partial pivoting for a small dense system."""
    size = len(matrix)
    augmented = [row[:] + [vector[index]] for index, row in enumerate(matrix)]
    for column in range(size):
        pivot = max(range(column, size), key=lambda row: abs(augmented[row][column]))
        if abs(augmented[pivot][column]) < _SINGULAR_TOLERANCE:
            raise ValueError("ridge system became singular; widen the penalty")
        augmented[column], augmented[pivot] = augmented[pivot], augmented[column]
        pivot_value = augmented[column][column]
        for row in range(column + 1, size):
            factor = augmented[row][column] / pivot_value
            if factor == 0.0:
                continue
            for index in range(column, size + 1):
                augmented[row][index] -= factor * augmented[column][index]

    solution = [0.0] * size
    for row in range(size - 1, -1, -1):
        remainder = sum(
            augmented[row][column] * solution[column] for column in range(row + 1, size)
        )
        solution[row] = (augmented[row][size] - remainder) / augmented[row][row]
    return solution


class RidgeRegression:
    """Ridge regression with deterministic imputation and standardization."""

    def __init__(
        self,
        feature_names: Sequence[str],
        *,
        ridge_lambda: float = DEFAULT_RIDGE_LAMBDA,
        standardize: bool = True,
    ) -> None:
        if ridge_lambda <= 0:
            raise ValueError("ridge_lambda must be positive")
        if not feature_names:
            raise ValueError("at least one feature name is required")
        self.feature_names: tuple[str, ...] = tuple(feature_names)
        self.ridge_lambda = float(ridge_lambda)
        self.standardize = standardize
        self._imputation: dict[str, float] = {}
        self._centers: dict[str, float] = {}
        self._scales: dict[str, float] = {}
        self._weights: tuple[float, ...] = ()
        self._intercept = 0.0
        self.training_samples = 0
        self.is_fitted = False

    def _raw_row(self, features: dict[str, float | None]) -> list[float]:
        if not self.is_fitted:
            raise RuntimeError("model must be fitted before it can transform features")
        values: list[float] = []
        for name in self.feature_names:
            value = features.get(name)
            values.append(self._imputation[name] if value is None else float(value))
        return values

    def _design_row(self, features: dict[str, float | None]) -> list[float]:
        raw = self._raw_row(features)
        if not self.standardize:
            return raw
        return [
            (value - self._centers[name]) / self._scales[name]
            for name, value in zip(self.feature_names, raw)
        ]

    def fit(
        self, feature_rows: Sequence[dict[str, float | None]], targets: Sequence[float]
    ) -> int:
        """Fit on training rows only; returns the number of training rows used."""
        if not feature_rows or len(feature_rows) != len(targets):
            raise ValueError("features and targets must be non-empty and equally sized")
        if any(not math.isfinite(target) for target in targets):
            raise ValueError("targets must be finite")

        self._imputation = {}
        for name in self.feature_names:
            observed = [
                float(row[name])
                for row in feature_rows
                if row.get(name) is not None and math.isfinite(float(row[name]))
            ]
            # A feature that is never observed collapses to zero and, after
            # standardization, contributes nothing to the fit.
            self._imputation[name] = fmean(observed) if observed else 0.0

        columns: list[list[float]] = []
        for name in self.feature_names:
            column = [
                self._imputation[name] if row.get(name) is None else float(row[name])
                for row in feature_rows
            ]
            columns.append(column)

        self._centers = {name: fmean(column) for name, column in zip(self.feature_names, columns)}
        self._scales = {}
        for name, column in zip(self.feature_names, columns):
            spread = pstdev(column)
            self._scales[name] = spread if spread > 0 else 1.0

        self.is_fitted = True
        self.training_samples = len(targets)
        design = [self._design_row(row) for row in feature_rows]

        target_mean = fmean(targets)
        centered = [target - target_mean for target in targets]
        size = len(self.feature_names)
        normal = [[0.0] * size for _ in range(size)]
        gradient = [0.0] * size
        for row, residual in zip(design, centered):
            for left in range(size):
                gradient[left] += row[left] * residual
                for right in range(size):
                    normal[left][right] += row[left] * row[right]
        for index in range(size):
            normal[index][index] += self.ridge_lambda

        self._weights = tuple(_solve_linear_system(normal, gradient))
        self._intercept = target_mean
        return self.training_samples

    def predict(self, features: dict[str, float | None]) -> float:
        """Predict the target ratio for one feature row."""
        row = self._design_row(features)
        return self._intercept + sum(
            weight * value for weight, value in zip(self._weights, row)
        )


class HorizonLinearModel:
    """One ridge model per horizon predicting ``close(cutoff + h) / reference``."""

    def __init__(
        self,
        *,
        horizon: str,
        spec: ModelSpec,
        ridge_lambda: float = DEFAULT_RIDGE_LAMBDA,
    ) -> None:
        if spec.feature_group not in FEATURE_GROUPS:
            raise ValueError(f"unknown feature group: {spec.feature_group}")
        self.horizon = horizon
        self.spec = spec
        self.name = spec.name
        self.regression = RidgeRegression(
            FEATURE_GROUPS[spec.feature_group], ridge_lambda=ridge_lambda
        )

    @property
    def feature_names(self) -> tuple[str, ...]:
        return self.regression.feature_names

    @property
    def is_fitted(self) -> bool:
        return self.regression.is_fitted

    @property
    def training_samples(self) -> int:
        return self.regression.training_samples

    def fit(self, rows: Sequence[SupervisedRow]) -> int:
        """Fit on training rows that have a reference close and this horizon label."""
        features: list[dict[str, float | None]] = []
        targets: list[float] = []
        for row in rows:
            reference = row.reference_close
            label = row.labels.get(self.horizon)
            if reference is None or reference <= 0 or label is None:
                continue
            ratio = label / reference
            if not math.isfinite(ratio) or ratio <= 0:
                continue
            features.append(row.features)
            targets.append(ratio)
        if not features:
            raise ValueError(
                f"no training rows carry a usable {self.horizon} label for {self.name}"
            )
        return self.regression.fit(features, targets)

    def predict_ratio(self, row: SupervisedRow) -> float | None:
        if row.reference_close is None or row.reference_close <= 0:
            return None
        return self.regression.predict(row.features)

    def predict_close(self, row: SupervisedRow) -> float | None:
        ratio = self.predict_ratio(row)
        if ratio is None or not math.isfinite(ratio) or ratio <= 0:
            return None
        return float(row.reference_close) * ratio
