# Current submission summary — 2026-11-01

**Repository:** https://github.com/rajaryan1111/x-sentiment-price-predictor
**Current branch:** `feat/availability-basis-and-preflight`
**Current verdict:** READY WITH DISCLOSED EXTERNAL BLOCKERS; no email or external submission has been made.

The current handoff is [submission/FINAL_HANDOFF.md](../submission/FINAL_HANDOFF.md). The exhaustive 28-ID matrix is [REQUIREMENTS_TRACEABILITY.md](REQUIREMENTS_TRACEABILITY.md); measured checks and blockers are in the `submission/` packet. Older branch/CI details in dated engineering logs describe only their stated historical revisions.

## Implementation

The Python CLI includes BTC-USD daily price ingestion, a configurable Apify adapter and safe preflight, UTC point-in-time alignment, sentiment and price feature generation, six forecast horizons, naive/price-only/sentiment-plus-price models, purged expanding walk-forward evaluation, strategy risk metrics, SQL persistence/joins, an SVG chart, a one-page outlook, Markdown reports, dataset profiling, and offline tests. Tavily is an optional, explicitly gated, context-only integration. Exa is not implemented.

## Assignment evidence

The original assignment PDF and companion dataset-reference PDF were re-opened and read in full on 2026-11-01 from user-provided copies outside the repository. Page counts and verified hashes are in the traceability matrix. They are not committed and are excluded from the ZIP.

The committed historical run records 180 BTC-USD candles and zero X posts / zero scored sentiment observations. Its aggregate metrics say naive persistence has mean MAE $1,828.36 and price-only ridge $2,264.62; sentiment-plus-price matches price-only because sentiment is absent. The raw price snapshot and per-row prediction file are not in this checkout, so these values were cross-checked against committed aggregate metrics, not freshly recomputed from raw rows.

The offline demo and mock-backed provider tests verify software behavior only. No live Apify, Tavily, Exa, or Coinbase call was made during this audit, and no paid Actor ran. No model-quality or profitability claim is made.

## Current external blockers

- Employer-approved X source/Actor, terms, query coverage, and real 180-day data.
- Explicit item/USD spend ceiling and secure private credential-transfer route.
- Employer clarification of `n+0`, absolute deadline, Tavily/Exa expectations, and any additional demo format.
- The recipient printed in the assignment PDF is `gilad@crowdwisdomtrading.com`; it is not independently mailbox-verified.
- The historical aggregate evaluation cannot be retrained from this checkout without its raw input and prediction rows.

See [submission/REMAINING_BLOCKERS.md](../submission/REMAINING_BLOCKERS.md) for owners and exact actions.
