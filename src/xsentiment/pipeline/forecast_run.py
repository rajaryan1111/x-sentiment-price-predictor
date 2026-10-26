"""End-to-end pipeline: price and post inputs -> features -> evaluation -> artefacts.

One run writes a directory containing a machine-readable manifest, the per-horizon
metrics, every out-of-sample prediction, the chart, the one-page outlook and the
Markdown evaluation report. Nothing in this module reaches the network: inputs are
loaded from files supplied by the caller, so a run is reproducible offline from the
same snapshot.
"""
from __future__ import annotations

import hashlib
import json
import platform
import subprocess
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

from xsentiment.backtesting.strategy import StrategyAssumptions
from xsentiment.features.dataset import (
    MAX_HORIZON,
    DatasetSummary,
    SupervisedRow,
    build_supervised_dataset,
    summarize,
)
from xsentiment.features.sentiment import (
    SentimentScorer,
    VaderSentimentScorer,
    score_posts,
    scorer_identity,
)
from xsentiment.ingestion.contracts import XPostRecord
from xsentiment.ingestion.prices import PriceCandle
from xsentiment.models.evaluation import (
    DEFAULT_MIN_TRAIN_SAMPLES,
    DEFAULT_TEST_SAMPLES,
    EvaluationResult,
    evaluate_walk_forward,
    mean_mae_by_model,
)
from xsentiment.models.forecasting import DEFAULT_RIDGE_LAMBDA
from xsentiment.reporting.charts import render_sentiment_price_chart
from xsentiment.reporting.outlook import build_outlook, render_outlook_markdown
from xsentiment.reporting.report import render_evaluation_report

PROJECT_NAME = "x-sentiment-price-predictor"


@dataclass(frozen=True, slots=True)
class RunArtifacts:
    """Paths written by one pipeline run."""

    output_dir: Path
    report_path: Path
    outlook_path: Path
    chart_path: Path
    manifest_path: Path
    predictions_path: Path
    metrics_path: Path


def sha256_file(path: str | Path) -> str:
    """Content hash of an input snapshot, used as provenance evidence."""
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_candles(path: str | Path) -> list[PriceCandle]:
    """Load validated daily candles from a JSON snapshot."""
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if isinstance(payload, dict):
        rows = payload.get("candles")
    else:
        rows = payload
    if not isinstance(rows, list) or not rows:
        raise ValueError("price snapshot must contain a non-empty list of candles")
    candles: list[PriceCandle] = []
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            raise ValueError(f"price snapshot row {index} must be an object")
        try:
            candles.append(
                PriceCandle(
                    product_id=str(row["product_id"]),
                    timestamp=_aware(row["timestamp"], f"row {index} timestamp"),
                    low=_decimal(row["low"], index, "low"),
                    high=_decimal(row["high"], index, "high"),
                    open=_decimal(row["open"], index, "open"),
                    close=_decimal(row["close"], index, "close"),
                    volume=_decimal(row["volume"], index, "volume"),
                )
            )
        except KeyError as exc:
            raise ValueError(f"price snapshot row {index} is missing {exc.args[0]!r}") from exc
        except (TypeError, ValueError) as exc:
            raise ValueError(f"price snapshot row {index} is invalid: {exc}") from exc
    return candles


