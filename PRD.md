# Product Requirements Document (PRD)
Status: canonical working baseline. Price ingestion, features, baselines, walk-forward evaluation, charts, outlook and report are implemented and verified on real public price data. The assessment PDFs were verified on 2026-10-26. Database schema, idempotent repositories and two joins are implemented and unit-tested (R15 partial), but the run CLI still uses file snapshots. X data access, the sentiment-versus-price comparison and employer clarifications remain open gates.
Authority: the supplied CWT X sentiment Agent - intern task.pdf defines assignment requirements. This document translates them into testable requirements; it does not claim incomplete work is done.

## Goal
Build a reproducible Python research pipeline to test whether X/Twitter sentiment adds out-of-sample predictive value beyond price-only baselines for Bitcoin spot reference BTC-USD. Expected outputs are aligned data, six forecast horizons, chronological evaluation, charts, a one-page current outlook and an evaluation report.

## Scope and working choices
- Asset: BTC-USD. Bar interval: daily, UTC.
- Default price source: Coinbase Exchange public BTC-USD candles, verified per run.
- Forecast cutoff: 00:00 UTC at start of day n. Predict closes of bars n through n+5. n+0 is the not-yet-completed close of day n.
- X: asset-related posts for a 180-day window via an approved Apify/provider route, using ticker, cashtag and keyword searches, only after source, terms, schema, coverage and cost checks.
- News: Tavily for context and the one-page outlook only by default. The brief says model inputs are sentiment and price only; clarify before adding news features.
- Modeling: supervised multi-horizon forecasting, a naive baseline and a price-only baseline. RL is out of initial scope unless explicitly confirmed and fully specified.
- Exa appears only in the submission line, not the main news requirement; it is optional unless actually used or employer-required.

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
- **Prices (verified).** 180/180 public Coinbase `BTC-USD` daily bars for 2026-04-29 through 2026-10-25 UTC, refetched 2026-10-26 with no missing or duplicate timestamps and the unfinished current day excluded; reproduced by `python -m xsentiment fetch-prices`.
- **Features and targets (implemented, unit-verified, run on real prices).** Point-in-time price and sentiment features plus n+0..n+5 ratio labels; the unfinished UTC day is dropped and no target column can enter a feature row.
- **Models and evaluation (implemented, run on real prices).** Naive persistence, price-only ridge and sentiment-plus-price ridge on identical folds and eligible rows: 5 expanding folds, 60→140 training rows, 20 test rows, 5-row purge, 100 out-of-sample days per model and horizon, 1800 stored predictions.
- **Measured result (negative).** Mean MAE across horizons: naive **$1,828.36**, price-only ridge **$2,264.62** (23.86% worse). No claim is made that any model adds predictive value, and the candidate model is identical to price-only because no sentiment was available.
- **Risk metrics (computed, short sample).** Predeclared long/flat strategy: +10.91% cumulative net return, Sharpe 1.807, Sortino 3.979, 4.08% maximum drawdown over 32 long days, against a +6.11% / 0.752 / 1.377 / 10.33% unconditional-long benchmark. The naive rule never trades, so its own strategy ratios are undefined; the benchmark is the same windows held long.
- **Reporting (implemented).** Chart, one-page outlook, evaluation report, metrics and manifest are produced by one offline command.
- **Assignment source (verified 2026-10-26).** Both supplied PDFs were read in full. The linked Google Doc is a 12-entry dataset-link compilation matching the companion PDF, not a tweet corpus. The ID/count and archive uploads contain no X text; the available archive files are unrelated air-quality and MQTT data. Hashes and page counts are in the traceability matrix.
- **Database join (implemented and verified offline).** The brief explicitly requires joining the datasets in a database. `src/xsentiment/storage/` has a versioned `price_bars`/`x_posts` schema, idempotent repositories and tested descriptive and leakage-safe cutoff joins, and the run CLI consumes persisted inputs (`xsentiment persist`, `run --database-url`; manifest provenance records `input_source = persisted_storage`). Verified on fixtures only; a database holding real X rows remains blocked on R2.
- **Still not evidenced.** X data access, terms and any accepted post-level X dataset; the sentiment-versus-price comparison; a live Apify Actor run; candidate dataset licenses/schema/180-day coverage; a live Tavily/Exa call; and every employer clarification of target semantics or deadline.

## Open gates
The assignment PDFs are verified. Remaining gates: verify X source legal access, platform identity, actual schema/text and 180-day coverage; select and verify an Actor's ticker/cashtag/keyword support, terms, pricing and limits before any run; select and license a candidate dataset; obtain a Tavily key if news context is to be fetched live; finish the pipeline integration of the tested database join (R15); and clarify target semantics and the exact deadline with the employer. See the other eight canonical files.
