"""One-page current sentiment outlook.

The outlook is an as-of snapshot, not a promise. It reports the last completed UTC
bar, the forecast cutoff, how much price and sentiment coverage stands behind it,
the model outputs for each horizon, and the uncertainty and limitations that apply.
News, when supplied, is explicitly contextual: it never enters the model features.
"""
from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime

from xsentiment.features.dataset import HORIZON_LABELS, DatasetSummary, SupervisedRow
from xsentiment.models.baseline import NaivePersistenceModel
from xsentiment.models.forecasting import (
    CANDIDATE_MODEL_SPECS,
    DEFAULT_RIDGE_LAMBDA,
    HorizonLinearModel,
)

_NOT_ADVICE = (
    "This outlook is a research artefact for an engineering assessment. It is not "
    "investment advice, and no accuracy or profit is claimed or implied."
)

# R11 structural contract for the one-page outlook, checked by tests so the page
# cannot silently grow into a multi-page report or lose its honesty sections.
REQUIRED_OUTLOOK_SECTIONS = (
    "# ",
    "**As of:**",
    "**Forecast cutoff:**",
    "## Data coverage",
    "## Model outputs at the cutoff",
    "## Contextual news (not a model input)",
    "## Uncertainty and limitations",
)
# A page holds roughly 50 lines of dense text; 90 lines is a generous ceiling that
# only trips when the outlook degenerates into a full report.
MAX_OUTLOOK_LINES = 90


def check_outlook_page(markdown: str) -> list[str]:
    """Return the R11 contract violations of a rendered outlook page, if any.

    The structural checks are: every required section heading is present, the page
    stays within the documented line ceiling, the disclaimer appears, and an
    empty-prediction page says so instead of inventing values.
    """
    violations: list[str] = []
    for section in REQUIRED_OUTLOOK_SECTIONS:
        if section not in markdown:
            violations.append(f"missing required section: {section!r}")
    line_count = len(markdown.splitlines())
    if line_count > MAX_OUTLOOK_LINES:
        violations.append(
            f"outlook is {line_count} lines, beyond the one-page ceiling of "
            f"{MAX_OUTLOOK_LINES}"
        )
    if "not investment advice" not in markdown:
        violations.append("missing the not-investment-advice disclaimer")
    if "No model predictions are available" in markdown and "unavailable" not in markdown:
        violations.append("an empty prediction block must keep the explicit unavailable state")
    return violations


@dataclass(frozen=True, slots=True)
class OutlookPrediction:
    model: str
    horizon: str
    predicted_close: float
    change_vs_reference: float | None


@dataclass(frozen=True, slots=True)
class OutlookReport:
    asset: str
    as_of: datetime
    cutoff: datetime | None
    latest_completed_close: float | None
    latest_completed_cutoff: datetime | None
    predictions: tuple[OutlookPrediction, ...]
    labelled_rows: int
    full_horizon_rows: int
    rows: int
    posts: int
    scored_posts: int
    days_with_sentiment: int
    scorer: dict[str, str]
    news_context: tuple[str, ...]
    model_notes: tuple[str, ...]
    limitations: tuple[str, ...]
    disclaimer: str = _NOT_ADVICE


