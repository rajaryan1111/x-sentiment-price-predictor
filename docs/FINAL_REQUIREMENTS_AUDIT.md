# Final requirements audit

**Status:** evidence-based audit independently re-verified on 2026-10-28. This document does
not replace the canonical [requirements traceability matrix](REQUIREMENTS_TRACEABILITY.md);
it independently classifies every requirement against code, tests, committed
artefacts and the verified offline run.

## 1. Source-of-truth limitation

The original assignment PDFs are **not present in this checkout**. The repository
records that they were read in full on 2026-10-26:

| Source | Pages | Recorded SHA-256 |
| --- | ---: | --- |
| `CWT X sentiment Agent - intern task.pdf` | 2 | `dc8211d11c5baf542b39b6e496e2a9b90e008b8a7b7108ba2b86b12b6ecbb19c` |
| `Historical Twitter_X Datasets_ Verified Download Links.pdf` | 2 | `511e71cba26df7dcbc089b89639ba4ea28a0f2697c5fd92ffdbf598ac82e75e7` |

Therefore **every row below is marked `T*`**: its exact definition is transcribed
from [PRD.md](../PRD.md), [PHASE_1_REQUIREMENTS.md](PHASE_1_REQUIREMENTS.md) and the
canonical matrix, and the primary-source wording is **NOT_VERIFIED against the
original PDF in this checkout**. No new requirement interpretation was invented.
The `Audit status` column describes implementation/evidence against that
transcription, not re-verification of the PDF itself.

## 2. Classification rules and evidence key

- **COMPLETE** — the implementable software is present and verified by tests,
  artefacts or CI; no external account is needed for the engineering acceptance.
- **PARTIAL** — code/artefacts exist, but full acceptance needs real data,
  employer confirmation or live verification.
- **BLOCKED_EXTERNAL** — the requirement cannot proceed without an approved
  external source, credential, licence or explicit authorization.
- **NOT_IMPLEMENTED** — no meaningful implementation exists.
- **NOT_VERIFIED** — the required external fact is unavailable in this checkout;
  it cannot be inferred from repository timestamps.

Evidence codes: **C** code inspection; **T** automated tests; **A** application or
committed artefact; **H** historical real-data run; **M** mocked provider; **S**
clearly labelled synthetic fixture; **X** external evidence missing. Historical
real-data numbers are from `reports/btc-usd-180d/`; the current sandbox could not
refetch public prices because its outbound network is restricted to package and
GitHub hosts. Synthetic numbers from `scripts/make_offline_demo.py` are never
treated as market evidence.

## 3. Status summary

| Status | Count | Requirement IDs |
| --- | ---: | --- |
| COMPLETE | 12 | R1, R3, R6, R12, R14, R15, NFR1, NFR2, NFR3, NFR5, NFR6, A5 |
| PARTIAL | 12 | R4, R5, R7, R8, R9, R10, R11, R13, NFR4, A4, A6, A7 |
| BLOCKED_EXTERNAL | 3 | R2, A2, A3 |
| NOT_IMPLEMENTED | 0 | None |
| NOT_VERIFIED | 1 | A1 |

Total: **28 requirements**. Externally blocked or clarification-dependent
rows: R2, A1, A2 and A3. Additional partial rows depend indirectly on the same
accepted-X-data gate. PR #14 delivery is separately gated by the session branch
policy B8, not by an unimplemented requirement.

This audit is intentionally more conservative than the canonical matrix for R8:
the six horizons are implemented, but the `n+0` target convention is still a
working default requiring employer confirmation. R15, NFR1 and the news CLI are
verified as offline engineering, not as live provider or real-X acceptance.

## 4. Verification basis

- On 2026-10-28, the full offline suite, Ruff, `scripts/validate_docs.py`,
  `scripts/validate_dataset_registry.py`, `python -m compileall -q src tests scripts`
  and `git diff --check` were rerun from a fresh Python 3.11.2 virtual environment;
  see [FINAL_VERIFICATION_REPORT.md](FINAL_VERIFICATION_REPORT.md). The suite now
  has 167 passing tests at this revision.
