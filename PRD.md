# Product Requirements Document (PRD)
Status: canonical working baseline. Price ingestion, features, baselines, walk-forward evaluation, charts, outlook and report are implemented and verified on real public price data. X data access, the sentiment-versus-price comparison and employer clarifications remain open gates.
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
- **Prices (verified).** 180/180 public Coinbase `BTC-USD` daily bars for 2026-04-29 through 2026-10-25 UTC, refetched 2026-10-26 with no missing or duplicate timestamps and the unfinished current day excluded; reproduced by `python -m xsentiment fetch-prices`.
- **Features and targets (implemented, unit-verified, run on real prices).** Point-in-time price and sentiment features plus n+0..n+5 ratio labels; the unfinished UTC day is dropped and no target column can enter a feature row.
- **Models and evaluation (implemented, run on real prices).** Naive persistence, price-only ridge and sentiment-plus-price ridge on identical folds and eligible rows: 5 expanding folds, 60→140 training rows, 20 test rows, 5-row purge, 100 out-of-sample days per model and horizon, 1800 stored predictions.
- **Measured result (negative).** Mean MAE across horizons: naive **$1,828.36**, price-only ridge **$2,264.62** (23.86% worse). No claim is made that any model adds predictive value, and the candidate model is identical to price-only because no sentiment was available.
- **Risk metrics (computed, short sample).** Predeclared long/flat strategy: +10.91% cumulative net return, Sharpe 1.807, Sortino 3.979, 4.08% maximum drawdown over 32 long days, against a +6.11% / 0.752 / 1.377 / 10.33% unconditional-long benchmark. The naive rule never trades, so its ratios are undefined.
- **Reporting (implemented).** Chart, one-page outlook, evaluation report, metrics and manifest are produced by one offline command.
- **Still not evidenced.** X data access, terms and any accepted post-level X dataset; the sentiment-versus-price comparison; a live Apify Actor run; uploaded ZIP archive contents; the runtime role of Tavily/Exa news; and every employer clarification of target semantics or deadline.

## Open gates
Verify legal access, platform identity, actual schema/text and 180-day coverage; verify Actor terms/pricing/limits before any run; clarify target/news/RL/Exa expectations and deadline with employer. See the other eight canonical files.
