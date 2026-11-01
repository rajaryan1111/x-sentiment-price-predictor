"""Standalone, offline dashboard assembled only from the current run's artifacts."""
# The multiline f-string contains embedded HTML/CSS where wrapping lines would harm
# readability and may split markup; Python source lines intentionally exceed E501.
# ruff: noqa: E501
from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
from html import escape

from xsentiment.features.dataset import DatasetSummary
from xsentiment.models.evaluation import EvaluationResult, mean_mae_by_model
from xsentiment.reporting.outlook import OutlookReport
from xsentiment.reporting.units import quote_currency


def render_dashboard_html(
    *,
    asset: str,
    generated_at: datetime,
    dataset_summary: DatasetSummary,
    evaluation: EvaluationResult,
    outlook: OutlookReport,
    provenance: dict[str, object],
    chart_svg: str,
) -> str:
    """Return one self-contained HTML report; no network assets or inferred data."""
    currency = quote_currency(asset, provenance)
    metadata = provenance.get("price_snapshot_metadata")
    metadata = metadata if isinstance(metadata, Mapping) else {}
    source = metadata.get("venue") or metadata.get("fetch_mode") or "caller-supplied snapshot"
    fetched_at = metadata.get("fetched_at") or provenance.get("price_snapshot_retrieved_at")
    license_name = metadata.get("source_license")
    mean_mae = mean_mae_by_model(evaluation)
    models = ("naive", "price_only", "sentiment_price")

    def metric(value: float | None, digits: int = 2) -> str:
        return "unavailable" if value is None else f"{value:,.{digits}f}"

    def strategy_cell(model: str, key: str) -> str:
        result = evaluation.strategies.get(model)
        if result is None:
            return "unavailable"
        return metric(result.metrics.get(key), 3)

    mae_rows = "".join(
        "<tr>"
        f"<th scope=\"row\">{escape(model.replace('_', ' '))}</th>"
        f"<td>{metric(mean_mae.get(model))} {escape(currency)}</td>"
        "</tr>"
        for model in models
    )
    strategy_rows = "".join(
        "<tr>"
        f"<th scope=\"row\">{escape(model.replace('_', ' '))}</th>"
        f"<td>{strategy_cell(model, 'sharpe_ratio')}</td>"
        f"<td>{strategy_cell(model, 'sortino_ratio')}</td>"
        f"<td>{strategy_cell(model, 'max_drawdown')}</td>"
        "</tr>"
        for model in models
    )
    forecast_rows = "".join(
        "<tr>"
        f"<th scope=\"row\">{escape(item.horizon)}</th>"
        f"<td>{escape(item.model.replace('_', ' '))}</td>"
        f"<td>{metric(item.predicted_close)} {escape(currency)}</td>"
        f"<td>{metric(item.change_vs_reference * 100)}%</td>"
        "</tr>"
        for item in outlook.predictions
    )
    sentiment_text = (
        f"{dataset_summary.scored_posts} posts scored across "
        f"{dataset_summary.rows_with_sentiment} cutoffs."
        if dataset_summary.scored_posts
        else "No posts were scored. Sentiment is unavailable, not neutral."
    )
    license_text = (
        f"Source license: {escape(str(license_name))}. See ATTRIBUTION.md when present."
        if license_name
        else "Source license: not recorded in the input snapshot."
    )
    links = " | ".join(
        f'<a href="{name}">{label}</a>'
        for name, label in (
            ("evaluation-report.md", "Evaluation report"),
            ("outlook.md", "One-page outlook"),
            ("metrics.json", "Metrics JSON"),
            ("predictions.jsonl", "Predictions JSONL"),
        )
    )
    safe_svg = chart_svg if "<svg" in chart_svg and "</svg>" in chart_svg else (
        "<p>Chart unavailable: the SVG artifact is missing or invalid.</p>"
    )
    return f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{escape(asset)} forecast dashboard</title>
