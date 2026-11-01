# Requirement traceability (submission view)

This is a condensed copy of the authoritative 28-row matrix in
[`docs/REQUIREMENTS_TRACEABILITY.md`](../docs/REQUIREMENTS_TRACEABILITY.md)
(acceptance criteria, verification methods, evidence pointers, gaps and
blockers are validated by `scripts/validate_docs.py`). Where wording differs,
the canonical matrix wins. Requirement definitions live in
[`PRD.md`](../PRD.md) (R1–R15, NFR1–NFR6) and
[`docs/PHASE_1_REQUIREMENTS.md`](../docs/PHASE_1_REQUIREMENTS.md) (A1–A7).

Statuses as reconciled on 2026-11-01: **11 verified complete, 14 partially
complete, 0 not implemented, 2 blocked by external dependency, 1 needs
clarification.**

| ID | Requirement (short) | Implementation | Evidence | Status |
| --- | --- | --- | --- | --- |
| R1 | Reproducible pipeline ingestion → reporting | `src/xsentiment/main.py`, `pipeline/forecast_run.py` | `tests/integration/test_offline_demo.py`, committed `reports/btc-usd-180d/manifest.json` | Verified complete |
| R2 | Accepted 180-day X ingestion (ticker/cashtag/keyword) | `ingestion/apify_x.py`, `local_dataset_profile.py`, preflight + bounded ingest | `tests/unit/test_apify_x.py`, `test_ingest_apify_x.py`; no live run, no accepted corpus | **Blocked by external dependency** |
| R3 | Matching BTC-USD prices with documented provider/tz | `ingestion/prices.py` | 180/180 Coinbase bars 2026-04-29→2026-10-25 UTC profiled 2026-10-26; `test_coinbase_prices.py` | Verified complete |
| R4 | Provenance: event vs first-observed time, UTC, offsets, hashes | `ingestion/contracts.py`, `apify_x.py` | `test_contracts.py`, `test_apify_x.py`, `test_pipeline.py`; no real payload profiled yet | Partially complete |
| R5 | Preserve post text, likes, reposts, views, follower counts (missing stays missing) | `contracts.py` | `test_contracts.py`, `test_apify_x.py`, engagement-not-a-feature test, profiler missingness counts | Partially complete |
| R6 | Deterministic posts↔bars alignment (tz, dupes, gaps) | `pipeline/phase2.py` | `test_phase2_pipeline.py`, `test_dataset.py` (late/future/gap/unfinished-day) | Verified complete |
| R7 | Predeclared time-based sentiment/price features; missing sentiment stays null | `features/sentiment.py`, `price_features.py`, `dataset.py` | `test_features.py`, `test_dataset.py`; 180 real-price cutoffs, zero posts | Partially complete |
| R8 | Horizons n+0…n+5 without leakage | `phase2.py` targets, `models/forecasting.py` | six horizons in `reports/btc-usd-180d/metrics.json`; `n+0` convention unconfirmed | Partially complete |
| R9 | Chronological out-of-sample evaluation vs baselines | `validation/walk_forward.py`, `models/evaluation.py` | 5 purged folds, 100 OOS days/model/horizon, 1800 predictions; repeat-run determinism | Partially complete |
| R10 | Visual matrix: sentiment **change** vs price | `reporting/charts.py` (`sentiment_change_points`) | `test_reporting.py`; committed SVG renders with labelled empty sentiment panels | Partially complete |
| R11 | One-page current sentiment outlook | `reporting/outlook.py` + page contract check | `reports/btc-usd-180d/outlook.md`; contract tests | Partially complete |
| R12 | Evaluation report with Sharpe/Sortino/max drawdown where valid | `backtesting/metrics.py`, `strategy.py`, `reporting/report.py` | `reports/btc-usd-180d/evaluation-report.md`; metric/strategy tests | Verified complete |
| R13 | Reproducibility package (setup, queries, hashes, secret route) | README, `.env.example`, manifest provenance | fresh-clone verification 2026-10-27 at `ed2c5a4`; placeholder-only env; candidate Actor ID is locally configured but not employer-approved | Partially complete |
| R14 | Automated schema/timestamp/alignment/feature/target/metric/report tests | `tests/unit`, `tests/integration` | 209 tests passed 2026-11-01 (code `4264469`); CI lint+validators green | Partially complete |
| R15 | Persist and join X posts and price bars in a database | `storage/models.py`, `repositories.py`, `persist` + `run --database-url` | `test_storage_join.py`, `test_phase3_ingestion_e2e.py` (manifest `input_source=persisted_storage`) | Verified complete |
| NFR1 | Reproducibility metadata without secrets | `forecast_run.py` provenance/lineage | `test_pipeline.py`, offline-demo lineage checks | Verified complete |
| NFR2 | Temporal integrity, naive timestamps rejected | `contracts.py` | `test_contracts.py`, `test_pipeline.py` | Verified complete |
| NFR3 | No tokens/cookies/private exports/large raw data in Git | `.gitignore`, `.env.example` | 2026-10-26 working-tree and history pattern scan clean | Verified complete |
| NFR4 | Bounded caps; no auto-retry of paid launches | settings, `apify_x.py`, `tavily_news.py` | `test_apify_x.py`, `test_retry.py`, `test_tavily_news.py`; live billing untested by design | Partially complete |
| NFR5 | Exclusions audited; post text never logged by default | `local_dataset_profile.py`, `reporting/report.py` | `test_local_dataset_profile.py`, `test_reporting.py` | Verified complete |
| NFR6 | Fixtures/in-sample never presented as real OOS | reports, docs validator | `test_reporting.py`, `scripts/validate_docs.py` | Verified complete |
| A1 | Submit within the stated timeline | n/a | brief gives "one week" and "5–7 days", no calendar date; employer reply needed | Needs clarification |
| A2 | Provide Apify/Tavily/Exa tokens and Actor IDs | `.env.example` placeholders only | Apify and Tavily credentials plus a candidate Actor ID are configured locally; no employer approval, spend cap, private transfer route or live call exists | **Blocked by external dependency** |
| A3 | Use the linked historical tweet resource | registry + profiler | Google Doc re-fetched 2026-10-29 = 12-link compilation, not a corpus; no rows profiled | Partially complete |
| A4 | Ingest recent news with Tavily (context) | `fetch-news --confirm-live-call`, `run --news-file` | mocked tests cover streaming bounds, sanitization, no-retry, offline isolation | Partially complete |
| A5 | ML / RL offering | supervised ML path | naive + price-only + candidate model unit-tested; no RL environment defined | Verified complete |
| A6 | Historical dataset link inventory | `data/registry/historical_twitter_x_datasets.json` + validator | 12 records validated; independently reverified three listing/card metadata | Partially complete |
| A7 | Email the repository link, tokens/Actor IDs, evaluation report | this package + `docs/EMPLOYER_CLARIFICATIONS.md` draft | no email sent; Apify/Tavily credentials and a candidate Actor ID are configured locally but not approved or delivered; packet assembled | Partially complete |

Legend: statuses use the canonical vocabulary **Verified complete /
Partially complete / Not implemented / Blocked by external dependency /
Needs clarification**.

The two externally blocked items (R2, A2) plus the single clarification (A1)
are the only things standing between this package and a fully evidenced
submission; every partial row is partial because it awaits real X data or a
live provider call, not because implementation is missing.
