# Phase 2 — Data access and ingestion progress

**Status: partially implemented; external data-access gates remain open.** This document distinguishes code and test evidence from provider/account verification. Live X ingestion, a verified 180-day dataset, model training, and performance evaluation are not yet complete.

## Implemented and locally verified

### Coinbase daily candles

- Public Coinbase Exchange daily-candle adapter for configured BTC-USD.
- UTC-aware bounds, daily granularity, provider range limit, Decimal OHLCV parsing, sorting, malformed-row and duplicate checks.
- Local smoke script checks seven completed daily bars without saving raw market data.
- User-run live smoke test succeeded for 2026-10-19 through 2026-10-25: 7 candles, no missing bars in that seven-day window.
- User-run 180-day live coverage profile succeeded for the half-open UTC range 2026-04-29 through 2026-10-26: 180 observed bars, no missing dates, duplicate timestamps, or out-of-range timestamps; current-day candle excluded; raw data not saved.
- User-run test output on the pre-Apify state showed 25 tests passing. Latest GitHub CI after the Apify adapter addition passed lint, registry validation and pytest.

### Data-quality and point-in-time primitives

Implemented in src/xsentiment/pipeline/phase2.py:

- Canonical XPostRecord keeps event time and retrieval/availability time distinct and validates timestamps and optional fields.
- Stable-ID deduplication fails closed on conflicting duplicate IDs.
- Daily price coverage report enumerates missing UTC days, duplicate timestamps, out-of-range records and possible incomplete current-day candles. It never fills missing candles.
- Point-in-time feature builder uses prior completed closes and only posts published and retrieved by each cutoff; current engagement counts are deliberately excluded as historical features.
- Close-target builder creates n+0 through n+5 labels only where the full horizon exists; target labels remain separate from features.
- Unit tests cover late-arriving/future-post exclusion, missing sentiment, duplicate IDs, missing price bars and horizon tails.

These are deterministic primitives, not a forecasting system. Sentiment scores remain null until a separately specified sentiment model is configured.

### Configurable Apify X adapter

- `src/xsentiment/ingestion/apify_x.py` now has an explicit Actor-run flow and normalization for common tweet field aliases.
- Requires a configured token and Actor ID; a run is never initiated by importing the module.
- Requires a caller-supplied Actor input JSON object and explicit max-items, max-total-charge and timeout caps.
- Uses a Bearer authorization header rather than a token query parameter; bounds response size; does not auto-retry the non-idempotent Actor launch request.
- Normalizes ID, text, timezone-aware creation time, optional engagement counts and provenance URL. Unknown/missing fields stay null; it does not fabricate sentiment.
- Adds an explicit small-run schema smoke-test CLI and setup instructions. The script can incur cost only when a user explicitly runs it.
- Unit tests use mocked HTTP; CI does not run the Actor or incur Apify costs.

**Live Apify remains unverified.** No particular Actor has been selected or run in this session. The Actor's exact input/output schema, terms, 180-day reach and actual account pricing must be checked in the user's Apify account before the smoke-test CLI is executed.

## External gates still open

1. **180-day Coinbase live price profile — verified by user-run check:** 180/180 daily bars for 2026-04-29 to 2026-10-26 UTC, no missing or duplicate dates and no out-of-range rows. Re-run at assessment time if newer coverage is needed; do not commit raw price data by default.
2. Historical X dataset: retrieve the assessment's linked resource and review contents, access permissions, terms/license, schema, event-time coverage, text availability and source platform before use.
3. Apify: inspect available Actors and account pricing/terms; verify query strategy, output fields, plan rate, 180-day coverage and strict run cost cap before any paid run. No actor selected and no paid run initiated.
4. Credentials: verify provider configuration privately; never add tokens, cookies or credentials to Git.
5. Employer constraints: confirm the actual submission deadline and any target-semantics clarification.

## Next steps after access gates