def load_posts(path: str | Path) -> list[XPostRecord]:
    """Load normalized X post records from JSONL; fails closed with a line number."""
    posts: list[XPostRecord] = []
    for number, line in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"posts line {number} is not valid JSON") from exc
        if not isinstance(payload, dict):
            raise ValueError(f"posts line {number} must be a JSON object")
        warnings = payload.get("warnings") or ()
        if not isinstance(warnings, (list, tuple)):
            raise ValueError(f"posts line {number} warnings must be a list")
        try:
            posts.append(
                XPostRecord(
                    post_id=str(payload["post_id"]),
                    created_at=_aware(payload["created_at"], f"line {number} created_at"),
                    retrieved_at=_aware(payload["retrieved_at"], f"line {number} retrieved_at"),
                    text=str(payload["text"]),
                    sentiment_score=_optional_float(payload.get("sentiment_score")),
                    likes=_optional_int(payload.get("likes")),
                    reposts=_optional_int(payload.get("reposts")),
                    views=_optional_int(payload.get("views")),
                    author_followers=_optional_int(payload.get("author_followers")),
                    provenance_url=payload.get("provenance_url"),
                    source_name=str(payload.get("source_name") or "supplied_file"),
                    source_platform=str(payload.get("source_platform") or "x"),
                    source_created_at_raw=payload.get("source_created_at_raw"),
                    source_utc_offset=payload.get("source_utc_offset"),
                    author_id=payload.get("author_id"),
                    query_mode=payload.get("query_mode"),
                    query=payload.get("query"),
                    source_record_hash=payload.get("source_record_hash"),
                    schema_version=str(payload.get("schema_version") or "x-post-v1"),
                    warnings=tuple(warnings),
                )
            )
        except KeyError as exc:
            raise ValueError(f"posts line {number} is missing {exc.args[0]!r}") from exc
        except (TypeError, ValueError) as exc:
            raise ValueError(f"posts line {number} is invalid: {exc}") from exc
    return posts


def load_news_context(path: str | Path) -> list[str]:
    """Load contextual news lines; these never become model features."""
    context: list[str] = []
    for number, line in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"news line {number} is not valid JSON") from exc
        if not isinstance(payload, dict):
            raise ValueError(f"news line {number} must be a JSON object")
        title = str(payload.get("title") or payload.get("headline") or "").strip()
        if not title:
            raise ValueError(f"news line {number} is missing a title")
        url = str(payload.get("url") or "").strip()
        published = str(payload.get("published_at") or "").strip()
        details = " — ".join(part for part in (published, url) if part)
        context.append(f"{title} ({details})" if details else title)
    return context


def _aware(value: object, label: str) -> datetime:
    if not isinstance(value, str):
        raise ValueError(f"{label} must be an ISO-8601 string")
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"{label} must include a timezone offset")
    return parsed.astimezone(UTC)


def _decimal(value: object, index: int, field: str) -> Decimal:
    try:
        parsed = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"row {index} {field} is not a number") from exc
    return parsed


def _optional_int(value: object) -> int | None:
    return None if value is None else int(str(value))


def _optional_float(value: object) -> float | None:
    return None if value is None else float(str(value))


# Editable installs and CI checkouts share the src/ layout, so the repository root
# is three parents above this module directory. Recorded per run as NFR1 provenance:
# the revision is read from the real checkout or explicitly marked unavailable —
# it is never inferred from a branch name or invented.
_REPO_ROOT = Path(__file__).resolve().parents[3]
_HASH_CHARS = frozenset("0123456789abcdef")


def _code_revision(root: Path | None = None) -> dict[str, str]:
    """Resolve the checked-out revision for the run manifest (NFR1).

    Returns ``{"code_revision": <40-hex sha>}`` when the repository metadata is
    actually available. Otherwise it returns ``{"code_revision": "unavailable",
    "code_revision_reason": <why>}`` — an explicit state, never an invented or
    inferred value. Failures (missing git executable, timeouts, non-repositories,
    source archives) are caught and reported, not raised.
    """
    checked_root = Path(root) if root is not None else _REPO_ROOT
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--verify", "HEAD^{commit}"],
            cwd=str(checked_root),
            capture_output=True,
            text=True,
            timeout=2.0,
            check=False,
        )
    except FileNotFoundError:
        return {
            "code_revision": "unavailable",
            "code_revision_reason": "git executable is not available",
        }
    except (OSError, subprocess.SubprocessError) as exc:
        return {
            "code_revision": "unavailable",
            "code_revision_reason": f"git rev-parse failed: {exc.__class__.__name__}",
        }
    revision = result.stdout.strip()
    if result.returncode == 0 and len(revision) == 40 and set(revision) <= _HASH_CHARS:
        return {"code_revision": revision}
    if not checked_root.is_dir():
        reason = "project directory does not exist"
    elif (checked_root / ".git").exists():
        reason = "git rev-parse returned no usable commit"
    else:
        reason = "not a git repository (source archive or imported install)"
    return {"code_revision": "unavailable", "code_revision_reason": reason}


