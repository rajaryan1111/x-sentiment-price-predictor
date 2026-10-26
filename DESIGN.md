# System Design and Contracts
Status: canonical contract. Breaking changes require synchronized updates to tests and other canonical documents.

## Forecast/time contract
All internal timestamps are timezone-aware and normalized to UTC. Daily bars are labelled by candle start. Forecasts issue at 00:00 UTC at start of day n. Features may use only completed prior price bars and posts whose event and defensible availability times are no later than cutoff. Horizon h in 0..5 targets the close of the daily candle starting at cutoff + h days. n+0 is not yet known at issue time.

## Normalized X post
Required: post_id (non-empty stable source ID), created_at (timezone-aware event time), retrieved_at (first observed time, never inferred from created_at), source/platform/provider provenance. Text is nullable and stored only if returned and permitted.
Optional nullable fields: sentiment_score in [-1,1], likes, reposts, views, author_followers. Counts are non-negative integers when present. Null means unknown/unavailable/unscored, not zero or neutral.
Reject/quarantine invalid core timestamps, malformed IDs and negative counts with explicit reasons. Deduplicate by stable ID; conflicting duplicate payloads fail closed. Do not print text in profiler summaries.

## Price bar
product_id currently BTC-USD; timestamp is UTC candle start; OHLC are positive Decimal values and volume is non-negative. Validate low <= open/close <= high. Requests use half-open [start,end) bounds. Report duplicate, malformed, out-of-range and missing dates; never fabricate candles. Exclude unfinished current UTC day from observed-close inputs.

## Feature row
Key by asset and cutoff. Include cutoff, feature-window bounds, source/run references, price features derived only from completed prior candles, sentiment aggregates over (cutoff-24h, cutoff], coverage/missingness flags and provenance. If no eligible scored posts exist, sentiment is null, not neutral zero. Targets remain separate from feature columns.

## Targets
Exactly horizons 0..5 daily steps. Emit only when the required future candle exists and is valid; omit incomplete or gap-crossing horizons under the current conservative rule. Do not use target timestamps/values during feature creation.

## Adapter contract
Explicit config, timeouts and bounded response/run controls. Validate Actor input against the chosen Actor's current schema before a real run. Common field aliases do not prove Actor compatibility. Live Apify calls are opt-in and may cost money; never run them in CI. Sanitize errors and never print credentials.

## Output contracts
Forecast: asset, issue cutoff, horizon, predicted close, model version, feature/data run IDs and uncertainty/limitations.
Evaluation: chronological fold boundaries, sample counts, target/horizon, baseline/candidate metrics, exclusions and reproducible references.
Current outlook: as-of UTC time, latest completed bar, data coverage, sentiment coverage, contextual news source/time, model output if available, uncertainty and limitations.

## Versioning
Version persisted schemas and run manifests. Any target/schema change requires updated tests and DECISIONS.md. Never silently change target semantics after evaluation; start a new experiment version.
