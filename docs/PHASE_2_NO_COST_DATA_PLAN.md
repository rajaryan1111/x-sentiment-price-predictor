# Phase 2 — No-cost X-data path

## Goal

Keep Phase 2 moving without requiring the project owner to purchase a scraper. The BTC-USD price path already uses Coinbase Exchange's public candles. X data must remain a separate, evidence-backed gate.

## Current status

- **Price history:** user-run profile verified 180/180 complete daily BTC-USD bars for 2026-04-29 through 2026-10-25 UTC (half-open end 2026-10-26), with no missing or duplicate timestamps in that checked range.
- **Provider-neutral contracts and point-in-time alignment:** implemented and covered by unit tests.
- **Apify adapter:** implemented and mocked in tests; no Actor is selected or run. Do not assume its free allowance will cover an Actor or 180-day search.
- **Historical X collection:** not complete. No real X dataset has yet been retrieved, profiled, or accepted for use.

## Zero-budget options to investigate

### Option A — Assessment-linked historical dataset

Start with the historical dataset resource named in the assessment brief. Review access, schema, timestamp coverage, license/terms, whether full text is present, and whether the rows are actual X posts. Do not assume the resource is accessible simply because a link exists. If it is accessible and permitted, record the exact snapshot/version and file hash, then profile it locally without committing the data.

### Option B — Existing public research corpus

The repository's dataset registry includes historical Bitcoin/X candidates, but their listed coverage ends by 2023. They can help test parsing and feature plumbing, **not** satisfy the required recent 180-day window. Confirm the live dataset card, current access, license and schema before downloading. Do not hydrate tweet IDs unless permitted and available.

### Option C — Free rolling public data offer

AWS Marketplace has listed a free-of-charge Twitter cryptocurrency dataset covering approximately the last 30 days of English-language posts from verified accounts. It is a rolling one-month source, not a 180-day archive; AWS infrastructure charges may apply, and access requires accepting the vendor terms. Treat it only as a possible recent-window supplement, not a substitute for the 180-day requirement. Re-check current listing and terms before subscribing.

### Option D — Apify Free plan credits

Apify advertises a Free plan with monthly platform usage credits and no credit card requirement, but Actor-specific charges and resource usage vary. This is not guaranteed to make any chosen X Actor free. Do not start a run until its current pricing, schema, limits and terms are reviewed; never exceed a user-approved zero-spend preference.

## Point-in-time rule for downloaded historical data

A dataset downloaded today has a current retrieval/availability time unless it contains reliable point-in-time availability snapshots. Do not backdate retrieval time to the post creation time. Without historical availability evidence, the data may be useful for descriptive/offline parser tests, but it must not be presented as leakage-safe historical forecasting input.

## Required acceptance evidence

Before calling X ingestion complete, produce a sanitized profile containing:
- provider/dataset name, URL, version or run ID, retrieval timestamp and license review status;
- row count, timestamp minimum/maximum, count within the target window, missing ID/text/time counts, duplicate IDs and invalid timestamps;
- counts of available engagement fields and their missingness;
- explicit statement whether the source covers the entire required 180-day period and whether retrieval-time/point-in-time availability is known.

Keep raw post text, cookies, API tokens and downloaded datasets out of Git. Do not claim a sentiment forecast, Sharpe ratio, Sortino ratio or drawdown until the corresponding model/backtest has actually run on valid out-of-sample data.
