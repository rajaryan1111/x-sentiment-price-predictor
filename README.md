# X Sentiment Price Predictor

Research pipeline that tests whether timestamped X (Twitter) sentiment adds
out-of-sample predictive value beyond price-only baselines for Bitcoin daily
close forecasts at horizons `n+0` through `n+5`.

> **Current evidence:** the current report is freshly recomputed from 180
> checksum-verified Binance Vision BTCUSDT daily bars (USDT quote), with source
> archives, snapshot, per-row predictions and metrics included. No accepted X
> posts were available, so no sentiment conclusion is possible. Price-only mean
> MAE is worse than naive. Binance-derived data and reports are CC BY-NC-SA 4.0,
> attribution/share-alike, non-commercial only. No live Apify run occurred; one
> bounded Tavily and Exa news searches were live-checked; a single Exa CLI dispatch
> bug found during verification was fixed and regression-tested. No Apify run or
> Coinbase data fetch occurred. See [provider verification](docs/PROVIDER_VERIFICATION_2026-11-01.md).
> The original assignment and companion
> dataset-reference PDFs were re-opened on 2026-11-01 from user-provided copies
> outside Git; they are not included in the repository or ZIP. CI and offline
> tests prove software behavior, not data access, licensing, model quality, or
> profitability. See `submission/` for the exact final handoff and blockers.

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
gap and external blocker, checked by `python scripts/validate_docs.py`). It preserves page counts and hashes for the assessment PDFs, re-opened on 2026-11-01
from user-provided copies outside the repository; they are not committed or included in the ZIP.
The matrix covers the 12 dataset candidates and outstanding requirements, including
provider access (R2) and the email submission packet (A7). The database join (R15) is
recorded as verified complete offline.

## Delivery status

The final branch is `feat/availability-basis-and-preflight`; its URL is
<https://github.com/rajaryan1111/x-sentiment-price-predictor/tree/feat/availability-basis-and-preflight>.
The exact final commit, remote state, current PR status, and successful Actions
run are recorded in [submission/FINAL_HANDOFF.md](submission/FINAL_HANDOFF.md)
after the release push. PR #14 was open/draft on an older head when this audit
began; it is advanced only by a normal fast-forward if the final verified commit
remains its strict descendant. It is not merged into `main`.

## Quick start

Python 3.11+ (notably, a bare `python3` can be older than 3.11 on some hosts; use
`python3.11` there). The current verification and CI use Python 3.11:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev,storage]"   # same extras CI installs
# .env is optional; no credentials are needed for the offline demo or public prices
pytest
ruff check src tests scripts
python scripts/validate_dataset_registry.py
python scripts/validate_docs.py
```

Reproduce the current BTCUSDT evaluation from its licensed source archives:

```bash
# Data and all derivatives are CC BY-NC-SA 4.0, non-commercial only.
python scripts/build_binance_snapshot.py \
  --archives-dir reports/btcusdt-180d/source \
  --start 2026-05-05 --end 2026-11-01 \
  --out /tmp/btcusdt-180d-snapshot.json

# 2. run the full evaluation and write every artefact
python -m xsentiment run \
  --prices /tmp/btcusdt-180d-snapshot.json \
  --asset BTCUSDT \
  --out /tmp/btcusdt-180d-run \
  --min-train 60 --test-size 20 --embargo 5
```

Add `--posts posts.jsonl` (normalized post records) to include sentiment. Post
availability defaults to the leakage-safe `observed` rule: a post must have been
published and first retrieved by the cutoff. A historical archive scraped after
the fact is therefore excluded from every earlier cutoff. If such a retrospective
archive is explicitly approved, run with `--availability-basis archive_created_at
--availability-note "<disclosure>"`; the manifest, report and outlook then carry a
look-ahead limitation. The archive basis is never the default.

For multiple approved query batches, first merge their normalized JSONL files and
per-query manifests. Duplicates are collapsed by post ID only when their stable
event time, text and platform agree; the earliest retrieval time is kept and every
query origin is recorded in the sidecar. The optional `--posts-provenance` flag
binds that sidecar hash into the run manifest. This does not make a post collected
later available at an earlier cutoff. See [Apify X setup](docs/APIFY_X_SETUP.md).

```bash
python scripts/merge_apify_x_posts.py \
  --posts data/apify-x-ticker.jsonl \
  --posts data/apify-x-cashtag.jsonl \
  --posts data/apify-x-keyword.jsonl \
  --run-manifest reports/generated/apify-x-ticker/manifest.json \
  --run-manifest reports/generated/apify-x-cashtag/manifest.json \
  --run-manifest reports/generated/apify-x-keyword/manifest.json \
  --out data/apify-x-merged.jsonl \
  --manifest-out reports/generated/apify-x-merged/manifest.json

