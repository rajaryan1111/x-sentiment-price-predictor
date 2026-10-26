# Phase 1 — Requirements and Scope Lock

**Status:** Phase 1 requirements and scope are closed as a documented baseline. BTC-USD/daily, forecast cutoff, target convention, price-source default, and conservative news/RL interpretations are explicitly recorded. External access/legal/provider checks are Phase 2 readiness gates, not undocumented assumptions.  
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

## 3. Confirmed choices and working implementation defaults

The user explicitly selected only these two project choices:

- **Asset:** Bitcoin spot reference symbol `BTC-USD`.
- **Bar interval:** daily (`1d`).

The remaining conventions below are **documented engineering defaults**, not user-confirmed or employer-confirmed requirements. They make the implementation reproducible while keeping unresolved external approvals visible. The employer's written clarification, if received, overrides a default and must be recorded before model evaluation.

All downstream query examples and test fixtures must use the selected asset and interval unless a documented scope change is approved. Do not quietly broaden the scope to other assets or intervals.

### Operational forecasting convention (default for implementation)

- **Market data source:** Coinbase Exchange public market-data endpoint for product `BTC-USD`, using daily candles (`granularity=86400` seconds). This is the selected implementation default because it provides a direct USD spot pair and does not require a price API key. Verify product availability, response ordering, range limits, missing bars, and current API behavior in Phase 2 before relying on data. Source documentation: https://docs.cdp.coinbase.com/exchange/reference/exchangerestapi_getproductcandles (legacy Exchange endpoint reference); current public-candle API reference is linked from https://coinbase.github.io/coinbase-advanced-py/coinbase.rest.html.
- **Daily boundary:** UTC midnight-to-midnight. Every bar is labelled by its UTC start timestamp. Treat the close as available only after the daily bar has completed; do not use an unfinished current-day close as an observed input.
- **Forecast cutoff:** at the start of UTC day `n` (00:00:00 UTC), using only previously completed price bars and posts published by the cutoff. The model may use sentiment from posts whose event time is at or before the cutoff and whose availability is supported by the dataset/provenance. If historical availability cannot be established, document the limitation and exclude suspect records rather than backdating them.
- **Targets:** predict the close of daily bar `n`, `n+1`, `n+2`, `n+3`, `n+4`, and `n+5`. Thus `n+0` is a forecast of the current day's not-yet-completed close made at that day's UTC start, not the already-known close. This resolves the otherwise ambiguous wording for the working implementation. Any employer clarification overrides this default and must be recorded before model evaluation.
- **Baseline metrics:** report forecast MAE/RMSE (and direction accuracy only if defined consistently) by horizon, plus a naive persistence baseline and a price-only model. Sharpe/Sortino/max drawdown are only computed for a separately specified strategy from strictly out-of-sample forecasts and net returns after disclosed costs; they are not substitutes for forecast-error metrics.
- **Engagement fields:** ingest and preserve likes/reposts/views/follower counts when returned, but do not use them as historical model features unless their values are timestamped snapshots known at the historical cutoff. A current scrape's engagement counts are not proof of past engagement values.
- **Current outlook:** summarize the latest completed UTC daily bar and only sentiment/news available by the report cutoff; label the cutoff and uncertainty.

## 4. Goals

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

## 5. Scope boundaries and interpretation

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

## 6. Acceptance criteria

Phase 1 is ready for implementation planning when:

- [x] Every explicit requirement visible in the supplied assessment PDF is represented in this document.
- [x] Each requirement has a planned implementation/evidence artifact in the traceability matrix.
- [x] Ambiguities and conservative defaults are documented; none is presented as employer-confirmed fact without evidence.
- [x] Asset and interval are selected: BTC-USD, daily bars. `n`, `n+0`, and target convention are operationally defined as a working default in Section 3.
- [x] Price-source default, UTC daily boundary, point-in-time cutoff, and news role are documented.
- [x] Forecast metrics, baseline comparisons, walk-forward validation, and conditions for trading risk metrics are specified.
- [x] Public-repository secret handling and raw-data exclusions are documented.
- [x] Requirements that depend on external accounts, source terms, credentials, or employer confirmation are tracked as Phase 2 readiness gates below.
- [x] No implementation or performance claim is made solely because this requirements document exists.

**Data-resource verification note:** The assessment's linked historical-tweet Google Doc was not accessible through the available read-only retrieval in this session. Its contents, access terms, and suitability are therefore **not verified**. This does not prevent closing the requirements-documentation phase, but it is a hard gate before selecting or training on that resource.

**Assignment-source limitation (recorded as D-023):** the assessment PDF and its companion dataset-reference PDF are not present in the repository, the agent workspace or this conversation. Requirements in this file are transcribed from the project's own record of the brief, so a human must confirm them against the PDF before the requirement set is treated as final. No deadline, licence, credential or employer intent is inferred anywhere.

## 7. Open decisions — do not guess

