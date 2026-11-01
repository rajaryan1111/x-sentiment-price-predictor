# Product Requirements Document (PRD)
Status: current execution evidence is in [FINAL_EXECUTION_STATUS_2026-11-01.md](docs/FINAL_EXECUTION_STATUS_2026-11-01.md). A fresh, checksum-verified Binance Vision BTCUSDT price-only evaluation is packaged under `reports/btcusdt-180d/`; the quote currency is USDT and Binance's non-commercial share-alike terms apply. Coinbase-derived result artifacts have been removed from the current tree because Coinbase terms prohibit their use to train/validate/benchmark ML and their redistribution without prior written consent. Real X posts remain unavailable, so sentiment contribution is not evidenced.
Authority: the supplied CWT X sentiment Agent - intern task.pdf defines assignment requirements. This document translates them into testable requirements; it does not claim incomplete work is done.

## Goal
Build a reproducible Python research pipeline to test whether X/Twitter sentiment adds out-of-sample predictive value beyond price-only baselines for Bitcoin spot. Expected outputs are aligned data, six forecast horizons, chronological evaluation, charts, a one-page current outlook and an evaluation report. Exact BTC-USD coverage and an empirical sentiment comparison remain blocked; the current price evaluation uses the disclosed BTCUSDT proxy.

## Scope and working choices
- Asset: Bitcoin spot. Bar interval: daily, UTC.
- Current evaluation source: Binance Vision Spot `BTCUSDT`, quote currency USDT, 2026-05-05 through 2026-10-31. This non-commercial CC BY-NC-SA 4.0 dataset is not USD and is not a substitute for employer approval of the target source.
- Forecast cutoff: 00:00 UTC at start of day n. Predict closes of bars n through n+5. n+0 is the not-yet-completed close of day n.
- X: asset-related posts for a 180-day window via an approved Apify/provider route, using ticker, cashtag and keyword searches, only after source, terms, schema, coverage and cost checks.
- News: Tavily for context and the one-page outlook only by default. The brief says model inputs are sentiment and price only; clarify before adding news features.
- Modeling: supervised multi-horizon forecasting, a naive baseline and a price-only baseline. RL is out of initial scope unless explicitly confirmed and fully specified.
- Exa appears in the submission line; an optional bounded adapter and CLI provider selector now exist, but no Exa key is configured and no live request is claimed.

## Functional requirements and acceptance criteria
These IDs (`R1`–`R15`) are the project's primary assessment IDs; the same IDs and their
statuses, gaps and blockers are maintained in
docs/REQUIREMENTS_TRACEABILITY.md and docs/PHASE_1_REQUIREMENTS.md.

| ID | Requirement | Acceptance criterion | Verification method |
| --- | --- | --- | --- |
| R1 | Reproducible workflow from ingestion through reporting | Documented commands produce every artefact from a pinned input, and a manifest records config, input hashes and versions | README quick start re-run; run manifest contents |
| R2 | X ingestion for the bounded 180-day window via an approved provider route, using ticker, cashtag and keyword searches | Accepted permitted source with a sanitized profile proving 180-day event-time coverage and required fields, with the three query modes exercised | Coverage profile; terms review; bounded end-to-end ingest |
| R3 | Matching BTC-USD daily prices | Provider, product, interval, timezone and currency documented; gap and duplicate checks pass | Price snapshot plus coverage table; adapter tests |
| R4 | Preserve post ID, event time, retrieval/availability time and provenance | Timezone-aware, distinct event and first-observed times; supplied offsets parsed and event time normalised to UTC; source identity retained | Contract tests; run provenance block |
| R5 | Preserve post text, likes, reposts, views and author follower counts | Text required for an admitted post; optional counts nullable; negatives rejected | Contract and adapter tests; missingness counts in profile |
| R6 | Normalize timestamps to UTC and align posts with bars deterministically | Documented UTC windows; duplicates and gaps reported, never filled; late and future posts excluded | Alignment and dataset tests |
| R7 | Generate documented time-based sentiment and price features | Predeclared features computed only from information available at the cutoff; missing sentiment stays null | Feature tests; feature definitions in MODEL_PLAN.md |
| R8 | Produce horizon targets/forecasts n+0 through n+5 with no leakage | Six horizons under the documented cutoff and target convention; targets never in features | Horizon tests; per-horizon metrics rows |
| R9 | Chronological out-of-sample evaluation against naive and price-only baselines | Purged walk-forward folds; all models on identical folds and eligible rows; no random split | Fold and evaluation tests; deterministic repeat-run test |
| R10 | Visual matrix of X sentiment change against price over time | Reproducible chart showing sentiment change, not only level, alongside price changes; empty panels labelled rather than fabricated | Chart artefact; rendering tests |
| R11 | One-page current sentiment outlook with cutoff, provenance and uncertainty | Outlook states as-of time, cutoff, coverage, model output or absence, news context and limitations; one-page constraint respected | Outlook artefact; rendering tests |
| R12 | Evaluation report (PDF or Markdown) with Sharpe, Sortino and maximum drawdown where valid | Report contains per-horizon MAE/RMSE and risk metrics only from a defined strategy on out-of-sample returns, with fees, annualisation and missing-data policy disclosed; unavailable metrics carry a reason | Report artefact; strategy specification; metric tests |
| R13 | Reproducibility package with configuration, provider/Actor identifiers, ticker/cashtag/keyword query configuration, snapshot hash and run instructions | Setup and reproduction documented; non-secret identifiers and query configuration documented; secrets excluded with a defined transfer route | README; APIFY_X_SETUP.md; manifest provenance |
| R14 | Automated schema, timestamp, alignment, feature, target, leakage, metric and report tests | Offline suite covers each area and runs in CI alongside lint, registry validation and documentation validation | pytest output; CI workflow |
| R15 | Persist and join X posts and price bars in a database | Normalized posts and bars persisted in a versioned schema and joined by asset and cutoff, with idempotent writes and a reproducible query; the run CLI consumes persisted data | Storage integration tests; pipeline run from persisted data |

