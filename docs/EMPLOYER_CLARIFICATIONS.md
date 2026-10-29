# Employer clarifications and submission draft

**Status:** prepared on 2026-10-28 and updated after rechecking available online
source metadata on 2026-10-29, **not sent**. No question on this page has been answered
by the employer, and no submission email has been delivered. This file
consolidates the exact external decisions that engineering cannot resolve on its
own, a provider/credential authorization checklist, and a ready-to-send email
draft. It does **not** invent answers, employer intent, credentials, an accepted
dataset, a submission format, or a delivery confirmation.

**Source-access outcome (2026-10-29).** The assessment PDF and companion
`Historical Twitter_X Datasets_ Verified Download Links.pdf` are absent from this
checkout (root and `docs/` checked). Their prior full inspection is recorded in
D-023 with page counts and hashes, but could not be repeated here. The assessment-
linked Google Doc was fetched as text at
<https://docs.google.com/document/d/1w-Y86OjkiOjlIIth0VgTAohql9zcGi3uoDNYTaTsZuw/export?format=txt>
and its full exported text was read: it is a 12-entry dataset-link list, not a
post corpus. The earlier recorded export hash remains historical; no current hash
was computed in this turn. Provider dataset pages and metadata were additionally
checked; findings are summarized in §3A and the dataset registry documentation.
The address `gilad@crowdwisdomtrading.com`, deadline wording and format remain
based on the recorded PDF transcription and must be confirmed before sending.

**Related documents.** The same blockers appear with owner/requirement detail in
[EXTERNAL_BLOCKERS.md](EXTERNAL_BLOCKERS.md); the evaluator-facing status is in
[SUBMISSION_SUMMARY.md](SUBMISSION_SUMMARY.md); the delivery procedure for the
PR is in [PR14_PROMOTION.md](PR14_PROMOTION.md).

---

## 1. Already resolved in the repository — do not re-ask

These are documented engineering defaults or verified facts from the recorded
brief. Asking the employer to repeat them wastes time; they are listed so the
questions in §2 stay short.

- **Asset, interval, price source:** BTC-USD daily candles from the public
  Coinbase Exchange API; historical report artefacts record a 180/180-bar
  snapshot verified on 2026-10-26 (SHA-256 in
  [SUBMISSION_SUMMARY.md](SUBMISSION_SUMMARY.md)). The raw file is absent here, so
  this pass could only check the committed record, not independently re-run it.
- **Forecast cutoff:** 00:00 UTC; features use completed bars and posts available
  by the cutoff only; the unfinished UTC day is dropped.
- **Horizons:** six targets `n+0` through `n+5` are implemented. The *meaning* of
  `n+0` still needs confirmation (Q2).
- **ML vs RL:** the brief's "machine learning / reinforcement learning" is treated
  as permitting the supervised ML path that is implemented (D-006).
- **News role:** by conservative default Tavily news is outlook context only and
  never a model feature; this still needs confirmation (Q4).
- **Security:** tokens are never committed to Git or placed in reports; a private
  credential-transfer channel is required (D-012, NFR3). The brief is recorded as asking
  for tokens "by email", which conflicts with that rule and is raised in Q6; the original PDF is not present here to recheck the wording.

Sources: [PHASE_1_REQUIREMENTS.md](PHASE_1_REQUIREMENTS.md),
[DECISIONS.md](../DECISIONS.md), [PRD.md](../PRD.md).

## 2. Open questions for the employer

Copy/paste this block. Each row maps to a documented blocker and requirement ID;
none has an employer answer on record.

