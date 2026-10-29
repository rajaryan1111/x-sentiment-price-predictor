# Decision Log
A code default is not employer confirmation. Material changes need rationale, impact analysis, updated tests and synchronized canonical documents.

## D-001 Asset
Status: selected working choice. BTC-USD Bitcoin spot reference. The verified brief says "an asset" and "the chosen asset" and does not mandate Bitcoin; BTC-USD is this project's choice. Do not expand assets without approval.

## D-002 Interval/timezone
Status: working default. Daily bars, UTC boundaries, timezone-aware timestamps normalized to UTC. The brief asks for UTC/EST alignment; source offsets are preserved where supplied and converted to UTC for calculations. EST is an input/display offset, not a second internal clock.

## D-003 Price source
Status: working default; verified again on 2026-10-26. Coinbase Exchange public BTC-USD daily candles. A read-only 7-bar smoke test passed and a 180-day profile returned 180/180 bars from 2026-04-29 through 2026-10-25 UTC with no missing or duplicate timestamps, no out-of-range rows and no incomplete current day. This does not prove future API behaviour or X coverage.

## D-004 Forecast cutoff and targets
Status: working default, not employer-confirmed. The verified brief requires n+0 through n+5 and says n is the current period, but does not define whether n+0 is a completed close. Issue at 00:00 UTC at the start of day n; predict closes of bars n through n+5. n+0 is the not-yet-completed close. Use completed prior bars as features and omit incomplete or gap-crossing labels. Employer clarification overrides before evaluation.

## D-005 News role
Status: conservative interpretation, based on the verified brief. The brief says to ingest "most recent and relevant news on the asset to complement the X sentiment (use tavily.com)" while also saying the predictive model uses "X sentiment and price only." News is therefore context for the current outlook, not a model feature. Tavily is the named news source. The implementation enforces two separate steps: `xsentiment fetch-news --confirm-live-call` may make one bounded provider request using `TAVILY_API_KEY` and writes normalized JSONL; `xsentiment run --news-file` consumes that file offline and records its hash and context-only policy. Tests prove that predictions and metrics are unchanged by news context. No live call has been made. Reopen only with employer clarification and synchronized feature-policy changes.

## D-006 ML versus RL
Status: documented interpretation, based on the verified brief. The brief says "a Python-based machine learning / reinforcement learning pipeline"; the slash offers either option and no explicit RL deliverable, action space, reward or execution model is defined. Supervised multi-horizon forecasting plus baselines satisfies the ML option. RL is not implemented and is not treated as required unless the employer explicitly reopens it.

## D-007 Risk metrics
Status: methodology decision. The verified brief requires Sharpe, Sortino and maximum drawdown in the evaluation report. They are computed only from a defined strategy on out-of-sample returns with positions, fees, slippage, return convention, annualization and missing-data policy. Otherwise state unavailable with a reason. They are never substitutes for forecast-error metrics.

## D-008 Historical dataset
Status: open/blocked. The assessment-linked Google Doc was re-fetched as full text on 2026-10-29 and remains a 12-entry dataset-link compilation, not a tweet corpus. Three public candidate listing/card metadata were partially checked (see `docs/data-sources.md`), but no candidate data were downloaded, rights-cleared, row-profiled or accepted. Raw uploaded files mentioned in earlier repository notes are absent from this checkout; no current local X corpus is available. No source is accepted until access, platform, terms, schema, text, event coverage, provenance and point-in-time limitations are reviewed.

## D-009 Apify Actor and cost
Status: open/blocked. The verified brief requires ticker, cashtag and keyword searches over the last 180 days. The adapter accepts a caller-supplied Actor input; that is not proof that a selected Actor supports all three query modes or the required fields. No Actor run until current schema, platform, query support, terms, plan price, limits, 180-day reach and cost cap are checked. Adapter is mocked, not live verified; token/Actor ID are not configured. No paid run without explicit spend approval.

## D-010 Engagement/followers
Status: rule. The brief asks for likes, reposts, views and author follower counts. Keep available counts nullable; exclude them from historical predictors without time-stamped snapshots proving historical values.

## D-011 Platform identity
Status: rule. StockTwits is not X. Do not merge platforms without explicit labels and a documented study design. The uploaded `Manuscript.pdf` is a StockTwits paper and is not evidence of X coverage.

## D-012 Secret handling
Status: rule. Never commit credentials. The brief asks for provider tokens and Actor IDs at submission; share secrets only through a verified employer-approved private channel, never in the repository or a public report.

## D-013 Exa
Status: optional by default. The main news requirement names Tavily. Exa appears only in the submission line ("including apify/tavily/exa") and in the request for tokens and Actor IDs used for scraping. Use Exa only if actually needed or employer-required, and submit credentials only for providers actually used.

