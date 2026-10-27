# Test Plan
A passing suite proves only the cases it actually exercises. The current suite is
**167 offline tests, all passing** (`pytest` -> `167 passed`, 0 failed, 0 skipped,
0 xfailed), last run on 2026-10-28 UTC in a clean Python 3.11.2 virtual environment
installed with `pip install -e '.[dev,storage,analysis]'`. CI runs the same command
set on Python 3.11, which is the supported baseline in `pyproject.toml`, with the
`dev` and `storage` extras; the offline pipeline itself needs no analysis extras.
CI runs lint, registry validation, documentation validation and pytest.

The suite collects 167 cases from 165 test functions across 22 modules in
`tests/unit/` and `tests/integration/`: one function is parametrized into three cases.
The checkpoint revision (commit `5af5bc7`) had 152 tests; nine added in
`test_fetch_news_cli.py` cover the gated news CLI, four added in
`tests/integration/test_offline_demo.py` cover deterministic synthetic input
generation, snapshot metadata allow-listing, mocked `fetch-prices` retrieval
metadata and a complete offline CLI run with artefact validation and repeatability,
one added in `test_tavily_news.py` proves the response ceiling is enforced while
streaming, and one added in `tests/integration/test_offline_demo.py` blocks network
access during an offline run. Earlier figures (149, 152, 161, 165) are historical
results for their own revisions.

**This file is the single authoritative source for the current count.** Counts quoted
elsewhere in the repository must be tied to a date or a commit and are historical
results for that revision. `scripts/validate_docs.py` enforces that rule, and
`tests/unit/test_docs_validation.py` asserts that the number stated above equals what
`pytest` actually collects, so the two can no longer drift apart silently.

## Layers
- Unit: validation, timestamps, deduplication, price coverage, sentiment scoring,
  price features, dataset assembly, fold generation, models, metrics, strategy,
  evaluation, chart/outlook/report rendering, input loaders.
- Adapter contracts: mocked provider responses, pagination, timeout/error behaviour,
  normalization and secret redaction; no billing and no live provider call. The
  Tavily adapter is exercised both directly and through `fetch-news` with an
  `httpx.MockTransport`, including one-request-only and oversized-response cases.
- Integration: the pipeline is exercised end to end in memory with synthetic snapshots.
  `tests/unit/test_storage_join.py` uses an in-memory SQLite database and exercises
  idempotent upserts plus both joins. The run CLI's use of persisted data **is** covered,
  in `tests/unit/test_phase3_ingestion_e2e.py`: `test_bounded_end_to_end_ingestion_persists_and_joins`
  drives a mocked Apify adapter through normalization into a real on-disk SQLite file and
  then through the leakage-safe cutoff join, and `test_run_cli_consumes_the_persisted_inputs`
  runs `xsentiment run --database-url` to completion on those persisted rows and asserts the
  manifest records `input_source = persisted_storage`. These remain fixture/mock based: they
  do not prove a production PostgreSQL deployment, and they do not prove acceptance of any
  real X corpus.
- End-to-end: `tests/integration/test_offline_demo.py` generates deterministic,
  explicitly labelled synthetic price/post snapshots, drives the real `run` CLI,
  validates every artefact (manifest lineage, six horizons, three models, finite
  metrics, prediction records, chart/outlook/report sections) and proves a repeat
  run produces byte-identical predictions and metrics. A separate regression blocks
  socket and HTTP client entry points during an offline run, so a future accidental
  network request fails the suite. A separately documented historical real-data run
  uses public Coinbase candles; it is not refetched in CI.
- CI: Ruff, registry structural validation, documentation validation (`scripts/validate_docs.py`)
  and pytest. No network call is made by the suite; `fetch-prices` is exercised manually,
  not in CI.
- Documentation: Markdown link resolution, unique requirement IDs and traceability-matrix
  completeness are checked by the same validator, including that the status summary in the
  matrix matches its own rows.

## Required matrix
- Config: missing/invalid config and caps fail clearly; secrets never logged.
- X records: valid/missing optional fields, empty or missing text, invalid IDs/timestamps,
  naive timestamp rejection, negative counts, out-of-range sentiment.
- Point-in-time: future event excluded; late-retrieved post excluded even if old; no
  backdating; unfinished current UTC day dropped from features and labels.
- Deduplication: stable-ID exact duplicate handled deterministically; conflicting
  duplicate fails closed.
- Prices: UTC half-open bounds, ordering, malformed OHLCV, invalid OHLC relation,
  duplicates, out-of-range rows, missing dates, incomplete current day.
- Alignment: UTC boundary cases and the trailing 24-hour window, including that a post
  created exactly at `cutoff - 24h` is excluded and a post created or retrieved exactly
  at the cutoff is included. (Exact half-open window boundaries.)
- Sentiment: scores stay inside [-1, 1] and keep their sign, blank text returns null,
  scoring reports post/scored/unscored counts, the scorer records a version, non-string
  text fails closed with `TypeError`, unicode text is scored without crashing, and
  scoring is identical across repeat runs.
- Features: every declared feature name is always present, short history yields null
  rather than zero, known values match hand-computed ones, and values are computed from
  completed candles only.
- Dataset: labels exist only with a complete gap-free horizon; the cutoff candle's own
  close never appears in its features; rows with missing sentiment keep null.
- Folds: expanding windows, purge gap equals the longest horizon, empty result when
  history is too short, invalid configuration fails closed, leaking folds rejected.
