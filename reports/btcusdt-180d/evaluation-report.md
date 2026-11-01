# BTCUSDT sentiment and price forecast evaluation

_Generated 2026-11-01T08:08:24+00:00 by the reproducible pipeline in this repository._

> Scope note: this report contains out-of-sample walk-forward results computed from the data described below. It states explicitly which requested metrics could not be produced and why.

## Data and provenance

- **input source:** file_snapshot
- **price snapshot:** reports/btcusdt-180d/btcusdt-180d-snapshot.json
- **price snapshot sha256:** b8e247382e9de64c95dddb63e1af20eddd78df11f3ff28961797be30d55a295f
- **price snapshot metadata:** {'granularity_seconds': 86400, 'requested_start': '2026-05-05T00:00:00+00:00', 'requested_end': '2026-11-01T00:00:00+00:00', 'fetched_at': '2026-11-01T08:06:32.369608+00:00', 'fetch_mode': 'binance_vision_public_archive', 'venue': 'Binance Spot', 'quote_currency': 'USDT', 'timestamp_unit': 'microseconds', 'source_license': 'CC BY-NC-SA 4.0', 'source_license_url': 'https://github.com/binance/binance-public-data/blob/master/TERMS_AND_CONDITIONS.md', 'source_archive_count': 36, 'source_archive_sha256': {'BTCUSDT-1d-2026-05.zip': '978936e8f1f80b570248f8d4478d6fe08d94b98bc1c7d372feb27573ff466cde', 'BTCUSDT-1d-2026-06.zip': '7020d4d850a875b93f0b0fa6df4a4c36ab615273e2ab03f9e896852330dad77e', 'BTCUSDT-1d-2026-07.zip': '74ddc3e39aae9445b9f9dae00d53fe2ce6ff503ee469417e207a8f5970bad11a', 'BTCUSDT-1d-2026-08.zip': 'fd8374a811ac7d3f4144d9c857c4f10796402c178316a25ed0c2f0ca6e16a8c1', 'BTCUSDT-1d-2026-09.zip': '4944279ced64d3b1822c7c535043f2bbf41bc97d9000b8d857753352c1949769', 'BTCUSDT-1d-2026-10-01.zip': '544d2565f54cb6347dde9c65301ecd6a5bc9128a95deacad1b86d0d36ca6c1cc', 'BTCUSDT-1d-2026-10-02.zip': '97f00f9530c1ee2f091bb0fd157c2097e676cb4882c568490b2fed9d17d048da', 'BTCUSDT-1d-2026-10-03.zip': '4fad26c8ad8e581d66200b523a7b0fc723571cfe6c760f30f16497eb920a5d1b', 'BTCUSDT-1d-2026-10-04.zip': '7fbfe9a84ad5d0c2936b7cb489ea09f620e0813033a7d40043dd989f614175e1', 'BTCUSDT-1d-2026-10-05.zip': 'af132ef68300bdb34acbdab1aec6d44d8b0f54d9e6f64f5f11f6b252f67a7ec7', 'BTCUSDT-1d-2026-10-06.zip': 'a9bfe3f7405ad80ca56d0719faf533dd66a405f7cea562b5afeb4ab220ae6982', 'BTCUSDT-1d-2026-10-07.zip': '0ddcb0b01671d17e7ee9956fdb19f594f408e6b6b60c632fc29ac4c9dddf05b8', 'BTCUSDT-1d-2026-10-08.zip': '0478666aeb380f07ada5c94b667188b6d622c3e7c376b42960c0504484965ad9', 'BTCUSDT-1d-2026-10-09.zip': 'abc8f686e5559268bd4fd8cdac4b478f9c0810fe26944fa582282becb33ee2f4', 'BTCUSDT-1d-2026-10-10.zip': '7980c0fc7d3e7ef67fc5b9abb0b6dce5668b8cbf76c4828616aa1c315498a5fa', 'BTCUSDT-1d-2026-10-11.zip': '6d01694528255af58912b5d72b48bcd0ad70e44afa625960af0bd407efe7ac84', 'BTCUSDT-1d-2026-10-12.zip': '6f116c20200f77a156f93710d4c96c007594634c6771e71741a9dbd9f4fc995b', 'BTCUSDT-1d-2026-10-13.zip': 'bee3a7d79cb4be4049a9b5dd5ef85c518ebb5e7b711d8fe13216d8ea550b2525', 'BTCUSDT-1d-2026-10-14.zip': 'f6b81a85f0cb71e819e848459be1204d1a68857608f8a4789b0f53a4b4af1bc1', 'BTCUSDT-1d-2026-10-15.zip': '0861fcb0775f75f1af7b5b875e272098cf7650d3a8689d6f368c2382cd4a33be', 'BTCUSDT-1d-2026-10-16.zip': 'a45767513118a5736df58561dd3e4ff01e44144f18e78ee8731b215cfa59b385', 'BTCUSDT-1d-2026-10-17.zip': '431913f651322f4e8054f75fd23abfad9defb7cb0214c2a531a76f984802dbad', 'BTCUSDT-1d-2026-10-18.zip': '29e500f7e5cfa3fc4a97f88ab56d16be5db9a79e170b678c356262721f6bfd36', 'BTCUSDT-1d-2026-10-19.zip': '50742ef26e59bf3fc771e7de72d8e91001bb4b399abdfb6ed8dca1f6a7c7a903', 'BTCUSDT-1d-2026-10-20.zip': 'f1177f718234b1a8837bf0272b23e641e4927434949859d362d3ce5996b2aac5', 'BTCUSDT-1d-2026-10-21.zip': '75d684ac9217f446257c28fa64adde496663e0d2f4ef1fc792d1c98bd352d8fe', 'BTCUSDT-1d-2026-10-22.zip': '1019822046990d74301d261b91ff6803f9fe9f17b656d2f301da9b283669c6eb', 'BTCUSDT-1d-2026-10-23.zip': '7fe5726e570ede3db78f73cfb89ad9bbded88c433fd582d1a854e25a527c7d8d', 'BTCUSDT-1d-2026-10-24.zip': 'b7108895d708c42135d5e285cc9192293c06f2c546658f86dc0c56e3fdb9007a', 'BTCUSDT-1d-2026-10-25.zip': '6e04c8c8b7c36710edc0417e0a2385903a4fab3dbde7071aad3ddac58e70adba', 'BTCUSDT-1d-2026-10-26.zip': '2048aede533388813b08dd5e88e7092db406112da2055a5ab93d5184db469c68', 'BTCUSDT-1d-2026-10-27.zip': '72c4db0f5228822273217c47c900b2a889dfa53fd8429547343eaf362a441bc6', 'BTCUSDT-1d-2026-10-28.zip': 'fbe07acc308d9af87ca696c034932157d473d7e228d840429e52f8738578df67', 'BTCUSDT-1d-2026-10-29.zip': '4b252a9ff74183d87c30c3bebffd2f1d75fe75fa351a1faed2238a4ac5fa4e78', 'BTCUSDT-1d-2026-10-30.zip': '5495ac3369173deab2ab22f4d76d92fc5ab0bd1b2452b4f06ed4bc7d9e86a880', 'BTCUSDT-1d-2026-10-31.zip': '4d96c50c23891145fa974645d41376e06d1ba135e01a921fd9ffd421edf0e80c'}}
- **price snapshot retrieved at:** 2026-11-01T08:06:32.369608+00:00
- **code revision:** 422ff53d6e378fb3dcbafb0ddaf1040409dd0174
- **asset:** BTCUSDT
- **availability basis:** observed
- **price candles supplied:** 180
- **posts supplied:** 0
- **sentiment scorer:** vader 3.3.2
- **pipeline versions:** {'python': '3.11.15', 'platform': 'macOS-26.1-arm64-arm-64bit', 'x-sentiment-price-predictor': '0.1.0', 'vaderSentiment': '3.3.2', 'pydantic': '2.14.2'}

