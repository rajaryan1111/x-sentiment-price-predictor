# Demo walkthrough (5–7 minutes)

This script is for an internship evaluator. Every command below was verified on
2026-10-28 from a clean Python 3.11 virtual environment on branch
`arena/cf79e7b7-x-sentiment-price-predictor`. The demonstration uses **explicitly
synthetic** data and mocked provider tests. It does not use live X, Tavily, Exa,
Apify or Coinbase data, and it makes no claim about real forecasting performance.

## Before the demo

```bash
git clone https://github.com/rajaryan1111/x-sentiment-price-predictor.git
cd x-sentiment-price-predictor
git checkout arena/cf79e7b7-x-sentiment-price-predictor
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev,storage]'
```

Keep `README.md`, `ARCHITECTURE.md` and this file open. Generated demo files go to
`reports/generated/`, which is ignored by Git.

---

## 0:00–0:45 — Problem statement

**Say:** “The assignment asks whether X sentiment adds out-of-sample predictive
value beyond price-only baselines for BTC-USD daily closes at `n+0` through
`n+5`. The honest answer in this repository is that the software can test it, but
no licensed real X corpus was available, so no sentiment improvement is claimed.”

**Show:** [README.md](../README.md) status box and
[FINAL_REQUIREMENTS_AUDIT.md](FINAL_REQUIREMENTS_AUDIT.md) status summary.

---

## 0:45–1:30 — Architecture

**Say:** “Inputs keep event time separate from first-observed time. Features are
computed at UTC cutoffs from completed bars and available posts only. Three models
are evaluated on identical purged walk-forward folds. News is a separate,
context-only input and never enters the feature matrix.”

**Show:** the architecture flow in [SUBMISSION_SUMMARY.md](SUBMISSION_SUMMARY.md)
or [ARCHITECTURE.md](../ARCHITECTURE.md).

---

## 1:30–2:15 — Verification baseline

```bash
pytest
ruff check src tests scripts
python scripts/validate_docs.py
python scripts/validate_dataset_registry.py
```

**Expected:** on 2026-10-28, the full offline suite passes with 167 tests; Ruff
reports “All checks passed!”; the docs validator reports valid links/requirement
rows; the registry validator reports 12 records. [TEST_PLAN.md](../TEST_PLAN.md)
is the authoritative current test count.

**Say:** “CI runs these same four checks on every push to the working branch.
CI is evidence of code health, not of data access or profitability.”

---

## 2:15–3:00 — Dataset ingestion and provenance

```bash
python scripts/make_offline_demo.py \
  --out reports/generated/offline-demo-inputs/prices.json \
  --posts-out reports/generated/offline-demo-inputs/posts.jsonl \
  --generated-at 2026-10-27T00:00:00+00:00
python -c "import json; p=json.load(open('reports/generated/offline-demo-inputs/prices.json')); print(p['synthetic'], p['fetch_mode'], len(p['candles']), p['recommended_now'])"
python -m xsentiment fetch-news --help
```

**Expected:** `True synthetic_offline_demo 210 2026-07-30T00:00:00+00:00` and CLI
help listing `--query`, `--max-results`, `--out` and `--confirm-live-call`.

**Say:** “These bars and posts are labelled synthetic. The generator is
deterministic, so a reviewer can reproduce the exact inputs. `fetch-news --help`
makes no network request; a real Tavily call would require an approved key and the
explicit confirmation flag, which we do not run.”

Also mention the historical real-price path: `reports/btc-usd-180d/manifest.json`
records 180 public Coinbase daily bars and the input SHA-256 from 2026-10-26. That
snapshot is not committed and cannot be refetched from this sandbox.

---

## 3:00–3:45 — Sentiment, features and leakage rules

**Show:** `src/xsentiment/features/sentiment.py`, `features/dataset.py` and
`pipeline/phase2.py`.

**Say:** “VADER produces a versioned post-level score. Daily aggregates are built
from the trailing `(cutoff - 24h, cutoff]` window using posts both published and
first observed by the cutoff. Missing sentiment stays null, not zero. Price
features use completed bars only. Targets are six future closes and are never
inputs. The unfinished current UTC day is dropped.”

**Optional proof command:**

```bash
python -m pytest tests/unit/test_dataset.py tests/unit/test_walk_forward.py -q
```

**Say:** “Those tests cover window boundaries, late/future posts, unfinished days,
target completeness and purged folds.”

---

## 3:45–4:45 — Forecast generation and model evaluation

```bash
python -m xsentiment run \
  --prices reports/generated/offline-demo-inputs/prices.json \
  --posts reports/generated/offline-demo-inputs/posts.jsonl \
  --out reports/generated/offline-demo \
  --now 2026-07-30T00:00:00+00:00 \
  --input-note "synthetic offline demo from scripts/make_offline_demo.py"
```