1. Run CI and local lint/tests on this branch.
2. Execute a bounded 180-day Coinbase price profile in chunks and inspect missing UTC days and boundary behavior.
3. Review historical dataset contents/terms and inspect the actual Apify actor schema before implementing a provider-specific X adapter.
4. Select/review the permitted Actor in the user's account, then run the bounded Apify schema smoke test and inspect its sanitized output before any larger collection.
5. Add an explicit sentiment model, train/evaluate baselines chronologically, and report only evidence-backed metrics.

## Guardrails

- No raw provider datasets, tokens, cookies or other secrets in Git.
- Current likes/reposts/views/follower counts are not historical features without point-in-time snapshots.
- No fabricated bars, missing fields, sentiment scores or evaluation metrics.
- No model training until X/price coverage and availability timestamps are profiled and point-in-time cutoffs are enforceable.
- Trading risk metrics are unavailable until a defined strategy has valid out-of-sample returns and disclosed cost assumptions.


## Latest repository verification

The latest CI run for commit `49d2970681a581dc97d77c41ab9f267c4e5f0ef7` passed all configured steps: Ruff lint, dataset-registry structural validation, and pytest. The local dataset profiler is implemented in `src/xsentiment/ingestion/local_dataset_profile.py`, with a thin CLI at `scripts/profile_local_x_dataset.py` and unit tests in `tests/unit/test_local_dataset_profile.py`.

This verifies code quality only. It does not close the external X-data access, license, recent-coverage, or point-in-time availability gates below.

## Zero-budget fallback added

A local CSV/JSONL profiler is available at `scripts/profile_local_x_dataset.py`. It reports field detection, timestamp coverage, duplicate/missing IDs, missing text/time, engagement-field presence and rows in the last N days. It never prints post text or persists the source file. Example:

```bash
python scripts/profile_local_x_dataset.py /absolute/path/to/local_dataset.csv --days 180
# If automatic field detection does not match the source schema:
python scripts/profile_local_x_dataset.py /absolute/path/to/local_dataset.csv \
  --id-column tweet_id --text-column full_text --timestamp-column created_at --days 180
```

This is an inspection utility, not an ingestion or licensing approval. The profiler intentionally reports `point_in_time_backtest_ready=false`: downloading an old dataset today does not establish what was observable at historical forecast cutoffs. Do not backdate retrieval times.

See [Phase 2 no-cost data plan](PHASE_2_NO_COST_DATA_PLAN.md) for zero-budget paths and limitations. Existing historical candidates in the registry end by 2023 and therefore cannot alone satisfy a recent 180-day window. A free rolling crypto-X dataset listing may cover only the last month; verify current availability, terms and any infrastructure costs before relying on it.

## Remaining Phase 2 acceptance gates

- Select a source that is accessible at zero cost and legally usable for the intended assessment.
- Profile the actual source file or bounded collection and establish coverage/schema/license evidence.
- Confirm 180-day coverage or explicitly record the shortfall; do not imply a 30-day sample satisfies 180 days.
- Validate real retrieval/availability timestamps before claiming leakage-safe historical features.
- Re-run local lint/tests and GitHub CI after these changes.


## Uploaded assessment-support files reviewed in this conversation

The uploaded `date-tweet-id.tsv` and `Twitter-historical-20060321-20090731-sample.txt` contain dates/counts or tweet IDs, not recoverable post text. The uploaded `statistics-full_dataset.tsv` and `statistics-full_dataset-clean.tsv` are date/count summaries (headers `date` and `tweet_id`), not post-level rows. These files can help describe archive coverage but cannot by themselves provide sentiment text or fulfill post-level X ingestion.

The user also uploaded `90-day-samples.zip` and `archive (2).zip`. The current execution environment could materialize these files but could not run archive inspection commands, and the file reader cannot parse ZIP contents. Their internal member names, schema, source platform, terms, and post-text coverage therefore remain **unverified**. Do not claim these archives were profiled or integrated.

**Acceptance status remains open:** CI verifies the repository code, not the contents of these binary archives. To close this gate, inspect the ZIP member manifest and profile an actual post-level CSV/JSONL member (if present), then document the source/license and event-time coverage. If the archives contain only tweet IDs, full text cannot be reconstructed from IDs without an authorized hydration/source path.