## D-014 Deadline
Status: open. The verified brief says both "submit it within 1 week" (page 1) and "You will have 5 - 7 days" (Timeline). It gives no calendar date. Confirm the actual due date from employer communication; do not infer a date from repository timestamps.

## D-015 Canonical governance
Status: agreed. Nine root-level files govern scope, contracts, data policy, model/evaluation, testing, rules, roadmap and decisions. Update affected documents/tests before merging material changes.

## D-016 Sentiment scorer
Status: working default with documented limits. VADER (`vaderSentiment` 3.3.x, MIT) is the versioned, deterministic, offline scorer; blank text stays null and is never treated as neutral. It is English-oriented and not finance-specific, so it is a reproducible baseline rather than a claim of understanding. Replacing it means implementing another `SentimentScorer`; the scorer name and installed version are recorded in every run manifest.

## D-017 Trading strategy and risk-metric gating
Status: predeclared. Long only when the predicted n+1 close exceeds close(n-1) x (1 + 2 x fee); entry at close(n), exit at close(n+1); default fee 10 bps per side; no shorting, no leverage, no sizing. Annualisation 365 periods, risk-free 0, Sortino MAR 0, benchmark is the same windows held long. Sharpe, Sortino and drawdown are withheld with a reason below 30 out-of-sample days or when dispersion is zero, and are reported only as strategy statistics, never as forecast accuracy.

## D-018 Walk-forward purge and determinism
Status: rule. Expanding-window folds with a purge gap equal to the longest horizon (5 rows) so labels from the training block cannot resolve into the test block. Defaults are 60 training and 20 test rows per fold. No random splitting exists in the code; repeated runs must produce identical predictions.

## D-019 Numerical stack
Status: decision. The candidate models are a from-scratch ridge regression with a deterministic normal-equation solve, so the core pipeline needs no numerical third-party library and stays testable in the extras that CI installs (`.[dev,storage]`). `vaderSentiment` is the only added runtime dependency and it is pure Python.

## D-020 Model target
Status: decision. Models predict the horizon ratio close(cutoff + h) / close(cutoff - 1) and multiply by the reference close, so predictions are directly comparable with the naive persistence baseline (ratio 1.0) and cannot drift outside plausible ranges. Canonical metrics remain USD MAE/RMSE on the implied closes.

## D-021 Artefact set and chart renderer
Status: decision. Each run writes evaluation-report.md, outlook.md, sentiment-vs-price.svg, metrics.json, predictions.jsonl and manifest.json. Charts are rendered as dependency-free SVG; a plotting library is not required. Generated prediction dumps stay out of Git while the report, outlook, chart, manifest and metrics are small enough to review.

## D-022 Post text requirement
Status: rule. A normalized post requires non-empty text, while text remains stored only when returned and permitted. Records without recoverable text are rejected at the adapter boundary rather than admitted with empty text, so post-volume features count only posts that were actually observed with text. Making the contract nullable is deferred until a real ID-only source is accepted and the quarantine policy is specified.

## D-023 Assignment source availability
Historical review recorded complete on 2026-10-26; current primary-source access unavailable. Both assessment PDFs were recorded as read in full: `CWT X sentiment Agent - intern task.pdf` (2 pages) and `Historical Twitter_X Datasets_ Verified Download Links.pdf` (2 pages). Their SHA-256 hashes and page counts are in docs/REQUIREMENTS_TRACEABILITY.md. The PDFs are absent from this checkout and could not be reopened for the 2026-10-29 audit, so that transcription is historical evidence, not fresh primary-source verification. The linked Google Doc was re-fetched as full text on 2026-10-29 and is a dataset-link compilation, not the dataset itself. Remaining ambiguities are the n+0 convention (D-004), the news role (D-005), the ML/RL slash (D-006) and the exact deadline (D-014), each recorded rather than guessed.

## D-024 Identifier and phase-label scheme
Status: agreed. Requirement IDs are `R1`–`R15` (functional, defined in PRD.md and PHASE_1_REQUIREMENTS.md), `NFR1`–`NFR6` (non-functional), `A1`–`A7` (assessment-specific items such as the timeline, credentials, supplied resources and submission delivery), `O1`–`O13` (open decisions) and `D-001`–`D-029` (decisions). Each ID is unique within its namespace and means the same requirement in every document; a definition may be repeated in the PRD, the detailed trace and the matrix, but no two requirements share an ID. Phase numbering has three distinct schemes mapped in PHASES.md; canonical Phase 1 is the requirements and scope baseline, and the repository's "Phase 2 data quality/alignment" workstream is canonical Phase 3, not canonical Phase 2.