## Non-functional requirements

| ID | Requirement | Acceptance criterion | Verification method |
| --- | --- | --- | --- |
| NFR1 | Reproducibility metadata: code revision, source/version, query/window, retrieval time, schema, non-secret run ID | Each run records the listed metadata and no secrets | Run manifest inspection |
| NFR2 | Temporal integrity: timezone-aware timestamps, event time distinct from first-observed time | Naive timestamps rejected; retrieval time never derived from creation time | Contract and loader tests |
| NFR3 | Security: never commit tokens, cookies, private exports or large raw datasets | Repository contains no credentials or raw private exports; ignored paths cover data and secrets | Secret scan; `.gitignore` review |
| NFR4 | Robustness: bounded timeouts, responses, concurrency and cost; no blind retry of paid launches | Caps configurable and enforced; paid Actor launch never auto-retried | Adapter and settings tests |
| NFR5 | Auditability: record exclusions and reasons without logging post text by default | Profiles and reports record counts and exclusions without printing post text | Profiler and report tests |
| NFR6 | Honest reporting: fixtures and in-sample metrics are never presented as real out-of-sample results | Artefacts label unavailable items and synthetic fixtures; no unverified claim is made | Report tests; docs validation |

## Out of scope
Other assets/intervals, live order execution, guaranteed returns, investment advice, automatic paid scraping, using current engagement as historical features without snapshots, mixing StockTwits into X, and RL without a defined action/reward/cost/evaluation design.

## Data/evaluation rules
At cutoff t, a post is eligible only when event time and defensible availability time are <= t. Use only completed prior candles as price inputs. Targets are separate from features; omit incomplete or gap-crossing horizons. Current engagement is metadata unless historical snapshots exist. Use walk-forward/chronological splits and fit transforms only on training folds; do not tune on test folds. Report MAE/RMSE by horizon and baseline comparisons. Trading metrics require a separately specified strategy, out-of-sample returns, costs, slippage, annualization and return conventions.

## Current evidence, not completion
- **Prices (recomputed).** 180/180 Binance Vision `BTCUSDT` daily bars for 2026-05-05 through 2026-10-31 UTC, with 36 archive checksum verifications and no gaps or duplicates. Exact snapshot and source archives are in `reports/btcusdt-180d/`; derivatives are CC BY-NC-SA 4.0, non-commercial only.
- **Features and targets (implemented, unit-verified, run on real prices).** Point-in-time price and sentiment features plus n+0..n+5 ratio labels; the unfinished UTC day is dropped and no target column can enter a feature row.
- **Models and evaluation (implemented, run on real prices).** Naive persistence, price-only ridge and sentiment-plus-price ridge on identical folds and eligible rows: 5 expanding folds, 60→140 training rows, 20 test rows, 5-row purge, 100 out-of-sample days per model and horizon, 1800 stored predictions.
- **Measured result (negative).** The current Binance Vision BTCUSDT run has mean MAE 1,824.23 USDT for naive persistence and 2,378.50 USDT for price-only ridge (30.38% worse). The sentiment-labelled candidate is identical because zero posts were scored; it is not evidence about sentiment.
- **Risk metrics (computed, short sample).** The predeclared price-only long/flat strategy has Sharpe 1.124, Sortino 2.431 and 5.885% maximum drawdown. Full fees, benchmark and return details are in the attributed report. These values derive from Binance Vision and remain CC BY-NC-SA 4.0, non-commercial only.
- **Reporting (implemented).** Chart, one-page outlook, evaluation report, metrics and manifest are produced by one offline command.
- **Assignment source (verified 2026-10-26).** Both supplied PDFs were read in full. The linked Google Doc is a 12-entry dataset-link compilation matching the companion PDF, not a tweet corpus. The ID/count and archive uploads contain no X text; the available archive files are unrelated air-quality and MQTT data. Hashes and page counts are in the traceability matrix.
- **Database join (implemented and verified offline).** The brief explicitly requires joining the datasets in a database. `src/xsentiment/storage/` has a versioned `price_bars`/`x_posts` schema, idempotent repositories and tested descriptive and leakage-safe cutoff joins, and the run CLI consumes persisted inputs (`xsentiment persist`, `run --database-url`; manifest provenance records `input_source = persisted_storage`). Verified on fixtures only; a database holding real X rows remains blocked on R2.
- **Still not evidenced.** Eligible 180-day X data and real sentiment contribution; exact BTC-USD prices; an Apify run (the configured Free plan forbids Actor API use); Exa live behavior (no key); provider credentials for employer handoff; and employer decisions on BTCUSDT acceptability, target semantics, Exa requirement and deadline. One bounded Tavily request was live-checked; it returned five results with no publication dates.

## Open gates
The assignment PDFs were re-opened on 2026-11-01 and are not packaged. External gates: an approved rights-cleared X corpus or paid Actor plan with spend cap; employer acceptance of a non-commercial BTCUSDT proxy or written rights-cleared BTC-USD source; Exa key/requirement decision; target convention; calendar deadline; and private credential channel. The database path and offline pipeline remain locally verified. See the other canonical files and the final execution status.
