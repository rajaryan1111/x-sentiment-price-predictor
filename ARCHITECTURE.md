# Architecture
Status: canonical target architecture; implementation is partial.

## Flow
Configuration/secrets -> source adapters (X/Apify, BTC prices, optional news context) -> response boundary and validation -> normalized records plus provenance -> approved storage -> point-in-time alignment -> feature and target generation -> naive/price-only/sentiment-plus-price models -> chronological evaluation -> optional strategy simulation -> metrics, charts, outlook and report.

## Components
- Config: typed validated settings from environment; secrets never logged.
- Ingestion contracts: normalized X records with explicit event/retrieval time semantics.
- X adapter: explicit Actor ID/input and bounded controls; schema must be verified for the selected Actor.
- Price adapter: Coinbase BTC-USD daily candles with UTC bounds and OHLCV validation.
- Phase 2 pipeline: deduplication, coverage profiling, point-in-time features and n+0..n+5 close labels.
- Features: sentiment aggregation and lagged price features, with definitions governed by MODEL_PLAN.md.
- Storage: project-owned schema/repository; raw social data only where terms permit.
- Models: naive baseline, price-only model and candidate sentiment-plus-price model.
- Validation: walk-forward splits, train-fold-only transforms and leakage guards.
- Backtesting: optional strategy simulation from out-of-sample forecasts only.
- Reporting: metric tables, charts, one-page outlook and report assembly.
- Dashboard: presentation only; authoritative metrics come from the pipeline.
- Scripts: explicit bounded entry points; no paid/network side effects on import.
- Tests: offline unit tests and mocked provider contracts by default.

## Temporal contract
Daily bars are labelled by UTC candle start. Forecast cutoff is 00:00 UTC. Price inputs use completed bars only. Posts require event time and availability/retrieval time <= cutoff. The current sentiment window is (t-24h, t]. Targets are closes of candles beginning at t and the next five daily cutoffs. Incomplete/gap-crossing horizons are omitted. Downloading historical posts today does not prove historical availability; never backdate.

## Boundaries and failure handling
Adapters normalize provider payloads without fabricating missing fields. Raw data, features and targets remain distinguishable. Targets never enter feature matrices. News is context-only unless the decision log changes. Fail closed on conflicting duplicate IDs, invalid timestamps, malformed OHLC and schema mismatches. Report missing bars instead of filling them. Use timeouts/response caps and retry only safe transient operations. Do not launch paid Actors automatically or switch sources silently when access is blocked.

## Security
Secrets via environment/approved secret manager; raw/private data out of Git; retention follows source terms; avoid full-text logs. Record provider, query/window, retrieval timestamp, schema, non-secret run ID and hash where possible.

## Implementation status
Implemented: Coinbase daily adapter; normalized X contract; configurable Apify adapter (mocked, not live verified); deduplication, coverage, point-in-time alignment and horizon-label primitives; local CSV/JSONL profiler; tests/CI.
Not evidenced complete: real X collection, accepted license/coverage, sentiment scoring, trained forecasts, walk-forward evaluation, trading metrics, charts, current outlook and full report.
