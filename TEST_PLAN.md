# Test Plan
A passing suite proves only the cases it actually exercises.

## Layers
- Unit: validation, timestamps, deduplication, price coverage, features, targets, metrics and report formatting.
- Adapter contracts: mocked responses, pagination, timeout/error behavior, normalization and secret redaction; no billing.
- Integration: temporary storage/database and normalized data flow.
- End-to-end: explicit opt-in using accepted permitted data; no paid scrape by default.
- CI: Ruff, registry structural validation and pytest; describe only actual workflow checks.

## Required matrix
- Config: missing/invalid config and caps fail clearly; secrets never logged.
- X records: valid/missing optional fields, invalid IDs/timestamps, naive time rejection, negative counts.
- Point-in-time: future event excluded; late-retrieved post excluded even if old; no backdating.
- Deduplication: stable-ID exact duplicate handled deterministically; conflicting duplicate fails closed.
- Prices: UTC half-open bounds, ordering, malformed OHLCV, invalid OHLC relation, duplicates, out-of-range rows, missing dates, incomplete current day.
- Alignment: UTC boundary cases and trailing 24-hour window.
- Features: lags exclude target period; no posts/scores yield null; engagement excluded without snapshots.
- Targets: correct horizon mapping; missing/gapped/incomplete targets omitted; no targets in features.
- Validation: chronological folds, no leakage, transforms fit only on training folds, holdout isolation.
- Models/metrics: baseline consistency, per-horizon MAE/RMSE, edge cases and deterministic config.
- Trading metrics: invalid/zero returns and assumptions; no metrics without strategy return series.
- Reporting: cutoff/provenance, separate observed facts/predictions/news and unavailable metric labels.
- Profiler: CSV/JSONL, custom mappings, invalid times, duplicate/missing fields, no text printed.
- Apify: mocked run/status/dataset, auth header, bounds, timeouts/errors, no launch retry and no real Actor in CI.
- Registry: source/platform identity and structural fields; validation does not imply live access or legal approval.

## Data profile acceptance
Report row count, UTC min/max, required-window coverage/gaps, missing IDs/text/timestamps, duplicates, invalid timestamps, engagement-field availability, provider/query/window/retrieval time, version/run ID, terms-review status, hash if retained, and point-in-time limitations. Never print raw text or credentials.

## Reproducibility
Record commit, non-secret config, seed, dataset version/hash, schema version and fold boundaries. Re-run from a clean environment. Do not commit raw data to make tests pass.

## Release gates
Documentation: all nine canonical files agree; links/commands checked; statuses honest.
Ingestion: terms and source verified, real profile exists, point-in-time limitations documented, bounded end-to-end ingest passes.
Model/report: baselines and sentiment model run; walk-forward is leakage-safe; charts/outlook/report derive from actual outputs; risk metrics only from valid strategy returns.

## Commands
From repo root:
python -m pip install -e ".[dev,storage]"
ruff check src tests scripts
python scripts/validate_dataset_registry.py
pytest
Live-provider tests remain opt-in and must not run in ordinary CI.
