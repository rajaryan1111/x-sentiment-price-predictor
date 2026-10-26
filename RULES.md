# Engineering, Git and Quality Rules
These rules apply to every change unless DECISIONS.md records a reviewed exception.

## Source of truth
The assessment PDF is assignment authority. PRD.md, ARCHITECTURE.md, DESIGN.md, DATA_POLICY.md, MODEL_PLAN.md, TEST_PLAN.md, RULES.md, PHASES.md and DECISIONS.md are the canonical engineering set. docs/PHASE_1_REQUIREMENTS.md is a detailed trace and must stay aligned. Resolve conflicts explicitly in DECISIONS.md, update affected documents/tests, then implement. Distinguish confirmed facts, working defaults, open questions, implementation, test evidence and external verification.

## Code quality
- Target Python 3.11+ as pyproject.toml declares.
- Prefer small typed functions and provider-neutral interfaces.
- Validate provider inputs at boundaries; preserve nulls.
- Use timezone-aware UTC timestamps and Decimal for price OHLC where appropriate.
- No hidden network, paid calls, filesystem mutations or Actor launches on import.
- Bound timeouts, payloads, concurrency, item counts and spend.
- Retry only transient safe/idempotent operations; never blindly retry paid Actor launches.
- Do not swallow exceptions broadly or weaken tests to get a green build.
- Add dependencies only with rationale and compatible project metadata.

## Data/model integrity
Never fabricate rows, labels, scores, timestamps, counts, metrics or approvals. Never backdate availability. Never use future data, unfinished candles or target columns as features. No random split as primary time-series evaluation. Fit transformations only on training folds. Compare naive and price-only baselines before claiming sentiment adds value. News stays out of model features unless clarified and logged. No Sharpe/Sortino/drawdown without a defined strategy and out-of-sample returns. Clearly label fixtures/synthetic data.

## Security and cost
Never commit tokens, cookies, .env, private exports, raw large datasets or unapproved post text. Use placeholders in .env.example and ignore secret/data paths. Never paste credentials into chat or public PRs. Share credentials only through verified employer-approved private channels. No paid collection without explicit budget approval. Honor source terms and retention/deletion requirements.

## Git/review
Use focused branches and reviewable commits; avoid direct main commits unless agreed. Behavior changes require tests. Schema/target changes update canonical docs and decisions. Run lint, registry validation and tests before review. Do not merge or mark a PR ready while material data/license/security gates remain open. Avoid destructive history changes without explicit coordination.

## Reporting
Use identical UTC/cutoff/target definitions everywhere. State evidence and limits next to claims. CI success is not evidence of data access, model quality or profitability. Report versions, sample counts, folds, exclusions and assumptions. Keep unresolved questions visible.
