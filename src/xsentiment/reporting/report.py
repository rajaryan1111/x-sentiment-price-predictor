"""Evaluation report assembly.

The report keeps four kinds of statement visibly separate:

* **observed** facts about the data that was actually supplied,
* **method** statements describing what was computed and how,
* **measured** out-of-sample results, always with sample counts,
* **unavailable** items with the reason they could not be produced.

Trading risk metrics are reported only next to the strategy that produced them, so
they can never be mistaken for forecast accuracy.
"""
from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime

from xsentiment.backtesting.metrics import DEFAULT_PERIODS_PER_YEAR
from xsentiment.backtesting.strategy import StrategyAssumptions, strategy_specification
from xsentiment.features.dataset import DatasetSummary
from xsentiment.models.evaluation import EvaluationResult, mean_mae_by_model
from xsentiment.reporting.outlook import OutlookReport

_DISCLAIMER = (
    "Fixtures and synthetic data are labelled as such and are never presented as real "
    "provider results. No accuracy, profitability or investment claim is made."
)


def _table(headers: Sequence[str], rows: Sequence[Sequence[str]]) -> list[str]:
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
    lines.extend("| " + " | ".join(row) + " |" for row in rows)
    return lines


def _number(value: float | None, digits: int = 4) -> str:
    return "unavailable" if value is None else f"{value:,.{digits}f}"


def _percent(value: float | None) -> str:
    return "unavailable" if value is None else f"{value * 100:+.2f}%"


def _iso(value: datetime | None) -> str:
    return value.isoformat() if value is not None else "unavailable"


def _provenance_section(provenance: dict[str, object]) -> list[str]:
    lines = ["## Data and provenance", ""]
    if not provenance:
        lines.append("- No provenance metadata was recorded for this run.")
        return lines
    for key, value in provenance.items():
        label = key.replace("_", " ")
        lines.append(f"- **{label}:** {value}")
    return lines


