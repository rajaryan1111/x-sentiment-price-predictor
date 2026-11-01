# Recomputed results

The Binance-derived observations and metrics in this document are included under
CC BY-NC-SA 4.0 with attribution to Binance Vision; non-commercial use only. See
[`reports/btcusdt-180d/ATTRIBUTION.md`](../reports/btcusdt-180d/ATTRIBUTION.md).

## Run basis

- Binance Spot BTCUSDT, quote USDT; daily UTC bars from 2026-05-05 through
  2026-10-31 (180 rows, 0 gaps, 0 duplicates).
- Five expanding walk-forward folds; 60 minimum training rows, 20 test rows and
  five-row purge/embargo; 100 out-of-sample samples per model and horizon.
- Models: naive persistence, price-only ridge, sentiment-plus-price ridge.
- X posts supplied: 0; posts scored: 0; cutoffs with scored sentiment: 0.

## Aggregate forecast result

| Model | Mean MAE (USDT) | Relative to naive |
| --- | ---: | ---: |
| Naive persistence | 1,824.23 | baseline |
| Price-only ridge | 2,378.50 | 30.38% worse |
| Sentiment-plus-price candidate | 2,378.50 | identical without sentiment |

No sentiment effect can be inferred. Per-horizon MAE/RMSE, fold predictions,
benchmarks, assumptions and limitations are in the generated files under
`reports/btcusdt-180d/`.

## Strategy risk metrics

The defined price-only long/flat strategy has Sharpe 1.124, Sortino 2.431 and
maximum drawdown 5.885%. The benchmark, fees, exposure and risk-metric conventions
are in `reports/btcusdt-180d/evaluation-report.md` and `metrics.json`. These are
out-of-sample sample statistics, not a claim of accuracy or profitability.

## Limitations

This is BTCUSDT (USDT quote), not the exact BTC-USD pair. There are no accepted X
posts, so sentiment contribution is not measured. Binance Vision terms limit this
data and its derivatives to non-commercial use with attribution and share-alike.
An employer decision is required on BTCUSDT acceptability or an approved exact-USD
source.