python -m xsentiment run --prices prices.json \
  --posts data/apify-x-merged.jsonl \
  --posts-provenance reports/generated/apify-x-merged/manifest.json \
  --out reports/generated/x-sentiment-run
```

News is a deliberately separate, two-step workflow: `fetch-news` makes one
explicitly confirmed provider request, and `run --news-file` is entirely offline.
The `fetch-prices` path is a legacy Coinbase adapter; do not use Coinbase data for
ML evaluation or distribute its derivatives without prior written permission.

```bash
# Inspect the gated command; --help makes no provider request.
python -m xsentiment fetch-news --help

# Only after authorizing one provider call and setting TAVILY_API_KEY or EXA_API_KEY in the
# environment or a local, ignored .env file. The flag is mandatory; there is no
# --api-key argument and the adapter performs one bounded streaming request
# with an enforced response ceiling and no retry.
python -m xsentiment fetch-news \
  --provider tavily --topic finance \
  --start-date 2026-10-26 --end-date 2026-11-01 \
  --query "Bitcoin BTC market news" \
  --max-results 5 \
  --out data/news-context.jsonl \
  --confirm-live-call

# Consume the resulting JSONL offline. News appears in the outlook only.
python -m xsentiment run \
  --prices data/btc-usd-daily-2026-04-29_2026-10-25.json \
  --news-file data/news-context.jsonl \
  --out reports/btcusdt-180d-with-news \
  --now 2026-10-26T00:00:00+00:00
```

Each JSONL line carries `title`, `url`, `published_at` (or an explicit note when the
provider omits it), `retrieved_at`, `source`, `provider`, `payload_sha256`, `query`
and a rendered `context_line`. Credentials are never written to the file, logged or
passed on the command line. One bounded Tavily finance request returned one result
whose malformed publication timestamp was withheld; one bounded Exa request
returned one result with a publication timestamp and source metadata. These were
single live smoke checks, not a quality or coverage assessment. News remains
context-only. See the [provider verification report](docs/PROVIDER_VERIFICATION_2026-11-01.md)
for the exact commands and limitations.

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
  --out reports/btcusdt-180d-persisted \
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

Each run writes `dashboard.html`, `evaluation-report.md`, `outlook.md`,
`sentiment-vs-price.svg`, `metrics.json`, `predictions.jsonl` and `manifest.json`
(code revision, config, hashes, input lineage, counts and warnings).

### Fully offline demonstration (synthetic inputs)

No network, credentials or accepted X corpus is needed for this walkthrough. The
generator writes deterministic, **explicitly labelled synthetic** daily bars and
posts; the resulting metrics demonstrate the software only and must never be
reported as real BTC-USD or X evidence.

```bash
python scripts/make_offline_demo.py \
  --out reports/generated/offline-demo-inputs/prices.json \
  --posts-out reports/generated/offline-demo-inputs/posts.jsonl \
  --generated-at 2026-10-27T00:00:00+00:00

python -m xsentiment run \
  --prices reports/generated/offline-demo-inputs/prices.json \
  --posts reports/generated/offline-demo-inputs/posts.jsonl \
  --out reports/generated/offline-demo \
  --now 2026-07-30T00:00:00+00:00 \
  --input-note "synthetic offline demo from scripts/make_offline_demo.py"
