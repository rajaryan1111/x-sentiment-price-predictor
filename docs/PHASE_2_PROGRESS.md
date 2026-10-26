# Phase 2 — Data access and ingestion progress

**Status:** In progress. This document records implementation evidence separately from external-provider verification. No live data pull, paid scrape, model training, or performance claim is implied.

## Work started

### 1. Coinbase daily candle adapter

Implemented in `src/xsentiment/ingestion/prices.py` on branch `feat/phase-2-coinbase-price-ingestion`.

- Uses Coinbase Exchange public endpoint `GET /products/{product_id}/candles`.
- Requests daily granularity (`86400` seconds) for the configured product (Phase 1 default: `BTC-USD`).
- Requires timezone-aware request bounds and converts them to UTC.
- Enforces the provider's 300-candle maximum per request.
- Parses the documented six-field response rows into typed candles using `Decimal` for OHLCV values.
- Sorts records chronologically, rejects malformed rows, inconsistent OHLC values and duplicate timestamps.
- Filters the returned records locally to the project's UTC `[start, end)` range because Coinbase documents that returned data may include candles preceding the requested start.
- Uses the repository's shared HTTP client with bounded retries and response-size limits. No price API key is required by this public endpoint.

Official provider reference: https://docs.cdp.coinbase.com/api-reference/exchange-api/rest-api/products/get-product-candles

### 2. Automated tests added

`tests/unit/test_coinbase_prices.py` covers chronological sorting, decimal values, daily granularity, timezone-aware bounds, provider range limits, duplicate timestamps, malformed JSON, invalid OHLC values, and UTC normalization.

These are mocked unit tests. They do **not** prove that the live endpoint currently accepts this product/range, that all expected candles are present, or that a real 180-day dataset has been obtained. A read-only local smoke-test command is available at `python scripts/smoke_test_coinbase.py`; it checks the latest seven completed UTC daily bars and prints a coverage summary without saving raw data.

## External gates still open

1. **Live Coinbase verification:** perform a small, read-only request; record HTTP status, product availability, returned schema/order, coverage, missing UTC daily bars, boundary behavior, and a sanitized data-profile artifact. The web documentation confirms the endpoint and 86400-second daily granularity, and states a 300-candle maximum; the live endpoint response was not accessible through the web retrieval tool in this session.
2. **Historical X dataset:** retrieve the linked resource from the assessment and review actual contents, access permissions, license/terms, schema, timestamps, and whether text is available. Do not train on it until these checks are recorded.
3. **Apify:** inspect the user's available Actors and account pricing/terms; verify 180-day query strategy, output fields, actual plan rate and a strict run cost cap. No actor has been selected and no paid run has been initiated.
4. **Credentials:** confirm configuration privately; never add tokens, cookies, or credentials to Git.
5. **Deadline:** confirm the employer's actual submission deadline from the original message.

## Next implementation steps

1. Run CI and correct any failures from the adapter/tests.
2. Complete a read-only live price API smoke test when an execution environment with outbound network access is available; save only non-secret metadata and a schema/coverage profile.
3. Add deterministic price-data quality checks for missing UTC days, duplicate timestamps, bounds, and incomplete current-day candles.
4. Inspect the historical dataset and Apify Actor before implementing X ingestion; do not assume engagement fields are historically point-in-time.
5. Add the approved X post schema and adapter only after actor output and terms are verified.

## Phase 2 acceptance guardrails

- Do not commit raw provider data or secrets.
- Do not use current engagement counts as historical features without point-in-time snapshots.
- Do not infer missing candles or fabricate post fields.
- Do not begin model training until price/X coverage and timestamp availability have been profiled and the point-in-time cutoff is enforceable.
- Do not calculate trading metrics until out-of-sample strategy returns and cost assumptions exist.
