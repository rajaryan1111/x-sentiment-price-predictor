# Data access and ingestion progress — Phase 2 workstream

> Naming note: this file belongs to the repository's historical "Phase 2 data quality/alignment" workstream, which maps to canonical Phase 3 in [PHASES.md](../PHASES.md). It is not canonical documentation Phase 2.

**Status: partially implemented; external data-access gates remain open.** This document distinguishes code and test evidence from provider/account verification. Live X ingestion and a verified 180-day X dataset are not yet complete, so the sentiment-versus-price comparison remains blocked. Price-only models, walk-forward evaluation and reporting are implemented on `feat/sentiment-features-and-forecasting`. The offline suite is 167 tests, all passing as of 2026-10-28; see [TEST_PLAN.md](../TEST_PLAN.md) for the authoritative current count.

## Implemented and locally verified

### Coinbase daily candles

- Public Coinbase Exchange daily-candle adapter for configured BTC-USD.
- UTC-aware bounds, daily granularity, provider range limit, Decimal OHLCV parsing, sorting, malformed-row and duplicate checks.
- Local smoke script checks seven completed daily bars without saving raw market data.
- User-run live smoke test succeeded for 2026-10-19 through 2026-10-25: 7 candles, no missing bars in that seven-day window.
- User-run 180-day live coverage profile succeeded for the half-open UTC range 2026-04-29 through 2026-10-26: 180 observed bars, no missing dates, duplicate timestamps, or out-of-range timestamps; current-day candle excluded; raw data not saved.
- User-run test output on the pre-Apify state showed 25 tests passing. The GitHub CI after the Apify adapter addition passed lint, registry validation and pytest at that stage.

### Data-quality and point-in-time primitives

Implemented in src/xsentiment/pipeline/phase2.py:

- Canonical XPostRecord keeps event time and retrieval/availability time distinct and validates timestamps and optional fields. It also preserves the raw provider timestamp, supplied UTC offset, payload hash, author ID, query mode/query, schema version and non-fatal warnings. The JSONL loader round-trips these audit fields.
- Stable-ID deduplication fails closed on conflicting duplicate IDs.
- Daily price coverage report enumerates missing UTC days, duplicate timestamps, out-of-range records and possible incomplete current-day candles. It never fills missing candles.
- Point-in-time feature builder uses prior completed closes and only posts published and retrieved by each cutoff; current engagement counts are deliberately excluded as historical features.
- Close-target builder creates n+0 through n+5 labels only where the full horizon exists; target labels remain separate from features.
- Unit tests cover late-arriving/future-post exclusion, missing sentiment, duplicate IDs, missing price bars and horizon tails.

These are the data-quality primitives. The sentiment branch now adds VADER scoring, price/sentiment features and a supervised dataset; this section describes only the data-quality layer.

### Configurable Apify X adapter

- `src/xsentiment/ingestion/apify_x.py` now has an explicit Actor-run flow and normalization for common tweet field aliases.
- Requires a configured token and Actor ID; a run is never initiated by importing the module.
- Requires a caller-supplied Actor input JSON object and explicit max-items, max-total-charge and timeout caps.
- Uses a Bearer authorization header rather than a token query parameter; bounds response size; does not auto-retry the non-idempotent Actor launch request.
- Unwraps the documented `data` envelope on Actor run responses; dataset items remain a JSON array.
- Normalizes ID, text, timezone-aware creation time, optional engagement counts and provenance URL. It preserves the raw timestamp/offset and records ticker/cashtag/keyword query provenance. Unknown/missing fields stay null; it does not fabricate sentiment.
- Pages dataset items with the documented `offset`/`limit` parameters and stops at the caller's item cap. Apify's documented `maxItems` run option caps charges for pay-per-result Actors but does not itself guarantee the returned row count, so the adapter enforces the returned-row cap.
- Adds an explicit small-run schema smoke-test CLI and setup instructions. The script can incur cost only when a user explicitly runs it.
- Unit tests use mocked HTTP; CI does not run the Actor or incur Apify costs.

**Live Apify remains unverified.** No particular Actor has been selected or run in this session. The Actor's exact input/output schema, terms, 180-day reach and actual account pricing must be checked in the user's Apify account before the smoke-test CLI is executed.

### Local dataset profiler

