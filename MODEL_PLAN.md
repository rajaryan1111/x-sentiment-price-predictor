# Model and Evaluation Plan

Status: the methodology below is implemented and verified on real public Coinbase
BTC-USD data. No accepted X corpus exists yet, so a sentiment result is still
**not** evidenced: the candidate model is flagged as not identifiable when no scored
posts are present. No trained model is described here as accurate or profitable.

## Question and target
Test whether point-in-time X sentiment improves BTC-USD daily close forecasts over
naive and price-only baselines. Issue at 00:00 UTC at start of day n. Horizons 0..5
target closes of bars beginning at cutoff plus h days. Use completed prior bars as
price inputs. Posts require event time and defensible availability time <= cutoff and
are aggregated over (t-24h, t]. Incomplete/gap-crossing labels are omitted, and the
unfinished current UTC day is dropped whenever the caller supplies the current time.

Models predict a **ratio**, `close(cutoff + h) / reference_close`, so predictions are
directly comparable with the naive baseline (ratio 1.0) and cannot drift outside
plausible price ranges. Realised MAE/RMSE are reported in USD on the implied closes.

## Features (implemented)
Price-only group: `return_1d`, `return_3d`, `return_7d`, `volatility_7d` (population
standard deviation of the last seven daily returns), `range_1d`, `close_vs_sma_7d`.
All are computed from candles that completed strictly before the cutoff; a value is
null when its window lacks history rather than zero-filled.

Sentiment-plus-price group: the price group plus `mean_sentiment_24h`,
`positive_share_24h`, `negative_share_24h`, `post_count_24h` and
`scored_post_count_24h`, aggregated over `(cutoff - 24h, cutoff]` from posts both
published and first observed by the cutoff.

Excluded by default and by construction: current engagement/follower counts without
historical snapshots, news features, future posts or prices, target columns in
features, and any synthetic value presented as observed data.

## Sentiment scorer (implemented)
VADER (`vaderSentiment` 3.3.x, MIT) through `xsentiment.features.sentiment`. It is
deterministic, offline, needs no model download or GPU, and returns the canonical
compound score in [-1, 1]; blank text yields null, which stays null downstream.

Documented limitations: the lexicon is English-oriented and not finance-specific, it
does not resolve sarcasm, author credibility, bots or coordinated campaigns, and it
cannot represent domain slang beyond its lexicon. The scorer is therefore a
*balanced, reproducible baseline* whose purpose is to make the sentiment-vs-price
comparison measurable, not a claim of sentiment understanding. Replacement requires
only another `SentimentScorer` implementation (for example VADER plus a
crypto-specific lexicon, or a domain-tuned transformer such as FinBERT), and the
scorer name and exact installed version are recorded in every run manifest.

## Baselines and candidate (implemented)
1. **Naive persistence**: predict the last completed close for every horizon.
2. **Price-only ridge**: ridge regression on the price group, one model per horizon.
3. **Sentiment-plus-price ridge**: identical folds, targets and eligible rows, with
   the sentiment group added.

All three see identical eligible rows, which are the rows with a complete forward
horizon and a reference close. Missing feature values are imputed with training-fold
means and features are standardised with training-fold statistics; a feature never
observed in training receives zero weight. The ridge penalty applies to slopes only.
No third-party numerical library is required, so the same code runs in the default
test environment and in CI. RL is out of scope until an action space, reward,
execution/cost model and evaluation protocol are specified.

## Validation (implemented)
Expanding-window walk-forward folds over rows ordered by cutoff; each fold trains on
a prefix only, then leaves a purge/embargo gap equal to the longest horizon (5 rows by
default) before testing on the next untouched block. Defaults are 60 minimum training
rows and 20 test rows per fold. Scaling, imputation and coefficients are fitted per
fold on training rows only. No random shuffling exists anywhere in the code. Results
are deterministic: repeated runs produce identical predictions.

## Forecast metrics (implemented)
Per model and horizon: sample count, MAE and RMSE in USD, and signed mean error.
Mean MAE across horizons is compared with the naive baseline and reported as a
percentage difference. Directional accuracy remains optional and is not currently
reported.

## Trading risk metrics (implemented, conditions disclosed)
The strategy is predeclared in `xsentiment.backtesting.strategy` and is applied only
to out-of-sample signal predictions:

- decision at 00:00 UTC at start of day n using the last completed close and the
  model's `n+1` close prediction;
- long only when the predicted `n+1` close exceeds `close(n-1) x (1 + 2 x fee)`,
  otherwise flat;
- entry at `close(n)`, exit at `close(n+1)`; net return `close(n+1)/close(n) - 1 - 2 x fee`;
- default fee 10 basis points per side, no shorting, no leverage, no position sizing;
- annualisation at 365 periods per year, risk-free rate 0, Sortino MAR 0;
- benchmark: the same windows held long unconditionally, charged the same fees;
- Sharpe, Sortino and maximum drawdown are withheld with an explicit reason until at
  least 30 out-of-sample days exist, and are reported as undefined when the return
  series has zero dispersion.

## Measured state (2026-10-26, real public data)
180 public Coinbase `BTC-USD` daily bars (2026-04-29 to 2026-10-25 UTC), 5 folds,
100 out-of-sample days per model and horizon, 1800 predictions, zero posts:
mean MAE across horizons was $1,828.36 for naive persistence and $2,264.62 for the
price-only ridge model, i.e. the fitted model was **23.86% worse than naive** on
forecast error, and the candidate model was identical to price-only because no
sentiment was available. No claim is made that any model adds predictive value.
Strategy statistics from the same run are short-sample research numbers on one asset
and period, not evidence of tradability.

## Robustness and go/no-go
Possible predeclared comparisons include horizons, naive/price-only/sentiment models
and coverage subsets. Do not repeatedly tune on a final holdout, and do not tune a
model to beat the baseline after inspecting results; the current honest result is
that the price-only model does not beat naive persistence on this sample, and that
finding stays in the report.
Do not train on X text until source terms/access, post-level text and time coverage,
point-in-time semantics, the sentiment/null policy, matching prices, targets and
chronological splits are validated.