**Expected:** a run directory, mean MAE by model, strategy metrics and a report
path. The numbers are synthetic demonstration values only.

**Say:** “One command trains naive, price-only and sentiment-plus-price models for
all six horizons on identical expanding folds. `--input-note` is recorded in the
manifest and in report/outlook limitations so the synthetic inputs cannot be
mistaken for observed data.”

---

## 4:45–5:30 — Inspect real application artefacts

```bash
ls -lh reports/generated/offline-demo
python - <<'PY'
import json
from pathlib import Path
out = Path("reports/generated/offline-demo")
manifest = json.loads((out / "manifest.json").read_text())
metrics = json.loads((out / "metrics.json").read_text())
print("folds:", len(manifest["evaluation"]["folds"]))
print("predictions:", manifest["evaluation"]["predictions"])
print("horizons:", manifest["evaluation"]["assumptions"]["horizons"])
print("models:", sorted(metrics["mean_mae_by_model"]))
print("metric rows:", len(metrics["forecast_metrics"]))
print("synthetic price:", manifest["input_lineage"]["price"]["synthetic"])
print("sentiment cutoffs:", manifest["dataset"]["rows_with_sentiment"])
print("query modes:", manifest["input_lineage"]["queries"]["modes"])
PY
head -n 12 reports/generated/offline-demo/predictions.jsonl
```

**Expected:** six non-empty artefacts; six horizons `n+0`..`n+5`; three model
names; 18 finite per-horizon metric rows; a positive prediction count; synthetic
price lineage and non-empty sentiment coverage.

**Say:** “Predictions and metrics are produced by the application, not hand
written. `input_lineage` records source, window, schema, retrieval, query modes
and synthetic flags without storing raw query terms or secrets.”

---

## 5:30–6:15 — Visualization, outlook and risk reporting

```bash
grep -n '^##' reports/generated/offline-demo/evaluation-report.md
grep -n -A8 'Uncertainty and limitations' reports/generated/offline-demo/outlook.md
grep -o 'Day-over-day change[^<]*' reports/generated/offline-demo/sentiment-vs-price.svg | head -1
```

**Expected:** report sections include out-of-sample metrics, trading strategy and
risk metrics, current outlook and limitations; the outlook includes explicit
synthetic limitations; the SVG includes the day-over-day sentiment-change panel.

**Say:** “The report separates forecast-error metrics from strategy risk metrics.
Sharpe, Sortino and max drawdown come only from out-of-sample net returns after
disclosed fees, and unavailable ratios carry a reason. The chart shows price,
sentiment level and sentiment change; empty panels would be labelled rather than
fabricated.”

Then show the historical real-price report:

```bash
sed -n '1,30p' reports/btc-usd-180d/evaluation-report.md
```

**Say:** “This is the committed 2026-10-26 real-price run. Naive MAE $1,828.36
beat price-only Ridge $2,264.62. Sentiment-plus-price is identical because there
were zero posts, and the report says it is not identifiable. That negative result
is reported rather than hidden.”

---

## 6:15–7:00 — News separation, limitations and conclusion

```bash
python -m pytest tests/unit/test_fetch_news_cli.py tests/integration/test_offline_demo.py -q
```

**Say:** “The news CLI tests use mocked HTTP. They prove that a live call is
blocked without `--confirm-live-call`, credentials come from the environment,
errors and caller notes are redacted, oversized responses are rejected while
streaming, JSONL can be loaded by `run --news-file`, and adding news context
leaves predictions and metrics byte-identical. A separate regression blocks
network access during the offline CLI run. No live Tavily or Exa call was made.”

**Close with:**

- Engineering pipeline: complete and reproducible offline, with CI evidence.
- Real X sentiment verdict: **not measurable** without an accepted licensed
  180-day corpus, approved Actor/credentials and spend authorization.
- Live news: implemented but unverified live; mocked only.
- Submission: repository, report, audit, verification evidence and demo are
  ready; email delivery and employer clarifications are external.

**Show:** [EXTERNAL_BLOCKERS.md](EXTERNAL_BLOCKERS.md),
[EMPLOYER_CLARIFICATIONS.md](EMPLOYER_CLARIFICATIONS.md) (consolidated questions
and unsent email draft) and
[FINAL_VERIFICATION_REPORT.md](FINAL_VERIFICATION_REPORT.md).

## Commands deliberately not demonstrated

Do **not** run these in the timed demo:

```bash
# Requires an approved key, spend authorization and a real provider call:
python -m xsentiment fetch-news --query "BTC news" --out news.jsonl --confirm-live-call

# Requires outbound Coinbase network access; the offline demo replaces it:
python -m xsentiment fetch-prices --start 2026-04-29 --end 2026-10-26 --out prices.json
```

The first would initiate a potentially paid request; the second needs a network
host unavailable in the verification sandbox. Neither is needed to evaluate the
software pipeline.