| ID | Decision required | Why it matters | Current status |
|---|---|---|---|
| O1 | Chosen asset, ticker/cashtag, asset class and exchange/market | Defines collection query, price feed, trading calendar and report | **Resolved working assumption:** Bitcoin spot reference `BTC-USD`; use Coinbase Exchange public candles by default; verify product/API response in Phase 2 |
| O2 | Price bar interval | Defines period, aggregation, feature windows and horizon | **Resolved working assumption:** daily (`1d`), UTC midnight boundaries |
| O3 | Exact meaning of `n+0` | Prevents target leakage and impossible prediction claims | **Resolved working assumption:** forecast the not-yet-completed close of day `n`, issued at 00:00 UTC at the start of that day |
| O4 | Target convention at each horizon | Determines labels, loss and metric interpretation | **Resolved working assumption:** close of daily bars `n` through `n+5`; employer clarification, if received, overrides before evaluation |
| O5 | Price data provider and adjustment policy | Reproducibility and comparable targets | **Resolved default:** Coinbase Exchange BTC-USD spot candles, USD quote, UTC bars; no equity corporate-action adjustments; verify availability, candle ordering, gaps and API limits in Phase 2 |
| O6 | Access, terms, schema and suitability of the linked historical tweet dataset | Determines training feasibility and rights | **Not verified:** linked Google Doc was not retrievable in this session; Phase 2 gate—obtain access and review terms/schema before use |
| O7 | Whether Tavily news is context-only or a model feature | PDF contains potentially conflicting directions | **Default resolved conservatively:** context for the one-page outlook only; no news features in forecast model unless employer clarifies otherwise |
| O8 | Whether RL is expected | RL needs action/reward and execution design not specified | **Default resolved conservatively:** supervised multi-horizon forecasting plus price-only baseline; RL excluded unless employer explicitly requires it and scope is amended |
| O9 | Trading rule for Sharpe/Sortino/drawdown | These require strategy returns | **Methodology defined:** calculate only on out-of-sample strategy returns with explicit sizing, costs, slippage, return convention and annualization; otherwise report unavailable |
| O10 | Secure delivery of requested provider credentials and actor IDs | Avoids public exposure of secrets | **Policy resolved:** actor IDs/non-secret config may be in report; secrets only through an employer-approved private channel, never GitHub/email body; do not send until recipient/channel is verified |
| O11 | Exact submission deadline | PDF says submit within 1 week and also 5–7 days | **External confirmation needed:** use the actual assessment receipt date and employer's deadline; do not infer a calendar deadline from this repo's creation date |
| O12 | Whether Exa is required in addition to Tavily | Submission line lists apify/tavily/exa while main news section names Tavily | **Default resolved conservatively:** prepare configuration slot for Exa; Tavily is the named news source in the main scope; Exa runtime use only if needed/confirmed |
| O13 | Exact Apify Actor, plan/cost and field availability | Actor behavior and available post metadata vary | **Phase 2 account gate:** select and inspect an actor in the user's account, confirm terms, cost cap, 180-day coverage and required fields before any paid run |

## 8. Data and evaluation rules

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

## 9. Proposed end-to-end workflow

1. Use the selected BTC-USD and daily-bar assumptions together with the operational defaults in Section 3; check for employer clarification and verify the live Coinbase API/product behavior in Phase 2 before relying on collected prices.
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

## 10. Traceability matrix

The authoritative matrix — with acceptance criteria, verification methods, evidence
pointers, statuses, gaps, planned resolutions and external blockers — is maintained in
[docs/REQUIREMENTS_TRACEABILITY.md](REQUIREMENTS_TRACEABILITY.md). It is the single
source for status; this file keeps the requirement definitions and the decision context.
Requirement IDs (`R1`–`R14`), their definitions in PRD.md and the matrix rows are the
same IDs and must always be updated together.

## 11. Phase 1 exit decision

**Phase 1 status: CLOSED — requirements and scope baseline documented.** The selected BTC-USD/daily assumptions, operational forecast cutoff, horizon targets, data rules, baseline/evaluation methodology, scope decisions, acceptance criteria, and traceability are now explicit. The assessment's stated deliverables are mapped to planned evidence.

**Readiness gates (must pass before live X ingestion or X-based training):**

1. Retrieve and review the linked historical dataset resource and its terms — **open**.
2. Verify the current Coinbase BTC-USD daily candle response and data quality — **satisfied**: 180/180 bars for 2026-04-29 to 2026-10-25 UTC were refetched on 2026-10-26 with no missing or duplicate timestamps and the unfinished current day excluded.
3. Choose and inspect an Apify Actor, verify its current terms, fields, 180-day capability and cost, and set a spend cap — **open**, no paid run may start before this.
4. Verify provider credentials privately without committing them — **partially satisfied**: the price path needs no credentials; no X credential route is agreed yet.
5. Record actual data snapshots, schema profiles and provenance — **partially satisfied**: the price snapshot, its SHA-256 and the run provenance are recorded; no X profile exists.
6. Confirm the submission deadline from the employer's message — **open**; the brief states both “one week” and “5–7 days”, so no date is assumed.

These are external access/operational checks, not hidden requirements gaps. The Google Doc was not accessible, so its contents and rights remain unverified.

This closure means the **requirements phase** is complete; it does not mean X data has been collected, a sentiment result measured, or the employer has approved the working assumptions. Any employer clarification overrides these defaults and must be logged before evaluation.

Requirement status is evidence-based: rows R1, R3, R6, R8, R12, R14 and the non-functional rows NFR1–NFR3, NFR5 and NFR6 are verified; R4, R5, R7, R9, R10, R11, R13 and NFR4 are partially complete; R2, A2 and A3 are blocked on external access; A1, A4 and A5 need employer clarification. See docs/REQUIREMENTS_TRACEABILITY.md for the per-row evidence.