- Models: naive persistence returns the last completed close; ridge recovers a known
  linear relationship; imputation and standardisation use training statistics only; an
  unobserved feature carries zero weight; the price-only model's feature list contains
  no sentiment column; the candidate model's does.
- Metrics: MAE/RMSE/mean error known values; equity curve and drawdown on a known path;
  Sharpe and Sortino closed-form checks; degenerate series return `None`; invalid input
  and non-finite values fail closed.
- Strategy: fee-charged long days, flat days earning zero, withheld risk metrics below
  the sample threshold, zero-dispersion reporting, assumption validation, disclosure text.
- Evaluation: all models scored on identical folds and rows with equal sample counts,
  purge gap measured in days, deterministic repeat runs, no test-fold row present in its
  own training block, warnings when sentiment is unidentifiable, and a stated reason when
  history is too short.
- Reporting: both chart panels render, an empty sentiment panel says so instead of
  drawing a fabricated curve, outlook coverage and limitations appear, the rendered
  outlook page meets the machine-checked one-page contract
  (`check_outlook_page`: required sections, line ceiling, disclaimer, explicit
  unavailable state on an empty prediction block), and the report
  separates measured tables from unavailable items and withheld metrics.
- Pipeline/CLI: input loaders reject malformed snapshots with line references, the run
  writes every documented artefact, manifest hashes match the inputs, prediction records
  match the manifest count, a zero-post run still completes, and CLI errors exit non-zero.
  `fetch-news` refuses a live request without `--confirm-live-call`, reads only
  `TAVILY_API_KEY`, and writes JSONL that `run --news-file` accepts. Matching runs with
  and without that file must produce byte-identical `predictions.jsonl` and
  `metrics.json`; only the outlook and report context may differ.
- Manifest provenance (NFR1): the run records the actual checked-out git revision
  automatically; missing git metadata records an explicit unavailable state with a
  reason; caller-supplied provenance is never silently overwritten; no secret is
  emitted.
- Apify: mocked run/status/dataset with the documented `data` envelope, auth header,
  bounds, timeouts/errors, no launch retry, and dataset offset/limit parameters;
  no real Actor in CI.
- Tavily news adapter: normalized headline/url/publication/retrieval/source plus
  payload hash under a strict response contract; empty results; malformed items
  excluded with reasons; duplicates removed; timeout and HTTP-error fail-closed;
  oversized bodies rejected; a missing API key raises an explicit, graceful error;
  error messages never contain the key or query secret. Mocked only: no live call,
  no billing, no network dependence in the suite.
- Registry: source/platform identity, text-availability vocabulary, ISO dates, date order,
  ID-only hydration caveats, recommended-source sanity, and that a rolling source without
  a coverage end must carry a coverage/cutoff limitation; validation does not imply live
  access or legal approval.
- Storage: in-memory SQLite tests cover one bar per product/UTC day,
  idempotent price/post upserts, earliest-retrieval retention, the descriptive same-day
  join's counts, and a cutoff join that excludes late-arriving and future posts and uses
  the prior completed close. `tests/unit/test_phase3_ingestion_e2e.py` additionally
  covers the persisted-input CLI integration: a bounded end-to-end ingest into a real
  SQLite file, the leakage-safe cutoff join over those rows, and a complete
  `xsentiment run --database-url` whose manifest records
  `input_source = persisted_storage`. They do not cover a production PostgreSQL
  deployment.
- Documentation: every relative Markdown link resolves; requirement IDs are unique and
  complete across the `R`, `NFR` and `A` namespaces; every matrix row has an acceptance
  criterion, an evidence pointer, a vocabulary status and a blocker entry.

## Data profile acceptance
Report row count, UTC min/max, required-window coverage/gaps, missing IDs/text/timestamps,
duplicates, invalid timestamps, engagement-field availability, provider/query/window/
retrieval time, version/run ID, terms-review status, hash if retained, and point-in-time
limitations. Never print raw text or credentials.

## Fixture policy
Unit and integration tests build clearly labelled synthetic series and records; no test
presents a fixture, mock or synthetic value as observed provider data. The only real-data
run committed to the repository is the public Coinbase price run documented in the README,
which contains no post text.

## Reproducibility
Record commit, non-secret config, seed, dataset version/hash, schema version and fold
boundaries. Re-run from a clean environment. Do not commit raw data to make tests pass.

## Release gates
Documentation: all nine canonical files agree; links/commands checked; statuses honest;
traceability matrix current.
Ingestion: terms and source verified, real profile exists, point-in-time limitations
documented, bounded end-to-end X ingest passes. **Unmet: no accepted X source yet.**
Model/report: baselines and sentiment model run; walk-forward is leakage-safe;
charts/outlook/report derive from actual outputs; risk metrics only from valid strategy
returns. **Met for prices; the sentiment comparison is blocked on X data.**
Storage: R15 schema, idempotent repositories and both joins have acceptance tests, and
the pipeline now consumes persisted inputs (`xsentiment persist`, run
`--database-url`), verified by `tests/unit/test_phase3_ingestion_e2e.py`. **Met offline
(on fixtures); a database holding real X rows remains blocked on R2.**

## Commands
From repo root:

```bash
python -m pip install -e ".[dev,storage]"
python -m pytest -q
ruff check src tests scripts
python scripts/validate_dataset_registry.py
python scripts/validate_docs.py
python -m compileall -q src tests scripts
git diff --check
```

Live-provider tests remain opt-in and must not run in ordinary CI.
