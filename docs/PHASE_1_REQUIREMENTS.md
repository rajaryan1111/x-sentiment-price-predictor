# Phase 1 — Requirements and Scope Lock

**Status:** Phase 1 requirements and scope are closed as a documented baseline. The two supplied assessment PDFs were recorded as read in full on 2026-10-26; they are absent from this checkout and were not re-opened in the 2026-10-29 audit. BTC-USD/daily, forecast cutoff, target convention, price-source default, and conservative news/RL interpretations are transcribed in this document. External data/provider checks and the exact deadline remain open gates.

**Primary sources:** `CWT X sentiment Agent - intern task.pdf` and `Historical Twitter_X Datasets_ Verified Download Links.pdf`, recorded as supplied and inspected 2026-10-26. The originals are absent from this checkout, so that review could not be repeated on 2026-10-29. Page counts and SHA-256 hashes from the recorded review are in [docs/REQUIREMENTS_TRACEABILITY.md](REQUIREMENTS_TRACEABILITY.md).

**Repository:** `rajaryan1111/x-sentiment-price-predictor`

**Purpose:** Convert the assessment brief into traceable, testable requirements before implementing the data pipeline or models.

## 1. Source-of-truth rules

1. The supplied assessment PDF is the authority for the assignment requirements.
2. This document translates the PDF into engineering requirements; it does not claim that any unimplemented feature already works.
3. Where the PDF is ambiguous, the ambiguity is recorded as an open decision rather than silently guessed.
4. Dataset registry entries are candidate sources, not proof that the dataset is accessible, licensed for this use, suitable, or compatible.
5. A successful test or CI run proves only the checks that actually ran. It does not prove forecasting quality or profitability.
6. Keep decisions in this document current; record material changes with rationale and update the traceability table.

## 2. Assignment summary (verified against the assessment PDF)

The verified assessment asks for a Python-based machine learning / reinforcement learning pipeline that predicts an asset's price at `n+0`, `n+1`, `n+2`, `n+3`, `n+4` and `n+5` based on X (Twitter) sentiment and price only. It describes the system as scraping X posts, ingesting recent news, joining the datasets in a database, and training a predictive model using rigorous out-of-sample validation.

The Technical Requirements point to Apify for data scraping and to a Google Doc (`https://docs.google.com/document/d/1w-Y86OjkiOjlIIth0VgTAohql9zcGi3uoDNYTaTsZuw/edit?tab=t.0`) described as historical tweets to learn/teach the model. The full text was re-fetched on 2026-10-29; it is a 12-entry compilation of dataset download links matching the previously reviewed companion dataset PDF, not a tweet corpus.

The Project Scope is:

1. **X sentiment and price ingestion (Apify-based).** Scrape X posts about the chosen asset using **ticker, cashtag and keyword searches** for the **last 180 days**, plus historical price data for the same period. Extract post timestamps (**UTC/EST alignment**), post text, engagement (**likes, reposts, views**) and **author follower counts**, and align them with the price bars. Ingest the **most recent and relevant news** on the asset to complement the X sentiment (**use tavily.com**).
2. **Quantitative feature engineering and sentiment summary.** Create time-based features from sentiment and price only (for example sentiment score, post volume, lagged returns and time horizon). Produce a **1-page summary of the current sentiment outlook** for the asset.
3. **Machine learning model and walk-forward validation.** Build a predictive model that uses sentiment and price only to forecast the price at `n+0` through `n+5`, where `n` is the current period, with rigorous out-of-sample validation.
4. **Visual matrix output generator.** Charts that visualize the **X sentiment change against price as time changes**.

**Submission (page 2):** email `gilad@crowdwisdomtrading.com` including apify/tavily/exa, with (1) a GitHub/GitLab repository link, (2) the APIFY/tavily/exa tokens and actor IDs used for scraping so the pipeline can be reproduced, and (3) an evaluation report (PDF or Markdown) detailing model performance metrics (**Sharpe Ratio, Sortino Ratio, Max Drawdown**).

**Timeline:** the brief says "submit it within 1 week" on page 1 and "You will have 5 - 7 days" in the Timeline section; it gives no calendar date.

