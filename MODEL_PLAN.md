# Model and Evaluation Plan
Status: methodology baseline only; no trained model or performance claim is currently evidenced.

## Question and target
Test whether point-in-time X sentiment improves BTC-USD daily close forecasts over naive and price-only baselines. Issue at 00:00 UTC at start of day n. Horizons 0..5 target closes of bars beginning at cutoff plus h days. Use completed prior bars as price inputs. Posts require event time and defensible availability time <= cutoff and are aggregated over (t-24h,t]. Incomplete/gap-crossing labels are omitted.

## Features
Price-only candidates: predeclared lagged returns, rolling volatility/range and other lagged price statistics when history supports them. Shift all windows so target-period information cannot enter.
Sentiment-plus-price candidates: sentiment mean/dispersion from scored eligible posts, post/scored-post volume, coverage/missingness indicators and price-only features. Sentiment model/version must be documented and suitable for the domain/language. Until implemented, sentiment scores remain null.
Exclude by default: current engagement/follower counts without historical snapshots; news features; future posts/prices; targets in features; synthetic values represented as real data.

## Baselines and candidate
1. Naive persistence baseline: implemented as persistence_forecast in src/xsentiment/models/baseline.py; repeats the last completed close for n+0 through n+5. This is a baseline prediction function, not an evaluation pipeline.
2. Price-only supervised baseline.
3. Sentiment-plus-price candidate using the same folds, targets and eligible rows as price-only.
Choose model family after profiling actual sample size and missingness. Start with simple, reproducible models. RL is out of initial scope unless explicitly required and its action space, reward, execution/cost model and evaluation are specified.

## Validation
The repository now includes a deterministic expanding-window split helper in src/xsentiment/validation/walk_forward.py. It creates positional train/test indices only; it is not a model evaluator and does not itself prevent target-label leakage.
Use expanding-window or rolling walk-forward splits. Define train/validation/test boundaries before tuning. Choose a gap sufficient for the maximum target horizon where label windows could overlap test periods. Fit scaling, imputation, selection and hyperparameters using training/validation folds only. Keep final holdout untouched until choices are frozen. Compare models on identical cutoffs and folds. Record boundaries, sample counts and exclusions. Use deterministic seeds where possible.

## Forecast metrics
Report MAE and RMSE in USD by horizon. Directional accuracy is optional only with a predeclared definition and consistent handling. Include naive and price-only comparisons, sample counts and fold variability where feasible. Never report metrics from invalid targets or leakage-prone splits.

## Trading risk metrics
Sharpe, Sortino and max drawdown require a defined trading strategy, not merely forecasts. Compute only on out-of-sample strategy returns. Document signal/position timing, sizing/leverage, compounding/return convention, fees/slippage, risk-free rate, annualization, Sortino downside target and missing-bar policy. If no defensible strategy exists, report unavailable with reason.

## Robustness and go/no-go
Possible predeclared comparisons include horizons, naive/price-only/sentiment models and coverage subsets. Do not repeatedly tune on final holdout.
Do not train until source terms/access, post-level text/time coverage, point-in-time semantics, sentiment scoring/null policy, matching prices, targets and chronological splits are validated.
Current state: alignment/target primitives and a split-boundary helper exist, but no accepted real X dataset, implemented sentiment scoring, trained forecast, walk-forward model evaluation, charts, current outlook or valid trading metrics are evidenced.
