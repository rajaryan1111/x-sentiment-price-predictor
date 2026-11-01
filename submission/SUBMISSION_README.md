# X Sentiment Price Predictor — internship submission

**Candidate project:** `rajaryan1111/x-sentiment-price-predictor`
**Assessment PR (draft, not merged):** <https://github.com/rajaryan1111/x-sentiment-price-predictor/pull/14>
**Assessment recipient:** gilad@crowdwisdomtrading.com
**Package date:** 2026-11-01

## What this project is

A reproducible Python research pipeline that tests whether timestamped
X/Twitter sentiment adds out-of-sample predictive value beyond price-only
baselines for the BTC-USD daily close at six horizons (`n+0` through `n+5`).

The pipeline is implemented end to end: bounded provider adapters, normalized
provenance-safe records, point-in-time alignment, deterministic VADER scoring,
predeclared price/sentiment features, three models (naive persistence, price-only
ridge, sentiment-plus-price ridge) on identical purged walk-forward folds,
per-horizon MAE/RMSE, a predeclared long/flat strategy with Sharpe/Sortino/max
drawdown, a database join, a chart matrix, a one-page outlook, an evaluation
report and a run manifest.

**Honest headline (verified):** on the available 180-day real BTC-USD price
sample, with zero accepted X posts, the naive baseline **beat** the fitted
models on mean forecast MAE, and the sentiment-plus-price model was identical
to the price-only model because no scored posts existed. This submission
reports that result as measured; it does not claim sentiment adds predictive
value. The sentiment question is gated on an accepted 180-day X corpus, which
remains blocked on employer/provider authorization (see
[DATA_LIMITATIONS.md](DATA_LIMITATIONS.md)).

## Package contents

| File | Purpose |
| --- | --- |
| [SUBMISSION_README.md](SUBMISSION_README.md) | Overview, architecture, workflow, limitations |
| [REQUIREMENT_TRACEABILITY.md](REQUIREMENT_TRACEABILITY.md) | Requirement → code → evidence → status (28 IDs) |
| [EXPERIMENT_METHODOLOGY.md](EXPERIMENT_METHODOLOGY.md) | Data, features, models, validation, metrics |
| [RESULTS.md](RESULTS.md) | Verified results only, with sources |
| [DATA_LIMITATIONS.md](DATA_LIMITATIONS.md) | Availability assumptions, missing data, blockers |
| [REPRODUCIBILITY.md](REPRODUCIBILITY.md) | Exact setup, commands and reproduction steps |
| [DEMO_SCRIPT.md](DEMO_SCRIPT.md) | 5–7 minute evaluator walkthrough |
| [SUBMISSION_CHECKLIST.md](SUBMISSION_CHECKLIST.md) | Completed vs outstanding, and the unsent email draft pointer |
| [FINAL_EVALUATION_REPORT.md](FINAL_EVALUATION_REPORT.md) | Independent final-gate audit: coverage, verified evidence, defects fixed and the final verdict |
| [EMPLOYER_EMAIL_DRAFT.md](EMPLOYER_EMAIL_DRAFT.md) | Unsent ready-to-send clarification email (snapshot; canonical text in `docs/EMPLOYER_CLARIFICATIONS.md`) |

Canonical engineering documentation stays in the repository root
(`PRD.md`, `ARCHITECTURE.md`, `DESIGN.md`, `DATA_POLICY.md`, `MODEL_PLAN.md`,
`TEST_PLAN.md`, `RULES.md`, `PHASES.md`, `DECISIONS.md`) and `docs/`; this
package indexes and summarizes it without overriding it.

## Architecture

```text
environment configuration (.env placeholders only; secrets stay outside Git)
        ↓
bounded adapters (Coinbase prices; optional Apify X; gated Tavily news)
        ↓
normalized records + provenance + payload hashes (event time ≠ first-observed time)
        ↓
optional persisted storage (SQLAlchemy)  ←→  file snapshots (JSON/JSONL + SHA-256)
        ↓
UTC point-in-time alignment, deduplication, unfinished-day drop
        ↓
VADER sentiment + price features + n+0..n+5 close-ratio targets (targets never in features)
        ↓
naive / price-only / sentiment-plus-price models — one model per horizon
        ↓
purged expanding walk-forward evaluation → long/flat strategy simulation → risk metrics
        ↓
SVG chart matrix + one-page outlook + Markdown evaluation report + manifest/metrics/predictions
```

Components: `src/xsentiment/ingestion/` (prices, apify_x, tavily_news,
contracts, local profiling), `src/xsentiment/features/`,
`src/xsentiment/models/`, `src/xsentiment/validation/walk_forward.py`,
`src/xsentiment/backtesting/`, `src/xsentiment/storage/`,
`src/xsentiment/reporting/`, and the `src/xsentiment/main.py` CLI.
Stack: Python 3.11, `httpx`, `pydantic[-settings]`, `vaderSentiment`;
optional `SQLAlchemy`/`aiosqlite` storage; `pytest`/`ruff` for QA; dependency-free
SVG charts.

## Execution at a glance

```bash
python -m xsentiment run --prices <prices.json> --posts <posts.jsonl> --out <dir>
```

produces `manifest.json`, `metrics.json`, `predictions.jsonl`,
`evaluation-report.md`, `outlook.md` and `sentiment-vs-price.svg`. Full
reproduction steps, including the labelled synthetic demo, are in
[REPRODUCIBILITY.md](REPRODUCIBILITY.md).

## Status summary (evidence-based)

- **Implemented and offline-verified:** all R1–R15 engineering paths that do not
  require a live X Actor or paid provider call — see
  [REQUIREMENT_TRACEABILITY.md](REQUIREMENT_TRACEABILITY.md).
- **Verified on real data:** the historical BTC-USD price run (180 public
  Coinbase daily bars, 2026-04-29 → 2026-10-25 UTC) with its committed manifest,
  metrics, chart, outlook and evaluation report.
- **Not yet demonstrated:** a genuine sentiment-versus-price comparison on
  accepted real X posts (R2/R9), a live Apify or Tavily call, and the email
  submission itself.
- **Overall verdict:** see [SUBMISSION_CHECKLIST.md](SUBMISSION_CHECKLIST.md).

## Top limitations

1. No accepted, licensed 180-day X corpus or live Apify Actor run exists; R2 is
   externally blocked, so sentiment features are null in the historical run and
   the sentiment model is not identifiable.
2. The `n+0` target convention and the exact calendar deadline are working
   defaults pending employer confirmation.
3. Live Tavily/Exa news has never been called; news is context-only and never a
   model feature.
4. The original assessment PDFs are absent from this checkout; requirement
   wording rests on the repository's recorded transcription with hashes.
