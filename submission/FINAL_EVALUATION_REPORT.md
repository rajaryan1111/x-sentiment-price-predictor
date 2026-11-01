# Independent final evaluation report — 2026-11-01

This report is the independent final-gate audit of the repository branch
`feat/availability-basis-and-preflight`. It re-verified the implementation,
.documentation, tests, CLI workflows and every artefact of this package from a
clean environment, fixed the defects it found, and states a final verdict.
All numbers below were re-measured on 2026-11-01 unless marked historical.

## 1. Assignment requirement coverage

The authoritative matrix is
[docs/REQUIREMENTS_TRACEABILITY.md](../docs/REQUIREMENTS_TRACEABILITY.md)
(28 IDs, machine-validated). Reconciled status:

| Verdict | Count | IDs |
| --- | --- | --- |
| PASS (verified complete) | 11 | R1, R3, R6, R12, R15, NFR1, NFR2, NFR3, NFR5, NFR6, A5 |
| PARTIAL (offline-complete, externally unverified) | 14 | R4, R5, R7, R8, R9, R10, R11, R13, R14, NFR4, A3, A4, A6, A7 |
| BLOCKED BY EXTERNAL INPUT | 2 | R2 (accepted 180-day X corpus), A2 (tokens/Actor ID via a private channel) |
| FAIL | 0 | — |
| NEEDS CLARIFICATION | 1 | A1 (calendar deadline; the brief states both "one week" and "5–7 days") |

No requirement is only superficially implemented: each partial row is partial
because real X data or a live provider call is gated by authorization
(B1–B10), not because code or tests are missing. The ML/RL slash (A5) is
resolved as supervised ML with a naive persistence baseline and unit tests.

## 2. Architecture and implementation summary

The pipeline is one CLI (`python -m xsentiment`) over: bounded adapters
(Coinbase prices, optional Apify X, gated Tavily news) → normalized
provenance-safe records (event time vs first-observed time, UTC only, payload
hashes) → optional idempotent SQLAlchemy storage → point-in-time alignment
(strict candle completion, post eligibility by `created_at` **and**
`retrieved_at`, unfinished-day drop) → deterministic VADER scoring and
predeclared features → naive / price-only-ridge / sentiment-plus-price-ridge
models, one per horizon `n+0…n+5` → purged expanding walk-forward evaluation →
long/flat strategy with Sharpe/Sortino/max drawdown → SVG chart matrix,
one-page outlook, Markdown report and a lineage-complete manifest. Full text:
[SUBMISSION_README.md](SUBMISSION_README.md) and [ARCHITECTURE.md](../ARCHITECTURE.md).

## 3. Data sources and provenance

| Source | Status on this branch |
| --- | --- |
| Coinbase public `BTC-USD` daily candles | **Verified.** 180/180 bars, 2026-04-29→2026-10-25 UTC, no gaps/duplicates; committed manifest pins the snapshot SHA-256 `09ce225a…` and every run records `fetched_at` |
| X/Twitter posts | **Zero accepted.** No Actor, licence, token or spend cap exists (B1–B3, B10). Adapter, preflight and bounded ingest are implemented and fixture-tested only |
| Tavily news | Adapter + gated single-call CLI, mocked-verified; never called live; context-only, never a feature |
| Registry candidates | 12 machine-validated records; none approved, downloaded or row-profiled |

## 4. Experimental methodology

Documented in [EXPERIMENT_METHODOLOGY.md](EXPERIMENT_METHODOLOGY.md). The
defaults are working defaults, not confirmed client instructions: `n+0`
forecasts the not-yet-completed close of day `n` issued at that day's 00:00
UTC start (open gate B4). Imputation/standardization fit on training folds
only; test folds are evaluation-only; no random splits anywhere.

## 5 and 6. Actual verified results and model comparison

From the committed historical run
([reports/btc-usd-180d/metrics.json](../reports/btc-usd-180d/metrics.json) and
[RESULTS.md](RESULTS.md), re-measured independently on 2026-11-01):

- **Naive persistence wins every horizon**: mean MAE **$1,828.36** vs
  price-only **$2,264.62** (23.86% worse). No claim that any fitted model
  beats the baseline is made.
- **Sentiment-plus-price is digit-for-digit identical to price-only** because
  zero scored posts existed; the committed metrics carry the explicit
  not-identifiable warning, and sentiment features stay null (never
  zero-filled).
- Strategy metrics (out-of-sample, net of 10 bps fees): price-only long/flat
  +10.91% cumulative return, Sharpe 1.807, Sortino 3.979, max drawdown 4.08%,
  exposure 32/100 days; the never-trading naive strategy's ratios are
  `null` with a recorded reason; short-sample and single-regime caveats are
  stated.
- 5 purged folds, 100 out-of-sample days per (model, horizon), 1,800 stored
  predictions.

## 7. Data leakage and availability limitations

- Default availability basis is `observed` (`retrieved_at <= cutoff`), fail-closed
  with tests. `archive_created_at` is opt-in, requires a non-empty disclosure
  note, stamps look-ahead caveats into every report/outlook, and was **not**
  used in any recorded run. It is never presented as a leakage-safe backtest.
- Prices: strictly completed candles before each cutoff; the unfinished day is
  dropped when `--now` is supplied; targets are structurally barred from
  features.
- The central limitation: no accepted X corpus, so the
  sentiment-versus-price question remains **unmeasured**; GitHub CI and test
  counts prove offline behavior only, never data access or model quality.

## 8. Testing and CI evidence (all re-run 2026-11-01)