- A real CLI end-to-end run used deterministic synthetic inputs from
  `scripts/make_offline_demo.py`; `tests/integration/test_offline_demo.py`
  validates all six artefacts, six horizons, three models, finite metrics,
  prediction records, input lineage, byte-identical repeatability and absence of
  network access. `tests/unit/test_tavily_news.py` proves the news response ceiling
  is enforced while streaming; `tests/unit/test_fetch_news_cli.py` proves secret
  redaction in provider errors and caller notes.
- GitHub Actions verified the pushed working branch with the same four checks;
  run URLs are recorded in the verification report.
- No live Tavily, Exa, Apify or Coinbase request was made during this audit.

## 4.1 Independent evidence cross-check (2026-10-28)

Documentation claims were not counted as implementation evidence. For every
requirement row, the named source path and automated-test path were checked
against the actual working tree. The concrete checks were:

- `pytest --collect-only -q` collected 167 cases at this revision; the full suite
  then passed with zero failures and zero skips on 2026-10-28.
- `tests/unit/test_coinbase_prices.py`, `test_contracts.py`,
  `test_phase2_pipeline.py`, `test_dataset.py`, `test_features.py`,
  `test_walk_forward.py`, `test_models.py`, `test_evaluation.py`,
  `test_metrics.py`, `test_strategy.py` and `test_reporting.py` were used to
  verify price validation, timestamps, alignment, sentiment/price features,
  leakage-safe targets, folds, models, metrics, risk and reporting.
- `tests/unit/test_storage_join.py` and `test_phase3_ingestion_e2e.py` verify the
  database join and persisted-input CLI. `tests/unit/test_apify_x.py`,
  `test_tavily_news.py`, `test_fetch_news_cli.py`, `test_retry.py` and
  `tests/integration/test_offline_demo.py` verify bounded adapters, gated news,
  redaction, streaming size limits, no-network operation and end-to-end artefacts.
- `scripts/validate_docs.py` and `scripts/validate_dataset_registry.py` verify
  documentation structure and the 12-entry dataset registry; they do **not**
  verify external URLs, licences or real provider behaviour.
- Committed `reports/btc-usd-180d/` artefacts were cross-checked for internal
  metric/manifest/report consistency. The original PDFs and raw price snapshot
  remain unavailable, so primary-source wording and live re-fetch were not
  re-verified in this checkout.

This cross-check supports the implementation statuses below; it does not convert
external data/authorization gates into completion.

## 5. Functional requirements (R1–R15)

