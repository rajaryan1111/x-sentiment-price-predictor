# Implementation Roadmap
This is the controlling roadmap. The earlier repository label “Phase 2 data ingestion” is a workstream label, not the same as canonical documentation Phase 2.

## Phase label mapping
Three numbering schemes exist in this project's history. They must not be conflated.

| Scheme | Meaning | Where it lives |
| --- | --- | --- |
| Canonical roadmap phases | The phases below (1–8), numbered for engineering sequencing | this file |
| Internship execution phases | The employer-facing labels (“Phase 1 requirements, scope and baseline”, then the next delivery phase) | docs/REQUIREMENTS_TRACEABILITY.md, PRD.md |
| Repository workstream labels | Historical branch names such as the “Phase 2 data quality/alignment” workstream | docs/PHASE_2_PROGRESS.md |

Canonical Phase 1 = internship execution Phase 1 = the requirements and scope baseline.
The repository's “Phase 2 data quality/alignment” workstream maps to canonical Phase 3
(data access and ingestion), not to canonical Phase 2 (canonical documentation).

## Status definitions
Not started = no evidence. In progress = some work exists but acceptance is unmet.
Blocked = external dependency. Complete = acceptance evidence exists and has been
reviewed. CI success alone does not complete a data/model phase, and a phase is never
complete merely because its interface or a mock test exists.

## Phase 1 — Requirements lock
Status: complete as a documented baseline, with two items that only the human can close.
- Parse the assessment into traceable requirements with unique IDs (`R1`–`R14`, `NFR1`–`NFR6`, `A1`–`A6`).
- Set working choices BTC-USD, daily UTC, n+0..n+5 close targets and Coinbase default.
- Separate required, optional/ambiguous and out-of-scope items.
- Record conservative news and RL interpretations.
- Give every requirement an acceptance criterion, a verification method, an evidence pointer, a status, a gap and a blocker.
Evidence: docs/PHASE_1_REQUIREMENTS.md, PRD.md and the authoritative matrix in
docs/REQUIREMENTS_TRACEABILITY.md, checked by `scripts/validate_docs.py`.
**Open items that engineering cannot close:** the assessment PDF was not accessible to the
authoring environment, so the requirement transcription needs human confirmation (D-023);
and the employer's deadline is unknown (A1, D-014). This does not mean X data has been
collected or any sentiment result measured.

## Phase 2 — Canonical documentation
Status: in progress until the documentation review completes on the open pull request.
- Maintain all nine root-level files: PRD, ARCHITECTURE, DESIGN, DATA_POLICY,
  MODEL_PLAN, TEST_PLAN, RULES, PHASES, DECISIONS.
- Keep docs/REQUIREMENTS_TRACEABILITY.md and docs/PHASE_1_REQUIREMENTS.md aligned.
Acceptance: files exist; asset, interval, cutoff, targets and scope agree; open gates are
explicit; implementation status is honest; links/commands are checked; reviewed in PR and
CI passes. No semantic implementation change without synchronized docs/tests.

## Phase 3 — Data access and ingestion
Status: in progress; X data externally blocked. Price ingestion is complete and verified.
- Price: 180/180 real public Coinbase `BTC-USD` daily bars for 2026-04-29 through
  2026-10-25 UTC, refetched 2026-10-26 with no missing or duplicate timestamps and the
  unfinished current day excluded. Reproduced with `python -m xsentiment fetch-prices`.
- X: no accepted dataset and no live Actor run. Local CSV/JSONL profiling exists and
  refuses to call an old download point-in-time ready; ZIP internals remain unverified.
Acceptance (unmet): accepted source, sanitized coverage evidence, time alignment and a
bounded end-to-end X ingestion test.

## Phase 4 — Sentiment and features
Status: implemented and unit-verified; real-data acceptance blocked on accepted X text.
- VADER scoring is implemented, versioned and recorded in each manifest; blank text
  stays null.
- Point-in-time price and sentiment features and the supervised dataset are implemented,
  with nulls preserved and no target leakage.
- 180 price cutoffs were feature-built with zero posts, and sentiment correctly stayed
  unavailable instead of being zero-filled.
Acceptance (unmet): a reproducible feature dataset and quality profile derived from
permitted real post text.

## Phase 5 — Baselines and forecasting
Status: implemented and verified on real price data; the sentiment comparison is blocked.
- Naive persistence, price-only ridge and sentiment-plus-price ridge run on identical
  folds and eligible rows, one model per horizon, predicting a close ratio.
- 5 folds, 100 out-of-sample days per model and horizon, 1800 stored predictions.
- Measured: price-only mean MAE $2,264.62 versus naive $1,828.36 (23.86% worse).
  No claim that any model beats the baseline is made.
Acceptance: met for prices; unmet for the sentiment-vs-price comparison, which requires
an accepted X source.

## Phase 6 — Evaluation and risk
Status: implemented and verified on real price data.
- Chronological walk-forward with a purge gap equal to the longest horizon; no random
  splits; transforms fitted on training folds only; results deterministic across runs.
- Per-horizon MAE/RMSE/sample counts and mean-MAE baseline comparison are reported.
- A predeclared long/flat strategy produces out-of-sample returns from which Sharpe,
  Sortino and maximum drawdown are computed with disclosed fees, annualisation,
  risk-free rate and missing-data policy; ratios are withheld with a stated reason when
  fewer than 30 out-of-sample days exist or dispersion is zero.
Acceptance: met for the price-only and naive comparison; the candidate-model comparison
stays pending X data.

## Phase 7 — Visualization and outlook
Status: implemented; the sentiment panel is empty until an accepted X source exists.
- `sentiment-vs-price.svg` renders the observed close panel plus the sentiment panel and
  states explicitly when no scored posts are available.
- `outlook.md` reports the cutoff, last completed close, coverage counts, per-horizon
  model outputs, contextual news and its limitations.
- News remains context-only and is supplied from an optional file; no Tavily or Exa call
  has been made and no news feature exists.
Acceptance (unmet): sentiment and price charts derived from real permitted X data.

## Phase 8 — Reproducibility and submission
Status: in progress.
- Done: offline reproducible CLI (`fetch-prices`, `run`), run manifest with input hashes,
  commit-able report/chart/outlook artefacts, 103 offline tests, lint, registry and
  documentation validation.
- Remaining: clean-environment run on a fresh clone, security/licence audit of any future
  X source, the secure credential route, and confirmation of the actual submission
  deadline from the employer.
