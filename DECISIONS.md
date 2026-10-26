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

## D-016 Sentiment scorer
Status: working default with documented limits. VADER (`vaderSentiment` 3.3.x, MIT) is the versioned, deterministic, offline scorer; blank text stays null and is never treated as neutral. It is English-oriented and not finance-specific, so it is a reproducible baseline rather than a claim of understanding. Replacing it means implementing another `SentimentScorer`; the scorer name and installed version are recorded in every run manifest.

## D-017 Trading strategy and risk-metric gating
Status: predeclared. Long only when the predicted n+1 close exceeds close(n-1) x (1 + 2 x fee); entry at close(n), exit at close(n+1); default fee 10 bps per side; no shorting, no leverage, no sizing. Annualisation 365 periods, risk-free 0, Sortino MAR 0, benchmark is the same windows held long. Sharpe, Sortino and drawdown are withheld with a reason below 30 out-of-sample days or when dispersion is zero, and are reported only as strategy statistics, never as forecast accuracy.

## D-018 Walk-forward purge and determinism
Status: rule. Expanding-window folds with a purge gap equal to the longest horizon (5 rows) so labels from the training block cannot resolve into the test block. Defaults are 60 training and 20 test rows per fold. No random splitting exists in the code; repeated runs must produce identical predictions.

## D-019 Numerical stack
Status: decision. The candidate models are a from-scratch ridge regression with a deterministic normal-equation solve, so the core pipeline needs no numerical third-party library and stays testable in the extras that CI installs (`.[dev,storage]`). `vaderSentiment` is the only added runtime dependency and it is pure Python.

## D-020 Model target
Status: decision. Models predict the horizon ratio close(cutoff + h) / close(cutoff - 1) and multiply by the reference close, so predictions are directly comparable with the naive persistence baseline (ratio 1.0) and cannot drift outside plausible ranges. Canonical metrics remain USD MAE/RMSE on the implied closes.

## D-021 Artefact set and chart renderer
Status: decision. Each run writes evaluation-report.md, outlook.md, sentiment-vs-price.svg, metrics.json, predictions.jsonl and manifest.json. Charts are rendered as dependency-free SVG; a plotting library is not required. Generated prediction dumps stay out of Git while the report, outlook, chart, manifest and metrics are small enough to review.

## D-023 Assignment source availability
Status: open, human action required. The assessment PDF (`CWT X sentiment Agent - intern task.pdf`) and its companion dataset-reference PDF are not present in the repository, the agent workspace or the conversation, so requirement wording is transcribed from the project's own record in docs/PHASE_1_REQUIREMENTS.md §2. Consequence: the requirement set, the `n+0` interpretation and the timeline are treated as provisional until a human confirms them against the PDF. No deadline, licence, credential or employer intent may be inferred from repository timestamps or from any summary.

## D-024 Identifier and phase-label scheme
Status: agreed. Requirement IDs are `R1`–`R14` (functional, defined in PRD.md and PHASE_1_REQUIREMENTS.md), `NFR1`–`NFR6` (non-functional), `A1`–`A6` (assessment-specific items such as the timeline, credentials and supplied resources), `O1`–`O13` (open decisions) and `D-001`–`D-024` (decisions). Each ID appears exactly once per namespace, and the same ID means the same requirement in every document. Phase numbering has three distinct schemes mapped in PHASES.md; canonical Phase 1 is the requirements and scope baseline, and the repository's “Phase 2 data quality/alignment” workstream is canonical Phase 3, not canonical Phase 2.

## D-022 Post text requirement
Status: rule. A normalized post requires non-empty text, while text remains stored only when returned and permitted. Records without recoverable text are rejected at the adapter boundary rather than admitted with empty text, so post-volume features count only posts that were actually observed with text. Making the contract nullable is deferred until a real ID-only source is accepted and the quarantine policy is specified.
