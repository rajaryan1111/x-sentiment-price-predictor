# Phase 1 — Requirements and Scope Lock

**Status:** Phase 1 requirements baseline drafted; approval-dependent decisions remain explicitly open.  
**Primary source:** `CWT X sentiment Agent - intern task.pdf` supplied by the user.  
**Repository:** `rajaryan1111/x-sentiment-price-predictor`  
**Purpose:** Convert the assessment brief into traceable, testable requirements before implementing the data pipeline or models.

## 1. Source-of-truth rules

1. The supplied assessment PDF is the authority for the assignment requirements.
2. This document translates the PDF into engineering requirements; it does not claim that any unimplemented feature already works.
3. Where the PDF is ambiguous, the ambiguity is recorded as an open decision rather than silently guessed.
4. Dataset registry entries are candidate sources, not proof that the dataset is accessible, licensed for this use, suitable, or compatible.
5. A successful test or CI run proves only the checks that actually ran. It does not prove forecasting quality or profitability.
6. Keep decisions in this document current; record material changes with rationale and update the traceability table.

## 2. Assignment summary (from the assessment PDF)

The assessment asks for a Python-based machine-learning / reinforcement-learning pipeline that predicts an asset's price at horizons `n+0` through `n+5`, using X (Twitter) sentiment and price as predictive inputs. It describes scraping asset-related X posts for the last 180 days with Apify, obtaining price data for the same period, aligning timestamps and engagement metadata with price bars, ingesting recent relevant news using Tavily, creating time-based sentiment/price features, running rigorous out-of-sample validation, generating visualizations, writing a one-page current sentiment outlook, and submitting a repository plus an evaluation report containing Sharpe ratio, Sortino ratio and maximum drawdown. The PDF lists a 5–7 day timeline and asks for repository, provider credentials/tokens and actor IDs for reproducibility.

The linked historical-tweet resource is referenced by the PDF as a potential learning/training dataset. Its exact contents, availability, rights, schema, and suitability must be verified before it is relied on.

## 3. Goals

### Required outcomes

- **R1 — Reproducible Python pipeline:** A documented, repeatable workflow from data acquisition/ingestion through alignment, features, modeling, evaluation and reporting.
- **R2 — X ingestion:** Collect asset-related posts for a rolling or explicitly bounded 180-day window using an approved Apify actor/provider route.
- **R3 — Price ingestion:** Obtain price observations for the same chosen asset and period, with a documented provider, bar interval, timezone, currency and adjustment policy.
- **R4 — Time and provenance integrity:** Preserve source identifiers, original event timestamps, UTC-normalized timestamps, retrieval timestamps, source/provider details and data lineage. Never silently substitute retrieval time for event time.
- **R5 — Post metadata:** Preserve available post text, engagement values (likes, reposts, views) and author follower counts. Missing fields must remain missing/null and be reported; do not fabricate them.
- **R6 — Alignment:** Define deterministic rules for mapping posts and sentiment aggregates to price bars, including bar boundaries, timezone conversion, duplicate handling and missing intervals.
- **R7 — Sentiment/price features:** Create documented, time-based features from sentiment and price, such as sentiment score, post volume, lagged returns and horizon-related features.
- **R8 — Forecast horizons:** Produce model outputs for `n+0`, `n+1`, `n+2`, `n+3`, `n+4`, and `n+5` after the period and target-price definition have been agreed and implemented.
- **R9 — Out-of-sample evaluation:** Evaluate chronologically on unseen future periods; avoid random time-series splits and leakage. Compare a sentiment-plus-price model with a price-only baseline.
- **R10 — Visual output:** Generate charts showing X sentiment changes alongside asset-price changes over time.
- **R11 — Outlook:** Generate a one-page current sentiment outlook for the chosen asset. Clearly distinguish observed data, model outputs, contextual news and uncertainty.
- **R12 — Evaluation report:** Produce a PDF or Markdown report documenting the evaluation and reporting Sharpe ratio, Sortino ratio and maximum drawdown only when valid strategy returns and explicit assumptions are available.
- **R13 — Reproducibility package:** Document repository setup, commands, provider/actor identifiers, configuration, data snapshots or hashes, and steps needed to reproduce the run without exposing secrets publicly.
- **R14 — Quality gates:** Provide automated tests for schemas, timestamp rules, alignment, feature generation, target construction, leakage safeguards, metrics and report outputs.

### Explicit non-goals / claims not permitted without evidence