def render_evaluation_report(
    *,
    asset: str,
    dataset_summary: DatasetSummary,
    evaluation: EvaluationResult,
    outlook: OutlookReport | None,
    provenance: dict[str, object],
    generated_at: datetime | None = None,
    warnings: Sequence[str] = (),
    limitations: Sequence[str] = (),
) -> str:
    """Render the Markdown evaluation report from measured artefacts only."""
    stamp = generated_at or datetime.now(UTC)
    lines: list[str] = [
        f"# {asset} sentiment and price forecast evaluation",
        "",
        f"_Generated {stamp.isoformat()} by the reproducible pipeline in this repository._",
        "",
        "> Scope note: this report contains out-of-sample walk-forward results computed "
        "from the data described below. It states explicitly which requested metrics could "
        "not be produced and why.",
        "",
        *_provenance_section(provenance),
        "",
        "## Dataset profile",
        "",
        *_table(
            ("Item", "Value"),
            (
                ("Forecast cutoffs built", str(dataset_summary.rows)),
                (
                    "Cutoffs with a full n+0..n+5 horizon",
                    str(dataset_summary.rows_with_full_horizon),
                ),
                ("Cutoffs with scored-post sentiment", str(dataset_summary.rows_with_sentiment)),
                ("First cutoff (UTC)", _iso(dataset_summary.first_cutoff)),
                ("Last cutoff (UTC)", _iso(dataset_summary.last_cutoff)),
                ("Posts supplied", str(dataset_summary.posts)),
                ("Posts scored", str(dataset_summary.scored_posts)),
                ("Unfinished current UTC day dropped", str(dataset_summary.unfinished_day_dropped)),
            ),
        ),
        "",
        "## Evaluation design",
        "",
        f"- Expanding-window walk-forward folds: **{evaluation.assumptions.get('folds', 0)}**",
        f"- Minimum training rows per fold: "
        f"**{evaluation.assumptions.get('min_train_samples')}**",
        f"- Test rows per fold: **{evaluation.assumptions.get('test_samples')}**",
        f"- Purge/embargo rows between training and testing: "
        f"**{evaluation.assumptions.get('embargo_samples')}**",
        f"- Ridge penalty (slope only): **{evaluation.assumptions.get('ridge_lambda')}**",
        "- Models compared on identical folds and eligible rows: naive persistence, "
        "price-only ridge, sentiment-plus-price ridge.",
        "- Feature groups: price features are predeclared lagged/rolling price statistics; "
        "the price-only model never receives sentiment columns.",
        "- Missing feature values are imputed with training-fold means and features are "
        "standardised with training-fold statistics only.",
        "- No random shuffling is used anywhere: folds are chronological and the purge gap "
        "equals the longest horizon so labels cannot straddle the boundary.",
        "",
        "## Out-of-sample forecast metrics",
        "",
    ]
    if evaluation.metrics:
        lines.extend(
            _table(
                ("Model", "Horizon", "Samples", "MAE (USD)", "RMSE (USD)", "Mean error (USD)"),
                tuple(
                    (
                        metrics.model,
                        metrics.horizon,
                        str(metrics.samples),
                        _number(metrics.mae, 2),
                        _number(metrics.rmse, 2),
                        _number(metrics.mean_error, 2),
                    )
                    for metrics in evaluation.metrics
                ),
            )
        )
        lines.extend(["", "### Mean MAE across horizons", ""])
        summary = mean_mae_by_model(evaluation)
        naive = summary.get("naive")
        rows: list[tuple[str, str, str]] = []
        for model, value in summary.items():
            delta = (
                f"{(value / naive - 1.0) * 100:+.2f}% vs naive"
                if naive not in (None, 0.0)
                else "n/a"
            )
            rows.append((model, _number(value, 2), delta))
        lines.extend(_table(("Model", "Mean MAE (USD)", "Difference"), tuple(rows)))
        lines.extend(
            [
                "",
                "A lower mean MAE than the naive persistence baseline is the minimum bar for "
                "claiming that a model adds information; this report makes no such claim "
                "beyond the numbers above.",
            ]
        )
    else:
        lines.append(
            "No out-of-sample metrics were produced. Reason: "
            f"{evaluation.unavailable.get('walk_forward', 'insufficient labelled history')}."
        )

    lines.extend(["", "## Trading strategy and risk metrics", ""])
    lines.extend(f"- {item}" for item in strategy_specification(_any_assumptions(evaluation)))
    lines.append(
        f"- Annualisation: {DEFAULT_PERIODS_PER_YEAR} periods per year; the same conventions "
        "apply to every model below."
    )
    lines.append("")
    if evaluation.strategies:
        rows = []
        for model, strategy in evaluation.strategies.items():
            rows.append(
                (
                    model,
                    str(strategy.long_days),
                    _percent(strategy.metrics.get("exposure")),
                    _percent(strategy.metrics.get("cumulative_return")),
                    _number(strategy.metrics.get("sharpe_ratio"), 3),
                    _number(strategy.metrics.get("sortino_ratio"), 3),
                    _percent(strategy.metrics.get("max_drawdown")),
                )
            )
        lines.extend(
            _table(
                (
                    "Model",
                    "Long days",
                    "Exposure",
                    "Cumulative net return",
                    "Sharpe",
                    "Sortino",
                    "Max drawdown",
                ),
                tuple(rows),
            )
        )
        lines.extend(["", "### Benchmark (unconditional long, identical windows and fees)", ""])
        lines.extend(
            _table(
                ("Model", "Cumulative net return", "Sharpe", "Sortino", "Max drawdown"),
                tuple(
                    (
                        model,
                        _percent(strategy.benchmark_metrics.get("cumulative_return")),
                        _number(strategy.benchmark_metrics.get("sharpe_ratio"), 3),
                        _number(strategy.benchmark_metrics.get("sortino_ratio"), 3),
                        _percent(strategy.benchmark_metrics.get("max_drawdown")),
                    )
                    for model, strategy in evaluation.strategies.items()
                ),
            )
        )
        withheld = [
            (model, strategy.risk_metrics_unavailable_reason)
            for model, strategy in evaluation.strategies.items()
            if strategy.risk_metrics_unavailable_reason
        ]
        if withheld:
            lines.extend(["", "### Risk metrics withheld", ""])
            lines.extend(
                f"- **{model}:** {reason}" for model, reason in withheld
            )
        lines.extend(
            [
                "",
                "Sharpe, Sortino and maximum drawdown above describe this predeclared strategy "
                "on out-of-sample days. They are trading-strategy statistics, not evidence of "
                "forecast accuracy, and they are not a forecast of future performance.",
            ]
        )
    else:
        lines.append("No strategy could be simulated, so no risk metrics are reported.")

    if evaluation.unavailable:
        lines.extend(["", "## Unavailable items and reasons", ""])
        lines.extend(
            f"- **{key}:** {reason}" for key, reason in sorted(evaluation.unavailable.items())
        )

    if evaluation.warnings:
        lines.extend(["", "## Warnings", ""])
        lines.extend(f"- {item}" for item in evaluation.warnings)

    if outlook is not None:
        lines.extend(
            [
                "",
                "## Current outlook snapshot",
                "",
                f"- As-of: {outlook.as_of.isoformat()}",
                f"- Forecast cutoff: {_iso(outlook.cutoff)}",
                f"- Last completed close (USD): "
                f"{_number(outlook.latest_completed_close, 2)}",
                f"- Cutoffs with sentiment: {outlook.days_with_sentiment}",
                "- Full one-page outlook: `outlook.md` in this run directory.",
            ]
        )

    lines.extend(["", "## Limitations", ""])
    combined = list(limitations) + list(outlook.limitations if outlook else ())
    if combined:
        lines.extend(f"- {item}" for item in combined)
    else:
        lines.append("- None recorded for this run.")
    lines.extend(["", "---", "", _DISCLAIMER, ""])
    return "\n".join(lines)


def _any_assumptions(evaluation: EvaluationResult) -> StrategyAssumptions | None:
    for strategy in evaluation.strategies.values():
        return strategy.assumptions
    return None
