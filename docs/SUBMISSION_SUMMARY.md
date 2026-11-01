# Current submission summary — 2026-11-01

**Repository:** https://github.com/rajaryan1111/x-sentiment-price-predictor
**Final branch:** `feat/availability-basis-and-preflight`
**Status:** SUBMISSION READY WITH EXTERNAL BLOCKERS; final email and delivery state are recorded in the external release handoff.

See [FINAL_EXECUTION_STATUS](FINAL_EXECUTION_STATUS_2026-11-01.md), the current
[evaluation report](../submission/FINAL_EVALUATION_REPORT.md), and the
[28-ID requirement matrix](REQUIREMENTS_TRACEABILITY.md).

The Python project has bounded Apify preflight/ingestion, Tavily and Exa news
adapters, point-in-time joins, sentiment/price feature generation, six horizons,
naive and ridge baselines, purged walk-forward evaluation, risk metrics, SQL
persistence, chart/outlook/report generation, and offline tests. Exa uses official
`/search` semantics and one bounded live smoke verification; no ongoing use or
coverage claim is made. Tavily has one bounded live search recorded; its malformed
publication timestamp was withheld.

The fresh real-price evaluation uses 180 Binance Vision BTCUSDT daily bars from
2026-05-05 through 2026-10-31 UTC, with source ZIPs/checksums and per-row predictions
packaged. Values are USDT. Binance Vision data and derived artifacts are
CC BY-NC-SA 4.0, with attribution/share-alike and non-commercial restrictions.
Naive mean MAE is 1,824.23 USDT and price-only MAE is 2,378.50 USDT; there are no X
posts, so no sentiment result can be inferred. Coinbase-derived artifacts were
removed from the current tree after the legal-terms review; Git history remains
unchanged.

The largest blockers are an approved rights-cleared 180-day X source and Actor or
employer-provided export; employer approval of BTCUSDT versus exact BTC-USD;
optional Exa key/requirement clarification; the conflicting deadline; and a private
credential channel. No live Apify run or Coinbase request was made. One bounded
Exa smoke request was made and one honest email was prepared for those unresolved
inputs. The exact delivery state is in the external release handoff.