<style>
:root {{ color-scheme: light; font-family: Inter, ui-sans-serif, system-ui, sans-serif; color: #172033; background: #f4f6fa; }}
body {{ margin: 0; }} main {{ max-width: 1120px; margin: auto; padding: 2rem 1.25rem 3rem; }}
header {{ display: flex; justify-content: space-between; align-items: end; gap: 1rem; flex-wrap: wrap; }}
h1 {{ margin: 0; font-size: clamp(1.8rem, 4vw, 2.8rem); }} h2 {{ font-size: 1.15rem; margin-top: 0; }}
.muted {{ color: #5b6577; }} .grid {{ display: grid; grid-template-columns: repeat(auto-fit,minmax(190px,1fr)); gap: 1rem; margin: 1.5rem 0; }}
.card, section {{ background: white; border: 1px solid #dce2eb; border-radius: 12px; padding: 1rem 1.1rem; }}
.card strong {{ display: block; font-size: 1.4rem; margin-top: .35rem; }} section {{ margin: 1rem 0; overflow-x: auto; }}
.status {{ border-left: 5px solid #b45309; background: #fff7ed; padding: .9rem 1rem; border-radius: 6px; }}
table {{ border-collapse: collapse; width: 100%; }} th,td {{ text-align: left; padding: .65rem; border-bottom: 1px solid #e7ebf1; }}
thead {{ background: #f4f6fa; }} a {{ color: #2459a6; }} footer {{ padding-top: 1rem; font-size: .9rem; }}
@media (max-width:600px) {{ main {{ padding: 1rem .65rem 2rem; }} th,td {{ padding: .45rem .3rem; }} }}
</style>
</head>
<body><main>
<header><div><p class="muted">Price and sentiment research</p><h1>{escape(asset)} dashboard</h1></div>
<p class="muted">Generated {escape(generated_at.isoformat())}</p></header>
<p class="status"><strong>Sentiment status:</strong> {escape(sentiment_text)}</p>
<div class="grid">
<div class="card">Price cutoffs<strong>{dataset_summary.rows}</strong></div>
<div class="card">Full n+0…n+5 coverage<strong>{dataset_summary.rows_with_full_horizon}</strong></div>
<div class="card">Posts supplied / scored<strong>{dataset_summary.posts} / {dataset_summary.scored_posts}</strong></div>
<div class="card">Cutoffs with sentiment<strong>{dataset_summary.rows_with_sentiment}</strong></div>
</div>
<section><h2>Observed price and sentiment panels</h2>{safe_svg}</section>
<section><h2>Walk-forward mean forecast error</h2>
<p class="muted">Mean MAE across the six horizons. Lower is better; sentiment is not identifiable when no posts were scored.</p>
<table><thead><tr><th scope="col">Model</th><th scope="col">Mean MAE</th></tr></thead><tbody>{mae_rows}</tbody></table></section>
<section><h2>Latest horizon outputs</h2>
<table><thead><tr><th scope="col">Horizon</th><th scope="col">Model</th><th scope="col">Predicted close</th><th scope="col">Change vs reference</th></tr></thead>
<tbody>{forecast_rows or '<tr><td colspan="4">No latest-cutoff predictions available.</td></tr>'}</tbody></table></section>
<section><h2>Out-of-sample strategy risk</h2>
<p class="muted">Sample-specific strategy metrics, not forecast accuracy or investment advice.</p>
<table><thead><tr><th scope="col">Model</th><th scope="col">Sharpe</th><th scope="col">Sortino</th><th scope="col">Max drawdown</th></tr></thead><tbody>{strategy_rows}</tbody></table></section>
<section><h2>Source and freshness</h2><p>Provider/source: {escape(str(source))}</p>
<p>Quote currency: {escape(currency)} · Bars: {dataset_summary.rows} · Retrieved: {escape(str(fetched_at or 'not supplied'))}</p>
<p>{license_text}</p></section>
<footer>{links}</footer>
</main></body></html>
'''