## 3. Confirmed choices and working implementation defaults

The user explicitly selected only these two project choices:

- **Asset:** Bitcoin spot reference symbol `BTC-USD`.
- **Bar interval:** daily (`1d`).

The remaining conventions below are **documented engineering defaults**, not user-confirmed or employer-confirmed requirements. They make the implementation reproducible while keeping unresolved external approvals visible. The employer's written clarification, if received, overrides a default and must be recorded before model evaluation.

All downstream query examples and test fixtures must use the selected asset and interval unless a documented scope change is approved. Do not quietly broaden the scope to other assets or intervals.

### Operational forecasting convention (default for implementation)

- **Market data source:** Coinbase Exchange public market-data endpoint for product `BTC-USD`, using daily candles (`granularity=86400` seconds). This is the selected implementation default because it provides a direct USD spot pair and does not require a price API key. The public price path was verified on 2026-10-26 with 180/180 daily bars; re-verify the live endpoint at submission time. Source documentation: https://docs.cdp.coinbase.com/exchange/reference/exchangerestapi_getproductcandles (legacy Exchange endpoint reference); current public-candle API reference is linked from https://coinbase.github.io/coinbase-advanced-py/coinbase.rest.html.
- **Daily boundary:** UTC midnight-to-midnight. Every bar is labelled by its UTC start timestamp. Treat the close as available only after the daily bar has completed; do not use an unfinished current-day close as an observed input.
- **Forecast cutoff:** at the start of UTC day `n` (00:00:00 UTC), using only previously completed price bars and posts published by the cutoff. The model may use sentiment from posts whose event time is at or before the cutoff and whose availability is supported by the dataset/provenance. If historical availability cannot be established, document the limitation and exclude suspect records rather than backdating them.
- **Targets:** predict the close of daily bar `n`, `n+1`, `n+2`, `n+3`, `n+4`, and `n+5`. Thus `n+0` is a forecast of the current day's not-yet-completed close made at that day's UTC start, not the already-known close. This resolves the otherwise ambiguous wording for the working implementation. Any employer clarification overrides this default and must be recorded before model evaluation.
- **Baseline metrics:** report forecast MAE/RMSE (and direction accuracy only if defined consistently) by horizon, plus a naive persistence baseline and a price-only model. Sharpe/Sortino/max drawdown are only computed for a separately specified strategy from strictly out-of-sample forecasts and net returns after disclosed costs; they are not substitutes for forecast-error metrics.
- **Engagement fields:** ingest and preserve likes/reposts/views/follower counts when returned, but do not use them as historical model features unless their values are timestamped snapshots known at the historical cutoff. A current scrape's engagement counts are not proof of past engagement values.
- **Database join:** the brief explicitly requires joining the datasets in a database. A versioned schema, idempotent repositories, a tested cutoff join and a persisted-input CLI path (`xsentiment persist`, `run --database-url`) now exist in `src/xsentiment/storage/` and `src/xsentiment/main.py` (R15, D-025, D-026), verified offline in `tests/unit/test_phase3_ingestion_e2e.py`; a database holding real X rows still depends on R2.
- **Current outlook:** summarize the latest completed UTC daily bar and only sentiment/news available by the report cutoff; label the cutoff and uncertainty.

## 4. Goals

### Required outcomes

