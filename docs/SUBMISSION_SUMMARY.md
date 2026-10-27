# Internship submission summary

**Project:** X Sentiment Price Predictor
**Repository:** <https://github.com/rajaryan1111/x-sentiment-price-predictor>
**Assessment PR:** <https://github.com/rajaryan1111/x-sentiment-price-predictor/pull/14>
**Verified working branch:** `arena/cf79e7b7-x-sentiment-price-predictor`
**Status on 2026-10-28:** ready with documented external limitations. No PR was merged.

## 1. Assignment objective

Build a reproducible Python research pipeline that tests whether timestamped
X/Twitter sentiment adds out-of-sample predictive value beyond price-only
baselines for BTC-USD daily closes at horizons `n+0` through `n+5`. The brief also
asks for a 180-day X window using ticker, cashtag and keyword searches, recent
news context, a database join, chronological evaluation, a visual sentiment-change
matrix, a one-page outlook and an evaluation report containing Sharpe, Sortino and
maximum drawdown. The original PDFs are not present in this checkout; exact
requirement wording is taken from the repository's recorded transcription and is
audited item by item in [FINAL_REQUIREMENTS_AUDIT.md](FINAL_REQUIREMENTS_AUDIT.md).

## 2. Implemented functionality

- **Ingestion:** validated public Coinbase Exchange BTC-USD daily candles with UTC
  bounds, Decimal OHLCV validation, duplicate/gap rejection and a UTC `fetched_at`
  in new snapshots. A configurable Apify X adapter and a local dataset profiler
  exist but have never been run against an approved live source.
- **Point-in-time integrity:** normalized post records preserve event time,
  first-observed time, raw provider timestamp, UTC offset, source identity and a
  payload hash. Naive timestamps and backdated retrieval are rejected. Posts are
  eligible only in the `(cutoff - 24h, cutoff]` window; late and future posts are
  excluded; the unfinished UTC day is dropped.
- **Sentiment and features:** deterministic VADER scoring, trailing-24h sentiment
  aggregates, predeclared lagged/rolling price features and six horizon close
  labels. Missing sentiment stays null and is never treated as neutral. Targets
  never enter the feature matrix.
- **Models and evaluation:** naive persistence, price-only ridge and
  sentiment-plus-price ridge, one model per horizon, on identical purged expanding
  walk-forward folds. Per-horizon MAE/RMSE/sample counts, mean-MAE comparison and
  a predeclared long/flat strategy produce Sharpe, Sortino and max drawdown with
  disclosed fees, annualisation and minimum-sample safeguards.
- **Storage:** versioned `price_bars`/`x_posts` tables, idempotent upserts,
  descriptive and leakage-safe cutoff joins, plus `xsentiment persist` and
  `xsentiment run --database-url`. Verified offline; real X rows are unavailable.
- **News:** `xsentiment fetch-news --confirm-live-call` is the only live-capable
  command. It reads `TAVILY_API_KEY` from the environment, makes one bounded,
  non-retried request and writes normalized JSONL. `run --news-file` consumes it
  offline; news appears in the outlook only and leaves predictions/metrics
  unchanged. All verification used mocked HTTP; no live call was made.
- **Reporting:** dependency-free SVG chart with price, sentiment-level and
  day-over-day sentiment-change panels; one-page outlook with an explicit page
  contract; Markdown evaluation report; JSON metrics, JSONL predictions and a
  manifest with code revision, input hashes, library versions and `input_lineage`.
- **Reproducibility:** `scripts/make_offline_demo.py` writes deterministic,
  explicitly synthetic price/post snapshots. `tests/integration/test_offline_demo.py`
  drives the real CLI and validates all artefacts and deterministic repeatability.

## 3. Architecture summary

```text
environment configuration
        ↓
bounded adapters (Coinbase prices, optional Apify X, gated Tavily news)
        ↓
normalized records + provenance + hashes
        ↓
optional persisted storage  ←→  file snapshots
        ↓
UTC point-in-time alignment and deduplication
        ↓
VADER sentiment + price features + n+0..n+5 targets
        ↓
naive / price-only / sentiment-plus-price models
        ↓
purged walk-forward evaluation → strategy simulation → risk metrics
        ↓
SVG chart + one-page outlook + evaluation report + manifest/metrics/predictions
```

The core pipeline uses Python 3.11, `httpx`, `pydantic`, `pydantic-settings` and
`vaderSentiment`; storage uses optional SQLAlchemy/aiosqlite; tests use `pytest`
and `ruff`; charts are dependency-free SVG. See
[ARCHITECTURE.md](../ARCHITECTURE.md) and [README.md](../README.md).

## 4. Dataset sources and provenance