| ID | Brief | Exact requirement (repository definition) | Audit status | Implementation and verified evidence | Missing functionality / dependency |
| --- | --- | --- | --- | --- | --- |
| R1 | T* | A reproducible Python pipeline from data acquisition through reporting | COMPLETE | C/T/A/S: `src/xsentiment/main.py`, `pipeline/forecast_run.py`; `tests/unit/test_pipeline.py`, `tests/integration/test_offline_demo.py`; README quick start; manifest with hashes, versions and `input_lineage`. A full offline CLI run writes all six artefacts. | Real X acquisition is covered by R2; this status is for the reproducible software workflow and its offline evidence. |
| R2 | T* | Collect asset-related X posts covering the most recent 180-day period via an approved Apify/provider route, using ticker, cashtag and keyword searches | BLOCKED_EXTERNAL | C/M: `ingestion/apify_x.py`, `local_dataset_profile.py`; `tests/unit/test_apify_x.py` and `test_phase3_ingestion_e2e.py` use mocked provider payloads and synthetic records. | No approved X source, Actor, credentials, spend cap, accepted 180-day corpus or real three-mode ingest. Requires B1/B2/B3. |
| R3 | T* | Obtain price observations for the same asset and period with documented provider, interval, timezone and currency | COMPLETE | C/T/H/A: `ingestion/prices.py`; `tests/unit/test_coinbase_prices.py`; committed `reports/btc-usd-180d/manifest.json` and coverage evidence record 180/180 public Coinbase daily bars. Current live endpoint was not refetched in this sandbox. | Historical evidence is from committed artefacts; current live endpoint availability is not re-verified in this network-restricted sandbox. |
| R4 | T* | Preserve source identifiers, timezone-aware event timestamps (supplied UTC/EST offsets), UTC normalisation, retrieval timestamps and provenance; align UTC/EST source timestamps | PARTIAL | C/T/S: `ingestion/contracts.py`, `apify_x.py`, `pipeline/forecast_run.py`; contract, adapter and loader tests cover non-UTC offsets, raw timestamp provenance, payload hashes and naive-time rejection. | Contract behaviour is fixture-verified only; actual provider timestamp/offset fields remain unprofiled. |
| R5 | T* | Preserve post text plus available likes, reposts, views and author follower counts, keeping missing values missing | PARTIAL | C/T/S: `ingestion/contracts.py` requires text, allows nullable engagement/follower fields, rejects negatives; feature-group tests prove current engagement is not a predictor. Synthetic demo records exercise nulls. | Real provider field availability and historical engagement snapshots are unavailable. |
| R6 | T* | Align social posts and price bars deterministically, covering bar boundaries, timezone, duplicates and gaps | COMPLETE | C/T/A: `pipeline/phase2.py`, `features/dataset.py`; tests for exact half-open UTC windows, duplicate IDs, late/future posts, missing days, unfinished-day exclusion and deterministic assembly. | Alignment is verified with fixtures and public price data, not a real X corpus. |
| R7 | T* | Create documented time-based sentiment and price features (for example sentiment score, post volume, lagged returns and time horizon) | PARTIAL | C/T/A/S: `features/sentiment.py`, `price_features.py`, `dataset.py`; predeclared feature groups, VADER scoring, null-preserving sentiment aggregation and one model per horizon are unit-tested and exercised by the offline demo. | Sentiment features are verified on synthetic text only; no permitted real X language has been scored. |
| R8 | T* | Produce model outputs for horizons n+0 through n+5 | PARTIAL | C/T/A: `pipeline/phase2.py` (`build_close_targets`), `models/forecasting.py`; `tests/unit/test_dataset.py`, `test_evaluation.py`; committed and generated metrics contain all six `n+0`..`n+5` horizons and keep targets out of features. | Implementation is complete, but the `n+0` target convention is a working default and needs employer confirmation (B4). More conservative than the canonical matrix. |
| R9 | T* | Evaluate chronologically on unseen periods and compare sentiment-plus-price against baselines with rigorous out-of-sample validation | PARTIAL | C/T/A: `validation/walk_forward.py`, `models/evaluation.py`; purged expanding folds, identical eligible rows for naive/price-only/sentiment-price, deterministic repeat-run tests and per-horizon MAE/RMSE tables. | Chronological evaluation is complete, but the sentiment-vs-price verdict cannot be measured without accepted X data (R2). |
| R10 | T* | Generate a visual matrix of X sentiment change against price over time | PARTIAL | C/T/A/S: `reporting/charts.py` has price, sentiment-level and day-over-day sentiment-change panels; `tests/unit/test_reporting.py` covers positive/zero change, unavailable days and deterministic rendering. Offline demo renders all panels. | The change-series code is complete and fixture-verified; a real-data sentiment chart needs R2. |
| R11 | T* | Produce a one-page summary of the current sentiment outlook for the asset | PARTIAL | C/T/A: `reporting/outlook.py` and `check_outlook_page`; report tests enforce sections, line ceiling, disclaimer and explicit unavailable states. Caller limitations now appear in the outlook as well as the report. | The page contract is complete; real sentiment and live news content are unavailable by design. |
| R12 | T* | Produce an evaluation report in PDF or Markdown including Sharpe ratio, Sortino ratio and maximum drawdown | COMPLETE | C/T/A/H: `backtesting/metrics.py`, `strategy.py`, `reporting/report.py`; known-value metric/strategy tests and committed `reports/btc-usd-180d/evaluation-report.md` with Sharpe, Sortino, max drawdown, fees and withheld-metric reasons. | Risk metrics come from a short, single-asset historical sample and a predeclared strategy; no sentiment variant is available. |
| R13 | T* | Provide a reproducibility package: setup, commands, provider and Actor identifiers, query configuration, snapshots or hashes and secure secrets | PARTIAL | C/T/A: README, `.env.example`, `scripts/make_offline_demo.py`, manifest provenance and `input_lineage`; docs validator, dataset validator and offline demo test. Query modes/hashes are recorded without raw query terms. | Actor identifiers, real query configuration and a secure credential transfer route remain external (R2, A2, B2). |
| R14 | T* | Provide automated tests for schemas, timestamps, alignment, features, targets, leakage, metrics and reports | COMPLETE | C/T/CI: `tests/unit/` and `tests/integration/` cover schemas, timestamps, alignment, features, targets, leakage, metrics, reports, storage, mocked providers, CLI, streaming response bounds, secret redaction and offline network isolation; on 2026-10-28 the suite has 167 passing tests at this revision; `TEST_PLAN.md` is the authoritative current count; GitHub Actions runs lint, both validators and pytest. | CI verifies the offline suite; it cannot verify live provider behaviour or real X acceptance. |
| R15 | T* | Join the X-post and price datasets in a database | COMPLETE | C/T/A: `storage/models.py`, `repositories.py`, `main.py`; `test_storage_join.py` and `test_phase3_ingestion_e2e.py` verify a versioned schema, idempotent upserts, descriptive/cutoff joins and a complete `run --database-url` with `input_source = persisted_storage`. | The offline database path is complete; a database holding licensed real X rows depends on R2. |