- **R1 — Reproducible Python pipeline:** A documented, repeatable workflow from data acquisition/ingestion through alignment, features, modeling, evaluation and reporting.
- **R2 — X ingestion:** Collect asset-related posts for the most recent 180-day window using an approved Apify/provider route, covering ticker, cashtag and keyword searches.
- **R3 — Price ingestion:** Obtain price observations for the same chosen asset and period, with a documented provider, bar interval, timezone, currency and adjustment policy.
- **R4 — Time and provenance integrity:** Preserve source identifiers, timezone-aware event timestamps (supplied UTC/EST offsets), UTC-normalized event times, retrieval timestamps, source/provider details and data lineage. Never silently substitute retrieval time for event time.
- **R5 — Post metadata:** Preserve available post text, engagement values (likes, reposts, views) and author follower counts. Missing fields must remain missing/null and be reported; do not fabricate them. The verified brief names all four fields explicitly.
- **R6 — Alignment:** Define deterministic rules for mapping posts and sentiment aggregates to price bars, including bar boundaries, timezone conversion, duplicate handling and missing intervals.
- **R7 — Sentiment/price features:** Create documented, time-based features from sentiment and price, such as sentiment score, post volume, lagged returns and horizon-related features.
- **R8 — Forecast horizons:** Produce model outputs for `n+0`, `n+1`, `n+2`, `n+3`, `n+4`, and `n+5` after the period and target-price definition have been agreed and implemented.
- **R9 — Out-of-sample evaluation:** Evaluate chronologically on unseen future periods; avoid random time-series splits and leakage. Compare a sentiment-plus-price model with a price-only baseline.
- **R10 — Visual output:** Generate a visual matrix of charts showing X sentiment change alongside asset-price changes over time.
- **R11 — Outlook:** Generate a one-page summary of the current sentiment outlook for the chosen asset. Clearly distinguish observed data, model outputs, contextual news and uncertainty.
- **R12 — Evaluation report:** Produce a PDF or Markdown report documenting the evaluation and reporting Sharpe ratio, Sortino ratio and maximum drawdown only when valid strategy returns and explicit assumptions are available. The verified brief explicitly requires these three metrics in the evaluation report.
- **R13 — Reproducibility package:** Document repository setup, commands, provider/actor identifiers, ticker/cashtag/keyword query configuration, configuration, data snapshots or hashes, and steps needed to reproduce the run without exposing secrets publicly.
- **R14 — Quality gates:** Provide automated tests for schemas, timestamp rules, alignment, feature generation, target construction, leakage safeguards, metrics and report outputs.
- **R15 — Database join:** Persist normalized X posts and price bars in a database and join them by asset and cutoff, with idempotent writes and a reproducible query. The verified brief explicitly asks to "join the datasets in a database"; storage schema, idempotent repositories, a tested cutoff join and the persisted-input CLI path now exist and are verified offline (`tests/unit/test_phase3_ingestion_e2e.py`), so R15 is complete for the offline path with real X rows still blocked on R2.

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

The verified PDF says to ingest the most recent and relevant news using Tavily "to complement the X sentiment", but it also says feature engineering and the predictive model must use **sentiment and price only**. To honor the stricter explicit model-input requirement, news is in scope for contextual research and the one-page outlook, but **excluded from predictive features by default**. Tavily is the named news source; Exa appears only in the submission line and is optional unless actually used. This is a conservative interpretation, not a claim that the employer has confirmed it. Record a clarification request if news is intended to influence the forecast.

### ML versus reinforcement learning

The verified brief says "machine learning / reinforcement learning." The slash offers either option, and the required forecast outputs and performance metrics do not define an RL environment or reward. The baseline plan is supervised forecasting plus a price-only comparator, which satisfies the ML option. An RL trading policy is not in the initial scope unless the employer explicitly requires it and a well-defined action space, reward, execution assumptions and evaluation design are approved. This avoids adding unnecessary complexity or implying that RL is mandatory.

### Performance metrics

Sharpe, Sortino and maximum drawdown are trading-strategy metrics, not standalone measures of forecast error. Report them only from a defined strategy applied to strictly out-of-sample predictions, using disclosed position sizing, return convention, transaction costs, slippage, risk-free-rate/annualization assumptions and treatment of missing bars. Also report forecast metrics appropriate to the target (for example MAE/RMSE and directional metrics when defined). If a strategy cannot be defensibly specified, mark trading metrics as unavailable and explain why rather than fabricating them.

### Credentials and submission security

The assessment requests provider tokens and actor IDs for reproducibility. Actor IDs and non-secret configuration can be documented in the repository. **Never publish API tokens in a public repository or report.** Share any required secrets only through an employer-approved private channel, with minimum necessary scope; rotate any secret that has been exposed. Before sending credentials, confirm the recipient and secure transfer method.

### Historical datasets

