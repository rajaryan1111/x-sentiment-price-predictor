"""Chronological walk-forward evaluation of the naive, price-only and candidate models.

Every model variant is fitted and scored on identical folds, identical cutoffs and
an identical eligible-row set, so a comparison between them is like-for-like. The
eligible set is the same for all models: rows with a reference close and a complete
forward horizon. Missing sentiment is handled by training-fold imputation, not by
dropping rows for one model only.

Out-of-sample predictions feed the predeclared strategy so that Sharpe, Sortino and
maximum drawdown are derived from strategy returns, never from forecast errors.
"""
from __future__ import annotations

import dataclasses
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime

from xsentiment.backtesting.metrics import mae, mean_error, rmse
from xsentiment.backtesting.strategy import (
    SIGNAL_HORIZON,
    StrategyAssumptions,
    StrategyResult,
    simulate_long_flat,
)
from xsentiment.features.dataset import (
    FEATURE_GROUPS,
    HORIZON_LABELS,
    MAX_HORIZON,
    SupervisedRow,
)
from xsentiment.models.baseline import NAIVE_MODEL_NAME, NaivePersistenceModel
from xsentiment.models.forecasting import (
    CANDIDATE_MODEL_SPECS,
    DEFAULT_RIDGE_LAMBDA,
    HorizonLinearModel,
    ModelSpec,
)
from xsentiment.validation.walk_forward import (
    WalkForwardFold,
    expanding_walk_forward,
    validate_folds,
)

DEFAULT_MIN_TRAIN_SAMPLES = 60
DEFAULT_TEST_SAMPLES = 20


@dataclass(frozen=True, slots=True)
class PredictionRecord:
    """One out-of-sample prediction with everything needed to re-derive its error."""

    fold: int
    cutoff: datetime
    horizon: str
    model: str
    predicted_close: float
    actual_close: float
    reference_close: float

    @property
    def error(self) -> float:
        return self.predicted_close - self.actual_close


@dataclass(frozen=True, slots=True)
class HorizonMetrics:
    model: str
    horizon: str
    samples: int
    mae: float
    rmse: float
    mean_error: float


@dataclass(frozen=True, slots=True)
class EvaluationResult:
    folds: tuple[WalkForwardFold, ...]
    metrics: tuple[HorizonMetrics, ...]
    predictions: tuple[PredictionRecord, ...]
    strategies: dict[str, StrategyResult]
    assumptions: dict[str, object]
    warnings: tuple[str, ...]
    unavailable: dict[str, str]

    @property
    def has_predictions(self) -> bool:
        return bool(self.predictions)


def eligible_rows(rows: Sequence[SupervisedRow]) -> list[SupervisedRow]:
    """Rows usable for supervised evaluation, identical for every model variant."""
    eligible = [row for row in rows if row.has_full_horizon and row.reference_close is not None]
    cutoffs = [row.cutoff for row in eligible]
    if len(set(cutoffs)) != len(cutoffs):
        raise ValueError("dataset contains duplicate forecast cutoffs")
    return eligible


def _horizon_metrics(predictions: Sequence[PredictionRecord]) -> tuple[HorizonMetrics, ...]:
    grouped: dict[tuple[str, str], list[float]] = {}
    for prediction in predictions:
        grouped.setdefault((prediction.model, prediction.horizon), []).append(prediction.error)
    return tuple(
        HorizonMetrics(
            model=model,
            horizon=horizon,
            samples=len(errors),
            mae=mae(errors),
            rmse=rmse(errors),
            mean_error=mean_error(errors),
        )
        for (model, horizon), errors in sorted(grouped.items())
    )


def mean_mae_by_model(result: EvaluationResult) -> dict[str, float]:
    """Average MAE across horizons per model; helper for reports and manifests."""
    pooled: dict[str, list[float]] = {}
    for metrics in result.metrics:
        pooled.setdefault(metrics.model, []).append(metrics.mae)
    return {model: sum(values) / len(values) for model, values in sorted(pooled.items())}