def build_outlook(
    rows: Sequence[SupervisedRow],
    summary: DatasetSummary,
    *,
    asset: str,
    as_of: datetime,
    scorer: dict[str, str] | None = None,
    news_context: Sequence[str] = (),
    ridge_lambda: float = DEFAULT_RIDGE_LAMBDA,
    caller_limitations: Sequence[str] = (),
) -> OutlookReport:
    """Fit every model on all labelled rows and predict the most recent cutoff."""
    labelled = [row for row in rows if row.has_full_horizon and row.reference_close is not None]
    target = rows[-1] if rows else None
    predictions: list[OutlookPrediction] = []
    model_notes: list[str] = []
    limitations: list[str] = []

    if target is None:
        limitations.append(
            "No forecast cutoff is available because no completed price bar was supplied."
        )

    horizon_order = {label: index for index, label in enumerate(HORIZON_LABELS)}
    for horizon in HORIZON_LABELS:
        if target is None:
            break
        naive = NaivePersistenceModel(horizon=horizon)
        candidates: list[NaivePersistenceModel | HorizonLinearModel] = [naive]
        for spec in CANDIDATE_MODEL_SPECS:
            candidates.append(
                HorizonLinearModel(horizon=horizon, spec=spec, ridge_lambda=ridge_lambda)
            )
        for model in candidates:
            if isinstance(model, HorizonLinearModel):
                if not labelled:
                    limitations.append(
                        f"{model.name} has no labelled training rows, so no {horizon} "
                        "prediction is produced."
                    )
                    continue
                try:
                    model.fit(labelled)
                except ValueError as exc:
                    limitations.append(f"{model.name} {horizon} was not fitted: {exc}")
                    continue
                model_notes.append(
                    f"{model.name} {horizon}: {model.training_samples} training rows, "
                    f"{len(model.feature_names)} features"
                )
            predicted = model.predict_close(target)
            if predicted is None:
                continue
            change = (
                predicted / target.reference_close - 1.0
                if target.reference_close
                else None
            )
            predictions.append(
                OutlookPrediction(
                    model=model.name,
                    horizon=horizon,
                    predicted_close=float(predicted),
                    change_vs_reference=change,
                )
            )

    days_with_sentiment = sum(row.has_sentiment for row in rows)
    if days_with_sentiment == 0:
        limitations.append(
            "No scored post sentiment is available, so observed sentiment is unreported "
            "and the sentiment-plus-price candidate carries no sentiment information."
        )
    if target is not None and target.has_full_horizon:
        limitations.append(
            "The most recent row already has realised labels; it is the latest cutoff in "
            "the supplied data rather than a live future forecast."
        )

    for note in caller_limitations:
        text = str(note).strip()
        if text and text not in limitations:
            limitations.append(text)

    predictions.sort(key=lambda item: (horizon_order[item.horizon], item.model))
    return OutlookReport(
        asset=asset,
        as_of=as_of,
        cutoff=target.cutoff if target is not None else None,
        latest_completed_close=target.reference_close if target is not None else None,
        latest_completed_cutoff=(
            target.cutoff if target is not None and target.reference_close is not None else None
        ),
        predictions=tuple(predictions),
        labelled_rows=len(labelled),
        full_horizon_rows=summary.rows_with_full_horizon,
        rows=len(rows),
        posts=summary.posts,
        scored_posts=summary.scored_posts,
        days_with_sentiment=days_with_sentiment,
        scorer=scorer or {"scorer": "unknown", "version": "unknown"},
        news_context=tuple(news_context),
        model_notes=tuple(model_notes),
        limitations=tuple(limitations),
    )


def render_outlook_markdown(outlook: OutlookReport) -> str:
    """Render the outlook as a short, evidence-labelled Markdown page."""
    lines: list[str] = [
        f"# {outlook.asset} — current sentiment outlook",
        "",
        f"**As of:** {outlook.as_of.isoformat()}  ",
        f"**Forecast cutoff:** {_iso(outlook.cutoff)}  ",
        f"**Last completed daily close (USD):** "
        f"{_money(outlook.latest_completed_close)}  ",
        f"**Sentiment scorer:** {outlook.scorer.get('scorer', 'unknown')} "
        f"`{outlook.scorer.get('version', 'unknown')}`",
        "",
        "## Data coverage",
        f"- Completed price cutoffs in the dataset: **{outlook.rows}**",
        f"- Cutoffs with a full n+0..n+5 horizon: **{outlook.full_horizon_rows}**",
        f"- Eligible cutoffs (full horizon and a known previous close): "
        f"**{outlook.labelled_rows}**",
        f"- Posts supplied: **{outlook.posts}** (scored: **{outlook.scored_posts}**)",
        f"- Cutoffs with scored-post sentiment: **{outlook.days_with_sentiment}**",
        "",
        "## Model outputs at the cutoff",
    ]
    if outlook.predictions:
        lines.extend(
            [
                "| Model | Horizon | Predicted close (USD) | Change vs last completed close |",
                "| --- | --- | --- | --- |",
            ]
        )
        for prediction in outlook.predictions:
            lines.append(
                f"| {prediction.model} | {prediction.horizon} | "
                f"{_money(prediction.predicted_close)} | "
                f"{_percent(prediction.change_vs_reference)} |"
            )
    else:
        lines.append("No model predictions are available for this cutoff.")

    lines.extend(["", "## Contextual news (not a model input)"])
    if outlook.news_context:
        lines.extend(f"- {item}" for item in outlook.news_context)
    else:
        lines.append(
            "- No recent-news context was supplied (Tavily was not configured or not run "
            "for this outlook)."
        )

    lines.extend(["", "## Uncertainty and limitations"])
    lines.extend(f"- {item}" for item in outlook.limitations)
    if outlook.model_notes:
        lines.extend(["", "## Model provenance", *(f"- {item}" for item in outlook.model_notes)])
    lines.extend(["", "---", "", outlook.disclaimer, ""])
    return "\n".join(lines)


def _iso(value: datetime | None) -> str:
    return value.isoformat() if value is not None else "unavailable"


def _money(value: float | None) -> str:
    return "unavailable" if value is None else f"{value:,.2f}"


def _percent(value: float | None) -> str:
    return "unavailable" if value is None else f"{value * 100:+.2f}%"
