# Phase 2 — Data access and ingestion progress

**Status: partially implemented; external data-access gates remain open.** This document distinguishes code and test evidence from provider/account verification. Live X ingestion, a verified 180-day dataset, model training, and performance evaluation are not yet complete.

## Implemented and locally verified

### Coinbase daily candles

- Public Coinbase Exchange daily-candle adapter for configured BTC-USD.
- UTC-aware bounds, daily granularity, provider range limit, Decimal OHLCV parsing, sorting, malformed-row and duplicate checks.
- Local smoke script checks seven completed daily bars without saving raw market data.
- User-run live smoke test succeeded for 2026-10-19 through 2026-10-25: 7 candles, no missing bars in that seven-day window.
- User-run local verification reported Ruff passing and 18 tests passing before the new Phase 2 tests in this branch.

### Data-quality and point-in-time primitives

Implemented in src/xsentiment/pipeline/phase2.py:

- Canonical XPostRecord keeps event time and retrieval/availability time distinct and validates timestamps and optional fields.
- Stable-ID deduplication fails closed on conflicting duplicate IDs.
- Daily price coverage report enumerates missing UTC days, duplicate timestamps, out-of-range records and possible incomplete current-day candles. It never fills missing candles.
- Point-in-time feature builder uses prior completed closes and only posts published and retrieved by each cutoff; current engagement counts are deliberately excluded as historical features.
- Close-target builder creates n+0 through n+5 labels only where the full horizon exists; target labels remain separate from features.
- Unit tests cover late-arriving/future-post exclusion, missing sentiment, duplicate IDs, missing price bars and horizon tails.

These are deterministic primitives, not a complete collection or forecasting system. They do not scrape X or calculate sentiment themselves; sentiment scores must come from an explicitly configured sentiment model.

## External gates still open

1. 180-day live price profile: collect in chunks no larger than the Coinbase endpoint limit, excluding the incomplete current UTC day. Record sanitized coverage metadata; do not commit raw market data by default.
2. Historical X dataset: retrieve the assessment's linked resource and review contents, access permissions, terms/license, schema, event-time coverage, text availability and source platform before use.
3. Apify: inspect available Actors and account pricing/terms; verify query strategy, output fields, plan rate, 180-day coverage and strict run cost cap before any paid run. No actor selected and no paid run initiated.
4. Credentials: verify provider configuration privately; never add tokens, cookies or credentials to Git.
5. Employer constraints: confirm the actual submission deadline and any target-semantics clarification.

## Next steps after access gates

1. Run CI and local lint/tests on this branch.
2. Execute a bounded 180-day Coinbase price profile in chunks and inspect missing UTC days and boundary behavior.
3. Review historical dataset contents/terms and inspect the actual Apify actor schema before implementing a provider-specific X adapter.
4. Add the approved X adapter and storage/export format, then run schema and point-in-time quality checks on a permitted sample.
5. Add an explicit sentiment model, train/evaluate baselines chronologically, and report only evidence-backed metrics.

## Guardrails

- No raw provider datasets, tokens, cookies or other secrets in Git.
- Current likes/reposts/views/follower counts are not historical features without point-in-time snapshots.
- No fabricated bars, missing fields, sentiment scores or evaluation metrics.
- No model training until X/price coverage and availability timestamps are profiled and point-in-time cutoffs are enforceable.
- Trading risk metrics are unavailable until a defined strategy has valid out-of-sample returns and disclosed cost assumptions.