## 6. Non-functional requirements (NFR1–NFR6)

| ID | Brief | Exact requirement (repository definition) | Audit status | Implementation and verified evidence | Missing functionality / dependency |
| --- | --- | --- | --- | --- | --- |
| NFR1 | T* | Reproducibility metadata: code revision, source/version, query/window, retrieval time, schema, non-secret run ID | COMPLETE | C/T/A: `pipeline/forecast_run.py` `_code_revision`, `_input_lineage`, `_manifest` and `load_price_snapshot_metadata`; `main.py` writes UTC `fetched_at`. Manifest records revision, run ID, versions, hashes, windows, retrieval, schema and non-secret query identity. | Price provider retrieval time is explicit when `fetch-prices` writes `fetched_at`; older or synthetic snapshots record an explicit unavailable reason instead of inventing one. |
| NFR2 | T* | Temporal integrity: timezone-aware timestamps, event time distinct from first-observed time | COMPLETE | C/T: `ingestion/contracts.py` requires timezone-aware `created_at` and `retrieved_at`, forbids backdated retrieval and normalizes offsets to UTC; contract and loader tests cover naive and offset cases. | Real provider payloads are unprofiled, but the contract is enforced in code and tests. |
| NFR3 | T* | Security: no tokens, cookies, private exports or large raw datasets in Git | COMPLETE | C/T/A: `.gitignore`, `.env.example`, secret-scan review, metadata allow-listing and CLI redaction tests. No live credential, raw private export or generated dataset is tracked in this checkout. | Git history outside this checkout cannot be independently rescanned here; no secret was introduced by this work. |
| NFR4 | T* | Robustness: bounded timeouts, payloads, concurrency and cost; no automatic retry of paid launches | PARTIAL | C/T/M: `config/settings.py`, `ingestion/http.py`, `apify_x.py`, `tavily_news.py`, `retry.py`; tests enforce timeouts, a streaming response ceiling, cost/item caps, no launch retry, one-request news behaviour and offline network isolation. | Live paid-run and billing semantics remain untested by design; no authorization exists to exercise them. |
| NFR5 | T* | Auditability: exclusions recorded with reasons; post text never logged by default | COMPLETE | C/T: `local_dataset_profile.py` and reporting modules record counts/exclusion reasons without printing post text; chart empty states are explicit; profiler/report tests cover the no-text guarantee. | No real post text exists to test the no-print guarantee against; fixtures and profiler behaviour are verified. |
| NFR6 | T* | Honest reporting: fixtures and in-sample values never presented as real out-of-sample results | COMPLETE | C/T/A: report/outlook separate measured, unavailable and synthetic states; docs validator rejects unqualified stale test-count claims; offline demo labels synthetic prices/posts in inputs, manifest, report and outlook. | Enforcement combines code, tests and documentation convention; not every free-text sentence can be machine-verified. |

## 7. Assessment-specific requirements (A1–A7)