The profiler now reports deterministic reference windows (`--as-of`), daily expected/observed/missing UTC dates and per-day counts, schema drift, duplicate/missing IDs, missing/invalid event and retrieval timestamps, invalid engagement counts, and rows with quality issues. It never prints post text, never writes the source file and always leaves `point_in_time_backtest_ready=false` because a downloaded snapshot cannot establish historical availability. Tests cover CSV/JSONL, duplicate/missing IDs, invalid counts, daily gaps, retrieval-time coverage, schema drift and deterministic output.

### Dataset registry

`validate_registry` now enforces the documented platform and text-availability vocabulary, ISO verification dates, date ordering, positive record counts, ID-only hydration caveats, and a recommendation only for X/Twitter sources with post text. The registry carries an explicit `independent_verification` object with status `not-reverified`; structural validity is not evidence of current provider access or legal approval.

### Persistent storage and join (R15 complete offline)

`src/xsentiment/storage/models.py` defines `price_bars` (composite key product/timestamp, one bar per product/UTC day) and `x_posts` (stable post ID, event/retrieval times, provenance, nullable engagement counts, warnings). `repositories.py` provides idempotent upserts and two joins: a descriptive same-UTC-day SQL join for reporting and a leakage-safe cutoff join that uses only posts published and retrieved by the cutoff plus the last completed prior close. `tests/unit/test_storage_join.py` verifies idempotency, earliest-retrieval retention, counts and late/future exclusion against in-memory SQLite. `scripts/persist_and_join.py` exposes the same path locally without network access and prints no post text. The end-to-end pipeline no longer reads file snapshots: `xsentiment persist` upserts snapshot inputs and `xsentiment run --database-url` runs the whole evaluation from persisted rows (manifest records `input_source = persisted_storage`), verified in `tests/unit/test_phase3_ingestion_e2e.py`; a database holding real X rows remains blocked on R2.

## External gates still open

1. **180-day Coinbase live price profile — verified by user-run check:** 180/180 daily bars for 2026-04-29 to 2026-10-26 UTC, no missing or duplicate dates and no out-of-range rows. Re-run at assessment time if newer coverage is needed; do not commit raw price data by default.
2. Historical X dataset: retrieve the assessment's linked resource and review contents, access permissions, terms/license, schema, event-time coverage, text availability and source platform before use.
3. Apify: inspect available Actors and account pricing/terms; verify query strategy, output fields, plan rate, 180-day coverage and strict run cost cap before any paid run. No actor selected and no paid run initiated.
4. Credentials: verify provider configuration privately; never add tokens, cookies or credentials to Git.
5. Employer constraints: confirm the actual submission deadline and any target-semantics clarification.

## Next steps recorded at the data-quality stage

Items 1, 2 and 5 below have since been completed on the sentiment branch and are retained as the historical plan. Items 3 and 4 remain open.

1. Run CI and local lint/tests on this branch.
2. Execute a bounded 180-day Coinbase price profile in chunks and inspect missing UTC days and boundary behavior.
3. Review historical dataset contents/terms and inspect the actual Apify actor schema before implementing a provider-specific X adapter.
4. Select/review the permitted Actor in the user's account, then run the bounded Apify schema smoke test and inspect its sanitized output before any larger collection.
5. Add an explicit sentiment model, train/evaluate baselines chronologically, and report only evidence-backed metrics.

## Guardrails

- No raw provider datasets, tokens, cookies or other secrets in Git.
- Current likes/reposts/views/follower counts are not historical features without point-in-time snapshots.
- No fabricated bars, missing fields, sentiment scores or evaluation metrics.
- No X-sentiment model training until X/price coverage and availability timestamps are profiled and point-in-time cutoffs are enforceable. Price-only models have been trained and evaluated on public price data.
- Trading risk metrics are unavailable until a defined strategy has valid out-of-sample returns and disclosed cost assumptions.


## CI at the data-quality workstream stage

The CI run for commit `49d2970681a581dc97d77c41ab9f267c4e5f0ef7` passed all configured steps: Ruff lint, dataset-registry structural validation, and pytest. This is a historical checkpoint, not the current branch head; current CI status is recorded in PHASES.md and the final Phase 1 report. The local dataset profiler is implemented in `src/xsentiment/ingestion/local_dataset_profile.py`, with a thin CLI at `scripts/profile_local_x_dataset.py` and unit tests in `tests/unit/test_local_dataset_profile.py`.

