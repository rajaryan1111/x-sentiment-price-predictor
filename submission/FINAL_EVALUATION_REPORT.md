# Final evaluation report — 2026-11-01

## Scope

This report records the freshly recomputed price-only evaluation in
[`reports/btcusdt-180d/`](../reports/btcusdt-180d/). Binance Vision public market
data and all derived values here are CC BY-NC-SA 4.0, attributed to Binance Vision,
and non-commercial only; see the included [attribution](../reports/btcusdt-180d/ATTRIBUTION.md).

The result is not a full completion of the assessment. No eligible X corpus was
available, so the empirical sentiment comparison is blocked. The selected price
source is BTCUSDT (USDT quote), not exact BTC-USD; employer acceptance or an
approved rights-cleared USD source is still needed.

## Assignment status

| Requirement | Status | Evidence or remaining work |
| --- | --- | --- |
| 180-day X post data | BLOCKED | 0 accepted posts and 0 scored posts. Apify Free plan prohibits Actor API runs. Employer must provide permitted data or approve a paid plan/Actor and spend cap. |
| Apify integration | IMPLEMENTED, NOT LIVE | Bounded adapter and preflight exist; current configured Actor is `apidojo/tweet-scraper`; no Actor run was launched. |
| Tavily | IMPLEMENTED, LIVE-CHECKED | One bounded dated finance search returned five results but no publication dates. Dates remain null. |
| Exa | IMPLEMENTED, MOCK-VERIFIED | Official `/search` adapter, typed response, date filters, bounded HTTP handling and CLI selector. No key configured, no live call. Employer must confirm whether required. |
| Price data | RECOMPUTED, SOURCE VARIANCE | 180 Binance Vision BTCUSDT bars, 2026-05-05 through 2026-10-31 UTC, 0 gaps/duplicates, 36 archive checksum matches. USDT is not USD. |
| Timestamped sentiment and features | SOFTWARE IMPLEMENTED, NO EMPIRICAL POSTS | Pipeline and point-in-time controls remain; this run has no sentiment observations. |
| Forecast horizons | RECOMPUTED | n+0 through n+5; five expanding folds, 100 OOS samples per model/horizon, five-row purge/embargo. |
| Model comparison | PRICE-ONLY RESULT | naive mean MAE 1,824.23 USDT; price-only 2,378.50 USDT; candidate sentiment+price identical without scored posts. Price-only is 30.38% worse than naive. |
| Risk metrics | RECOMPUTED | Price-only strategy: Sharpe 1.124, Sortino 2.431, max drawdown 5.885%. These are defined OOS strategy statistics, not a profit claim. |
| Outlook/dashboard/chart | COMPLETE FOR AVAILABLE INPUT | Fresh one-page outlook, standalone offline HTML dashboard and SVG; sentiment panels are explicitly empty/unavailable and the quote unit is USDT. |
| Database and offline flow | VERIFIED OFFLINE | Existing idempotent storage, point-in-time join and run path are covered with fixtures. No real-X database flow is possible. |
| Demo | PARTIAL | Offline deterministic demo script exists. No recorded demo video is included. |
| Submission email | DRAFT ONLY | Not sent. No provider secret is included in the repository or package. |

## Recomputed forecast results

| Model | Mean MAE (USDT) | Relative to naive |
| --- | ---: | ---: |
| Naive persistence | 1,824.23 | baseline |
| Price-only ridge | 2,378.50 | 30.38% worse |
| Sentiment-plus-price candidate | 2,378.50 | identical because no sentiment was scored |

The evaluation used `[2026-05-05, 2026-11-01)` UTC source coverage. The 180-row
input snapshot is included with all archive ZIPs and published checksum sidecars.
There are 100 OOS rows per horizon/model and 1,800 prediction rows in total. The
full per-horizon MAE/RMSE, fold assignments, strategy benchmark and methodology are
in the generated evaluation report, metrics, manifest and predictions.

## Source restriction and limitations

Coinbase Market Data Terms prohibit use for ML training, validation, benchmarking
or improvement and prohibit distributing derived analytics without prior written
consent. No Coinbase data was fetched in this execution. Older Coinbase-derived
artifacts were removed from the current tree; prior Git objects remain because no
history rewrite was performed.

Binance Vision terms dated 2026-08-26 allow non-commercial open-source data-science
evaluations under CC BY-NC-SA 4.0, with attribution and the same license for
derivatives. The current report folder carries those terms. Do not use it
commercially. Exact BTC-USD remains open.

The assessment brief also states conflicting deadlines (“within 1 week” and
“5–7 days”). Employer clarification is required for the calendar deadline, whether
BTCUSDT is acceptable, whether Exa is required, and the target convention. The
full blocker/action list is in [FINAL_EXECUTION_STATUS](../docs/FINAL_EXECUTION_STATUS_2026-11-01.md).
