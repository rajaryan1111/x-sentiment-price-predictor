# X Sentiment Price Predictor

Research pipeline that tests whether timestamped X (Twitter) sentiment adds
out-of-sample predictive value beyond price-only baselines for **BTC-USD** daily
close forecasts at horizons `n+0` through `n+5`.

> **Status: prices, features, models, evaluation and reporting are implemented and
> verified on real public Coinbase data. X data access remains an open external
> gate.** No live X corpus has been accepted, no Apify Actor has been run, and no
> sentiment result is claimed. The database schema, idempotent repositories and
> cutoff join now exist and are unit-tested (R15 partial); the `run` CLI still
> joins file snapshots in memory. The two assessment PDFs were read in full on
> 2026-10-26; the linked Google Doc is a 12-entry dataset-link compilation, not a
> tweet corpus. The pipeline runs end to end today with zero posts and reports
> sentiment as unavailable rather than inventing it. CI passing is not evidence of
> data access, model quality or profitability.

## Canonical engineering documents

Read these before changing behaviour. They are the source of truth for scope,
contracts and status, and they list what is verified versus still open.

| Document | Purpose |
| --- | --- |
| [PRD.md](PRD.md) | Product objective, requirements and acceptance evidence |
| [ARCHITECTURE.md](ARCHITECTURE.md) | Components, data flow, failure handling, implementation status |
| [DESIGN.md](DESIGN.md) | Data contracts, timestamps, features, targets, output schemas |
| [DATA_POLICY.md](DATA_POLICY.md) | Source access, licensing, provenance, point-in-time and cost policy |
| [MODEL_PLAN.md](MODEL_PLAN.md) | Features, baselines, walk-forward design, risk-metric conditions |
| [TEST_PLAN.md](TEST_PLAN.md) | Required unit, integration, leakage and adapter coverage |
| [RULES.md](RULES.md) | Code quality, security, Git and reporting rules |
| [PHASES.md](PHASES.md) | Roadmap, phase status and completion gates |
| [DECISIONS.md](DECISIONS.md) | Every working default, rule and open question |

Phase 1 deliverable: the authoritative [requirements traceability matrix](docs/REQUIREMENTS_TRACEABILITY.md)
(every requirement with its acceptance criterion, verification method, evidence, status,
gap and external blocker, checked by `python scripts/validate_docs.py`). The matrix also
records the verified assignment PDFs (page counts and SHA-256), the 12 dataset candidates,and the requirements that remain partial, including provider access (R2) and the email
submission packet (A7). The database join (R15) is recorded as verified complete offline.

Supporting detail: [requirements traceability](docs/REQUIREMENTS_TRACEABILITY.md),
[Phase 1 requirements trace](docs/PHASE_1_REQUIREMENTS.md),
[historical dataset registry](docs/data-sources.md),
[Apify setup](docs/APIFY_X_SETUP.md),
[Phase 2 data-quality workstream](docs/PHASE_2_PROGRESS.md).

**Naming note:** the repository workstream labelled “Phase 2 data quality/alignment”
is not canonical documentation Phase 2. See [PHASES.md](PHASES.md).

## Quick start

Python 3.11+ (notably, a bare `python3` can be older than 3.11 on some hosts; use
`python3.12` or `python3.11` there). Verified across a fresh clone of this branch on
Python 3.11.15 and 3.12.4:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev,storage]"   # same extras CI installs
cp .env.example .env                        # required for fetch-prices; not needed for an existing snapshot
pytest
ruff check src tests scripts
python scripts/validate_dataset_registry.py
python scripts/validate_docs.py
```

Run the real pipeline on public BTC-USD daily candles (no credentials, no cost):

```bash
# 1. download a bounded, no-cost price snapshot (half-open [start, end) UTC range)
python -m xsentiment fetch-prices --start 2026-04-29 --end 2026-10-26 \
  --out data/btc-usd-daily-2026-04-29_2026-10-25.json

# 2. run the full evaluation and write every artefact
python -m xsentiment run \
  --prices data/btc-usd-daily-2026-04-29_2026-10-25.json \
  --out reports/btc-usd-180d \
  --now 2026-10-26T00:00:00+00:00
```

Add `--posts posts.jsonl` (normalized post records) to include sentiment, and
`--news-file news.jsonl` for contextual news lines that never enter the features.

Profile a local candidate corpus without printing post text or uploading it:

```bash
python scripts/profile_local_x_dataset.py /absolute/path/to/posts.csv --days 180 \
  --as-of 2026-10-26T00:00:00+00:00
