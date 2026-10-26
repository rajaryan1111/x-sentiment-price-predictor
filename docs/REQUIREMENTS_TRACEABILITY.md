# Requirements traceability matrix

Every explicit assignment requirement, mapped to the canonical document that owns it,
the code that implements it, the evidence that exists for it, and the next action.

## Authority and a limitation to read first

The authoritative source is the supplied assessment PDF (`CWT X sentiment Agent -
intern task.pdf`) together with its dataset-reference PDF. **Those PDFs are not
available in the environment where this matrix was last updated**, so the requirement
wording below is transcribed from this repository's own record of the brief in
[PHASE_1_REQUIREMENTS.md](PHASE_1_REQUIREMENTS.md) §2. If the PDF differs, the PDF
wins and this matrix must be corrected. Requirement text, deadlines and employer
clarifications are never inferred from repository timestamps.

## Status vocabulary

- **verified complete** — implemented and evidenced by tests plus a real-data run.
- **implemented, evidence limited** — code exists and is unit-tested, but the real
  input it needs is not available, so the end-to-end claim is unproven.
- **partial** — some sub-parts are verified while others are open.
- **blocked** — needs an external decision, account, dataset or clarification.
- **ambiguous** — the brief permits more than one reading; a documented default is in
  force and the ambiguity is recorded rather than silently resolved.

## Matrix

| ID | Requirement (faithful summary) | Canonical doc | Implementation | Evidence | Status | Next action |
| --- | --- | --- | --- | --- | --- | --- |
| R1 | Reproducible Python pipeline from acquisition through reporting | PRD §FR1, RULES | `src/xsentiment/main.py`, `pipeline/forecast_run.py`, `pipeline/phase2.py` | `python -m xsentiment run` writes report/outlook/chart/metrics/predictions/manifest; manifest records input hashes, config and versions; README commands | verified complete | Keep commands and hashes current as code changes |
| R2 | Collect asset-related X posts for the 180-day window via an approved Apify/provider route | PRD §FR2, DATA_POLICY §X source, DECISIONS D-009 | `ingestion/apify_x.py` (bounded, mocked), `ingestion/local_dataset_profile.py` | `tests/unit/test_apify_x.py`, `test_local_dataset_profile.py`; no live run, no accepted dataset | blocked | Inspect a real Actor's schema/terms/pricing and obtain spend approval, or accept a permitted post-level dataset |
| R3 | Price observations for the same asset and period with documented provider, interval, timezone and currency | PRD §FR3, DATA_POLICY §Price source, DECISIONS D-003 | `ingestion/prices.py`, `scripts/profile_coinbase_180d.py` | 180/180 public Coinbase `BTC-USD` daily bars for 2026-04-29→2026-10-25 UTC refetched 2026-10-26 with no missing/duplicate timestamps; `tests/unit/test_coinbase_prices.py` | verified complete | Re-run the profile at submission time if newer coverage is wanted |
| R4 | Preserve source IDs, event time, UTC normalisation, retrieval time and provenance | DESIGN §Normalized X post, PHASE_2_DATA_CONTRACT | `ingestion/contracts.py`, `pipeline/phase2.py` | `test_contracts.py`, `test_phase2_pipeline.py` (naive timestamp rejection, late-arrival exclusion, no backdating) | implemented, evidence limited | Real provider records still need a provenance profile on accepted data |
| R5 | Preserve post text plus available engagement and follower counts; missing values stay missing | DESIGN, DECISIONS D-010/D-022 | `ingestion/contracts.py`, `ingestion/apify_x.py` | Nullable engagement/follower fields with rejection of negative counts; current counts are excluded from historical features | implemented, evidence limited | Confirm field availability on the selected Actor before any collection |
| R6 | Deterministic alignment of posts and price bars (bar boundaries, timezone, duplicates, gaps) | DESIGN §Forecast/time contract, PRD §FR5 | `pipeline/phase2.py` (`build_point_in_time_features`, `profile_daily_price_coverage`) | `test_phase2_pipeline.py`, `test_dataset.py`: trailing-24h window, late/future exclusion, gap reporting, unfinished-day drop | verified complete | None |
| R7 | Time-based sentiment and price features | MODEL_PLAN §Features, PRD §FR7 | `features/sentiment.py`, `features/price_features.py`, `features/dataset.py` | `test_features.py`, `test_dataset.py`; feature groups are fixed and the price-only group excludes sentiment columns | implemented, evidence limited | Score real permitted text once an X source is accepted |
| R8 | Outputs for horizons n+0 through n+5 | DESIGN §Targets, MODEL_PLAN §Question and target, DECISIONS D-004 | `pipeline/phase2.py` (`build_close_targets`), `models/forecasting.py`, `models/evaluation.py` | `reports/btc-usd-180d/metrics.json` has all six horizons for three models; `test_evaluation.py` asserts horizon coverage | verified complete | Target semantics still need employer confirmation |
| R9 | Chronological out-of-sample evaluation against price-only and naive baselines | MODEL_PLAN §Validation, PRD §FR9 | `validation/walk_forward.py`, `models/evaluation.py` | 5 purged expanding folds, 100 test days per model/horizon, 1800 predictions; deterministic repeat-run test; no random split in code | verified complete for prices; blocked for the sentiment comparison | Add sentiment rows when an X source is accepted |
| R10 | Charts comparing X sentiment and price over time | PRD §FR10, MODEL_PLAN | `reporting/charts.py` | `reports/btc-usd-180d/sentiment-vs-price.svg`; `test_reporting.py` covers both panels and the explicit empty-sentiment message | implemented, evidence limited | The sentiment curve appears only once real scored posts exist |
| R11 | One-page current sentiment outlook | PRD §FR11, DESIGN §Output contracts | `reporting/outlook.py` | `reports/btc-usd-180d/outlook.md`; `test_reporting.py` checks coverage, limitations and disclaimer | implemented, evidence limited | Outlook currently states sentiment unavailability by design |
| R12 | Evaluation report including Sharpe, Sortino and maximum drawdown | MODEL_PLAN §Trading risk metrics, DECISIONS D-007/D-017 | `backtesting/metrics.py`, `backtesting/strategy.py`, `reporting/report.py` | `reports/btc-usd-180d/evaluation-report.md`; ratios computed only from out-of-sample strategy returns with fees/annualisation disclosed, and withheld with a reason when the sample is under 30 days or dispersion is zero | implemented, evidence limited | Report trading metrics only as strategy statistics; re-run once sentiment exists |
| R13 | Reproducibility package: setup, commands, provider/Actor identifiers, configuration, secure secrets | PRD §FR13, RULES §Security, DATA_POLICY | `README.md`, `main.py`, run `manifest.json`, `.env.example` | README quick start, manifest provenance block, documented secret-handling policy | partial | Actor ID is not chosen yet; credentials must go through an employer-approved private channel, never Git |
| R14 | Automated tests for schemas, timestamps, alignment, features, targets, leakage, metrics and reports | TEST_PLAN | `tests/unit/*` (97 tests) | Local `pytest` 97 passed; CI runs Ruff + registry validation + pytest | verified complete for implemented behaviour | Add X-provider contract tests when a real source is accepted |
| A1 | Submission timeline (brief says “within one week” and “5–7 days”) | DECISIONS D-014 | — | Repo contains no employer deadline; none is inferred | ambiguous | Confirm the actual deadline from the employer's message |
| A2 | Provider tokens and Actor IDs for reproducibility | PHASE_1_REQUIREMENTS §5 Credentials | `.env.example` placeholders only | No token or Actor ID is required in Git; secrets stay out of the repository | blocked | Decide the secure transfer route with the employer |
| A3 | Historical dataset resource linked by the assessment | DATA_POLICY §Historical datasets, DECISIONS D-008 | `ingestion/dataset_registry.py`, `data/registry/*.json` | 12 candidate sources validated structurally; platform identity and rights unchecked; uploaded ZIP internals unverified | blocked | Retrieve the linked resource (or inspect the archives locally with `scripts/profile_local_x_dataset.py`) and review terms |
| A4 | Recent news ingestion via Tavily (Exa also named in the checklist) | DECISIONS D-005/D-013, DATA_POLICY §News | `ingestion/news.py` (placeholder), `--news-file` context loader | No Tavily/Exa call was made; news is context-only and never a feature | ambiguous | Confirm whether news is contextual or predictive, then implement the adapter if needed |
| A5 | Machine learning / reinforcement learning wording | DECISIONS D-006 | `models/baseline.py`, `models/forecasting.py` | Supervised multi-horizon forecasting with baselines; RL excluded until an action/reward/execution model is specified | ambiguous | Revisit only with an explicit RL requirement and a specified design |