This verifies code quality only. It does not close the external X-data access, license, recent-coverage, or point-in-time availability gates below.

## Zero-budget fallback added

A local CSV/JSONL profiler is available at `scripts/profile_local_x_dataset.py`. It reports field detection, timestamp coverage, duplicate/missing IDs, missing text/time, engagement-field presence and rows in the last N days. It never prints post text or persists the source file. Example:

```bash
python scripts/profile_local_x_dataset.py /absolute/path/to/local_dataset.csv \
  --days 180 --as-of 2026-10-26T00:00:00+00:00
# If automatic field detection does not match the source schema:
python scripts/profile_local_x_dataset.py /absolute/path/to/local_dataset.csv \
  --id-column tweet_id --text-column full_text --timestamp-column created_at \
  --retrieved-column collected_at --days 180 --as-of 2026-10-26T00:00:00+00:00
```

This is an inspection utility, not an ingestion or licensing approval. The profiler intentionally reports `point_in_time_backtest_ready=false`: downloading an old dataset today does not establish what was observable at historical forecast cutoffs. A retrieval column is reported for coverage but is not assumed to be a defensible historical availability record. Do not backdate retrieval times.

See [Phase 2 no-cost data plan](PHASE_2_NO_COST_DATA_PLAN.md) for zero-budget paths and limitations. Most historical candidates in the registry end by 2023; two rolling sources have no verified coverage end. None can alone prove the required recent 180-day window without live verification. A free rolling crypto-X dataset listing may cover only the last month; verify current availability, terms and any infrastructure costs before relying on it.

## Remaining workstream acceptance gates

- Select a source that is accessible at zero cost and legally usable for the intended assessment.
- Profile the actual source file or bounded collection and establish coverage/schema/license evidence.
- Confirm 180-day coverage or explicitly record the shortfall; do not imply a 30-day sample satisfies 180 days.
- Validate real retrieval/availability timestamps before claiming leakage-safe historical features.
- Re-run local lint/tests and GitHub CI after these changes.


## Uploaded assessment-support files reviewed in this conversation

The uploaded `date-tweet-id.tsv` and `Twitter-historical-20060321-20090731-sample.txt` contain dates/counts or tweet IDs, not recoverable post text. The uploaded `statistics-full_dataset.tsv` and `statistics-full_dataset-clean.tsv` are date/count summaries (headers `date` and `tweet_id`), not post-level rows. These files can help describe archive coverage but cannot by themselves provide sentiment text or fulfill post-level X ingestion.

The earlier note said the ZIPs could not be inspected. That limitation was resolved on 2026-10-26 with local archive tools; the verified facts are:

- `90-day-samples.zip`: 14 text files (about 7.7 MB uncompressed) containing numeric tweet IDs only, no post text; the first and last members cover 2006-03-21 to 2009-07-31.
- `archive.zip`: one `globalAirQuality.csv`; unrelated to social data.
- The available `archive (1).zip`: 13 monthly JSON files (about 4.8 GB uncompressed) of MQTT environmental-sensor readings (CO2, temperature, humidity, etc.); unrelated to X; not social text.
- `archive (2).zip`, named in an earlier handoff, is not present in the accessible Downloads folder. Do not claim it was inspected.
- `Manuscript.pdf`: a 42-page StockTwits paper, not X data.

**Acceptance status remains open.** No uploaded file contains post-level X text or recent 180-day coverage. To close this gate, inspect a candidate dataset's member manifest and profile an actual post-level CSV/JSONL file (if present), then document the source/license and event-time coverage. If a source contains only tweet IDs, full text cannot be reconstructed without an authorized hydration/source path.

## Continuation after this workstream log

Sentiment scoring, price features, the supervised dataset, the naive/price-only/candidate models, purged walk-forward evaluation, the predeclared long/flat strategy, charts, the one-page outlook, the evaluation report and the offline CLI are now implemented and unit-tested on the branch `feat/sentiment-features-and-forecasting`. The X-data gate above is still open, so no sentiment result is claimed. Current status and measured evidence live in [PHASES.md](../PHASES.md), [MODEL_PLAN.md](../MODEL_PLAN.md) and [REQUIREMENTS_TRACEABILITY.md](REQUIREMENTS_TRACEABILITY.md); this file remains a historical log of the data-quality workstream, and its earlier test counts and CI references describe that period only.