| Gate | Result |
| --- | --- |
| `pytest -q` in a clean checkout of the pushed tip | **209 passed** (authoritative count: [TEST_PLAN.md](../TEST_PLAN.md)) |
| `ruff check src tests scripts` | clean |
| `compileall -q src tests scripts` | clean |
| `scripts/validate_docs.py` | OK — all links, 28 matrix rows valid |
| `scripts/validate_dataset_registry.py` | OK — 12 records |
| `git diff --check` | clean |
| GitHub Actions CI | success: [run `41267305862`](https://github.com/rajaryan1111/x-sentiment-price-predictor/actions/runs/41267305862) checked out exact branch tip `33c24dcb7d9d6664bd456f00ae9f477278cdb8cf` (confirmed in checkout logs); lint, dataset-registry validation, documentation validation and pytest all succeeded; **209 passed** |

Clean-environment reproduction (fresh venv, install from committed
`pyproject.toml` only, all offline):

- `scripts/make_offline_demo.py` + `xsentiment run` — six artefacts
  (`manifest.json`, `metrics.json`, `predictions.jsonl`,
  `evaluation-report.md`, `outlook.md`, `sentiment-vs-price.svg`); **two
  consecutive runs are byte-identical on all six files**.
- Public price refetch (`fetch-prices --start 2026-04-29 --end 2026-10-26`):
  180 candles; candle payload byte-equal across two immediate refetches and
  the run with `--now 2026-10-26T00:00:00+00:00` reproduced the committed
  forecast metrics exactly.
- Persisted-database path: upserted 180 bars (idempotent), then
  `run --database-url …` produced `input_source = persisted_storage` and
  identical forecast metrics.
- Apify preflight (`--input-json config/apify_actor_input.example.json
  --validate-only`): exit 0; `network_call_made: false`,
  `paid_run_launched: false`, credential presence reported as booleans, and
  it fails fast before any spend.

Defects found and fixed by this audit (all documentation defects, verified by
re-running the documented commands):

1. `submission/REPRODUCIBILITY.md` and `submission/DEMO_SCRIPT.md` showed the
   unsupported `--now` flag on `fetch-prices` (rejected by the CLI) —
   corrected.
2. `submission/REPRODUCIBILITY.md` claimed a refetched snapshot's file
   SHA-256 would match the committed hash. It cannot: `fetched_at` is
   embedded by design; the data-level comparison (candle equality + exact
   metrics) is what holds — corrected and re-verified.
3. The same two files showed the preflight without its required
   `--input-json` argument (exit 2 otherwise) — corrected and re-verified.
4. "Pushed tip" current-state sentences were made date-qualified so they stay
   true when future commits advance the branch.

## 9. Reproduction instructions

See [REPRODUCIBILITY.md](REPRODUCIBILITY.md). In one pass: create a Python
3.11 venv, `pip install -e '.[dev,storage]'`, run the six verification gates,
then either the synthetic demo (fully offline) or the real-price path
(refetch + `xsentiment run`). Optional paid paths require employer
authorization and are gated by design.

## 10. Remaining external blockers

| Blocker | Exact missing input | Owner |
| --- | --- | --- |
| B1/B3/B10 | Approved X source + hard item/USD spend cap | employer |
| B2 | Apify/Tavily tokens via an approved private channel (never chat/Git/email) | employer |
| B4–B7 | n+0 convention, calendar deadline, news role, submission format/channel | employer |
| B9 | Availability-basis approval for any retrospective-archive experiment | employer |
| A1 | Calendar deadline (brief says both "one week" and "5–7 days") | employer |

The unsent email draft is in
[docs/EMPLOYER_CLARIFICATIONS.md](../docs/EMPLOYER_CLARIFICATIONS.md).

## 11. Submission recommendation and verdict

**Verdict: READY TO SUBMIT WITH DISCLOSED LIMITATIONS.**

Every deliverable that does not require external authorization is complete,
tested (209 offline tests re-passed on 2026-11-01 per
[TEST_PLAN.md](../TEST_PLAN.md)), lint-clean, validator-clean and CI-green on the
pushed tip, with a reproducible clean-environment workflow verified this
audit. The only outstanding items — the real X corpus, its credentials and
cap, and four employer convention decisions — are exactly the ones the
original assignment requires the user/employer to provide, and they are
documented with exact handoff instructions rather than hidden.

## Scorecard (evidence-based, not inflated)

| Dimension | Rating | Evidence |
| --- | --- | --- |
| Functional completeness | **4.5/5** with limits: | All offline mandatory requirements implemented and tested; the real-data path cannot be demonstrated by design until authorized (R2/A2 blocked, 1 clarification) |
| ML methodology correctness | **4.5/5** | Point-in-time alignment, purged walk-forward, identical folds, honest nulls, fail-closed availability; `n+0` convention is a recorded working default (B4 open) |
| Data integrity | **3/5** | Price data fully verified (coverage, gaps, duplicates, hash lineage); zero accepted X data, sentiment unmeasured |
| Software engineering quality | **4.5/5** | Typed boundaries, bounded ingestion, no paid-call retries, idempotent storage, no secrets committed, 209 offline tests at the 2026-11-01 verification (see
[TEST_PLAN.md](../TEST_PLAN.md)), gate discipline |
| Reproducibility | **4.5/5** | Byte-identical demo re-runs; exact metric reproduction from both file and persisted-database paths; manifest lineage; `fetched_at` snapshot limitation now documented honestly |
| Documentation quality | **4.5/5** | Nine canonical docs + 10-artifact package, machine-validated links/matrix; the audit's four defects fixed and re-verified |
| Submission readiness | **4/5** | Everything submittable is submitted; empirical sentiment conclusion awaits the authorized corpus |

The 0.5-point deductions across methodology/reproducibility/engineering are
for the same root cause: without a live provider run, adapter behavior
against the real Actor schema and the live-notifiable behavior of gated
commands remain synthetically verified only.