The existing registry records 12 candidate sources from the supplied dataset list. The assessment-linked Google Doc full text was re-fetched on 2026-10-29; it is that same 12-entry dataset-link compilation, not a tweet corpus. Three public candidate listing/card metadata were partially checked and are documented in `docs/data-sources.md`; no data rows, rights, license or coverage have been verified. The registry does not mean all sources should be downloaded. Some entries are StockTwits (not X), some are tweet-ID-only and require rehydration, some have licensing/count/schema caveats, and some may be too large for the assessment window. Raw files mentioned in earlier repository notes are not present in this checkout. Select one primary training dataset only after checking relevance, access, rights, text availability, timestamp coverage, schema and feasible size. Keep source platform identity explicit; do not relabel StockTwits as X.

## 6. Acceptance criteria

Phase 1 is ready for implementation planning when:

- [x] Every explicit requirement visible in the supplied assessment PDF is represented in this document.
- [x] Each requirement has a planned implementation/evidence artifact in the traceability matrix.
- [x] Ambiguities and conservative defaults are documented; none is presented as employer-confirmed fact without evidence.
- [x] Asset and interval are selected: BTC-USD, daily bars. `n`, `n+0`, and target convention are operationally defined as a working default in Section 3.
- [x] Price-source default, UTC daily boundary, point-in-time cutoff, and news role are documented.
- [x] Forecast metrics, baseline comparisons, walk-forward validation, and conditions for trading risk metrics are specified.
- [x] Public-repository secret handling and raw-data exclusions are documented.
- [x] Requirements that depend on external accounts, source terms, credentials, or employer confirmation are tracked as canonical Phase 3 readiness gates below.
- [x] No implementation or performance claim is made solely because this requirements document exists.

**Data-resource verification note (updated 2026-10-29):** The assessment-linked Google Doc full text was re-fetched and still lists 12 dataset candidates; it is not itself a tweet corpus. Three candidate public listing/card metadata were partially checked; no candidate dataset has been downloaded, rights-cleared, row-profiled or approved for 180-day text coverage. Raw uploaded files mentioned in earlier repository notes are absent from this checkout. This remains a hard gate before training.

**Assignment-source verification (D-023, historical record):** both supplied PDFs were recorded as read in full on 2026-10-26 and reconciled with this document and [docs/REQUIREMENTS_TRACEABILITY.md](REQUIREMENTS_TRACEABILITY.md); hashes and page counts are recorded there. The PDFs are not committed and are absent from the current checkout, so this review could not be repeated on 2026-10-29. The recorded transcription remains historical evidence only; no deadline, licence, credential or employer intent is newly inferred.

## 7. Open decisions — do not guess

