# Decision Log
A code default is not employer confirmation. Material changes need rationale, impact analysis, updated tests and synchronized canonical documents.

## D-001 Asset
Status: selected working choice. BTC-USD Bitcoin spot reference. Do not expand assets without approval.

## D-002 Interval/timezone
Status: working default. Daily bars, UTC boundaries, timezone-aware timestamps normalized to UTC.

## D-003 Price source
Status: working default; verify each run. Coinbase Exchange public BTC-USD daily candles. User-run profile reported 180/180 bars from 2026-04-29 through 2026-10-25 UTC with no missing/duplicate timestamps. This does not prove future API behavior or X coverage.

## D-004 Forecast cutoff and targets
Status: working default, not employer-confirmed. Issue at 00:00 UTC; predict closes of bars n..n+5. n+0 is the not-yet-completed close. Use completed prior bars as features and omit incomplete/gap-crossing labels. Employer clarification overrides before evaluation.

## D-005 News role
Status: conservative interpretation. Tavily news is context for current outlook, not model features, because the brief says predictive inputs are sentiment and price only. Reopen only with clarification and updated docs.

## D-006 ML versus RL
Status: conservative initial scope. Supervised multi-horizon forecasting and baselines; no RL until employer confirms and action/reward/execution/cost/evaluation are specified.

## D-007 Risk metrics
Status: methodology decision. Sharpe, Sortino and max drawdown only from a defined strategy on out-of-sample returns with positions, fees, slippage, return convention, annualization and missing-data policy. Otherwise state unavailable.

## D-008 Historical dataset
Status: open/blocked. No source accepted until access, platform, terms, schema, text, event coverage, provenance and point-in-time limitations are reviewed. Assessment-linked Google Doc was not accessible in prior retrieval; ID/date-count files do not provide text; ZIP internals remain unverified. No training on unverified/rights-unclear data.

## D-009 Apify Actor and cost
Status: open/blocked. No Actor run until current schema, platform, query, terms, plan price, limits, 180-day reach and cost cap are checked. Adapter is mocked, not live verified; token/Actor ID are not configured. No paid run without explicit spend approval.

## D-010 Engagement/followers
Status: rule. Keep available counts nullable; exclude from historical predictors without time-stamped snapshots proving historical values.

## D-011 Platform identity
Status: rule. StockTwits is not X. Do not merge platforms without explicit labels and a documented study design.

## D-012 Secret handling
Status: rule. Never commit credentials. Share only through a verified employer-approved private channel.

## D-013 Exa
Status: open. Tavily is named in the main brief; Exa appears in submission checklist. Do not require Exa at runtime without clarification.

## D-014 Deadline
Status: open. Confirm actual due date from employer communication; the brief says within one week and also 5–7 days. Do not infer a date from repo timestamps.

## D-015 Canonical governance
Status: agreed. Nine root-level files govern scope, contracts, data policy, model/evaluation, testing, rules, roadmap and decisions. Update affected documents/tests before merging material changes.