- Do not claim guaranteed price accuracy, profitable trades, investment advice, or future selection/performance.
- Do not report invented, placeholder, in-sample-only, or synthetic-fixture metrics as real results.
- Do not claim a complete live pipeline while provider ingestion, training, evaluation or reporting remains unimplemented.
- Do not commit raw large datasets, private exports, API tokens, cookies, or other credentials to Git.
- Do not use random train/test splits as the primary time-series evaluation.
- Do not treat a dataset registry entry or a source PDF's license statement as legal approval.
- Do not add news-derived variables to the predictive model unless the specification is clarified and the feature policy is deliberately revised.
- Do not introduce reinforcement learning merely to satisfy terminology; its role must be justified by a clearly defined action/reward and evaluated without leakage if it is used.

## 4. Scope boundaries and interpretation

### Predictive inputs versus news context

The PDF says to ingest recent news using Tavily, but it also says feature engineering and the predictive model must use **sentiment and price only**. To honor the stricter explicit model-input requirement, news is in scope for contextual research and the one-page outlook, but **excluded from predictive features by default**. This is a conservative interpretation, not a claim that the employer has confirmed it. Record a clarification request if news is intended to influence the forecast.

### ML versus reinforcement learning

The brief says “machine learning / reinforcement learning.” The required forecast outputs and performance metrics do not, by themselves, define an RL environment or reward. The baseline plan is supervised forecasting plus a price-only comparator. An RL trading policy is not in the initial scope unless a well-defined action space, reward, execution assumptions and evaluation design are approved. This avoids adding unnecessary complexity or implying that RL is mandatory.

### Performance metrics

Sharpe, Sortino and maximum drawdown are trading-strategy metrics, not standalone measures of forecast error. Report them only from a defined strategy applied to strictly out-of-sample predictions, using disclosed position sizing, return convention, transaction costs, slippage, risk-free-rate/annualization assumptions and treatment of missing bars. Also report forecast metrics appropriate to the target (for example MAE/RMSE and directional metrics when defined). If a strategy cannot be defensibly specified, mark trading metrics as unavailable and explain why rather than fabricating them.

### Credentials and submission security

The assessment requests provider tokens and actor IDs for reproducibility. Actor IDs and non-secret configuration can be documented in the repository. **Never publish API tokens in a public repository or report.** Share any required secrets only through an employer-approved private channel, with minimum necessary scope; rotate any secret that has been exposed. Before sending credentials, confirm the recipient and secure transfer method.

### Historical datasets

The existing registry records 12 candidate sources from a user-supplied dataset list. It does not mean all sources should be downloaded. Some entries are StockTwits (not X), some are tweet-ID-only and require rehydration, some have licensing/count/schema caveats, and some may be too large for the assessment window. Select one primary training dataset only after checking relevance, access, rights, text availability, timestamp coverage, schema and feasible size. Keep source platform identity explicit; do not relabel StockTwits as X.

## 5. Acceptance criteria

Phase 1 is ready for implementation planning when:

- [ ] Every explicit requirement from the assessment PDF is represented in this document.
- [ ] Each requirement has a planned implementation/evidence artifact in the traceability matrix.
- [ ] Known ambiguities are logged with owner/decision needed; none is silently converted into a fact.
- [ ] The asset and asset class, bar interval, definition of `n`, meaning of `n+0`, and forecast target convention are confirmed or clearly remain blocking open decisions.
- [ ] Price source, adjustment policy, market timezone/calendar, and news role are decided or remain documented blockers.
- [ ] The historical training-data link has been inspected; access, terms, schema, time coverage and fit are recorded before use.
- [ ] Forecast evaluation and trading-metric methodology are specified before results are produced.
- [ ] Public-repository secret handling and raw-data exclusions are documented.
- [ ] The user/employer-facing scope and remaining unknowns are clearly communicated.
- [ ] No implementation or performance claim is made solely because this requirements document exists.

## 6. Open decisions — do not guess

| ID | Decision required | Why it matters | Current status |
|---|---|---|---|
| O1 | Chosen asset, ticker/cashtag, asset class and exchange/market | Defines collection query, price feed, trading calendar and report | Open — blocking |
| O2 | Price bar interval (for example hourly or daily) | Defines “period,” aggregation, feature windows and horizon | Open — blocking |
| O3 | Exact meaning of `n+0` and whether it is a nowcast/current observed bar or a future target | Prevents target leakage and impossible prediction claims | Open — blocking |
| O4 | Target convention: close price, return, or another explicitly defined value at each horizon | Determines labels, loss and metric interpretation | Open — blocking |
| O5 | Price data provider and adjustment policy (splits/dividends where relevant) | Reproducibility and comparable targets | Open — blocking |
| O6 | How the linked historical tweet dataset is accessed and whether full text can legally be used | Determines training feasibility and licensing | Open — blocking |
| O7 | Whether Tavily news is context-only or may become a model feature | The PDF's statements point in different directions | Default: context-only; confirmation needed |
| O8 | Whether RL is actually expected, versus a supervised forecasting model | RL needs action/reward and execution design not specified in the PDF | Default: supervised baseline; confirmation needed |
| O9 | Trading rule and assumptions for Sharpe/Sortino/drawdown | These metrics require strategy returns | Open before trading metrics |
| O10 | Secure method for delivering requested provider credentials and actor IDs | Avoids public exposure of secrets | Open before submission |
| O11 | Exact submission deadline and expected interpretation of 5–7 days | PDF uses both “within 1 week” and “5–7 days” | Confirm due date |
| O12 | Whether Exa is required in addition to Tavily | PDF's body mentions Tavily; submission line says “apify/tavily/exa” | Treat Exa as requested-for-reproducibility but optional for runtime until clarified |