def _installed_versions() -> dict[str, str]:
    versions = {"python": sys.version.split()[0], "platform": platform.platform()}
    for package in (PROJECT_NAME, "vaderSentiment", "pydantic"):
        try:
            versions[package] = version(package)
        except PackageNotFoundError:  # pragma: no cover - defensive
            versions[package] = "not installed"
    return versions


def run_forecast_pipeline(
    *,
    candles: Sequence[PriceCandle],
    posts: Sequence[XPostRecord] = (),
    output_dir: str | Path,
    asset: str = "BTC-USD",
    now: datetime | None = None,
    min_train_samples: int = DEFAULT_MIN_TRAIN_SAMPLES,
    test_samples: int = DEFAULT_TEST_SAMPLES,
    embargo_samples: int = MAX_HORIZON,
    ridge_lambda: float = DEFAULT_RIDGE_LAMBDA,
    strategy_assumptions: StrategyAssumptions | None = None,
    scorer: SentimentScorer | None = None,
    news_context: Sequence[str] = (),
    provenance: dict[str, object] | None = None,
    limitations: Sequence[str] = (),
) -> RunArtifacts:
    """Run the full offline pipeline and write every artefact to ``output_dir``."""
    as_of = now.astimezone(UTC) if now is not None else datetime.now(UTC)
    active_scorer = scorer or VaderSentimentScorer()
    scored_posts = score_posts(posts, active_scorer)

    rows: list[SupervisedRow] = build_supervised_dataset(
        candles, scored_posts, max_horizon=MAX_HORIZON, now=now
    )
    summary: DatasetSummary = summarize(
        rows, scored_posts, candles=candles, max_horizon=MAX_HORIZON, now=now
    )
    evaluation: EvaluationResult = evaluate_walk_forward(
        rows,
        min_train_samples=min_train_samples,
        test_samples=test_samples,
        embargo_samples=embargo_samples,
        ridge_lambda=ridge_lambda,
        strategy_assumptions=strategy_assumptions,
    )
    scorer_id = scorer_identity(active_scorer)
    outlook = build_outlook(
        rows,
        summary,
        asset=asset,
        as_of=as_of,
        scorer=scorer_id,
        news_context=news_context,
        ridge_lambda=ridge_lambda,
    )

    run_provenance: dict[str, object] = dict(provenance or {})
    if "code_revision" not in run_provenance:
        run_provenance.update(_code_revision())
    run_provenance.setdefault("asset", asset)
    run_provenance.setdefault("price_candles_supplied", len(candles))
    run_provenance.setdefault("posts_supplied", len(posts))
    run_provenance.setdefault("sentiment_scorer", f"{scorer_id['scorer']} {scorer_id['version']}")
    run_provenance.setdefault("pipeline_versions", _installed_versions())

    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    chart_path = render_sentiment_price_chart(
        candles,
        rows,
        output / "sentiment-vs-price.svg",
        title=f"{asset} close and X sentiment",
        subtitle=f"Forecast cutoff {_iso(outlook.cutoff) or 'unavailable'}",
        now=now,
    )
    report_path = output / "evaluation-report.md"
    report_path.write_text(
        render_evaluation_report(
            asset=asset,
            dataset_summary=summary,
            evaluation=evaluation,
            outlook=outlook,
            provenance=run_provenance,
            generated_at=as_of,
            limitations=limitations,
        ),
        encoding="utf-8",
    )
    outlook_path = output / "outlook.md"
    outlook_path.write_text(render_outlook_markdown(outlook), encoding="utf-8")

    predictions_path = output / "predictions.jsonl"
    predictions_path.write_text(_predictions_jsonl(evaluation), encoding="utf-8")
    metrics_path = output / "metrics.json"
    metrics_path.write_text(
        json.dumps(_metrics_payload(evaluation), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    manifest_path = output / "manifest.json"
    manifest_path.write_text(
        json.dumps(
            _manifest(
                as_of=as_of,
                asset=asset,
                summary=summary,
                evaluation=evaluation,
                provenance=run_provenance,
                posts=len(posts),
            ),
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    return RunArtifacts(
        output_dir=output,
        report_path=report_path,
        outlook_path=outlook_path,
        chart_path=chart_path,
        manifest_path=manifest_path,
        predictions_path=predictions_path,
        metrics_path=metrics_path,
    )


def _predictions_jsonl(evaluation: EvaluationResult) -> str:
    lines = [
        json.dumps(
            {
                "fold": prediction.fold,
                "cutoff": prediction.cutoff.isoformat(),
                "horizon": prediction.horizon,
                "model": prediction.model,
                "predicted_close": prediction.predicted_close,
                "actual_close": prediction.actual_close,
                "reference_close": prediction.reference_close,
                "error": prediction.error,
            },
            sort_keys=True,
        )
        for prediction in evaluation.predictions
    ]
    return "\n".join(lines) + ("\n" if lines else "")


def _metrics_payload(evaluation: EvaluationResult) -> dict[str, object]:
    return {
        "forecast_metrics": [
            {
                "model": metrics.model,
                "horizon": metrics.horizon,
                "samples": metrics.samples,
                "mae": metrics.mae,
                "rmse": metrics.rmse,
                "mean_error": metrics.mean_error,
            }
            for metrics in evaluation.metrics
        ],
        "mean_mae_by_model": mean_mae_by_model(evaluation),
        "strategies": {
            model: {
                "long_days": strategy.long_days,
                "metrics": strategy.metrics,
                "benchmark_metrics": strategy.benchmark_metrics,
                "risk_metrics_unavailable_reason": strategy.risk_metrics_unavailable_reason,
                "assumptions": {
                    "fee_rate": strategy.assumptions.fee_rate,
                    "periods_per_year": strategy.assumptions.periods_per_year,
                    "risk_free_rate": strategy.assumptions.risk_free_rate,
                    "minimum_acceptable_return": strategy.assumptions.minimum_acceptable_return,
                    "min_returns_for_risk_metrics": (
                        strategy.assumptions.min_returns_for_risk_metrics
                    ),
                },
            }
            for model, strategy in evaluation.strategies.items()
        },
        "unavailable": evaluation.unavailable,
        "warnings": list(evaluation.warnings),
    }


def _manifest(
    *,
    as_of: datetime,
    asset: str,
    summary: DatasetSummary,
    evaluation: EvaluationResult,
    provenance: dict[str, object],
    posts: int,
) -> dict[str, object]:
    return {
        "run_id": as_of.strftime("run-%Y%m%dT%H%M%SZ"),
        "generated_at": as_of.isoformat(),
        "asset": asset,
        "dataset": {
            "rows": summary.rows,
            "rows_with_full_horizon": summary.rows_with_full_horizon,
            "rows_with_sentiment": summary.rows_with_sentiment,
            "first_cutoff": _iso(summary.first_cutoff),
            "last_cutoff": _iso(summary.last_cutoff),
            "posts": posts,
            "scored_posts": summary.scored_posts,
            "unfinished_day_dropped": summary.unfinished_day_dropped,
        },
        "evaluation": {
            "assumptions": evaluation.assumptions,
            "folds": [
                {
                    "index": fold.index,
                    "train_rows": len(fold.train_indices),
                    "test_rows": len(fold.test_indices),
                    "embargo_rows": fold.embargo_samples,
                }
                for fold in evaluation.folds
            ],
            "predictions": len(evaluation.predictions),
            "untestable": evaluation.unavailable,
            "warnings": list(evaluation.warnings),
        },
        "provenance": provenance,
    }


def _iso(value: datetime | None) -> str | None:
    return value.isoformat() if value is not None else None
