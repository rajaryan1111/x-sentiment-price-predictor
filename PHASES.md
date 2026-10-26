# Implementation Roadmap
This is the controlling roadmap. The earlier repository label “Phase 2 data ingestion” is a workstream label, not the same as canonical documentation Phase 2.

## Status definitions
Not started = no evidence. In progress = some work exists but acceptance is unmet. Blocked = external dependency. Complete = acceptance evidence exists and has been reviewed. CI success alone does not complete a data/model phase.

## Phase 1 — Requirements lock
Status: complete as a documented baseline; employer clarifications remain open.
- Parse the assessment into traceable requirements.
- Set working choices BTC-USD, daily UTC, n+0..n+5 close targets and Coinbase default.
- Separate required, optional/ambiguous and out-of-scope items.
- Record conservative news and RL interpretations.
Evidence: docs/PHASE_1_REQUIREMENTS.md and PRD.md. This does not mean data or models are complete.

## Phase 2 — Canonical documentation
Status: in progress until review and documentation checks pass.
- Maintain all nine root-level files: PRD, ARCHITECTURE, DESIGN, DATA_POLICY, MODEL_PLAN, TEST_PLAN, RULES, PHASES, DECISIONS.
Acceptance: files exist; asset, interval, cutoff, targets and scope agree; open gates are explicit; implementation status is honest; links/commands are checked; reviewed in PR and CI passes. No semantic implementation change without synchronized docs/tests.

## Phase 3 — Data access and ingestion
Status: in progress; X data externally blocked.
- Verify dataset access, platform, terms, schema, text and event-time coverage.
- Verify Apify Actor schema, query, limits, pricing and 180-day reach before any run.
- Run bounded tests only after approval.
- Profile real post-level records and matching prices, provenance and gaps.
Acceptance: accepted source, sanitized coverage evidence, time alignment and bounded end-to-end ingestion test.
Evidence now: 180/180 BTC-USD daily bars for 2026-04-29 through 2026-10-25 UTC; no accepted X dataset/live Actor run.

## Phase 4 — Sentiment and features
Status: not complete. Select/version a suitable sentiment model, score permitted text, preserve nulls, build price and sentiment features, and test no leakage. Acceptance: reproducible feature data and quality profile.

## Phase 5 — Baselines and forecasting
Status: not complete. Implement naive and price-only baselines plus candidate sentiment+price forecasts for all horizons on matching folds. Acceptance: reproducible predictions and baseline comparisons.

## Phase 6 — Evaluation and risk
Status: not complete. Walk-forward validation and per-horizon MAE/RMSE. Define strategy before Sharpe/Sortino/drawdown; include costs and annualization. Acceptance: evidence-backed out-of-sample report or reasoned unavailable status for trading metrics.

## Phase 7 — Visualization and outlook
Status: not complete. Produce timestamped sentiment-vs-price charts and one-page current outlook with news as context, provenance and uncertainty.

## Phase 8 — Reproducibility and submission
Status: not complete. Clean-environment run, test/security/data-license audit, sanitized provenance, report and repository links; confirm actual deadline and secure credential-sharing route.
