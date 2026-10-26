# Product Requirements Document (PRD)
Status: canonical working baseline; data-access and employer-clarification gates remain open.
Authority: the supplied CWT X sentiment Agent - intern task.pdf defines assignment requirements. This document translates them into testable requirements; it does not claim incomplete work is done.

## Goal
Build a reproducible Python research pipeline to test whether X/Twitter sentiment adds out-of-sample predictive value beyond price-only baselines for Bitcoin spot reference BTC-USD. Expected outputs are aligned data, six forecast horizons, chronological evaluation, charts, a one-page current outlook and an evaluation report.

## Scope and working choices
- Asset: BTC-USD. Bar interval: daily, UTC.
- Default price source: Coinbase Exchange public BTC-USD candles, verified per run.
- Forecast cutoff: 00:00 UTC at start of day n. Predict closes of bars n through n+5. n+0 is the not-yet-completed close of day n.
- X: asset-related posts for a 180-day window via an approved Apify/provider route, only after source, terms, schema, coverage and cost checks.
- News: Tavily for context and the one-page outlook only by default. The brief says model inputs are sentiment and price only; clarify before adding news features.
- Modeling: supervised multi-horizon forecasting, a naive baseline and a price-only baseline. RL is out of initial scope unless explicitly confirmed and fully specified.
- Exa appears in the submission checklist but not the main news requirement; its runtime role remains open.

## Functional requirements and acceptance evidence
1. Reproducible workflow from ingestion through reporting — commands, config and run metadata.
2. X ingestion for the bounded 180-day period — verified source, terms, schema and sanitized coverage profile.
3. Matching BTC-USD daily prices — provider/window metadata and gap/duplicate checks.
4. Preserve post ID, text where permitted, event time, retrieval/availability time, provenance and available engagement/follower metadata.
5. Normalize timestamps to UTC and deterministically align posts and bars.
6. Preserve missingness; never fabricate rows, counts, prices or sentiment.
7. Generate documented time-based sentiment and price features.
8. Produce horizon targets/forecasts n+0 through n+5 with no leakage.
9. Chronological out-of-sample evaluation against naive and price-only baselines.
10. Charts comparing X sentiment and price over time.
11. One-page current outlook with cutoff, provenance and uncertainty.
12. PDF/Markdown evaluation report. Sharpe, Sortino and max drawdown only when valid strategy returns exist; otherwise explain unavailable status.
13. Reproducibility package with configuration, provider/Actor identifiers, data snapshot/hash and run instructions.
14. Automated schema, timestamp, alignment, feature, target, leakage, metric and report tests.

## Non-functional requirements
- Reproducibility: record code revision, source/version, query/window, retrieval time, schema and non-secret run ID.
- Temporal integrity: timezone-aware timestamps; event time is distinct from first-observed time.
- Security: never commit tokens, cookies, private exports or large raw datasets.
- Robustness: bounded timeouts/responses/concurrency/cost; do not blindly retry paid Actor launches.
- Auditability: record exclusions and reasons without logging post text by default.
- Honest reporting: fixtures and in-sample metrics are never presented as real out-of-sample results.

## Out of scope
Other assets/intervals, live order execution, guaranteed returns, investment advice, automatic paid scraping, using current engagement as historical features without snapshots, mixing StockTwits into X, and RL without a defined action/reward/cost/evaluation design.

## Data/evaluation rules
At cutoff t, a post is eligible only when event time and defensible availability time are <= t. Use only completed prior candles as price inputs. Targets are separate from features; omit incomplete or gap-crossing horizons. Current engagement is metadata unless historical snapshots exist. Use walk-forward/chronological splits, fit transforms only on training folds, and keep a final holdout untouched. Report MAE/RMSE by horizon and baseline comparisons. Trading metrics require a separately specified strategy, out-of-sample returns, costs, slippage, annualization and return conventions.

## Current evidence, not completion
The user-run Coinbase profile reported 180/180 daily BTC-USD bars for 2026-04-29 through 2026-10-25 UTC with no missing/duplicate timestamps. Ingestion/alignment primitives are implemented and CI passed lint, registry validation and pytest. No live Apify Actor is selected or run; no real post-level X dataset is accepted; uploaded ZIP contents remain unverified. No trained model, walk-forward results, charts, outlook or valid trading metrics are claimed complete.

## Open gates
Verify legal access, platform identity, actual schema/text and 180-day coverage; verify Actor terms/pricing/limits before any run; clarify target/news/RL/Exa expectations and deadline with employer. See the other eight canonical files.
