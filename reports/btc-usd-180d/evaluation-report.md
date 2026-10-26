# BTC-USD sentiment and price forecast evaluation

_Generated 2026-10-26T00:00:00+00:00 by the reproducible pipeline in this repository._

> Scope note: this report contains out-of-sample walk-forward results computed from the data described below. It states explicitly which requested metrics could not be produced and why.

## Data and provenance

- **input source:** file_snapshot
- **price snapshot:** data/btc-usd-daily-2026-04-29_2026-10-25.json
- **price snapshot sha256:** 09ce225a405aea390ae2f21c72634da1211a321aed1b39b52febfadf64083f75
- **asset:** BTC-USD
- **price candles supplied:** 180
- **posts supplied:** 0
- **sentiment scorer:** vader 3.3.2
- **pipeline versions:** {'python': '3.11.15', 'platform': 'macOS-26.1-arm64-arm-64bit', 'x-sentiment-price-predictor': '0.1.0', 'vaderSentiment': '3.3.2', 'pydantic': '2.14.1'}

## Dataset profile

| Item | Value |
| --- | --- |
| Forecast cutoffs built | 180 |
| Cutoffs with a full n+0..n+5 horizon | 175 |
| Cutoffs with scored-post sentiment | 0 |
| First cutoff (UTC) | 2026-04-29T00:00:00+00:00 |
| Last cutoff (UTC) | 2026-10-25T00:00:00+00:00 |
| Posts supplied | 0 |
| Posts scored | 0 |
| Unfinished current UTC day dropped | False |

## Evaluation design

- Expanding-window walk-forward folds: **5**
- Minimum training rows per fold: **60**
- Test rows per fold: **20**
- Purge/embargo rows between training and testing: **5**
- Ridge penalty (slope only): **1.0**
- Models compared on identical folds and eligible rows: naive persistence, price-only ridge, sentiment-plus-price ridge.
- Feature groups: price features are predeclared lagged/rolling price statistics; the price-only model never receives sentiment columns.
- Missing feature values are imputed with training-fold means and features are standardised with training-fold statistics only.
- No random shuffling is used anywhere: folds are chronological and the purge gap equals the longest horizon so labels cannot straddle the boundary.

## Out-of-sample forecast metrics

| Model | Horizon | Samples | MAE (USD) | RMSE (USD) | Mean error (USD) |
| --- | --- | --- | --- | --- | --- |
| naive | n+0 | 100 | 946.70 | 1,462.93 | -211.58 |
| naive | n+1 | 100 | 1,434.59 | 2,112.26 | -398.14 |
| naive | n+2 | 100 | 1,758.95 | 2,653.80 | -593.36 |
| naive | n+3 | 100 | 2,003.41 | 3,190.92 | -769.00 |
| naive | n+4 | 100 | 2,257.53 | 3,669.37 | -957.08 |
| naive | n+5 | 100 | 2,568.99 | 4,104.76 | -1,149.71 |
| price_only | n+0 | 100 | 1,056.82 | 1,561.29 | -146.43 |
| price_only | n+1 | 100 | 1,665.02 | 2,332.84 | -295.58 |
| price_only | n+2 | 100 | 2,108.22 | 3,115.22 | -432.18 |
| price_only | n+3 | 100 | 2,527.34 | 3,831.48 | -671.17 |
| price_only | n+4 | 100 | 2,897.59 | 4,384.25 | -1,066.44 |
| price_only | n+5 | 100 | 3,332.72 | 4,952.22 | -1,504.82 |
| sentiment_price | n+0 | 100 | 1,056.82 | 1,561.29 | -146.43 |
| sentiment_price | n+1 | 100 | 1,665.02 | 2,332.84 | -295.58 |
| sentiment_price | n+2 | 100 | 2,108.22 | 3,115.22 | -432.18 |
| sentiment_price | n+3 | 100 | 2,527.34 | 3,831.48 | -671.17 |
| sentiment_price | n+4 | 100 | 2,897.59 | 4,384.25 | -1,066.44 |
| sentiment_price | n+5 | 100 | 3,332.72 | 4,952.22 | -1,504.82 |

### Mean MAE across horizons

| Model | Mean MAE (USD) | Difference |
| --- | --- | --- |
| naive | 1,828.36 | +0.00% vs naive |
| price_only | 2,264.62 | +23.86% vs naive |
| sentiment_price | 2,264.62 | +23.86% vs naive |

A lower mean MAE than the naive persistence baseline is the minimum bar for claiming that a model adds information; this report makes no such claim beyond the numbers above.

## Trading strategy and risk metrics

- Decision at 00:00 UTC at the start of day n, using the last completed close close(n-1) and the model's n+1 close prediction.
- Long only when predicted n+1 close > close(n-1) * (1 + 2 x 0.001 fees); otherwise flat.
- Entry at close(n), exit at close(n+1); net return = close(n+1)/close(n) - 1 - 2 x 0.001.
- Annualisation uses 365 periods per year; risk-free rate 0 and Sortino MAR 0 are annualised before conversion.
- No shorting, no leverage, no position sizing; flat days contribute zero return.
- Benchmark: the same windows held long unconditionally with the same fees.
- Annualisation: 365 periods per year; the same conventions apply to every model below.

| Model | Long days | Exposure | Cumulative net return | Sharpe | Sortino | Max drawdown |
| --- | --- | --- | --- | --- | --- | --- |
| naive | 0 | +0.00% | +0.00% | unavailable | unavailable | +0.00% |
| price_only | 32 | +32.00% | +10.91% | 1.807 | 3.979 | +4.08% |
| sentiment_price | 32 | +32.00% | +10.91% | 1.807 | 3.979 | +4.08% |

### Benchmark (unconditional long, identical windows and fees)

| Model | Cumulative net return | Sharpe | Sortino | Max drawdown |
| --- | --- | --- | --- | --- |
| naive | +6.11% | 0.752 | 1.377 | +10.33% |
| price_only | +6.11% | 0.752 | 1.377 | +10.33% |
| sentiment_price | +6.11% | 0.752 | 1.377 | +10.33% |

### Risk metrics withheld

- **naive:** the strategy return series has zero dispersion over this sample, so the risk ratios are undefined

Sharpe, Sortino and maximum drawdown above describe this predeclared strategy on out-of-sample days. They are trading-strategy statistics, not evidence of forecast accuracy, and they are not a forecast of future performance.

## Warnings

- No eligible row has a scored-post sentiment mean, so the sentiment-plus-price candidate is not identifiable in this run and its coefficients cannot be interpreted.

## Current outlook snapshot

- As-of: 2026-10-26T00:00:00+00:00
- Forecast cutoff: 2026-10-25T00:00:00+00:00
- Last completed close (USD): 80,769.67
- Cutoffs with sentiment: 0
- Full one-page outlook: `outlook.md` in this run directory.

## Limitations

- Post text comes from the supplied snapshot only; no live X collection was performed for this run.
- Trading metrics describe a simple long/flat research strategy, not a deployable trading system.
- No scored post sentiment is available, so observed sentiment is unreported and the sentiment-plus-price candidate carries no sentiment information.

---

Fixtures and synthetic data are labelled as such and are never presented as real provider results. No accuracy, profitability or investment claim is made.
