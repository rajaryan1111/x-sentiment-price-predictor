# BTCUSDT — current sentiment outlook

**As of:** 2026-11-01T08:08:24+00:00<br>
**Forecast cutoff:** 2026-10-31T00:00:00+00:00<br>
**Last completed daily close (USDT):** 77,368.77<br>
**Sentiment scorer:** vader `3.3.2`

## Data coverage
- Completed price cutoffs in the dataset: **180**
- Cutoffs with a full n+0..n+5 horizon: **175**
- Eligible cutoffs (full horizon and a known previous close): **174**
- Posts supplied: **0** (scored: **0**)
- Cutoffs with scored-post sentiment: **0**

## Model outputs at the cutoff
| Model | Horizon | Predicted close (USDT) | Change vs last completed close |
| --- | --- | --- | --- |
| naive | n+0 | 77,368.77 | +0.00% |
| price_only | n+0 | 77,116.52 | -0.33% |
| sentiment_price | n+0 | 77,116.52 | -0.33% |
| naive | n+1 | 77,368.77 | +0.00% |
| price_only | n+1 | 76,917.16 | -0.58% |
| sentiment_price | n+1 | 76,917.16 | -0.58% |
| naive | n+2 | 77,368.77 | +0.00% |
| price_only | n+2 | 76,838.48 | -0.69% |
| sentiment_price | n+2 | 76,838.48 | -0.69% |
| naive | n+3 | 77,368.77 | +0.00% |
| price_only | n+3 | 76,890.42 | -0.62% |
| sentiment_price | n+3 | 76,890.42 | -0.62% |
| naive | n+4 | 77,368.77 | +0.00% |
| price_only | n+4 | 76,830.16 | -0.70% |
| sentiment_price | n+4 | 76,830.16 | -0.70% |
| naive | n+5 | 77,368.77 | +0.00% |
| price_only | n+5 | 76,746.17 | -0.80% |
| sentiment_price | n+5 | 76,746.17 | -0.80% |

## Contextual news (not a model input)
- No recent-news context was supplied (Tavily was not configured or not run for this outlook).

## Uncertainty and limitations
- No scored post sentiment is available, so observed sentiment is unreported and the sentiment-plus-price candidate carries no sentiment information.
- Post text comes from the supplied snapshot only; no live X collection was performed for this run.
- Trading metrics describe a simple long/flat research strategy, not a deployable trading system.

## Model provenance
- price_only n+0: 174 training rows, 6 features
- sentiment_price n+0: 174 training rows, 11 features
- price_only n+1: 174 training rows, 6 features
- sentiment_price n+1: 174 training rows, 11 features
- price_only n+2: 174 training rows, 6 features
- sentiment_price n+2: 174 training rows, 11 features
- price_only n+3: 174 training rows, 6 features
- sentiment_price n+3: 174 training rows, 11 features
- price_only n+4: 174 training rows, 6 features
- sentiment_price n+4: 174 training rows, 11 features
- price_only n+5: 174 training rows, 6 features
- sentiment_price n+5: 174 training rows, 11 features

---

This outlook is a research artefact for an engineering assessment. It is not investment advice, and no accuracy or profit is claimed or implied.
