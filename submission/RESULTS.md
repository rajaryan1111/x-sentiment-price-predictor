# Results (verified artefacts only)

Everything below is read from committed, reproducible artefacts in
[`reports/btc-usd-180d/`](../reports/btc-usd-180d/) (`manifest.json`,
`metrics.json`, `evaluation-report.md`, `outlook.md`,
`sentiment-vs-price.svg`), cross-checked against
[`docs/SUBMISSION_SUMMARY.md`](../docs/SUBMISSION_SUMMARY.md) and
[`docs/FINAL_VERIFICATION_REPORT.md`](../docs/FINAL_VERIFICATION_REPORT.md).
No number here is invented; where a metric could not be computed honestly, the
reason is stated.

## Run basis

- **Asset:** BTC-USD daily, UTC. **Price source:** Coinbase Exchange public
  candles — 180/180 bars, 2026-04-29 → 2026-10-25 UTC, no gaps or duplicates.
- **X data:** none accepted — 0 posts. This is the crunch limitation.
- **Evaluation:** 5 purged expanding walk-forward folds (60→140 training rows,
  20-row test blocks, 5-row purge); 100 out-of-sample days per model and
  horizon; 1,800 stored predictions.
- **Models:** naive persistence; price-only ridge; sentiment-plus-price ridge.

## Forecast metrics (MAE in USD; RMSE in parentheses)

| Horizon | Naive | Price-only ridge | Sentiment-plus-price ridge |
| --- | --- | --- | --- |
| n+0 | 946.70 (1462.93) | 1056.82 (1561.29) | 1056.82 (1561.29) |
| n+1 | 1434.59 (2112.26) | 1665.02 (2332.84) | 1665.02 (2332.84) |
| n+2 | 1758.95 (2653.80) | 2108.22 (3115.22) | 2108.22 (3115.22) |
| n+3 | 2003.41 (3190.92) | 2527.34 (3831.48) | 2527.34 (3831.48) |
| n+4 | 2257.53 (3669.37) | 2897.59 (4384.25) | 2897.59 (4384.25) |
| n+5 | 2568.99 (4104.76) | 3332.72 (4952.22) | 3332.72 (4952.22) |
| **Mean MAE** | **1828.36** | **2264.62** | **2264.62** |

Each cell is over n = 100 out-of-sample days.

## What the comparison shows

- The fitted price-only ridge is **23.86% worse** than naive persistence on
  mean MAE. On this sample, the extra features hurt rather than help.
- The sentiment-plus-price model is **identical, digit for digit**, to the
  price-only model — because zero scored posts existed, all sentiment features
  were null and the sentiment columns were not identifiable. The committed
  metrics carry the warning: *"No eligible row has a scored-post sentiment
  mean, so the sentiment-plus-price candidate is not identifiable in this run
  and its coefficients cannot be interpreted."*
- **Honest conclusion:** nothing here demonstrates that sentiment adds
  predictive value. That experiment cannot run until an accepted, permitted
  180-day X corpus exists (blockers R2/A2/B1–B10). We report the price-only
  finding as measured rather than substituting synthetic sentiment.

## Strategy / risk metrics (predeclared long/flat, out-of-sample, net of 10 bps fees)

| Metric | Naive-rule strategy | Price-only strategy | Sentiment strategy | Unconditional long benchmark |
| --- | --- | --- | --- | --- |
| Cumulative net return | 0.00% (never trades) | **+10.91%** | +10.91% | +6.11% |
| Sharpe ratio | unavailable | **1.807** | 1.807 | 0.752 |
| Sortino ratio | unavailable | **3.979** | 3.979 | 1.377 |
| Max drawdown | 0.00% (never trades) | **4.08%** | 4.08% | 10.33% |
| Annualized volatility | 0.00% | 22.25% | 22.25% | 38.25% |
| Exposure / long days | 0.00 (0 days) | 32% (32 of 100) | 32% (32) | 100% |

- Naive never trades on this sample, so its risk ratios are undefined; the
  principled reason is preserved in `metrics.json`
  (`risk_metrics_unavailable_reason`), it is not a hidden gap.
- Fee rate 0.001 per side, 365-period annualization, zero risk-free rate,
  minimum 30 return observations — all recorded in the metrics artefact.
- Short-sample caveats: 32 long days, one asset, one 180-day period — the ratios
  are strategy statistics over one regime, not a robust performance claim.

## Availability-basis status

No run in this submission uses `archive_created_at`. Retrospective archive mode
is implemented and regression-tested but, by policy, unused until the
employer explicitly approves the availability assumption and the disclosure
note it requires (blocker B9). Every recorded artefact uses the leakage-safe
`observed` basis only.
