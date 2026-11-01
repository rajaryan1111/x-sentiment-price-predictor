# Final execution status — 2026-11-01

> Provider follow-up: see [the 2026-11-01 provider verification report](PROVIDER_VERIFICATION_2026-11-01.md) for the subsequent one-result Exa smoke check, the Tavily recheck and the CLI dispatch fix. The baseline observations below predate that follow-up.

This is the current evidence record for the execution audit. It supersedes older
handoff statements about Coinbase-derived results, missing price rows, and the
absence of a live Tavily request. Historical decision records remain in Git history.

## Assignment acceptance checklist

| Requirement | Current evidence | Status |
| --- | --- | --- |
| 180-day X post coverage | No accepted real posts or permitted current-period corpus; Apify Free plan blocks API actor use | Blocked externally |
| Apify integration and actor setup | Existing bounded adapter and preflight remain; configured actor is `apidojo/tweet-scraper`, but current account plan forbids API runs | Implemented, live collection blocked |
| Tavily news | Live bounded dated finance search; five results saved for audit, provider supplied no publication dates; news remains context-only | Implemented and live-checked; date metadata incomplete |
| Exa news | Official `/search` adapter, typed response envelope, date filters, timeout/body bounds, no retry, normalized provenance, CLI selector, mocked tests | Implemented; no live key |
| Price data | Binance Spot BTCUSDT, daily UTC, 2026-05-05 through 2026-10-31; 180 bars, no gaps or duplicates; source ZIPs and published checksums packaged | Recomputed; USDT proxy, not exact BTC-USD |
| Timestamped sentiment and features | Pipeline and point-in-time joins are implemented; this run supplied 0 posts and scored 0 | Software verified; empirical sentiment blocked |
| Horizons n+0 through n+5 | Six horizons, five expanding folds, 100 OOS samples per horizon/model | Recomputed on price data |
| Naive/price/sentiment model comparison | naive mean MAE 1,824.23 USDT; price-only 2,378.50 USDT; sentiment+price is numerically identical because no sentiment observations exist | Price-only measured; sentiment contribution not identifiable |
| Walk-forward, leakage and forecast metrics | 5 folds, 60 minimum train rows, 20 test rows/fold, 5-row purge/embargo, train-fold transforms; per-row predictions and per-horizon metrics packaged | Recomputed; existing tests cover temporal boundaries |
| Strategy risk metrics | Price-only Sharpe 1.124, Sortino 2.431, max drawdown 5.885%; identical sentiment-labelled candidate is not a sentiment result | Recomputed, with no performance claim |
| One-page outlook and dashboard | Fresh report, outlook, SVG and standalone offline HTML dashboard; empty sentiment is explicit and price unit is USDT | Complete for available data |
| Persistence and end-to-end flow | Existing database path remains offline-tested; source archives → snapshot → forecasting/report run completed | Offline workflow verified; no real X database run |
| Documentation/reproducibility | Canonical docs and submission materials reconciled; source build script verifies checksums and coverage | Verified locally |
| Demo/video | Reproducible demo script exists; no recorded video supplied or generated | Partial |

## Data and evaluation facts

- Price source: Binance Vision official Spot `BTCUSDT` daily klines; quote currency
  is **USDT**, not USD. Window is `[2026-05-05, 2026-11-01)` UTC. The 36 official
  archive ZIPs passed their published SHA-256 checksums. There are 180 daily rows,
  zero duplicates and zero missing dates. `reports/btcusdt-180d/` contains the
  checksummed archives, exact pipeline snapshot, manifest, metrics, predictions,
  chart, offline HTML dashboard, report and outlook.
- Binance Vision terms dated 2026-08-26 license the data and derivative works under
  CC BY-NC-SA 4.0, require Binance Vision attribution and the same license for
  redistributed derivatives, and exclude commercial use. The report folder carries
  that attribution/license. Do not use this dataset or its derivatives commercially.
- The fresh pipeline run used five chronological folds, 60 minimum train rows, 20
  test rows per fold, a five-row purge/embargo, and produced 100 out-of-sample rows
  per horizon and model (1,800 prediction rows total). The six horizons are n+0 to
  n+5. No X posts were supplied or scored.
- The mean MAEs are 1,824.23 USDT (naive), 2,378.50 USDT (price-only), and 2,378.50
  USDT (sentiment+price placeholder with no sentiment). Price-only did not beat
  naive on mean MAE. The output labelled sentiment+price must not be interpreted as
  an empirical sentiment model.
- The defined out-of-sample long/flat strategy reports price-only Sharpe 1.124,
  Sortino 2.431 and maximum drawdown 0.05885 (5.885%). Benchmark unconditional-long
  metrics and all per-horizon metrics are in `reports/btcusdt-180d/metrics.json`.

## Provider and external constraints

- Apify actor ID `61RPP7dywgiy0JPD0` resolves to `apidojo/tweet-scraper`. Its current
  Free plan is demo-only, limits API use, and the user's account cannot run it over
  API. No Actor run was launched. A paid plan or employer-provided export would be
  required; no purchase was made.
- Tavily's existing Researcher account had 0/1,000 plan usage before the one live
  search. The search requested finance news, an inclusive UTC date range, publication
  metadata and five results. Tavily returned null publication dates for all five;
  these are not treated as dated observations. News never enters predictive features.
- At this baseline audit, Exa API key was not configured. A subsequent bounded
  request is recorded in the provider follow-up report; account credit balance was
  not queried.
- Coinbase Market Data Terms prohibit using Coinbase Market Data to train, validate,
  benchmark or improve AI/ML models and prohibit redistributing derived analytics
  without prior written consent. No Coinbase data was fetched in this execution.
  Older Coinbase-derived metrics have been removed from the current repository tree;
  their prior Git objects remain in history because history rewriting is prohibited.
- Exact BTC-USD comparison, real sentiment contribution, Exa live verification, and
  the submission deadline remain unresolved. The assessment PDF gives both “within
  1 week” and “5–7 days”; ask the employer for the calendar deadline and whether
  BTCUSDT is acceptable in place of BTC-USD.

## Required next external actions

1. Ask the employer to provide an approved, rights-cleared X dataset/export covering
   the required period, or to approve a specific paid Apify plan/Actor and explicit
   maximum spend. Do not use the current Free-plan Actor API.
2. Ask whether the non-commercial BTCUSDT source is acceptable or obtain written
   permission/data access for an exact BTC-USD source suitable for model evaluation
   and redistribution.
3. Ask whether Exa is mandatory and, if so, provide an authorized Exa key/account
   with an explicit credit limit.
4. Confirm the calendar deadline and secure credential handoff channel. Keep tokens
   out of Git and plaintext email.
5. No email has been sent; the existing employer email remains a draft for separate
   explicit user authorization.
