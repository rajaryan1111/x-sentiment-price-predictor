# Data contract — Phase 2 data-quality workstream

> Naming note: this file belongs to the repository's historical "Phase 2 data quality/alignment" workstream, which maps to canonical Phase 3 in [PHASES.md](../PHASES.md). It is not canonical documentation Phase 2.

## Scope

The first implementation target is BTC-USD with UTC daily bars. This contract defines normalized records and cutoff rules; it does not assert that any X provider is approved or available.

## Normalized X post

| Field | Type | Rule |
|---|---|---|
| post_id | string | Stable source identifier; required for deduplication |
| created_at | timezone-aware datetime | Original event time, normalized to UTC for calculations |
| retrieved_at | timezone-aware datetime | When the system first observed the record; never backdate it |
| text | non-empty string | Required for an admitted post; original text, subject to source terms and storage policy. A record without recoverable text is rejected at the adapter boundary rather than admitted with empty text, so post-volume counts only describe posts observed with text (see DESIGN.md and DECISIONS.md D-022) |
| sentiment_score | float or null | Optional model output in [-1, 1]; null means unscored, not neutral |
| likes/reposts/views/author_followers | non-negative integer or null | Preserve missingness; exclude from historical features without point-in-time snapshots |
| source_name / source_platform | non-empty string | Provider and platform identity; StockTwits must not be labelled X |
| source_created_at_raw | string or null | Original provider timestamp string retained for audit; never substituted for normalized time |
| source_utc_offset | string or null | Supplied UTC offset in `±HH:MM`; normalized event time is still UTC |
| author_id | string or null | Pseudonymous stable author reference when the source permits it |
| query_mode / query | enum or null / string or null | Ticker, cashtag, keyword or mixed search provenance; null when the source did not record it |
| source_record_hash | 64-char hex or null | SHA-256 of the provider item for reproducibility; contains no text in the clear |
| schema_version | non-empty string | Normalization contract version |
| warnings | tuple/list of strings | Non-fatal data-quality notes; missing remains missing |

The JSONL loader round-trips these fields and rejects malformed timestamps or an unknown query mode. The profiler can separately report a source's retrieval-time column, but a supplied retrieval field is not assumed to establish historical observability.

## Persistence keys

`price_bars` is keyed by `(product_id, timestamp)` with one row per `(product_id, UTC bar_date)`. `x_posts` is keyed by stable `post_id`; a later snapshot updates content/counts but retains the earliest `retrieved_at`. See DESIGN.md §Persistence and DECISIONS.md D-026.

## Price bars

- Product ID remains explicit (BTC-USD for this project).
- Timestamp is the start of a UTC daily candle.
- OHLC values are positive decimals, low <= open/close <= high; volume is non-negative.
- Requested ranges use a half-open interval [start, end) where end is exclusive.
- Missing daily bars are reported, never fabricated.
- Exclude an unfinished current UTC day from observed close inputs.

## Prediction cutoff and leakage prevention

For a forecast issued at UTC midnight t:

- Price-derived input features use only previously completed candles, never the close of the candle beginning at t.
- A post is eligible only if its event time and system retrieval time are both at or before t.
- The current implementation aggregates the trailing 24-hour interval (t - 24h, t]. A post retrieved after t is excluded even if its event time is earlier.
- Engagement values are retained for provenance but not used as historical predictors absent point-in-time snapshots.
- Sentiment features are null when no scored posts exist; do not replace null with zero without an explicit, train-fitted missing-data policy.

## Targets

Targets are separate labels, never input features. n+0 through n+5 refer to closes of candles beginning at the forecast cutoff and the next five daily cutoffs. Rows with incomplete forward horizons are omitted rather than padded.

## Evidence and limits

Unit tests validate deterministic rules. They do not prove source terms, provider coverage, predictive quality, profitability, or correctness of a sentiment model. Record provider, query/window, retrieval timestamp, schema version and a non-secret run identifier for each real collection.