```

Inspect `reports/generated/offline-demo/dashboard.html`,
`evaluation-report.md`, `outlook.md`, `sentiment-vs-price.svg`, `metrics.json`,
`predictions.jsonl` and `manifest.json`.
The generated paths are ignored by Git. `tests/integration/test_offline_demo.py`
executes the same CLI and validates every artefact and deterministic repeatability.

## What the pipeline does

1. **Ingest** — validated UTC OHLCV candles and normalized X post records that keep
   event time and first-observed time distinct. The current reproducible price path
   uses the checksum-verified Binance Vision BTCUSDT archives; the Coinbase adapter
   is legacy and subject to the restriction above.
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
7. **Report** — standalone offline HTML dashboard, chart, one-page outlook and evaluation report that label observed
   facts, method, measured results and unavailable items separately.

## Recomputed price-only evidence (2026-11-01)

The current `reports/btcusdt-180d/` package contains 180 checksum-verified Binance
Vision BTCUSDT daily candles for 2026-05-05 through 2026-10-31 UTC, the exact
normalized snapshot, source archives, per-row predictions, metrics, report,
outlook and SVG. Quote values are USDT, not USD. The archive builder is
`scripts/build_binance_snapshot.py`; the documented walk-forward command is in
`submission/REPRODUCIBILITY.md`.

Across five chronological folds and 100 out-of-sample samples per horizon, mean
MAE is 1,824.23 USDT for naive persistence and 2,378.50 USDT for price-only ridge.
Zero X posts were supplied, so sentiment-plus-price is not identifiable and does
not evidence a sentiment effect. The price-only strategy's Sharpe is 1.124,
Sortino 2.431 and maximum drawdown 5.885% under the documented strategy rules.
These are sample-specific research figures, not claims of future accuracy or
profitability. Binance Vision source data and derived artefacts are licensed under
CC BY-NC-SA 4.0, require attribution/share-alike, and are non-commercial only; see
`reports/btcusdt-180d/ATTRIBUTION.md`.

Older Coinbase-derived evaluation artifacts were removed from the current tree
after the source terms review. They remain in earlier Git history; no history was
rewritten. Do not reuse those artifacts without prior written consent.

**Source audit:** the assignment PDF and companion dataset-reference PDF were
re-opened and read in full on 2026-11-01; hashes and page counts are in the
[traceability matrix](docs/REQUIREMENTS_TRACEABILITY.md). Their copies are outside
the repository and not included in the submission ZIP. The linked Google Doc was
reviewed as a 12-entry dataset-link compilation, not a tweet corpus. No candidate
X dataset has been approved, licensed, downloaded or profiled as an accepted
180-day corpus.

## Module map

- `src/xsentiment/config/` — validated environment-backed settings.
- `src/xsentiment/ingestion/` — provider-neutral contracts, bounded HTTP boundary,
  legacy Coinbase adapter, Apify X adapter, Tavily/Exa news adapters, and local profiler.
- `src/xsentiment/pipeline/phase2.py` — coverage profiling, deduplication,
  point-in-time features, horizon labels.
- `src/xsentiment/features/` — sentiment scoring, price features, supervised dataset.
- `src/xsentiment/models/` — naive baseline, ridge forecasting, walk-forward evaluation.
- `src/xsentiment/validation/` — purged chronological fold generation.
- `src/xsentiment/backtesting/` — forecast/risk metrics and the long/flat strategy.
- `src/xsentiment/reporting/` — standalone HTML dashboard, SVG charts, one-page outlook, evaluation report.
- `src/xsentiment/pipeline/forecast_run.py` — offline end-to-end run and artefacts.
- `src/xsentiment/storage/` — versioned `price_bars`/`x_posts` tables, idempotent
  upserts and descriptive/cutoff joins, tested with in-memory SQLite; `xsentiment
  persist` and `xsentiment run --database-url` evaluate from persisted rows
  (manifest records `input_source = persisted_storage`); verified offline.
- `src/xsentiment/main.py` — `fetch-prices`, `fetch-news`, `persist` and `run` CLI
  entry points; `fetch-news` is gated and `run` is offline.
- `scripts/validate_docs.py` — Phase 1 documentation validator: link resolution,
  unique requirement IDs, matrix completeness and status-summary consistency.
- `scripts/make_offline_demo.py` — deterministic, explicitly synthetic price/post
  snapshots for a no-credential, no-network end-to-end demonstration.
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
  feature policy; see [DECISIONS.md](DECISIONS.md) D-005. The bounded adapter
  (`src/xsentiment/ingestion/tavily_news.py`) is reachable only through
  `xsentiment fetch-news --confirm-live-call`, reads `TAVILY_API_KEY` from the
  environment, performs one bounded streaming request with an enforced response ceiling
  and no automatic retry, and writes normalized JSONL. `run --news-file` consumes that file offline and records its
  hash and context-only policy in the manifest. Both steps are verified against
  mocked HTTP transports only; no live call has been made, so live provider behaviour
  is unverified.

## Branch strategy

- `main` — stable integration branch.
- `feat/phase-2-data-quality-alignment` — price/post ingestion, profiler, point-in-time primitives.
- `docs/canonical-source-of-truth` — the nine canonical documents.
- `feat/availability-basis-and-preflight` — current reviewed submission branch, including the forecasting pipeline, preflight and bounded ingestion work.

Feature work is merged through review after lint, registry validation, documentation
validation and pytest pass, as configured in [.github/workflows/ci.yml](.github/workflows/ci.yml).