def evaluate_walk_forward(
    rows: Sequence[SupervisedRow],
    *,
    min_train_samples: int = DEFAULT_MIN_TRAIN_SAMPLES,
    test_samples: int = DEFAULT_TEST_SAMPLES,
    embargo_samples: int = MAX_HORIZON,
    ridge_lambda: float = DEFAULT_RIDGE_LAMBDA,
    max_folds: int | None = None,
    horizons: Sequence[str] = HORIZON_LABELS,
    specs: Sequence[ModelSpec] = CANDIDATE_MODEL_SPECS,
    include_naive: bool = True,
    strategy_assumptions: StrategyAssumptions | None = None,
) -> EvaluationResult:
    """Fit and score every model on identical expanding-window folds."""
    active_strategy = strategy_assumptions or StrategyAssumptions()
    eligible = eligible_rows(rows)
    folds = expanding_walk_forward(
        len(eligible),
        min_train_samples=min_train_samples,
        test_samples=test_samples,
        embargo_samples=embargo_samples,
        max_folds=max_folds,
    )
    validate_folds(folds, len(eligible), embargo_samples=embargo_samples)

    assumptions: dict[str, object] = {
        "min_train_samples": min_train_samples,
        "test_samples": test_samples,
        "embargo_samples": embargo_samples,
        "ridge_lambda": ridge_lambda,
        "max_folds": max_folds,
        "horizons": list(horizons),
        "feature_groups": {spec.name: list(FEATURE_GROUPS[spec.feature_group]) for spec in specs},
        "strategy": dataclasses.asdict(active_strategy),
        "eligible_rows": len(eligible),
        "rows": len(rows),
        "folds": len(folds),
    }
    warnings: list[str] = []
    unavailable: dict[str, str] = {}
    with_sentiment = sum(row.has_sentiment for row in eligible)
    assumptions["eligible_rows_with_sentiment"] = with_sentiment
    if eligible and with_sentiment == 0:
        warnings.append(
            "No eligible row has a scored-post sentiment mean, so the sentiment-plus-price "
            "candidate is not identifiable in this run and its coefficients cannot be "
            "interpreted."
        )
    if not folds:
        unavailable["walk_forward"] = (
            f"{len(eligible)} eligible rows cannot fill a first fold of {min_train_samples} "
            f"training rows plus a {embargo_samples}-row purge plus {test_samples} test rows"
        )
        return EvaluationResult((), (), (), {}, assumptions, tuple(warnings), unavailable)

    predictions: list[PredictionRecord] = []
    for fold in folds:
        train_rows = [eligible[index] for index in fold.train_indices]
        test_rows = [eligible[index] for index in fold.test_indices]
        for horizon in horizons:
            models: list[NaivePersistenceModel | HorizonLinearModel] = []
            if include_naive:
                models.append(NaivePersistenceModel(horizon=horizon))
            models.extend(
                HorizonLinearModel(horizon=horizon, spec=spec, ridge_lambda=ridge_lambda)
                for spec in specs
            )
            for model in models:
                if isinstance(model, HorizonLinearModel):
                    try:
                        model.fit(train_rows)
                    except ValueError as exc:
                        unavailable[f"{model.name}:{horizon}"] = str(exc)
                        continue
                for row in test_rows:
                    actual = row.labels.get(horizon)
                    predicted = model.predict_close(row)
                    if actual is None or predicted is None or row.reference_close is None:
                        continue
                    predictions.append(
                        PredictionRecord(
                            fold=fold.index,
                            cutoff=row.cutoff,
                            horizon=horizon,
                            model=model.name,
                            predicted_close=float(predicted),
                            actual_close=float(actual),
                            reference_close=float(row.reference_close),
                        )
                    )

    row_by_cutoff = {row.cutoff: row for row in eligible}
    strategies: dict[str, StrategyResult] = {}
    signal_models = sorted(
        {prediction.model for prediction in predictions if prediction.horizon == SIGNAL_HORIZON}
    )
    for model_name in signal_models:
        pairs = [
            (row_by_cutoff[prediction.cutoff], prediction.predicted_close)
            for prediction in predictions
            if prediction.model == model_name and prediction.horizon == SIGNAL_HORIZON
        ]
        try:
            strategies[model_name] = simulate_long_flat(
                pairs, model=model_name, assumptions=active_strategy
            )
        except ValueError as exc:
            unavailable[f"strategy:{model_name}"] = str(exc)

    return EvaluationResult(
        folds=tuple(folds),
        metrics=_horizon_metrics(predictions),
        predictions=tuple(predictions),
        strategies=strategies,
        assumptions=assumptions,
        warnings=tuple(warnings),
        unavailable=unavailable,
    )


__all__ = [
    "DEFAULT_MIN_TRAIN_SAMPLES",
    "DEFAULT_TEST_SAMPLES",
    "EvaluationResult",
    "HorizonMetrics",
    "NAIVE_MODEL_NAME",
    "PredictionRecord",
    "eligible_rows",
    "evaluate_walk_forward",
    "mean_mae_by_model",
]
