# Unsent employer email draft

**To:** gilad@crowdwisdomtrading.com
**Status:** draft only. The recipient is from the assessment PDF and has not been independently mailbox-verified. No credentials are included.

**Subject:** X sentiment and BTC price forecasting assignment — results and required data decisions

Hello Gilad,

I have completed the forecasting pipeline, point-in-time data alignment, persistence path, six-horizon model comparison, purged walk-forward evaluation, risk metrics, offline dashboard, one-page outlook, and reproducibility package. PR #14 is open as a draft at https://github.com/rajaryan1111/x-sentiment-price-predictor/pull/14 on branch `feat/availability-basis-and-preflight`.

The reproducible evaluation covers 180 Binance Spot BTCUSDT daily bars from May 5 through October 31, 2026 (USDT quote, not USD), with five expanding folds, a five-row purge/embargo, six horizons, and 1,800 saved out-of-sample predictions. Naive persistence mean MAE is 1,824.23 USDT; price-only mean MAE is 2,378.50 USDT. Price-only is 30.38% worse than naive. There were zero accepted real X posts and zero scored posts, so no sentiment contribution can be established. The accompanying price-only strategy metrics are sample-specific research statistics, not a profitability claim.

One bounded live finance search each was made to Tavily and Exa. Tavily's result had a malformed publication timestamp, which was withheld; Exa's result had a publication timestamp and source metadata. No Apify Actor run or X collection was launched. The provider verification report records exact commands and remaining data-access blockers.

Attached are `x-sentiment-price-predictor-submission.zip` and `x-sentiment-price-predictor-FINAL_HANDOFF.md`.

To close the remaining data requirements, could you please confirm:

1. Whether you can provide a rights-cleared 180-day X export, or approve a named Actor/account and explicit item/spend cap with permission to use and retain the returned fields.
2. Whether BTCUSDT is acceptable, or provide/approve a rights-cleared BTC-USD source. Coinbase Market Data was not used; its current terms restrict ML use absent express written consent.
3. Whether live Exa verification is required and, if so, provide an authorized credential route and credit limit.
4. The `n+0` target convention and calendar deadline (the assessment gives both “within 1 week” and “5–7 days”).

The Binance Vision source data and its derived evaluation artifacts are attributed and licensed CC BY-NC-SA 4.0 for non-commercial use with share-alike obligations. I have not sent this message or submitted the assignment externally.

Regards,

Raj