# For non-standard field names, add --id-column, --text-column and --timestamp-column.
# Add --retrieved-column when the source has a first-observed/retrieval timestamp.
```

The profiler reports schema drift, duplicate/missing IDs, missing/invalid timestamps,
engagement-column coverage, malformed counts, daily gaps and whether the requested
calendar window is complete. A complete window is still not proof of point-in-time
availability, licensing or X platform identity.

Persist local snapshots into the storage database, then run the whole evaluation from
the persisted rows (the database file is ignored by Git and post text is never
printed; requires `pip install -e ".[storage]"` already present with the dev extras):

```bash
# populate the local database from snapshots; repeating this command is idempotent
python -m xsentiment persist \
  --prices data/btc-usd-daily-2026-04-29_2026-10-25.json \
  --posts posts.jsonl \
  --database-url sqlite+aiosqlite:///./data/xsentiment.db

# run the full evaluation from the persisted rows; the manifest records
# "input_source": "persisted_storage" and the source snapshot IDs
python -m xsentiment run \
  --database-url sqlite+aiosqlite:///./data/xsentiment.db \
  --out reports/btc-usd-180d-persisted \
  --now 2026-10-26T00:00:00+00:00

# optionally inspect the leakage-safe cutoff join as a JSON report
python scripts/persist_and_join.py \
  --prices data/btc-usd-daily-2026-04-29_2026-10-25.json \
  --posts posts.jsonl \
  --database-url sqlite+aiosqlite:///./data/xsentiment.db \
  --start 2026-04-30 --end 2026-10-25 --out data/cutoff-join.json