## Dataset profile

| Item | Value |
| --- | --- |
| Forecast cutoffs built | 180 |
| Cutoffs with a full n+0..n+5 horizon | 175 |
| Cutoffs with scored-post sentiment | 0 |
| First cutoff (UTC) | 2026-05-05T00:00:00+00:00 |
| Last cutoff (UTC) | 2026-10-31T00:00:00+00:00 |
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

| Model | Horizon | Samples | MAE (USDT) | RMSE (USDT) | Mean error (USDT) |
| --- | --- | --- | --- | --- | --- |
| naive | n+0 | 100 | 960.01 | 1,472.49 | -182.61 |
| naive | n+1 | 100 | 1,396.09 | 2,085.90 | -362.15 |
| naive | n+2 | 100 | 1,730.20 | 2,639.37 | -543.35 |
| naive | n+3 | 100 | 2,003.62 | 3,181.11 | -735.83 |
| naive | n+4 | 100 | 2,294.72 | 3,668.23 | -953.42 |
| naive | n+5 | 100 | 2,560.77 | 4,087.64 | -1,117.14 |
| price_only | n+0 | 100 | 1,083.98 | 1,582.70 | -146.32 |
| price_only | n+1 | 100 | 1,693.37 | 2,372.30 | -349.65 |
| price_only | n+2 | 100 | 2,202.64 | 3,181.43 | -529.32 |
| price_only | n+3 | 100 | 2,657.87 | 3,918.41 | -842.16 |
| price_only | n+4 | 100 | 3,078.52 | 4,529.73 | -1,318.36 |
| price_only | n+5 | 100 | 3,554.60 | 5,117.97 | -1,755.76 |
| sentiment_price | n+0 | 100 | 1,083.98 | 1,582.70 | -146.32 |
| sentiment_price | n+1 | 100 | 1,693.37 | 2,372.30 | -349.65 |
| sentiment_price | n+2 | 100 | 2,202.64 | 3,181.43 | -529.32 |
| sentiment_price | n+3 | 100 | 2,657.87 | 3,918.41 | -842.16 |
| sentiment_price | n+4 | 100 | 3,078.52 | 4,529.73 | -1,318.36 |
| sentiment_price | n+5 | 100 | 3,554.60 | 5,117.97 | -1,755.76 |

