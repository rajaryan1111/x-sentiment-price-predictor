# Historical results recorded in committed artifacts

Source: `reports/btc-usd-180d/metrics.json`, `manifest.json`, `evaluation-report.md`, `outlook.md`, and `sentiment-vs-price.svg`. The underlying 180-day price snapshot and per-prediction rows are not present in this checkout. Values below were cross-checked against the aggregate metrics artifact and report; they were not freshly recomputed from raw data in this audit.

## Run basis

- BTC-USD daily, UTC; manifest records 180 bars from 2026-04-29 through 2026-10-25.
- X posts supplied: 0; posts scored: 0; eligible cutoffs with scored sentiment: 0.
- Five purged expanding walk-forward folds, 20-row test blocks and five-row purge.
- The metrics artifact records 100 evaluation samples for each model/horizon and 1,800 model/horizon evaluations (3 × 6 × 100). Per-row `predictions.jsonl` is not included.
- Models: naive persistence, price-only ridge, sentiment-plus-price ridge.

## Forecast results (reported MAE in USD; RMSE in parentheses)

| Horizon | Naive | Price-only ridge | Sentiment-plus-price ridge |
| --- | ---: | ---: | ---: |
| n+0 | 946.70 (1,462.93) | 1,056.82 (1,561.29) | 1,056.82 (1,561.29) |
| n+1 | 1,434.59 (2,112.26) | 1,665.02 (2,332.84) | 1,665.02 (2,332.84) |
| n+2 | 1,758.95 (2,653.80) | 2,108.22 (3,115.22) | 2,108.22 (3,115.22) |
| n+3 | 2,003.41 (3,190.92) | 2,527.34 (3,831.48) | 2,527.34 (3,831.48) |
| n+4 | 2,257.53 (3,669.37) | 2,897.59 (4,384.25) | 2,897.59 (4,384.25) |
| n+5 | 2,568.99 (4,104.76) | 3,332.72 (4,952.22) | 3,332.72 (4,952.22) |
| **Mean MAE** | **1,828.36** | **2,264.62** | **2,264.62** |

The aggregate metrics say naive persistence outperformed price-only ridge by 23.86% on mean MAE. The sentiment-plus-price candidate is identical because no posts were scored; no sentiment benefit is shown.

## Strategy metrics recorded in the artifact

| Strategy | Cumulative net return | Sharpe | Sortino | Max drawdown | Exposure |
| --- | ---: | ---: | ---: | ---: | ---: |
| Naive rule | 0.00% (never trades) | undefined | undefined | 0.00% | 0/100 days |
| Price-only | +10.91% | 1.807 | 3.979 | 4.08% | 32/100 days |
| Sentiment-plus-price | +10.91% | 1.807 | 3.979 | 4.08% | 32/100 days |
| Unconditional long benchmark | +6.11% | 0.752 | 1.377 | 10.33% | 100/100 days |

The report records 0.1% fee per side and 365-period annualization. The values are sample-specific strategy statistics, not future-return claims. The naive ratios are undefined because its return series has no dispersion.