## Known gaps that block a complete submission

1. **X data access (R2, R7, R9, R10, R11).** The only blocker for the sentiment half of
   the assignment. Needs an accepted, permitted, profiled post-level source with event
   times and defensible availability, plus a spend decision if a paid Actor is used.
2. **Sentiment-versus-price result (RE9/R12).** Cannot be produced honestly until (1) is
   resolved; the pipeline already reports it as not identifiable instead of guessing.
3. **Employer clarifications (A1, A2, target semantics).** Deadline, credential route and
   confirmation of the `n+0` interpretation.
4. **News role (A4).** Tavily/Exa runtime role remains undecided.

## Corrections made on this branch

- Added an unfinished-UTC-day guard to `build_point_in_time_features` and
  `build_close_targets`, so a partial intraday close can no longer act as a completed
  prior close or as a horizon label; covered by new tests.
- Corrected `DESIGN.md`, which described post text as nullable while the implemented
  contract requires non-empty text; recorded the rule as DECISIONS D-022.
- Fixed a real defect found by the new tests: the evaluation report passed a
  `StrategyResult` where `StrategyAssumptions` was expected, which raised at render time.
- Fixed the CLI hashing its inputs before its error handling, which turned a missing
  input file into an unhandled traceback instead of a non-zero exit.
- Replaced placeholder modules (`features`, `models`, `validation`, `backtesting`,
  `reporting`, `main`) with implemented, tested code and updated every canonical
  document that made a status or interface claim about them.
