# Architecture
Status: canonical architecture with an offline, reproducible BTCUSDT evaluation. Current execution facts and external blockers are in [FINAL_EXECUTION_STATUS_2026-11-01.md](docs/FINAL_EXECUTION_STATUS_2026-11-01.md). Live X collection remains blocked; persisted joins remain locally verified.

## Flow
Configuration/secrets -> source adapters (X/Apify, BTC prices, optional news context) -> response boundary and validation -> normalized records plus provenance -> approved storage -> point-in-time alignment -> feature and target generation -> naive/price-only/sentiment-plus-price models -> chronological evaluation -> optional strategy simulation -> metrics, charts, outlook and report.

## Components
- Config: typed validated settings from environment; secrets never logged.
- Ingestion contracts: normalized X records with explicit event/retrieval time semantics.
- X adapter: explicit Actor ID/input and bounded controls; schema, ticker/cashtag/keyword query support and required fields must be verified for the selected Actor.
- Price input: normalized UTC OHLCV records. The current 180-day evaluation is built from checksum-verified Binance Vision BTCUSDT daily archives by `scripts/build_binance_snapshot.py`; the generic Coinbase adapter remains legacy code and no Coinbase data was fetched in this execution.
- News providers: bounded Tavily and Exa `/search` adapters normalize contextual items and provenance. Both are explicitly selected by `fetch-news`; news is not a model input.
- Data-quality pipeline (historical Phase 2 workstream): deduplication, coverage profiling, point-in-time features and n+0..n+5 close labels.
- Features: VADER sentiment scoring, predeclared lagged/rolling price features, trailing-24h sentiment aggregation and supervised dataset assembly, with definitions governed by MODEL_PLAN.md.
- Storage: project-owned `price_bars`/`x_posts` schema, idempotent repositories and a leakage-safe cutoff join; tested in `tests/unit/test_storage_join.py`. The run CLI consumes persisted inputs (`xsentiment persist`, `run --database-url`; R15 verified offline in `tests/unit/test_phase3_ingestion_e2e.py`). Raw social data only where terms permit.
- Models: naive persistence baseline, price-only ridge model and candidate sentiment-plus-price ridge model, one per horizon, fitted on ratio targets.
- Validation: expanding walk-forward splits with a purge gap equal to the longest horizon, train-fold-only transforms and leakage guards.
- Backtesting: forecasts-to-returns strategy simulation and risk metrics from out-of-sample predictions only.
- Reporting: metric tables, SVG charts, one-page outlook and report assembly.
- Pipeline: offline run orchestration plus JSON/JSONL input loaders and the
  `fetch-prices`, gated `fetch-news`, `persist` and `run` CLI commands.
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
Implemented and verified on real public price data: checksum-verified Binance Vision BTCUSDT 180-day input (USDT quote); normalized X contract with raw-timestamp/offset provenance; deduplication, coverage, point-in-time alignment and horizon-label primitives with unfinished-day exclusion; VADER sentiment scoring; price features and supervised dataset; naive, price-only and candidate ridge models; purged walk-forward evaluation with per-horizon MAE/RMSE; predeclared long/flat strategy with Sharpe/Sortino/drawdown and disclosure; SVG charts; one-page outlook; evaluation report; and an offline CLI. News adapters are mocked-tested; one bounded Tavily call is live-checked. Current test counts are in [TEST_PLAN.md](TEST_PLAN.md).
Implemented and verified offline: versioned price/post tables, idempotent repositories, descriptive/cutoff joins, and a persisted-input CLI path (`xsentiment persist`, `run --database-url` with `input_source = persisted_storage` provenance; R15).
Implemented but not live-verified: configurable Apify X adapter with response-envelope handling, offset pagination and query provenance (mocked only; no Actor selected or run; ticker/cashtag/keyword inputs not exercised against a real Actor).
Implemented and verified offline: a gated Tavily news adapter and CLI with a streaming response ceiling writing normalized JSONL, `run --news-file` context-only integration, an SVG chart with price, sentiment-level and day-over-day sentiment-change panels, and a deterministic synthetic offline demo generator with full CLI end-to-end and network-isolation tests.
Not evidenced complete: live X ingestion, accepted licensing/coverage, sentiment-backed evaluation on real X text, a real-data sentiment-versus-price comparison, a real-data sentiment-change chart, Exa live behavior, exact BTC-USD pricing, and any claim that a model beats the naive baseline (the price-only measurement is worse than naive).