```

This is verified offline on fixtures (`tests/unit/test_phase3_ingestion_e2e.py`); a
database populated with real X rows is still blocked until R2 supplies an accepted,
permitted source.

Each run writes `evaluation-report.md`, `outlook.md`, `sentiment-vs-price.svg`,
`metrics.json`, `predictions.jsonl` and `manifest.json` (code revision, config,
hashes, counts, warnings).

## What the pipeline does

1. **Ingest** — validated Coinbase Exchange daily candles (Decimal OHLCV, UTC,
   half-open ranges, duplicate/malformed rejection) and normalized X post records
   that keep event time and first-observed time distinct.
2. **Align** — deduplicate by stable ID, aggregate posts over the trailing
   `(cutoff - 24h, cutoff]` window using only posts published *and* observed by the
   cutoff, and drop the unfinished current UTC day so partial bars cannot leak.
3. **Feature** — predeclared lagged/rolling price statistics plus sentiment
   aggregates (mean, positive/negative share, post and scored-post volume).
   Missing sentiment stays null; it is never treated as neutral.
4. **Target** — close labels for `n+0`..`n+5`, emitted only when the whole horizon
   exists and contains no gap; labels never enter the feature matrix.
5. **Model** — naive persistence, a price-only ridge model and a
   sentiment-plus-price ridge model fitted on ratio targets, on identical folds and
   eligible rows. Imputation and standardisation are fitted on training folds only.
6. **Evaluate** — expanding-window walk-forward folds with a purge gap equal to the
   longest horizon; per-horizon MAE/RMSE/sample counts plus a predeclared long/flat
   strategy whose out-of-sample returns yield Sharpe, Sortino and maximum drawdown
   under disclosed fees, annualisation and missing-data rules.
7. **Report** — chart, one-page outlook and evaluation report that label observed
   facts, method, measured results and unavailable items separately.

## Measured evidence (real data, 2026-10-26)

From `reports/btc-usd-180d/`, computed by the commands above:

- **Prices:** 180/180 public Coinbase `BTC-USD` daily bars, 2026-04-29 → 2026-10-25
  UTC, no missing or duplicate timestamps; unfinished current day excluded.
- **X posts:** 0. No permitted post-level dataset is accepted yet, so sentiment is
  reported unavailable and the candidate model is flagged as not identifiable.
- **Verified fresh-clone reproduction (2026-10-27):** a clean checkout of this branch,
  installed strictly from the committed `pyproject.toml` on Python 3.12.4, ran the 130
  offline tests, both validators and the documented commands above after refetching the
  public snapshot — whose SHA-256 matched the committed provenance exactly — and
  reproduced every metric within 5e-13 (platform float noise only). No credentials,
  paid services or network X calls are needed for this offline reproduction.
- **Mean MAE across horizons:** naive persistence **$1,828.36**, price-only ridge
  **$2,264.62** (+23.86% worse), sentiment-plus-price identical to price-only
  because no sentiment was available.
- **Strategy (predeclared long/flat, 10 bps per side):** price-only cumulative
  **+10.91%**, Sharpe **1.807**, Sortino **3.979**, max drawdown **4.08%** over 32
  long days, versus a +6.11% / 0.752 / 1.377 / 10.33% unconditional-long benchmark.
  The naive rule never trades, so its own risk ratios are undefined; the benchmark is the same windows held long.

**Honest reading:** on this 180-day sample the fitted price-only model does *not*
beat the naive persistence baseline on forecast error, so no claim is made that the
model adds predictive value. The strategy numbers are short-sample research
statistics on a single asset and period, not evidence of tradability.

**Source audit (2026-10-26):** both assessment PDFs were read in full. The linked
Google Doc is a dataset-link compilation matching the companion PDF, not a tweet
corpus. Uploaded local files contain tweet IDs, date/count summaries, unrelated
air-quality/MQTT data or a StockTwits paper; none contains X post text. No candidate
dataset has been accepted, licensed or profiled for 180-day text coverage.

## Module map

- `src/xsentiment/config/` — validated environment-backed settings.
- `src/xsentiment/ingestion/` — provider-neutral contracts, bounded HTTP boundary,
  Coinbase price adapter, configurable Apify X adapter, local CSV/JSONL profiler.
- `src/xsentiment/pipeline/phase2.py` — coverage profiling, deduplication,
  point-in-time features, horizon labels.
- `src/xsentiment/features/` — sentiment scoring, price features, supervised dataset.
- `src/xsentiment/models/` — naive baseline, ridge forecasting, walk-forward evaluation.
- `src/xsentiment/validation/` — purged chronological fold generation.
- `src/xsentiment/backtesting/` — forecast/risk metrics and the long/flat strategy.
- `src/xsentiment/reporting/` — SVG charts, one-page outlook, evaluation report.
- `src/xsentiment/pipeline/forecast_run.py` — offline end-to-end run and artefacts.
- `src/xsentiment/storage/` — versioned `price_bars`/`x_posts` tables, idempotent
  upserts and descriptive/cutoff joins, tested with in-memory SQLite; `xsentiment
  persist` and `xsentiment run --database-url` evaluate from persisted rows
  (manifest records `input_source = persisted_storage`); verified offline.
- `src/xsentiment/main.py` — `fetch-prices` and `run` CLI entry points.
- `scripts/validate_docs.py` — Phase 1 documentation validator: link resolution,
  unique requirement IDs, matrix completeness and status-summary consistency.
- `scripts/persist_and_join.py` — optional local persistence and cutoff-join report;
  requires the `storage` extra, makes no network call and prints no post text.
- `xsentiment persist` — the CLI form of the same persistence step; `xsentiment run
  --database-url` then evaluates from the persisted rows instead of file snapshots.
- `tests/` — offline unit tests; live provider calls are never made in CI.

## Data, security and evaluation rules

- Keep credentials, raw private X exports, hydrated text and large generated
  datasets out of Git; only sanitized snapshots, hashes and counts are committed.
- Preserve source IDs, event time, first-observed time and provenance; never
  backdate availability, and never fabricate bars, sentiment, counts or metrics.
- Sentiment scoring uses VADER (`vaderSentiment`, MIT) as a documented, versioned,
  offline baseline scorer; its limitations and replacement path are in
  [MODEL_PLAN.md](MODEL_PLAN.md) and [DECISIONS.md](DECISIONS.md).
- Compare against naive and price-only baselines before claiming any value from
  sentiment, and report risk metrics only from out-of-sample strategy returns.
- News (Tavily/Exa) stays context for the outlook unless a clarification changes the
  feature policy; see [DECISIONS.md](DECISIONS.md) D-005. A bounded Tavily adapter
  exists (`src/xsentiment/ingestion/tavily_news.py`, opt-in with `TAVILY_API_KEY`,
  context-only, never a model feature, no automatic retry) and is verified against
  mocked responses only; no live call has been made, so live provider behaviour is
  unverified.

## Branch strategy

- `main` — stable integration branch.
- `feat/phase-2-data-quality-alignment` — price/post ingestion, profiler, point-in-time primitives.
- `docs/canonical-source-of-truth` — the nine canonical documents.
- `feat/sentiment-features-and-forecasting` — sentiment, features, models, evaluation, reporting, CLI.

Feature work is merged through review after lint, registry validation, documentation
validation and pytest pass, as configured in [.github/workflows/ci.yml](.github/workflows/ci.yml).