| Source | Status in this submission | Use |
| --- | --- | --- |
| Coinbase Exchange public BTC-USD daily candles | Historical real-data run recorded on 2026-10-26; 180/180 bars, SHA-256 `09ce225a405aea390ae2f21c72634da1211a321aed1b39b52febfadf64083f75`. The raw snapshot is not committed and was not refetched here. | Price features, targets, historical evaluation |
| X/Twitter 180-day corpus | **Not accepted.** No approved Actor, licence, credential, spend cap or post-level text dataset exists. | Required for a genuine sentiment result; currently unavailable |
| Tavily/Exa live news | **Not called.** Adapter and CLI are mocked-verified only. | Optional outlook context |
| Assessment dataset-link Google Doc | Retrieved previously; 12-entry link compilation, not a tweet corpus. Registry is structurally validated, not independently re-verified. | Candidate inventory only |
| Synthetic offline demo | Deterministic generator; labelled `synthetic` in files, records, manifest, report and outlook. | Software demonstration only; never reported as market evidence |

## 5. Model methodology

At each 00:00 UTC cutoff, features use only completed prior daily closes and
posts published and first observed by the cutoff. Six separate horizon targets
predict closes of bars `n` through `n+5`; incomplete or gap-crossing horizons are
omitted. Models predict a close ratio relative to the last completed close and are
converted back to USD prices. Expanding walk-forward folds use a purge gap equal
to the longest horizon; imputation and standardisation are fitted on training
folds only. MAE/RMSE are reported by horizon and model. A predeclared long/flat
strategy derives out-of-sample net returns after 10 bps per-side fees, from which
Sharpe, Sortino and maximum drawdown are computed only when the sample and
dispersion safeguards are met. News is never a model feature.

## 6. Verified evaluation results

### Historical real-price run (committed artefacts, 2026-10-26)

Source: `reports/btc-usd-180d/`. These are historical results from the committed
manifest, metrics and report; the current sandbox could not refetch the public
price snapshot because its network allowlist excludes Coinbase. They were
cross-checked for internal consistency, not recomputed from raw rows.

- 180 public Coinbase BTC-USD daily bars, 2026-04-29 to 2026-10-25 UTC; 0 X posts.
- Five expanding folds, 60→140 training rows, 20 test rows, 5-row purge;
  100 out-of-sample days per model and horizon; 1,800 stored predictions.
- Mean MAE across horizons: naive **$1,828.36**, price-only ridge **$2,264.62**
  (23.86% worse). Sentiment-plus-price is identical to price-only because no
  sentiment data was available, and the report flags it as not identifiable.
- Price-only strategy: **+10.91%** cumulative net return, Sharpe **1.807**,
  Sortino **3.979**, max drawdown **4.08%** over 32 long days, versus a
  +6.11% / 0.752 / 1.377 / 10.33% unconditional-long benchmark. Naive never
  trades, so its ratios are explicitly unavailable.

**Key finding:** on this sample the fitted price-only model does **not** beat naive
persistence on forecast error. No claim is made that sentiment improves forecasting;
that question remains untestable without accepted X data.

### Current offline verification (2026-10-28)

A real CLI run on 210 synthetic bars and 209 synthetic posts produced six
non-empty artefacts, six walk-forward folds, 2,160 out-of-sample predictions and
18 per-horizon metric rows. Repeat execution produced byte-identical predictions
and metrics. The current offline suite has 167 passing tests; new regressions prove
that an oversized news response is rejected while streaming and that an offline
run makes no network connection. These results demonstrate pipeline operation only;
they are not market or sentiment evidence. Full verification evidence is in
[FINAL_VERIFICATION_REPORT.md](FINAL_VERIFICATION_REPORT.md).

## 7. Key limitations

- No accepted, licensed 180-day X corpus and no live Apify Actor run. Therefore
  R2 is externally blocked and the sentiment-versus-price comparison is unmeasured.
- No APIFY/Tavily/Exa credential, Actor ID, private transfer channel or paid-spend
  authorization. No live provider call was made.
- The employer has not confirmed the `n+0` target convention, exact calendar
  deadline, whether live Tavily news is mandatory or the final submission format.
- The assignment PDFs and the raw historical price snapshot are not in this
  checkout; recorded hashes and committed artefacts are used instead.
- No submission email was sent and PR #14 was not merged. This Arena session may
  push only to the working branch, so PR #14's head still needs the authorized
  fast-forward procedure in [PR14_PROMOTION.md](PR14_PROMOTION.md).

## 8. Reproduction instructions

```bash
git clone https://github.com/rajaryan1111/x-sentiment-price-predictor.git
cd x-sentiment-price-predictor
git checkout arena/cf79e7b7-x-sentiment-price-predictor
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev,storage]'

pytest
ruff check src tests scripts
python scripts/validate_docs.py
python scripts/validate_dataset_registry.py

python scripts/make_offline_demo.py \
  --out reports/generated/offline-demo-inputs/prices.json \
  --posts-out reports/generated/offline-demo-inputs/posts.jsonl \
  --generated-at 2026-10-27T00:00:00+00:00
python -m xsentiment run \
  --prices reports/generated/offline-demo-inputs/prices.json \
  --posts reports/generated/offline-demo-inputs/posts.jsonl \
  --out reports/generated/offline-demo \
  --now 2026-07-30T00:00:00+00:00 \
  --input-note "synthetic offline demo from scripts/make_offline_demo.py"
```