| ID | Decision required | Why it matters | Current status |
|---|---|---|---|
| O1 | Chosen asset, ticker/cashtag, asset class and exchange/market | Defines collection query, price feed, trading calendar and report | **Resolved working assumption:** Bitcoin spot reference `BTC-USD`; use Coinbase Exchange public candles by default. The public price path was verified on 2026-10-26; re-verify at submission time |
| O2 | Price bar interval | Defines period, aggregation, feature windows and horizon | **Resolved working assumption:** daily (`1d`), UTC midnight boundaries |
| O3 | Exact meaning of `n+0` | Prevents target leakage and impossible prediction claims | **Resolved working assumption:** forecast the not-yet-completed close of day `n`, issued at 00:00 UTC at the start of that day |
| O4 | Target convention at each horizon | Determines labels, loss and metric interpretation | **Resolved working assumption:** close of daily bars `n` through `n+5`; employer clarification, if received, overrides before evaluation |
| O5 | Price data provider and adjustment policy | Reproducibility and comparable targets | **Resolved default:** Coinbase Exchange BTC-USD spot candles, USD quote, UTC bars; no equity corporate-action adjustments. Verified 2026-10-26 with no gaps or duplicates; re-verify availability and limits at submission time |
| O6 | Access, terms, schema and suitability of the linked historical dataset resource | Determines training feasibility and rights | **Resource retrieved 2026-10-26:** the Google Doc is a 12-entry dataset-link compilation matching the companion PDF, not a tweet corpus. **Still open:** select a candidate, verify its terms/schema/text/180-day coverage, and profile it before use |
| O7 | Whether Tavily news is context-only or a model feature | PDF contains potentially conflicting directions | **Default resolved conservatively:** context for the one-page outlook only; no news features in forecast model unless employer clarifies otherwise |
| O8 | Whether RL is expected | RL needs action/reward and execution design not specified | **Default resolved conservatively:** the verified brief says "machine learning / reinforcement learning"; the slash permits either. Supervised multi-horizon forecasting satisfies the ML option; RL excluded unless the employer explicitly requires it and scope is amended |
| O9 | Trading rule for Sharpe/Sortino/drawdown | These require strategy returns | **Methodology defined:** calculate only on out-of-sample strategy returns with explicit sizing, costs, slippage, return convention and annualization; otherwise report unavailable |
| O10 | Secure delivery of requested provider credentials and actor IDs | Avoids public exposure of secrets | **Policy resolved:** actor IDs/non-secret config may be in report; secrets only through an employer-approved private channel, never GitHub/email body; do not send until recipient/channel is verified |
| O11 | Exact submission deadline | The verified PDF says "submit it within 1 week" on page 1 and "You will have 5 - 7 days" in the Timeline, with no calendar date | **External confirmation needed:** use the actual assessment receipt date and the employer's deadline; do not infer a calendar deadline from this repo's creation date |
| O12 | Whether Exa is required in addition to Tavily | Submission line lists apify/tavily/exa while the main news section names Tavily | **Default resolved conservatively:** the main news requirement names Tavily; Exa appears only in the submission line and token request. Prepare a configuration slot, use Exa only if actually needed or employer-required, and submit only credentials for providers actually used |
| O13 | Exact Apify Actor, plan/cost and field availability | Actor behavior and available post metadata vary | **Canonical Phase 3 account gate:** select and inspect an Actor in the user's account, confirm ticker/cashtag/keyword input support, terms, cost cap, 180-day coverage and required fields before any paid run |

## 8. Data and evaluation rules

1. Store all timestamps as timezone-aware values; preserve source timestamp and normalized UTC timestamp.
2. Preserve both `event_time` and `retrieved_at`; never backdate data to pretend it was available earlier.
3. Every feature row must be computable only from information available at that prediction cutoff.
4. Define whether the bar interval is closed before using its final price or aggregate sentiment. Never use incomplete-bar data as if it were final.
5. For prediction at cutoff (t), a post can enter a feature only if it was published and available to the system by (t). Late-arriving records must not leak backward into historical features.
6. Use chronological train/validation/test periods or walk-forward evaluation. Fit scalers, imputers, feature selection and model parameters only on each training fold.
7. Do not tune features, hyperparameters or strategy choices on test folds; walk-forward test blocks are evaluation-only.
8. Compare against at least a price-only baseline and a simple naive forecast baseline where appropriate.
9. Deduplicate by stable source IDs and document handling of reposts/quotes/replies; do not assume all similar text is duplicate.
10. Log data counts and exclusions at each stage, with reasons; missing metadata must remain missing.
11. Pin source dataset versions/revisions when possible; record retrieval date, license/terms review, file hashes and schema profile.
12. Clearly label historical backtests as simulations, disclose limitations and transaction costs, and avoid causal claims without evidence.

## 9. Proposed end-to-end workflow

1. Use the selected BTC-USD and daily-bar assumptions together with the operational defaults in Section 3; check for employer clarification and re-verify the live Coinbase API/product behavior at submission time before relying on collected prices.
2. Verify candidate historical dataset(s) and provider access/terms; select the smallest suitable reproducible sample for schema/prototype checks.
3. Define canonical schemas and timestamp/availability rules.
4. Ingest the 180-day X window and matching price window through bounded, logged provider adapters.
5. Validate raw records, deduplicate, normalize timestamps and create an audit trail.
6. Aggregate post-level sentiment/engagement into point-in-time bar-level features; generate price features.
7. Construct horizon-specific targets without using future information in features.
8. Establish naive and price-only baselines.
9. Run walk-forward evaluation; no separate final holdout is reserved, and test folds are never used for model selection.
10. Only if a defensible trading rule is approved, convert out-of-sample predictions to strategy returns and calculate risk metrics.
11. Generate charts, the one-page contextual sentiment outlook and the evaluation report.
12. Re-run the pipeline from documented commands, verify outputs, and prepare the secure submission package.

