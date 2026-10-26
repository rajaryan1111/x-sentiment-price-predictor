from datetime import UTC, datetime, timedelta

import pytest

from xsentiment.features.dataset import (
    FEATURE_GROUPS,
    SENTIMENT_FEATURE_NAMES,
    SupervisedRow,
)
from xsentiment.features.price_features import PRICE_FEATURE_NAMES
from xsentiment.models.baseline import NAIVE_MODEL_NAME, NaivePersistenceModel
from xsentiment.models.forecasting import (
    PRICE_ONLY_SPEC,
    SENTIMENT_PRICE_SPEC,
    HorizonLinearModel,
    RidgeRegression,
)


def make_row(
    index: int,
    *,
    reference: float | None = 100.0,
    features: dict[str, float | None] | None = None,
    labels: dict[str, float] | None = None,
) -> SupervisedRow:
    row_features: dict[str, float | None] = {name: None for name in PRICE_FEATURE_NAMES}
    row_features.update({name: None for name in SENTIMENT_FEATURE_NAMES})
    row_features.update(features or {})
    return SupervisedRow(
        cutoff=datetime(2026, 1, 1, tzinfo=UTC) + timedelta(days=index),
        reference_close=reference,
        entry_open=reference,
        features=row_features,
        labels={"n+0": 100.0, "n+1": 110.0} if labels is None else labels,
    )


def test_naive_model_predicts_the_last_completed_close() -> None:
    model = NaivePersistenceModel(horizon="n+5")
    row = make_row(0)

    assert model.fit([row]) == 1
    assert model.name == NAIVE_MODEL_NAME == "naive"
    assert model.feature_names == ()
    assert model.is_fitted
    assert model.predict_close(row) == 100.0
    assert model.predict_close(make_row(1, reference=None)) is None


def test_ridge_regression_recovers_a_linear_relationship() -> None:
    model = RidgeRegression(["x"], ridge_lambda=1e-6)
    features = [{"x": float(index)} for index in range(20)]
    model.fit(features, [2.0 * index + 5.0 for index in range(20)])

    assert model.predict({"x": 10.0}) == pytest.approx(25.0, rel=1e-3)
    assert model.predict({"x": -5.0}) == pytest.approx(-5.0, rel=1e-3)
    assert model.training_samples == 20


def test_missing_values_are_imputed_from_training_statistics_only() -> None:
    model = RidgeRegression(["x"], ridge_lambda=1e-6)
    model.fit([{"x": 1.0}, {"x": 2.0}, {"x": 3.0}], [1.0, 2.0, 3.0])

    assert model.predict({"x": None}) == pytest.approx(model.predict({"x": 2.0}))


def test_a_feature_never_observed_in_training_carries_no_weight() -> None:
    model = RidgeRegression(["x", "y"], ridge_lambda=1.0)
    model.fit(
        [{"x": 1.0, "y": None}, {"x": 2.0, "y": None}, {"x": 3.0, "y": None}], [1.0, 2.0, 3.0]
    )

    assert model.predict({"x": 2.0, "y": 999.0}) == pytest.approx(
        model.predict({"x": 2.0, "y": -999.0})
    )


def test_invalid_training_inputs_fail_closed() -> None:
    with pytest.raises(ValueError, match="non-empty"):
        RidgeRegression(["x"]).fit([], [])
    with pytest.raises(ValueError, match="equally sized"):
        RidgeRegression(["x"]).fit([{"x": 1.0}], [1.0, 2.0])
    with pytest.raises(ValueError, match="finite"):
        RidgeRegression(["x"]).fit([{"x": 1.0}], [float("nan")])
    with pytest.raises(ValueError, match="ridge_lambda"):
        RidgeRegression(["x"], ridge_lambda=0.0)
    with pytest.raises(ValueError, match="at least one feature"):
        RidgeRegression([])


def test_feature_groups_keep_sentiment_out_of_the_price_only_baseline() -> None:
    price_only = HorizonLinearModel(horizon="n+1", spec=PRICE_ONLY_SPEC)
    candidate = HorizonLinearModel(horizon="n+1", spec=SENTIMENT_PRICE_SPEC)

    assert set(price_only.feature_names) == set(FEATURE_GROUPS["price_only"])
    assert not set(price_only.feature_names) & set(SENTIMENT_FEATURE_NAMES)
    assert set(candidate.feature_names) == set(FEATURE_GROUPS["sentiment_price"])
    assert set(SENTIMENT_FEATURE_NAMES) <= set(candidate.feature_names)


def test_horizon_model_predicts_a_close_from_the_ratio_target() -> None:
    rows = [
        make_row(
            index,
            features={"return_1d": 0.01 * index},
            labels={"n+1": 100.0 + index},
        )
        for index in range(1, 21)
    ]
    model = HorizonLinearModel(horizon="n+1", spec=PRICE_ONLY_SPEC, ridge_lambda=1e-6)

    assert model.fit(rows) == 20
    predicted = model.predict_close(rows[0])
    assert predicted is not None and predicted > 0
    assert model.predict_ratio(rows[0]) == pytest.approx(predicted / 100.0)
    assert model.predict_close(make_row(0, reference=None)) is None


def test_horizon_model_fails_closed_without_usable_training_rows() -> None:
    model = HorizonLinearModel(horizon="n+1", spec=PRICE_ONLY_SPEC)
    with pytest.raises(ValueError, match="no training rows"):
        model.fit([make_row(0, labels={})])
