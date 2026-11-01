# Employer email — prepared for final release

**To:** gilad@crowdwisdomtrading.com

**Subject:** X sentiment and BTC price forecasting assignment — results and data decisions
**State:** Prepared; the actual send is gated on final PR, CI, and package verification. The recipient is the address printed in the assessment PDF and has not been independently mailbox-verified. No credentials are included.

Hello Gilad,

The repository contains the forecasting and data pipeline, point-in-time feature controls, multi-query X-post merge with provenance, optional `--posts-provenance` binding, price-only baselines, purged walk-forward evaluation, provider integrations, reproducibility instructions, and offline dashboard. The current implementation is available in [PR #14](https://github.com/rajaryan1111/x-sentiment-price-predictor/pull/14); the X-post integration commit is [8fab74e](https://github.com/rajaryan1111/x-sentiment-price-predictor/commit/8fab74e09cf0ae6ecfc5a69dde00519ce9163bc2). The exact final PR-head commit is linked in the release handoff.

The measured evaluation uses 180 Binance Vision Spot BTCUSDT daily bars from May 5 through October 31, 2026. The quote is USDT, not USD. Across five expanding folds, a five-row purge/embargo, six horizons, and 1,800 saved out-of-sample prediction rows, naive persistence mean MAE is 1,824.23 USDT and price-only ridge mean MAE is 2,378.50 USDT. Price-only is 30.38% worse than naive. The price-only strategy reports Sharpe 1.124, Sortino 2.431, and maximum drawdown 5.885%; these are sample-specific research statistics, not a profitability claim.

There were zero accepted real X posts and zero scored posts. Real sentiment forecasting has **not** been validated, and the candidate model result does not establish sentiment lift. Tests use deterministic synthetic records only. One bounded live request each was made to Tavily and Exa: Tavily's returned publication timestamp was malformed and withheld; Exa returned one item with publication time and source metadata. Apify authentication and Actor metadata were verified, but no Actor run or scraping-credit use occurred. Apify historical search does not guarantee complete historical coverage. News remains context-only and separate from predictive sentiment features.

The Binance Vision source data and derived evaluation artifacts are CC BY-NC-SA 4.0, attributed to Binance Vision, and non-commercial only. Coinbase Market Data was not used because its terms restrict ML evaluation and derived-artifact distribution without express written consent.

The report and documentation are available in the repository, including the [evaluation PDF](https://github.com/rajaryan1111/x-sentiment-price-predictor/blob/feat/availability-basis-and-preflight/submission/FINAL_EVALUATION_REPORT.pdf), [Markdown evaluation](https://github.com/rajaryan1111/x-sentiment-price-predictor/blob/feat/availability-basis-and-preflight/submission/FINAL_EVALUATION_REPORT.md), [provider verification](https://github.com/rajaryan1111/x-sentiment-price-predictor/blob/feat/availability-basis-and-preflight/docs/PROVIDER_VERIFICATION_2026-11-01.md), and [reproducibility guide](https://github.com/rajaryan1111/x-sentiment-price-predictor/blob/feat/availability-basis-and-preflight/submission/REPRODUCIBILITY.md). The curated submission ZIP was integrity-checked, but the connected Gmail sender cannot attach files; the ZIP will need a separate delivery method. No file is described as attached.

To complete the empirical assignment, could you please confirm:

1. Whether you can provide a rights-cleared 180-day X export, or approve a named source/Actor, its terms, and an explicit item/spend cap.
2. Whether BTCUSDT is acceptable, or provide/approve a rights-cleared BTC-USD source suitable for ML evaluation and distribution.
3. Whether ongoing Exa use is required and, if so, the authorized account and credit limit.
4. The intended `n+0` target convention and calendar deadline; the brief states both “within 1 week” and “5–7 days.”

Regards,

Raj