## 10. Traceability matrix

The authoritative matrix — with acceptance criteria, verification methods, evidence
pointers, statuses, gaps, planned resolutions and external blockers — is maintained in
[docs/REQUIREMENTS_TRACEABILITY.md](REQUIREMENTS_TRACEABILITY.md). It is the single
source for status; this file keeps the requirement definitions and the decision context.
Requirement IDs (`R1`–`R15`), their definitions in PRD.md and the matrix rows are the
same IDs and must always be updated together.

## 11. Phase 1 exit decision

**Phase 1 status: CLOSED — requirements and scope baseline documented and verified against the supplied PDFs on 2026-10-26.** The selected BTC-USD/daily assumptions, operational forecast cutoff, horizon targets, data rules, baseline/evaluation methodology, scope decisions, acceptance criteria, and traceability are now explicit. The assessment's stated deliverables are mapped to planned evidence.

**Readiness gates (must pass before live X ingestion or X-based training):**

1. Retrieve and review the linked historical dataset resource and its terms — **partially satisfied**: the Google Doc was retrieved and is a 12-entry dataset-link compilation matching the companion PDF; no candidate dataset has been downloaded, licensed or profiled.
2. Verify the current Coinbase BTC-USD daily candle response and data quality — **satisfied**: a 7-bar smoke test passed and 180/180 bars for 2026-04-29 to 2026-10-25 UTC were re-profiled on 2026-10-26 with no missing or duplicate timestamps, no out-of-range rows and the unfinished current day excluded.
3. Choose and inspect an Apify Actor, verify its current terms, fields, ticker/cashtag/keyword support, 180-day capability and cost, and set a spend cap — **open**, no paid run may start before this.
4. Verify provider credentials privately without committing them — **partially satisfied**: the price path needs no credentials; no X credential route is agreed yet.
5. Record actual data snapshots, schema profiles and provenance — **partially satisfied**: the price snapshot, its SHA-256 and the run provenance are recorded; no X profile exists.
6. Confirm the submission deadline from the employer's message — **open**; the verified brief states both "within 1 week" and "5 - 7 days", so no calendar date is assumed.
7. Persist and join the datasets in a database — **implemented and offline-verified**: schema, idempotent repositories, a leakage-safe cutoff join and a persisted-input CLI path (`xsentiment persist`, `run --database-url`) exist and are tested. Populating that path with accepted real X rows remains blocked on R2 (D-025, D-026).

These are external access/operational checks, not hidden requirements gaps. The Google Doc is now identified and transcribed, but its candidate datasets' contents and rights remain unverified.

This closure means the **requirements phase** is complete; it does not mean X data has been collected, a real-data sentiment result measured, the database populated with real X rows, or the employer has approved the working assumptions. Any employer clarification overrides these defaults and must be logged before evaluation.

Requirement status is evidence-based across 28 rows: **11 verified complete**, **14 partially complete**, **0 not implemented**, **2 blocked by external dependency** and **1 not verified pending clarification**. Verified: R1, R3, R6, R12, R15, NFR1, NFR2, NFR3, NFR5, NFR6 and A5. Partially complete: R4, R5, R7, R8, R9, R10, R11, R13, R14, NFR4, A3, A4, A6 and A7. R14's automated tests and static checks passed locally on code commit `d801661`; the current PR head at the live metadata check was `fa69d53f70535dec03dd7f48c1c0d212b565e336`, with two successful CI runs (`40787633232`, `40787639350`) on that exact pushed SHA. Current local uncommitted documentation/registry edits are not covered by those CI runs. R14 stays partial because coverage is synthetic-fixture based, with no live-provider or real-X verification. R2 and A2 are blocked on external access; A1 needs the employer's calendar deadline. These statuses align with the canonical matrix at [docs/REQUIREMENTS_TRACEABILITY.md](REQUIREMENTS_TRACEABILITY.md), which validates against all 28 rows.