| ID | Brief | Exact requirement (repository definition) | Audit status | Implementation and verified evidence | Missing functionality / dependency |
| --- | --- | --- | --- | --- | --- |
| A1 | T* | Submit within the stated timeline (the brief says both one week and 5–7 days) | NOT_VERIFIED | X: no employer message or calendar due date exists in the repository. The brief is recorded as saying both one week and 5–7 days. | Exact calendar deadline and timezone require employer clarification. Primary-source wording is also not re-verifiable from this checkout. |
| A2 | T* | Provide the APIFY/Tavily/Exa tokens and Actor IDs used for scraping | BLOCKED_EXTERNAL | C/A: `.env.example` has placeholders only; no Actor ID or token exists and no private credential channel is defined. | Requires approved Actor/provider selection and a private credential channel; secrets must never be committed or shared in chat. |
| A3 | T* | Use the historical tweets resource linked by the assessment | BLOCKED_EXTERNAL | C/T/A: `local_dataset_profile.py`, `profile_local_x_dataset.py`, dataset registry and validator; the linked Google Doc is a 12-entry link list, not a tweet corpus, and no accepted candidate exists. | Requires candidate dataset selection, licence/terms review, download, schema/text check and 180-day coverage profile. |
| A4 | T* | Ingest the most recent and relevant news with Tavily to complement X sentiment; Exa appears in the submission line | PARTIAL | C/T/M: `main.py` `fetch-news` and `run --news-file`, `tavily_news.py`, `pipeline/forecast_run.py`; adapter and CLI tests use mocked HTTP and prove context-only behaviour, streaming size bounds, redaction in errors/caller notes, no retry, offline network isolation and unchanged predictions/metrics. | Live Tavily behaviour and a real news snapshot require an approved key, authorization and confirmation that live news is mandatory (B6). |
| A5 | T* | The brief offers a machine learning / reinforcement learning pipeline | COMPLETE | C/T: `models/baseline.py` and `forecasting.py` implement supervised multi-horizon ML with naive and price-only baselines; no RL environment is defined or claimed. | RL is not implemented; the brief does not define an RL environment. Reopen only on explicit employer instruction. |
| A6 | T* | Reference inventory of historical Twitter/X datasets with verified download links | PARTIAL | C/T/A: `data/registry/historical_twitter_x_datasets.json` and `scripts/validate_dataset_registry.py`; structural validator checks platform identity, ID-only caveats, coverage limitations and the explicit `not-reverified` state. | Registry entries are transcribed; live provider pages, current availability and licence terms were not independently re-verified. |
| A7 | T* | Submit the repository link, provider tokens and Actor IDs, and the evaluation report by email to gilad@crowdwisdomtrading.com | PARTIAL | A: repository URL, Markdown evaluation report and the four submission documents exist. No email was sent and no provider identifiers/tokens were delivered. | Email delivery, provider identifiers/tokens and a sentiment-backed evaluation require user authorization and R2/A2. |

## 8. External blockers and their requirement impact

The exact questions and owners remain in [EXTERNAL_BLOCKERS.md](EXTERNAL_BLOCKERS.md).
In summary:

- **B1/B3** approved X source, dataset/Actor selection, licence and spend cap —
  blocks R2, R4, R5, R7, R9, R10, R11, A3, A6 and the real-data part of R15.
- **B2** secure credential-transfer route — blocks A2 and any live provider run.
- **B4** `n+0` target convention — prevents treating R8/R9 as employer-confirmed.
- **B5** exact calendar deadline — leaves A1 NOT_VERIFIED.
- **B6** live Tavily requirement and news feature policy — leaves A4 PARTIAL.
- **B7** submission format/email authorization — leaves A7 PARTIAL.
- **B8** session branch policy — PR #14's head cannot be advanced from this
  restricted Arena session; see [PR14_PROMOTION.md](PR14_PROMOTION.md). This is a
  delivery permission blocker, not an implementation defect.

## 9. Defensible conclusion

The implementable engineering pipeline is complete and reproducible offline,
including the gated news CLI, streaming response bound, input-lineage provenance,
a full CLI end-to-end demonstration, offline network isolation and CI verification.
The assignment is not fully satisfiable in this environment because no accepted X
corpus, provider credential, paid-call authorization, employer clarification,
PR-head promotion permission or submission email exists. Those limitations are
recorded here rather than hidden. See
[SUBMISSION_SUMMARY.md](SUBMISSION_SUMMARY.md) for the evaluator-facing summary
and [DEMO_WALKTHROUGH.md](DEMO_WALKTHROUGH.md) for the timed demonstration.