### Mean MAE across horizons

| Model | Mean MAE (USDT) | Difference |
| --- | --- | --- |
| naive | 1,824.23 | +0.00% vs naive |
| price_only | 2,378.50 | +30.38% vs naive |
| sentiment_price | 2,378.50 | +30.38% vs naive |

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
| price_only | 28 | +28.00% | +6.35% | 1.124 | 2.431 | +5.88% |
| sentiment_price | 28 | +28.00% | +6.35% | 1.124 | 2.431 | +5.88% |

### Benchmark (unconditional long, identical windows and fees)

| Model | Cumulative net return | Sharpe | Sortino | Max drawdown |
| --- | --- | --- | --- | --- |
| naive | +4.81% | 0.636 | 1.167 | +10.70% |
| price_only | +4.81% | 0.636 | 1.167 | +10.70% |
| sentiment_price | +4.81% | 0.636 | 1.167 | +10.70% |

### Risk metrics withheld

- **naive:** the strategy return series has zero dispersion over this sample, so the risk ratios are undefined

Sharpe, Sortino and maximum drawdown above describe this predeclared strategy on out-of-sample days. They are trading-strategy statistics, not evidence of forecast accuracy, and they are not a forecast of future performance.

## Warnings

- No eligible row has a scored-post sentiment mean, so the sentiment-plus-price candidate is not identifiable in this run and its coefficients cannot be interpreted.

## Current outlook snapshot

- As-of: 2026-11-01T08:08:24+00:00
- Forecast cutoff: 2026-10-31T00:00:00+00:00
- Last completed close (USDT): 77,368.77
- Cutoffs with sentiment: 0
- Full one-page outlook: `outlook.md` in this run directory.

## Limitations

- Post text comes from the supplied snapshot only; no live X collection was performed for this run.
- Trading metrics describe a simple long/flat research strategy, not a deployable trading system.
- No scored post sentiment is available, so observed sentiment is unreported and the sentiment-plus-price candidate carries no sentiment information.
- Post text comes from the supplied snapshot only; no live X collection was performed for this run.
- Trading metrics describe a simple long/flat research strategy, not a deployable trading system.

---

Fixtures and synthetic data are labelled as such and are never presented as real provider results. No accuracy, profitability or investment claim is made.