## 7. Data and evaluation rules

1. Store all timestamps as timezone-aware values; preserve source timestamp and normalized UTC timestamp.
2. Preserve both `event_time` and `retrieved_at`; never backdate data to pretend it was available earlier.
3. Every feature row must be computable only from information available at that prediction cutoff.
4. Define whether the bar interval is closed before using its final price or aggregate sentiment. Never use incomplete-bar data as if it were final.
5. For prediction at cutoff (t), a post can enter a feature only if it was published and available to the system by (t). Late-arriving records must not leak backward into historical features.
6. Use chronological train/validation/test periods or walk-forward evaluation. Fit scalers, imputers, feature selection and model parameters only on each training fold.
7. Keep the final holdout untouched until model and strategy choices are frozen.
8. Compare against at least a price-only baseline and a simple naive forecast baseline where appropriate.
9. Deduplicate by stable source IDs and document handling of reposts/quotes/replies; do not assume all similar text is duplicate.
10. Log data counts and exclusions at each stage, with reasons; missing metadata must remain missing.
11. Pin source dataset versions/revisions when possible; record retrieval date, license/terms review, file hashes and schema profile.
12. Clearly label historical backtests as simulations, disclose limitations and transaction costs, and avoid causal claims without evidence.

## 8. Proposed end-to-end workflow

1. Confirm O1–O5 to define the forecasting problem.
2. Verify candidate historical dataset(s) and provider access/terms; select the smallest suitable reproducible sample for schema/prototype checks.
3. Define canonical schemas and timestamp/availability rules.
4. Ingest the 180-day X window and matching price window through bounded, logged provider adapters.
5. Validate raw records, deduplicate, normalize timestamps and create an audit trail.
6. Aggregate post-level sentiment/engagement into point-in-time bar-level features; generate price features.
7. Construct horizon-specific targets without using future information in features.
8. Establish naive and price-only baselines.
9. Run walk-forward evaluation and a final untouched holdout.
10. Only if a defensible trading rule is approved, convert out-of-sample predictions to strategy returns and calculate risk metrics.
11. Generate charts, the one-page contextual sentiment outlook and the evaluation report.
12. Re-run the pipeline from documented commands, verify outputs, and prepare the secure submission package.

## 9. Traceability matrix

| Requirement | Evidence expected | Planned component / report |
|---|---|---|
| R1 | Reproducible commands and run manifest | README, pipeline entry point, run manifest |
| R2 | Source IDs, query/window, retrieval logs, counts | Apify adapter and ingestion report |
| R3 | Price rows, provider/source, interval, adjustment policy | Price adapter and price schema |
| R4 | Timestamp/provenance assertions and tests | Canonical records, storage, tests |
| R5 | Field coverage and missingness report | X post schema and data-quality report |
| R6 | Alignment tests around bar boundaries/timezones | Aggregation/alignment module and tests |
| R7 | Feature schema, definitions and unit tests | Feature module and feature report |
| R8 | Horizon-specific target tests and predictions | Target builder/model output schema |
| R9 | Walk-forward folds, baseline comparisons, held-out predictions | Evaluation module and report |
| R10 | Reproducible sentiment/price charts | Reporting/visualization module |
| R11 | One-page asset outlook with data cutoff and uncertainty | Outlook report |
| R12 | Metrics, formulas and assumptions in report | Backtest/evaluation report |
| R13 | Provider/actor IDs, environment guide, secure secret procedure | README and submission checklist |
| R14 | CI plus deterministic unit/integration tests | Tests and GitHub Actions |

## 10. Phase 1 exit decision

**Current decision: NOT YET CLEARED for full modeling implementation.** The requirement inventory and default interpretations are documented, but O1–O6 are blocking decisions/data checks. Safe work can proceed on documentation, schema contracts, offline fixtures and tests that do not depend on an unconfirmed asset or target definition. Provider-backed ingestion and target/model implementation should wait until those blockers are resolved.

This is a requirements baseline, not a claim that the project is complete or that the employer has approved the interpretations above.
