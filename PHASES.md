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
Status: complete as a documented baseline, with external data/provider and deadline items still open.
- Parse the assessment into traceable requirements with unique IDs (`R1`–`R15`, `NFR1`–`NFR6`, `A1`–`A7`).
- Set working choices BTC-USD, daily UTC, n+0..n+5 close targets and Coinbase default.
- Separate required, optional/ambiguous and out-of-scope items.
- Record conservative news and RL interpretations.
- Give every requirement an acceptance criterion, a verification method, an evidence pointer, a status, a gap and a blocker.
Evidence: docs/PHASE_1_REQUIREMENTS.md, PRD.md and the authoritative matrix in
docs/REQUIREMENTS_TRACEABILITY.md, checked by `scripts/validate_docs.py`. Both assessment
PDFs were read in full on 2026-10-26 and the requirement set was reconciled against them;
D-023 is closed. The linked Google Doc was retrieved and is a dataset-link compilation,
not a tweet corpus.
**Open items that engineering cannot close:** the employer's calendar deadline is unknown
(A1, D-014); provider access, credentials and the private transfer channel remain external
(R2, A2, O10); dataset/Actor selection remains open (O6, O13); a Tavily key is needed for
live news context (A4); and the n+0 convention still needs employer confirmation (O3/O4).
R15 (database join) now has a tested storage layer plus a persisted-input CLI path
(`xsentiment persist`, `run --database-url`), verified offline with fixtures. This
does not mean X data has been collected or any sentiment result measured.

## Phase 2 — Canonical documentation
Status: complete for the current verified baseline. The canonical documents were reconciled
with the verified assignment source on 2026-10-26 and again with the Phase 3 storage,
contract and profiler changes on the same date.
- Maintain all nine root-level files: PRD, ARCHITECTURE, DESIGN, DATA_POLICY,
  MODEL_PLAN, TEST_PLAN, RULES, PHASES, DECISIONS.
- Keep docs/REQUIREMENTS_TRACEABILITY.md and docs/PHASE_1_REQUIREMENTS.md aligned.
Acceptance: files exist; asset, interval, cutoff, targets and scope agree; open gates are
explicit; implementation status is honest; links/commands are checked; reviewed before
merge and CI passes. No semantic implementation change without synchronized docs/tests.

## Phase 3 — Data access and ingestion
Status: in progress; X data externally blocked. Price ingestion is complete and verified.
- Price: 180/180 real public Coinbase `BTC-USD` daily bars for 2026-04-29 through
  2026-10-25 UTC, refetched 2026-10-26 with no missing or duplicate timestamps and the
  unfinished current day excluded. Reproduced with `python -m xsentiment fetch-prices`.
- X: no accepted dataset and no live Actor run. Local CSV/JSONL profiling exists and
  refuses to call an old download point-in-time ready. The uploaded ZIPs were inspected on
  2026-10-26: `90-day-samples.zip` contains numeric tweet IDs only; the available archives
  are an air-quality CSV and MQTT sensor JSON, unrelated to X; `archive (2).zip` is absent.
  No uploaded file contains X post text.
- Data contract: the normalized record preserves the raw provider timestamp, supplied UTC
  offset, payload hash, author reference, query mode/query and warnings; the JSONL loader
  round-trips these fields. The profiler detects retrieval-time columns, reports daily
  coverage gaps and invalid engagement counts, and accepts `--as-of` for reproducible
  windows. The Apify adapter unwraps the documented `data` envelope, pages dataset items
  with `offset`/`limit`, and records query provenance; it remains mocked-only.
- Registry: 12 source records validate structurally, with an explicit
  `independent_verification.status = not-reverified` and no implied legal approval.
- Database join (R15): complete for the offline path. Versioned `price_bars`/`x_posts`
  tables, idempotent repositories and tested descriptive/cutoff joins exist in
  `src/xsentiment/storage/`, and the pipeline now consumes persisted inputs:
  `xsentiment persist` upserts snapshots into the local database and
  `xsentiment run --database-url` runs the full evaluation from those rows (manifest
  records `input_source = persisted_storage`).
- Bounded end-to-end X ingestion: `tests/unit/test_phase3_ingestion_e2e.py` drives a
  mocked adapter response (offline) through normalization, persistence and the
  leakage-safe cutoff join, and then runs the persisted-input CLI end to end. This is
  wiring evidence only; it proves no provider access and contains no real posts.
Acceptance: met for the persisted-join pipeline integration and the bounded end-to-end
ingestion test (offline, fixtures). Still unmet: an accepted X source, sanitized
180-day coverage evidence and reviewed licensing/terms — all external (R2, O6, O13).

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
- The implemented sentiment series is the mean level; the brief asks for sentiment change.
  The missing change series is recorded as a gap in R10.
Acceptance (unmet): sentiment and price charts derived from real permitted X data, with a
sentiment-change series.

## Phase 8 — Reproducibility and submission
Status: in progress.
- Done: offline reproducible CLI (`fetch-prices`, `run`), run manifest with input hashes,
  commit-able report/chart/outlook artefacts, 120 offline tests, lint, registry and
  documentation validation.
- Remaining: clean-environment run on a fresh clone, security/licence audit of any future
  X source, the secure credential route, confirmation of the actual submission deadline
  from the employer, and the email submission packet required by the brief (A7).