| # | Question | Why it matters | Blocker / requirement IDs |
| --- | --- | --- | --- |
| Q1 | What is the exact calendar submission deadline, including timezone? The brief is recorded as saying both "one week" and "5–7 days" with no date. | Sets the delivery date; without it the submission timeline cannot be confirmed. | B5 / A1, A7, O11 |
| Q2 | For the `n+0` target, should we forecast the current day's not-yet-completed close issued at that day's 00:00 UTC start (the current working default), or the next available close after the issue time? | Changing the convention changes labels, folds and recorded metrics; it must be fixed before the real-data evaluation. | B4 / R8, R9, O3, O4 |
| Q3 | Is a live Tavily news call mandatory for submission, or is the implemented mocked-verified, gated `fetch-news` plus offline `run --news-file` context acceptable? | Determines whether one authorized, bounded provider call is needed. | B6 / A4, A7, O12 |
| Q4 | May news ever be a predictive model feature, or must it remain context for the one-page outlook only? | The brief says both "complement X sentiment" and "use sentiment and price only". We defaulted to context-only; a change requires a new, documented evaluation. | B6 / A4, O7 |
| Q5 | Which X data source should be used? Please confirm the provider, licence/terms, specific Apify Actor ID or historical dataset, its input/output schema, text availability, timestamp semantics, and that it covers the most recent 180 days with ticker/cashtag/keyword searches. A 2025–2026 Bitcoin Kaggle candidate is listed in §3B but has not been accepted or row-profiled. | No accepted, licensed 180-day post-level X corpus exists; the real sentiment-vs-price result depends entirely on it. | B1 / R2, R4, R5, R9, R10, A3, O6, O13 |
| Q6 | How should provider tokens and Actor IDs be delivered? The brief asks for them "by email"; our security rule forbids sending secrets in email/chat/Git. Please name an approved private channel and recipient for each secret, and confirm that non-secret Actor IDs/query config may be documented in the repo. | Unblocks credential provisioning without exposing secrets. | B2 / A2, O10, NFR3 |
| Q7 | What is the hard spend ceiling (USD) and per-run item cap for any paid Apify/Tavily operation? If Exa is expected, please confirm that separately before integration. | Paid Actor launches cost money; no provider call is authorized without a cap. | B3 / R2, NFR4, O13 |
| Q8 | What is the accepted final submission format and packet? Please confirm whether a Markdown evaluation report is sufficient or a PDF is additionally required, whether a video/screenshots are expected, and the delivery channel. Also re-confirm the recipient address in Q9. | Determines the exact artifacts to produce before submitting. | B7 / A7, A1 |
| Q9 | Please confirm the submission email recipient is `gilad@crowdwisdomtrading.com` (recorded from the brief) and state who should receive it. | Avoids sending to an unverified address. | B5 / A7 |

## 3. Provider / credential authorization checklist

### 3A. Provider role and integration evidence (checked 2026-10-29)

| Provider | Assignment role | Repository integration evidence | Identifiers / live status | Assessment |
| --- | --- | --- | --- | --- |
| **Apify** | Named by the assessment's X-post scraping requirement and submission credential/Actor-ID request. | A real configurable adapter exists at `src/xsentiment/ingestion/apify_x.py`, settings/environment configuration and `.env.example` placeholders exist, and `tests/unit/test_apify_x.py` plus end-to-end fixture tests cover mocked payloads. Setup guidance is in `docs/APIFY_X_SETUP.md`. | No Actor ID or configured credential is available in the inspected environment. No authorized live run, accepted post corpus, or live integration test has occurred. | Required adapter path is engineering-ready but actual 180-day data collection is blocked on employer source/terms approval, Actor choice, credentials and an explicit cost ceiling. Never infer Actor identity from an adapter. |
| **Tavily** | The assessment names Tavily for recent relevant news to complement X sentiment; conservative project interpretation is context for outlook only, not a model feature. | A working bounded Tavily adapter, explicitly gated CLI (`fetch-news --confirm-live-call`), offline JSONL handoff and tests exist. Provider behavior is mocked, including bounds and sanitization. | No key was available in the inspected environment; no live call or integration test. | Engineering adapter complete offline; whether a live call is required and its spend limit need employer/user authorization. |
| **Exa** | Appears in the assessment's submission line requesting credentials; the detailed project scope names Tavily, not Exa. No other required Exa operation is evidenced by the recorded brief. | No Exa client/adapter, Exa-specific tests or usage documentation were found. There is only a SecretStr configuration placeholder and a configuration-presence check; that is not an integration. | No key was available in the inspected environment and no usage was found; no Exa identifier is required or available. | Do not add an unnecessary Exa integration. Ask whether Exa is actually required. If not used, report no Exa credential/identifier rather than claiming integration. |

