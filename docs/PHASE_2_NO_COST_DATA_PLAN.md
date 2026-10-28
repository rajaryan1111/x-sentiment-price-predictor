# No-cost X-data path — Phase 2 workstream

> Naming note: this file belongs to the repository's historical "Phase 2 data quality/alignment" workstream, which maps to canonical Phase 3 in [PHASES.md](../PHASES.md). It is not canonical documentation Phase 2.

## Goal

Keep the data workstream moving without requiring the project owner to purchase a scraper. The BTC-USD price path already uses Coinbase Exchange's public candles. X data must remain a separate, evidence-backed gate.

## Current status

- **Price history:** user-run profile verified 180/180 complete daily BTC-USD bars for 2026-04-29 through 2026-10-25 UTC (half-open end 2026-10-26), with no missing or duplicate timestamps in that checked range.
- **Provider-neutral contracts, profiler and point-in-time alignment:** implemented and covered by unit tests. The profiler supports deterministic `--as-of` windows, daily coverage gaps, retrieval-column coverage, schema drift and invalid engagement counts.
- **Apify adapter:** implemented and mocked in tests, including the documented `data` envelope and dataset offset/limit paging; no Actor is selected or run. Do not assume its free allowance will cover an Actor or 180-day search.
- **Storage:** a versioned price/post schema, idempotent repositories, descriptive and leakage-safe cutoff joins, and `xsentiment persist` plus `run --database-url` are implemented and fixture-verified end-to-end. This verifies the offline persisted-input path for R15; no accepted real X rows are available to populate it.
- **Historical X collection:** not complete. The assessment-linked Google Doc was retrieved on 2026-10-26 and is a 12-entry dataset-link compilation, not a tweet corpus. No candidate dataset has been downloaded, profiled, or accepted for use. Uploaded local files contain IDs, date/count summaries, unrelated air-quality/MQTT data or a StockTwits paper; none contains X post text.

## Zero-budget options to investigate

### Option A — Assessment-linked historical dataset

The assessment-linked Google Doc was retrieved on 2026-10-26. It is a 12-entry dataset-link compilation matching the companion dataset PDF, **not** a tweet corpus. Select one candidate from it and review access, schema, timestamp coverage, license/terms, whether full text is present, and whether the rows are actual X posts. Do not assume a dataset is usable simply because its link appeared in the assessment. If it is accessible and permitted, record the exact snapshot/version and file hash, then profile it locally without committing the data.

### Option B — Existing public research corpus

The repository's dataset registry includes historical Bitcoin/X candidates. Most listed coverage ends by 2023, and two rolling entries have no verified coverage end. None alone proves the required recent 180-day window. They can help test parsing and feature plumbing, **not** satisfy the requirement without live coverage evidence. Confirm the live dataset card, current access, license and schema before downloading. Do not hydrate tweet IDs unless permitted and available.

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

Keep raw post text, cookies, API tokens and downloaded datasets out of Git. Do not claim a sentiment forecast, Sharpe ratio, Sortino ratio or drawdown until the corresponding model/backtest has actually run on valid out-of-sample data. The registry's `independent_verification.status` is `not-reverified`: selecting a link from the PDF or Google Doc is not independent confirmation of current access, schema, coverage or license.
