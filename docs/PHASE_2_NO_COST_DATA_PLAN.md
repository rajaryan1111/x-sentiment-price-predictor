# No-cost X-data path — Phase 2 workstream

> Naming note: this file belongs to the repository's historical "Phase 2 data quality/alignment" workstream, which maps to canonical Phase 3 in [PHASES.md](../PHASES.md). It is not canonical documentation Phase 2.

## Goal

Keep the data workstream moving without requiring the project owner to purchase a scraper. The current price-only evaluation uses checksum-verified Binance Vision BTCUSDT archives under non-commercial CC BY-NC-SA 4.0 terms. X data remains a separate, evidence-backed gate.

## Current status

- **Price history:** current evaluation verifies 180 Binance Vision BTCUSDT daily bars for 2026-05-05 through 2026-10-31 UTC, with 36 matching published archive checksums and no missing or duplicate dates. Quote is USDT, not USD; exact BTC-USD requires employer approval or another licensed source.
- **Provider-neutral contracts, profiler and point-in-time alignment:** implemented and covered by unit tests. The profiler supports deterministic `--as-of` windows, daily coverage gaps, retrieval-column coverage, schema drift and invalid engagement counts.
- **Apify adapter:** implemented and mocked in tests, including the documented `data` envelope and dataset offset/limit paging. The candidate Actor is identified but not employer-approved; current account Free plan prohibits API use. No Actor was run.
- **Storage:** a versioned price/post schema, idempotent repositories, descriptive and leakage-safe cutoff joins, and `xsentiment persist` plus `run --database-url` are implemented and fixture-verified end-to-end. This verifies the offline persisted-input path for R15; no accepted real X rows are available to populate it.
- **Historical X collection:** not complete. The assessment-linked Google Doc was retrieved on 2026-10-29 and is a 12-entry dataset-link compilation, not a tweet corpus. Three public candidate listing/card metadata were checked, but no candidate dataset has been downloaded, row-profiled, or accepted for use. No raw candidate corpus is present in this checkout.

## Zero-budget options to investigate

### Option A — Assessment-linked historical dataset

The assessment-linked Google Doc full text was re-fetched on 2026-10-29. It is a 12-entry dataset-link compilation matching the previously recorded companion PDF, **not** a tweet corpus. Three candidate listings/cards were partially inspected and documented in `docs/data-sources.md`; this does not establish row contents, current 180-day coverage, complete schema, rights or license. Ask the employer to approve a candidate and permitted bounded inspection before downloading. If approved, record the exact snapshot/version and file hash, then profile it locally without committing the data.

### Option B — Existing public research corpus

The repository's dataset registry includes historical Bitcoin/X candidates. Most listed coverage ends by 2023, and two rolling entries have no verified coverage end. None alone proves the required recent 180-day window. They can help test parsing and feature plumbing, **not** satisfy the requirement without live coverage evidence. Confirm the live dataset card, current access, license and schema before downloading. Do not hydrate tweet IDs unless permitted and available.

### Option C — Free rolling public data offer

AWS Marketplace has listed a free-of-charge Twitter cryptocurrency dataset covering approximately the last 30 days of English-language posts from verified accounts. It is a rolling one-month source, not a 180-day archive; AWS infrastructure charges may apply, and access requires accepting the vendor terms. Treat it only as a possible recent-window supplement, not a substitute for the 180-day requirement. Re-check current listing and terms before subscribing.

### Option D — Apify Free plan

The inspected account's current Free plan is demo-only: 5 runs/month, maximum 10 items/run, and no Actor API use. It cannot collect the required recent corpus through the configured API path. Do not use a browser workaround or purchase a paid plan; ask the employer for a permitted export or explicit approval of an Actor, plan and spend cap.

## Point-in-time rule for downloaded historical data

A dataset downloaded today has a current retrieval/availability time unless it contains reliable point-in-time availability snapshots. Do not backdate retrieval time to the post creation time. Without historical availability evidence, the data may be useful for descriptive/offline parser tests, but it must not be presented as leakage-safe historical forecasting input.

## Required acceptance evidence

Before calling X ingestion complete, produce a sanitized profile containing:
- provider/dataset name, URL, version or run ID, retrieval timestamp and license review status;
- row count, timestamp minimum/maximum, count within the target window, missing ID/text/time counts, duplicate IDs and invalid timestamps;
- counts of available engagement fields and their missingness;
- explicit statement whether the source covers the entire required 180-day period and whether retrieval-time/point-in-time availability is known.

Keep raw post text, cookies, API tokens and downloaded datasets out of Git. Do not claim a sentiment forecast, Sharpe ratio, Sortino ratio or drawdown until the corresponding model/backtest has actually run on valid out-of-sample data. The registry's `independent_verification.status` is `partially-reverified`: three candidate listing/card metadata were checked, but this is not independent confirmation of current access, row schema, 180-day coverage or license.
