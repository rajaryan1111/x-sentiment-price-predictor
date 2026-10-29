# System Design and Contracts
Status: canonical contract. Breaking changes require synchronized updates to tests and other canonical documents.

## Forecast/time contract
All internal timestamps are timezone-aware and normalized to UTC. Daily bars are labelled by candle start. Forecasts issue at 00:00 UTC at start of day n. Features may use only completed prior price bars and posts whose event and defensible availability times are no later than cutoff. Horizon h in 0..5 targets the close of the daily candle starting at cutoff + h days. n+0 is not yet known at issue time.
When the caller supplies the current time, the unfinished UTC day is dropped before any feature or label is built, so a partial intraday close can never act as a completed prior close or as a horizon label.

## Normalized X post
Required: post_id (non-empty stable source ID), created_at (timezone-aware event time), retrieved_at (first observed time, never inferred from created_at), source/platform/provider provenance, and non-empty text. Text is stored only if returned and permitted; a record without recoverable text is rejected at the adapter boundary instead of being admitted with empty or fabricated text (D-022), so post-volume counts only describe posts that were actually observed with text.
Optional nullable fields: sentiment_score in [-1,1], likes, reposts, views, author_followers. Counts are non-negative integers when present. Null means unknown/unavailable/unscored, not zero or neutral.
Audit fields: source_created_at_raw preserves the provider timestamp string, source_utc_offset records the supplied offset, author_id is a pseudonymous stable reference when present, query_mode/query record ticker/cashtag/keyword provenance, source_record_hash is a SHA-256 of the provider item, schema_version identifies the normalization contract, and warnings records non-fatal data-quality notes. These fields are persisted with the post; raw text stays in the local ignored database.
Reject/quarantine invalid core timestamps, malformed IDs and negative counts with explicit reasons. Deduplicate by stable ID; conflicting duplicate payloads fail closed. Do not print text in profiler summaries.

## Price bar
product_id currently BTC-USD; timestamp is UTC candle start; OHLC are positive Decimal values and volume is non-negative. Validate low <= open/close <= high. Requests use half-open [start,end) bounds. Report duplicate, malformed, out-of-range and missing dates; never fabricate candles. Exclude unfinished current UTC day from observed-close inputs.

## Feature row
Key by asset and cutoff. Include cutoff, feature-window bounds, source/run references, price features derived only from completed prior candles, sentiment aggregates over (cutoff-24h, cutoff], coverage/missingness flags and provenance. If no eligible scored posts exist, sentiment is null, not neutral zero. Targets remain separate from feature columns.

## Targets
Exactly horizons 0..5 daily steps. Emit only when the required future candle exists and is valid; omit incomplete or gap-crossing horizons under the current conservative rule. Do not use target timestamps/values during feature creation.

## Supervised row and model target
Each supervised row is anchored at one UTC cutoff and carries exactly the predeclared feature groups in `xsentiment.features.dataset.FEATURE_GROUPS`:

- price group: `return_1d`, `return_3d`, `return_7d`, `volatility_7d`, `range_1d`, `close_vs_sma_7d`;
- sentiment group: `post_count_24h`, `scored_post_count_24h`, `mean_sentiment_24h`, `positive_share_24h`, `negative_share_24h`.

A feature is null when its window lacks the required history. Imputation with training-fold means and standardisation with training-fold statistics happen inside the model layer only. The price-only baseline never receives sentiment columns; the candidate model receives both groups.
Models predict the horizon ratio `close(cutoff + h) / reference_close`, where `reference_close` is the last completed close known at the cutoff. A predicted close is `reference_close x predicted ratio`, which keeps model output directly comparable with the naive persistence baseline, whose prediction is exactly ratio `1.0`.
The strategy uses the `n+0` close as its entry price and the `n+1` close as its exit price, with `reference_close` only in the signal; see MODEL_PLAN.md for the rule and its assumptions.

## Adapter contract
Explicit config, timeouts and bounded response/run controls. Validate Actor input against the chosen Actor's current schema before a real run. Common field aliases do not prove Actor compatibility. The brief requires ticker, cashtag and keyword searches for the chosen asset; because the adapter accepts a caller-supplied input, the selected Actor's schema must map all three query modes explicitly and the non-secret query configuration must be recorded. No universal payload is assumed. Live Apify calls are opt-in and may cost money; never run them in CI. Sanitize errors and never print credentials.

## Persistence
`src/xsentiment/storage/models.py` defines versioned `price_bars` and `x_posts` tables. Price bars are keyed by `(product_id, timestamp)` and constrained to one row per `(product_id, UTC bar_date)`; posts use the stable source `post_id` as primary key and keep `created_at`, `retrieved_at`, provenance, nullable engagement counts and a JSON warnings column. `repositories.py` provides idempotent upserts and two joins:

- `daily_post_price_join` is a descriptive SQL join by UTC event date. It must not feed a historical model because the same-day close is not known at that day's cutoff.
- `cutoff_post_price_join` aggregates only posts in `(cutoff - 24h, cutoff]` with `retrieved_at <= cutoff`, and joins the last completed bar strictly before the cutoff. This is the leakage-safe shape.

The pipeline consumes this path offline: `xsentiment persist` upserts snapshot inputs and `xsentiment run --database-url` reads candles and posts from the same rows (manifest provenance records `input_source = persisted_storage` and the snapshot IDs; verified in `tests/unit/test_phase3_ingestion_e2e.py`). Row provenance keeps each row's non-null `source_snapshot_id`. Raw post text and private data stay out of Git; the database is a local ignored artefact.

## Output contracts
Forecast: asset, issue cutoff, horizon, predicted close, model version, feature/data run IDs and uncertainty/limitations.
Evaluation: chronological fold boundaries, sample counts, target/horizon, baseline/candidate metrics, exclusions and reproducible references.
Current outlook: as-of UTC time, latest completed bar, data coverage, sentiment coverage, contextual news source/time, model output if available, uncertainty and limitations.
Chart: price, sentiment-level and sentiment-change panels sharing a time axis; each sentiment panel shows its own availability state and is labelled as empty when no scored posts exist, never zero-filled. The change series is the day-over-day difference of the trailing-24h mean between consecutively scored UTC cutoffs, unavailable when either day is unscored; it is reporting-only and never a model feature. The R10 gap is closed in code and fixtures; real-data rendering remains blocked on accepted X text.

## Artefacts of one run
A run directory contains `evaluation-report.md`, `outlook.md`, `sentiment-vs-price.svg`, `metrics.json`, `predictions.jsonl` and `manifest.json`. The manifest records the run ID, as-of time, dataset profile, fold boundaries, warnings, unavailable items, input hashes and library versions. Every record in `predictions.jsonl` is out-of-sample; in-sample predictions are never written into an evaluation artefact.

## Versioning
Version persisted schemas and run manifests. Any target/schema change requires updated tests and DECISIONS.md. Never silently change target semantics after evaluation; start a new experiment version.
