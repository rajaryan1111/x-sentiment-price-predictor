# Experiment methodology

The price evaluation and all derived values below are based on Binance Vision
Spot BTCUSDT data and are CC BY-NC-SA 4.0, with attribution and non-commercial
restriction. Full notice: [`reports/btcusdt-180d/ATTRIBUTION.md`](../reports/btcusdt-180d/ATTRIBUTION.md).

| Input | Use | Verification |
| --- | --- | --- |
| Binance Vision Spot BTCUSDT daily kline archives | Price features, targets, forecast labels and strategy replay | 36 ZIP archives with published checksum sidecars; May 5–Oct 31, 2026 UTC; 180 rows, no gaps/duplicates; reproducible using `scripts/build_binance_snapshot.py` |
| Real X posts | Sentiment features and time alignment | None accepted; no X posts were collected or scored |
| Tavily news | Outlook context only | One bounded live finance query returned one result with a malformed publication timestamp withheld; not a model input |
| Exa news | Optional outlook context | One bounded live search returned one result with publication/source metadata; not a model input |

Forecasts are issued at 00:00 UTC. The implementation predicts n+0 through n+5
daily closes and only uses completed prior bars and posts whose availability passes
the selected cutoff rule. Evaluation uses five chronological expanding folds,
training-fold-only scaling/imputation, a five-row purge/embargo, and 20-row test
blocks. Models are naive persistence, price-only ridge, and candidate sentiment+
price ridge; with no sentiment, the latter is not identifiable. The report includes
per-horizon MAE/RMSE and a predeclared long/flat strategy with fee and benchmark
assumptions. No accuracy or profitability claim is made.

Coinbase Market Data terms preclude ML use and redistribution of derived analytics
without written consent; no Coinbase data is included in this current evaluation.