For the real public-price path, `python -m xsentiment fetch-prices --start ... --end ...`
requires outbound access to Coinbase; it is not part of the offline demo. For news,
set `TAVILY_API_KEY` locally and use `--confirm-live-call` only after explicit
authorization, then pass the JSONL to `run --news-file`. Never commit credentials.

## 9. GitHub delivery and references

- Repository: <https://github.com/rajaryan1111/x-sentiment-price-predictor>
- Existing draft PR #14: <https://github.com/rajaryan1111/x-sentiment-price-predictor/pull/14>
  (base `docs/canonical-source-of-truth`, head `feat/sentiment-features-and-forecasting`
  at checkpoint `5af5bc7a50c4b56edc1efe3aae4fce2501bdc656`).
- Verified working branch: `arena/cf79e7b7-x-sentiment-price-predictor`.
  This session's environment permits pushing only to that branch, so PR #14's
  head was deliberately not modified. Verified code checkpoints:
  `2620dc34d76a38a14b7815e76d207fb32edc1a33` (gated news CLI),
  `20a0e9641a4ed8705d65bf5c93d3ce50c56cbcaf` (offline demo and lineage),
  `8bc4f7ffc45ece3402060578fe14aa5c4a89bef7` (submission documentation) and the
  final engineering checkpoint
  `15478906bbc2cb6c5806f366141b5cd35cac0523` (streaming news ceiling and final
  delivery evidence). A later documentation-only checkpoint adds
  [EMPLOYER_CLARIFICATIONS.md](EMPLOYER_CLARIFICATIONS.md); it changes no code.
- GitHub Actions runs `40534245216`, `40536670278` and `40540034819` passed all
  four checks on the earlier commits; run `40566013522` completed `success` on the
  final engineering SHA `15478906bbc2cb6c5806f366141b5cd35cac0523`; and run
  `40569320293` passed on the `a19ee2f` documentation checkpoint (with further
  documentation commits reported in the execution response). These are
  Arena-branch checks; PR #14's head still needs its own fresh CI after the
  authorized fast-forward. The exact promotion commands are in
  [PR14_PROMOTION.md](PR14_PROMOTION.md).

## 10. Submission documents

- [FINAL_REQUIREMENTS_AUDIT.md](FINAL_REQUIREMENTS_AUDIT.md) — all 28 requirement IDs.
- [FINAL_VERIFICATION_REPORT.md](FINAL_VERIFICATION_REPORT.md) — commands, outputs and artefacts.
- [DEMO_WALKTHROUGH.md](DEMO_WALKTHROUGH.md) — timed 5–7 minute evaluator demonstration.
- [EXTERNAL_BLOCKERS.md](EXTERNAL_BLOCKERS.md) — exact unresolved questions.
- [EMPLOYER_CLARIFICATIONS.md](EMPLOYER_CLARIFICATIONS.md) — consolidated question set, provider/credential authorization checklist and an unsent ready-to-send email draft.
- [EXECUTION_CHECKPOINT.md](EXECUTION_CHECKPOINT.md) — recovery state and next commands.
- [PR14_PROMOTION.md](PR14_PROMOTION.md) — safe fast-forward delivery procedure for PR #14.

## 11. Final submission checklist

Engineering-owned items are done and CI-verified; the remaining items require
employer/user action and must not be marked done until confirmed.

- [x] Reproducible pipeline, gated news CLI, offline demo, database join, chart,
  outlook and evaluation report implemented and tested.
- [x] `README.md`, architecture, data policy, tech stack and reproduction
  commands present; `TEST_PLAN.md` is the authoritative test count.
- [x] Full offline verification suite, both documentation validators and Ruff
  green; offline demo reproducible byte-for-byte; network-isolation regression
  present.
- [x] Requirements audit (28 IDs), traceability matrix, external blockers and
  employer clarifications updated with honest statuses.
- [x] GitHub repository link, draft PR #14 link and Markdown evaluation report
  (Sharpe, Sortino, max drawdown) available.
- [x] Timed 5–7 minute demo script and submission-package documents present.
- [ ] PR #14 head advanced to the final Arena SHA from an authorized normal
  clone, with fresh PR-specific CI green (B8;
  [PR14_PROMOTION.md](PR14_PROMOTION.md)).
- [ ] Accepted licensed 180-day X corpus / Actor / spend cap provided (B1/B3),
  and sentiment-enhanced evaluation run with real metrics (R2, R9).
- [ ] Provider tokens / Actor IDs delivered through an approved private channel
  (B2/Q6) — never in email, chat or Git.
- [ ] Employer clarifications answered: deadline (Q1), `n+0` (Q2), live news
  (Q3), news feature policy (Q4), X source (Q5), spend cap (Q7), submission
  format and recipient (Q8/Q9).
- [ ] A live Tavily/news call is performed **only** if the employer confirms it
  is required and authorizes one bounded, capped request.
- [ ] Final packet produced in the confirmed format (Markdown/PDF, any required
  video or screenshots) and sent through the agreed channel with a recorded
  date, only after explicit user authorization.
