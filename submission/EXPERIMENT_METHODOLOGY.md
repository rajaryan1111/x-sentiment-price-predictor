# Experiment methodology

This summarizes [`MODEL_PLAN.md`](../MODEL_PLAN.md),
[`DESIGN.md`](../DESIGN.md), [`DATA_POLICY.md`](../DATA_POLICY.md)
and the committed run manifest into one evaluator-facing page. All choices
below are recorded defaults, not employer-confirmed client instructions;
conflicts with the verified assignment brief are logged as open gates in
[`docs/EXTERNAL_BLOCKERS.md`](../docs/EXTERNAL_BLOCKERS.md).

## Data sources

| Source | Role | Current state |
| --- | --- | --- |
| Coinbase Exchange public `BTC-USD` candles (`granularity=86400`) | price features, targets, backtest | verified historical run: 180/180 daily bars 2026-04-29→2026-10-25 UTC, no gaps/duplicates, unfinished day dropped; snapshot SHA-256 `09ce225a405aea390ae2f21c72634da1211a321aed1b39b52febfadf64083f75` in the committed manifest |
| X/Twitter posts (Apify route, 180 days, ticker/cashtag/keyword) | sentiment | not accepted: no Actor, licence, credential, spend cap or corpus; adapter + preflight + bounded ingest are implemented and fixture-tested |
| Tavily news | outlook context only, never a model feature | adapter and gated CLI mocked-verified; no live call ever made |
| Registry candidates (`data/registry/historical_twitter_x_datasets.json`) | candidate inventory only | 12 records structurally validated; none approved or coverage-profiled |

## Timestamp and availability contract

- All timestamps normalize to UTC; naive timestamps are rejected at the record
  boundary.
- `created_at` is event time; `retrieved_at` is first observation. Retrieved
  time is never backdated and never derived from creation time. Raw provider
  timestamp, UTC offset, source identity and a payload hash are retained.
- Availability has two explicit bases. `observed` (default, leakage-safe): a
  post enters a cutoff only when `retrieved_at <= cutoff`.
  `archive_created_at` is an opt-in retrospective mode for archives whose true
  first-observation times are unknowable: it requires a non-empty disclosure
  note, records the basis in the manifest, and stamps the look-ahead limitation
  into every report and outlook. It is **not** a fully leakage-safe historical
  backtest and was not used in any recorded run.
- Posts aggregate into the half-open 24-hour window `(cutoff − 24h, cutoff]`;
  late and future posts are excluded, duplicates are reported and never filled.

## Feature construction

- Predeclared point-in-time price features (lagged returns, rolling windows)
  and trailing-24h sentiment aggregates (mean score, post volume) only from
  information available at each 00:00 UTC cutoff.
- Missing sentiment remains `null`; it is never zero-filled or treated as
  neutral. With zero accepted posts, all sentiment features are null — this is
  reported, not hidden.
- Targets are per-horizon close ratios against the last completed close for
  bars `n+0`…`n+5`. `n+0` forecasts the not-yet-completed close of day `n`,
  issued at that day's UTC start (working default; employer confirmation is
  open gate B4). Target columns are structurally barred from the feature
  matrix; incomplete or gap-crossing horizons are dropped.

## Models and validation

- Three models, one per horizon, on **identical** folds and eligible rows:
  1. **Naive persistence** — last completed close carried forward.
  2. **Price-only ridge** — price features only.
  3. **Sentiment-plus-price ridge** — adds sentiment features when present.
- Expanding walk-forward folds with a 5-row purge gap (longest horizon):
  training windows grow 60→140 rows, test blocks are 20 rows, evaluation uses
  only unseen future days. Imputation and standardization are fitted on
  training folds only; test folds are evaluation-only. No random split is used
  anywhere.
- Per-horizon MAE/RMSE with sample counts; mean MAE across horizons for the
  model comparison; deterministic repeat-run check.

## Strategy and risk metrics

- Sharpe/Sortino/max drawdown require a separately specified strategy and
  strictly out-of-sample returns. The predeclared strategy is long/flat: go
  long when the model's `n+0` forecast exceeds the last completed close, flat
  otherwise, with 10 bps per-side fees, 365-period annualization, zero
  risk-free rate and a 30-period minimum for ratio computation.
- The unconditional long-and-hold benchmark over the same windows is reported
  alongside. When a strategy never trades (naive here), ratios are reported
  as unavailable with the reason, never fabricated.
