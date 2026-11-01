# Model and Evaluation Plan

Status: methodology is implemented and freshly recomputed on checksum-verified Binance Vision
BTCUSDT (USDT quote) data. Binance-derived artifacts carry CC BY-NC-SA 4.0 terms and are non-commercial only. No accepted X corpus exists yet, so a sentiment result is still
**not** evidenced: the candidate model is flagged as not identifiable when no scored
posts are present. No trained model is described here as accurate or profitable.

## Question and target
Test whether point-in-time X sentiment improves Bitcoin daily close forecasts over
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

Reporting-only series (never a model feature): the R10 visual sentiment-change series
is `mean_sentiment_24h(T) - mean_sentiment_24h(T-1 UTC day)`, emitted only for
consecutive scored cutoffs; an unscored day leaves the change unavailable rather than
zero. See `src/xsentiment/reporting/charts.py`.

## X-post input path and provenance
The feature implementation already accepts normalized `XPostRecord` values:
`scripts/ingest_apify_x.py` writes one normalized JSONL batch per approved query;
`xsentiment run --posts` loads those records, scores text with VADER, builds the
sentiment columns above, and evaluates the sentiment-plus-price model. The missing
multi-query seam is deterministic assembly when the same post appears in multiple
batches. The merge command records every source query in a sanitized provenance
sidecar, keeps one canonical post row, and the run manifest hashes both the posts
snapshot and sidecar. Existing single-file `--posts` runs remain supported.

Duplicate IDs must agree on stable post identity (`created_at`, text and platform)
or the merge fails closed. For compatible duplicates, the earliest observed
`retrieved_at` is retained and all source query modes/hashes are preserved in the
sidecar. A retrospective scrape has its actual retrieval time: it is excluded from
earlier cutoffs under `observed` and is not evidence for leakage-safe historical
sentiment. The opt-in archive basis remains explicitly retrospective.


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

Earlier Coinbase-derived strategy metrics are excluded from this current report
after the provider terms review; they are not repeated or relied on here. Git history
remains unchanged.

## Measured state (2026-11-01, Binance Vision BTCUSDT)
The current checked run has 180 daily bars from 2026-05-05 through 2026-10-31 UTC,
5 folds, 100 out-of-sample rows per model and horizon, 1,800 prediction rows, and
zero posts. Mean MAE across horizons is 1,824.23 USDT for naive persistence and
2,378.50 USDT for price-only ridge; price-only is 30.38% worse than naive. The
sentiment-labelled candidate is identical because there are no scored posts and is
not evidence about sentiment. Price-only strategy Sharpe is 1.124, Sortino 2.431,
and max drawdown 5.885%; these are short-sample research measures, not evidence of
tradability. Details and reproducibility artifacts are in `reports/btcusdt-180d/`.

Prior Coinbase-derived metrics have been removed from the current tree after the
2026 Coinbase Market Data Terms review; they are not reproduced or redistributed
here. Exact BTC-USD and real sentiment evaluation remain blocked.

## Robustness and go/no-go
Possible predeclared comparisons include horizons, naive/price-only/sentiment models
and coverage subsets. Do not tune on test folds, and no separate final holdout is
currently reserved; do not add one after inspecting results and then present it as
untouched. The current honest result is that the price-only model does not beat naive
persistence on this sample, and that finding stays in the report.
Do not train on X text until source terms/access, post-level text and time coverage,
point-in-time semantics, the sentiment/null policy, matching prices, targets and
chronological splits are validated.