Provider configuration was inspected without displaying values: `.env.example` contains placeholders only, and the prior 2026-10-29 environment inspection recorded `APIFY_TOKEN`,
`APIFY_API_TOKEN`, `APIFY_ACTOR_ID`, `TAVILY_API_KEY` and `EXA_API_KEY` absent
from the process environment and project `.env`. No live API calls were made in this audit.

### 3B. Candidate dataset checks (2026-10-29; page/metadata review only)

| Candidate | Current public source evidence | Match to this assignment | Decision |
| --- | --- | --- | --- |
| [Bitcoin Tweets Dataset (2025–2026), Kaggle](https://www.kaggle.com/datasets/pokeash/bitcoin-tweets-dataset-20252026) | Kaggle metadata endpoint is accessible. Uploader claims X Bitcoin-related posts from 2025 “to present,” CSV around 2.10 GB, `text`, `date`, `user_followers`, user profile fields, hashtags and source. License field says CC0. Dataset version 1 was last updated 2026-03-04. | Best topical candidate, but a published end date / exact recent-180-day row coverage is not proven; listed schema has no likes/reposts/views; CSV not downloaded, so timestamp quality, duplicates, actual coverage and row schema remain unknown. Uploader's CC0 label does not establish rights clearance for underlying X content/profile data. | Candidate only. Do not download or train until employer approves use and a bounded local inspection is authorized. |
| [Crypto & Stock Tweets, Hugging Face](https://huggingface.co/datasets/StephanAkkerman/crypto-stock-tweets) | Public, ungated repository and card; CC-BY-4.0 declared. Card lists 8,024,269 cleaned rows, including 4,820,915 Bitcoin tweets, merged from ten sources; dataset revision last modified 2023-12-22. | Published feature schema is `text` and `url`, with no structured timestamp, author or engagement fields, and no post-2023 coverage. Card says it follows the original sources' terms; those source rights/terms are not validated. | Does not meet recent 180-day window or required metadata; not accepted. |
| [Tweets about the Top Companies (2015–2020), Kaggle](https://www.kaggle.com/datasets/omermetinn/tweets-about-the-top-companies-from-2015-to-2020) | Kaggle metadata accessible; uploader claims >3M posts for Amazon, Apple, Google, Microsoft and Tesla, with author, date, text, comments, likes and retweets; CC0 declared; last updated 2020-11-26. | Historical equities, not BTC/X recent 180-day coverage. Row-level schema/quality not downloaded or verified. CC0 label alone is not rights clearance. | Not a match; do not use for this BTC task. |

**Conclusion:** none of the candidates has been downloaded, rights-cleared,
row-profiled or approved; none currently proves an acceptable recent 180-day
BTC-related X corpus with the requested coverage and available metadata. The
Kaggle 2025–2026 Bitcoin listing is the only plausible candidate to ask the
employer about, not an accepted dataset. Public page access and an uploader's
license label do not prove collection rights, acceptable use, or field/coverage
quality. Do not label the historical price-only run or synthetic demo as a
sentiment evaluation.

Availability of a credential never implies authorization to spend. The prior
2026-10-29 inspection recorded APIFY_TOKEN, APIFY_API_TOKEN, TAVILY_API_KEY and
EXA_API_KEY absent from the process environment and project-local `.env` files;
`.env.example` contains placeholders only. No private transfer route is defined,
and no paid call is authorized. This is the exact checklist to satisfy before any
live call.

| Provider | Purpose | Expected operation | May incur cost? | Required cap | Required approval |
| --- | --- | --- | --- | --- | --- |
| Apify (X corpus) | Obtain the accepted 180-day post-level X dataset | One bounded Actor run (ticker, cashtag, keyword queries), then profile and ingest | **Yes** — Actor runs are billed | Hard USD ceiling + per-run item cap (Q7) | Employer source approval (Q5) + user spend authorization + private token route (Q6) |
| Tavily (news) | Optional recent-news outlook context | One bounded, single-request `fetch-news --confirm-live-call` search | **Yes** — API usage is billed | Per-call USD cap (Q7) | Employer confirmation it is required (Q3) + user authorization + private key route (Q6) |
| Exa (news, optional; not integrated) | No operation in this repository; implement only if the employer requires it | None unless scope is approved and adapter is built | **Yes** if later used | Per-call USD cap (Q7) | Employer confirmation, explicit user authorization, private key route (Q6); do not imply current integration |
| Coinbase (prices) | Reproducible public daily price snapshot | Free public `fetch-prices` re-fetch of the recorded 180-bar window | No (public endpoint) | n/a (bounded request) | Network allowlist to `api.exchange.coinbase.com`; no credential |
| Private credential channel | Transfer any token safely | Password-manager share / encrypted attachment | No | n/a | Employer-named channel and recipient (Q6) |

Engineering rule: no live Tavily/Exa/Apify/Coinbase request is made until the
matching row is fully approved, the cap is recorded, and the user explicitly
authorizes the call. The verification report records that as of 2026-10-29, **no live provider call had been made**;
Apify and Tavily have mocked adapter coverage, while Exa has only a configuration
placeholder and no adapter-level tests.

## 4. Ready-to-send email draft (NOT SENT)

**To:** `gilad@crowdwisdomtrading.com` (re-verify against the original brief — Q9)
**Subject:** X Sentiment Price Predictor — internship assignment deliverables and clarification request

> Hello,
>
> Please find the X Sentiment Price Predictor assignment deliverables below.
>
> **Repository:** <https://github.com/rajaryan1111/x-sentiment-price-predictor>
> **Assessment PR:** <https://github.com/rajaryan1111/x-sentiment-price-predictor/pull/14>
> **Branch:** `feat/sentiment-features-and-forecasting` (PR #14; check GitHub for the live SHA)
> **Evaluation report:** [Markdown report](https://github.com/rajaryan1111/x-sentiment-price-predictor/blob/feat/sentiment-features-and-forecasting/reports/btc-usd-180d/evaluation-report.md) (per-horizon MAE/RMSE and methodology, plus Sharpe, Sortino and max drawdown where valid).
> **Documentation:** the submission summary, requirements audit, verification
> report, demo walkthrough and outlook/chart artifacts are also in the repository.
>
> **What is delivered.** A reproducible Python research pipeline for BTC-USD
> daily closes at horizons `n+0`..`n+5`: validated price ingestion, point-in-time
> X-post alignment, VADER sentiment and price features, naive / price-only /
> sentiment-plus-price ridge models on identical purged walk-forward folds, and an
> evaluation report with Sharpe ratio, Sortino ratio and maximum drawdown. It has
> a full offline test suite and CI, a gated Tavily news step, a database join, a
> sentiment-change chart and a one-page outlook. Installation and reproduction
 > commands are in the README and the demo walkthrough.
>
> **Verification evidence.** On the final commit, 187 tests pass, together with
> `ruff`, byte-compilation and both documentation/registry validators, locally and
> in GitHub Actions. The documented setup was repeated from a clean checkout on
> Python 3.11 and re-run on Python 3.12 with the same result. The committed
> real-price metrics were independently re-derived from the recorded snapshot with
> zero differences, so the report is reproducible rather than merely asserted.
>
> **Reproduction:** from the repository root, install with `python -m pip install -e '.[dev,storage]'`; run `pytest`, `ruff check src tests scripts`, `python scripts/validate_docs.py`, and `python scripts/validate_dataset_registry.py`. For a fully offline software demonstration, run `python scripts/make_offline_demo.py --out reports/generated/offline-demo-inputs/prices.json --posts-out reports/generated/offline-demo-inputs/posts.jsonl --generated-at 2026-10-27T00:00:00+00:00`, then follow the README's `python -m xsentiment run` command using those generated files and label outputs synthetic. The historical real-price report is also reproducible: re-running `python -m xsentiment run --prices data/btc-usd-daily-2026-04-29_2026-10-25.json --out <dir> --now 2026-10-26T00:00:00+00:00` reproduces its `metrics.json` with zero differences, provided that public snapshot is re-fetched with `fetch-prices` first (it is not committed).
>
> **Provider identifiers and credentials:** no Apify Actor was selected or run, so there is no Actor ID or Apify credential used to report. Tavily has a mocked-tested adapter but no live request/key was used. Exa is not integrated or used, and no Exa identifier exists. No secrets are included. No secure credential-transfer channel has been agreed; please specify an approved private method and recipient. I will not send tokens in plaintext email.
>
> **Verified results (honest).** On the committed historical real-price run (180
> public Coinbase daily bars, zero X posts), mean MAE was naive $1,828.36 vs
> price-only ridge $2,264.62; sentiment-plus-price is identical because there was
> no sentiment data, and the report flags it as not identifiable. **No claim is
> made that sentiment improves forecasts**, because no accepted, licensed 180-day
> X corpus was available. The current offline demo uses clearly labelled synthetic
> data and is a software demonstration only, not market evidence.
>
> **What is blocked and what I need from you.** To finish the real-data sentiment
> evaluation and the submission packet, I need your answers to the clarification
> questions below (full detail is in the repository's
> `docs/EMPLOYER_CLARIFICATIONS.md`):
>
> 1. Exact calendar submission deadline and timezone (Q1).
> 2. Confirmation of the `n+0` target convention (Q2).
> 3. Whether a live Tavily news call is required, and whether news may be a
>    model feature (Q3, Q4).
> 4. The approved X data source / Actor or historical dataset, its licence, and
>    confirmation of 180-day coverage (Q5).
> 5. The approved private channel for delivering any provider tokens/Actor IDs,
>    since I will not put secrets in email, chat or the repository (Q6).
> 6. A hard spend cap for any paid collection (Q7).
> 7. The accepted final submission format (Markdown vs PDF, video/screenshots),
>    delivery channel, and re-confirmation of this recipient address (Q8, Q9).
>
> Once the data source, credential route, spend cap and target convention are
> confirmed, I can run the sentiment-enhanced evaluation, record the actual
> metrics, and assemble the final packet in the required format.
>
> Thank you,
> [Your name]

This is a **draft only**. It has not been sent. Before sending, the user must:
(a) explicitly authorize sending; (b) use an authorized/connected email tool
(none exists in this session); (c) re-verify the recipient from the original PDF;
(d) add their name; and (e) never include tokens in the email body — use the
approved private channel from Q6 instead. Any token/Actor identifiers requested
by the brief must be delivered separately and securely, not committed to Git.

## 5. Submission-format artifacts to prepare if required (unconfirmed)

The original submission instructions are not in this checkout, so whether these
are required is **unconfirmed** (Q8). If confirmed, produce them from the real
application, never from mockups:

- **Markdown evaluation report:** already present at
  `reports/btc-usd-180d/evaluation-report.md`; a PDF can be produced from it.
- **Screenshots:** capture the generated `sentiment-vs-price.svg`/`outlook.md`
  and the CLI run output from a real offline run (see
  [DEMO_WALKTHROUGH.md](DEMO_WALKTHROUGH.md)); label them as synthetic.
- **Video (5–7 min):** record the timed script in
  [DEMO_WALKTHROUGH.md](DEMO_WALKTHROUGH.md), which uses verified commands only.
- **GitHub links:** repository URL and PR #14 URL above; the verified code was
  promoted to the existing PR #14 feature branch by non-forced fast-forward.
  At the last recorded inspection the PR was still OPEN and DRAFT, and was not
  merged. Check GitHub for the live head and CI before sending.