## D-025 Database join requirement
Status: implemented, verified offline. The verified brief says the system will "join the datasets in a database." The storage package has versioned `price_bars` and `x_posts` tables, idempotent upserts keyed by product/timestamp and post ID, and two tested joins: a descriptive same-UTC-day SQL join (not usable as a historical feature) and a leakage-safe cutoff join that uses only posts published and first observed by the cutoff plus the last completed prior close. The end-to-end pipeline now consumes the persisted path: `xsentiment persist` upserts snapshot inputs and `xsentiment run --database-url` reads the same rows from storage, recording `input_source = persisted_storage` in the manifest. `tests/unit/test_phase3_ingestion_e2e.py` drives a mocked adapter through persistence and the cutoff join and runs the persisted-input CLI, so R15 is Verified complete for this offline path; a database holding real X rows still depends on R2. Raw post text and private data remain out of Git; the database is a local ignored artefact.

## D-026 Persistence keys and join semantics
Status: implemented. Price bars are keyed by `(product_id, timestamp)` with a second uniqueness rule on `(product_id, bar_date)` so one UTC day cannot have two bars. Posts are keyed by stable source `post_id`; a later snapshot may update counts/sentiment but the earliest `retrieved_at` is retained so availability cannot be backdated. The descriptive daily join aggregates posts by `created_date` and joins the same UTC day's bar; it is reporting-only because the same-day close is not known at that day's 00:00 cutoff. The cutoff join aggregates posts in `(cutoff - 24h, cutoff]` with `retrieved_at <= cutoff` and joins the last completed bar strictly before the cutoff. No current engagement value is used as a predictor. Raw text stays in the local database, never in Git.

## D-027 Gated news CLI, lineage metadata and offline demo
Status: implemented and verified offline (2026-10-27). News ingestion is a separate
opt-in step: `xsentiment fetch-news --confirm-live-call` reads `TAVILY_API_KEY` from
environment configuration, makes one bounded, non-retried provider request and
writes normalized JSONL context; `xsentiment run --news-file` consumes that file
without any network access. Tests prove the live-call gate, bounds, redaction and
that predictions/metrics are unchanged by news context. Manifests now carry
`input_lineage` (source, window, retrieval, schema, query-mode/hash and synthetic
flags) and `fetch-prices` records a UTC `fetched_at`. `scripts/make_offline_demo.py`
generates deterministic, explicitly labelled synthetic inputs so the full CLI can
be demonstrated without credentials; its outputs are ignored by Git and its
metrics must never be reported as real-data results. No live provider call was made.

## D-028 Streaming news ceiling and offline network isolation
Status: implemented and verified offline (2026-10-28). The Tavily adapter now
enforces `HTTP_MAX_RESPONSE_BYTES` while reading the response stream instead of
buffering the whole body first, while preserving the single-request/no-retry
policy. A streaming regression test proves that an oversized response stops chunk
consumption early. The offline demo now has a regression that blocks socket and
HTTP client entry points during a real `run` CLI execution, so accidental network
use cannot silently turn the reproducible demo into a live-data run. These changes
harden robustness only; they do not alter forecasting methodology, feature policy
or the context-only role of news. No live provider call was made.

## D-029 Consolidated employer clarifications and unsent submission draft
Status: prepared (2026-10-28), no answer received. `docs/EMPLOYER_CLARIFICATIONS.md`
consolidates the unresolved employer questions (deadline, `n+0`, live news,
news-as-feature, X source/Actor, private credential route, spend cap, submission
format, recipient), the provider/credential authorization checklist, the exact
artifacts to capture if video/screenshots are required, and a ready-to-send email
draft addressed to the recipient recorded in `docs/PHASE_1_REQUIREMENTS.md`. The
brief's instruction to email provider tokens conflicts with the project's
never-commit/never-email-secrets rule (NFR3, D-012); the draft therefore requests
a private channel and contains no secrets. No email was sent, no sending tool is
connected to this session, and no employer answer, deadline, credential, dataset
or submission confirmation is invented. The draft is inert until the user
explicitly authorizes sending and re-verifies the recipient against the original
PDF, which is not in this checkout.

## D-030 Tavily URL sanitization and publication timestamp handling
Status: implemented and offline-tested (2026-10-28). Provider result URLs are parsed structurally before persistence: user-info and fragments are removed; credential-like query keys (case/encoding-insensitive, including common token, API key, signature, auth, session and cloud-signature names) have values replaced while useful non-secret article and attribution parameters are preserved; unsafe schemes and malformed URLs are excluded without echoing the raw URL. UTC-aware publication timestamps are normalized to UTC. Naive timestamps are withheld, with a reason and bounded raw source string retained; malformed/missing timestamps also have explicit reasons. This avoids host-timezone-dependent inference. Regression coverage includes encoded/case-varied auth keys, query and URL component redaction, output artifact checks, timezone offsets, naive/invalid/missing timestamps and a non-UTC host TZ. Provider payload hashes still identify the source payload but are one-way digests; raw URL strings are never written into news records or logs. This hardening does not establish live Tavily compatibility; no provider call was made.
