# Employer clarifications and submission draft

**Status:** prepared on 2026-10-28, **not sent**. No question on this page has been
answered by the employer, and no submission email has been delivered. This file
consolidates the exact external decisions that engineering cannot resolve on its
own, a provider/credential authorization checklist, and a ready-to-send email
draft. It does **not** invent answers, employer intent, credentials, an accepted
dataset, a submission format, or a delivery confirmation.

**Recipient provenance.** The address `gilad@crowdwisdomtrading.com` comes from
the recorded transcription of the assessment PDFs on page 2 ("Submission") in
[PHASE_1_REQUIREMENTS.md](PHASE_1_REQUIREMENTS.md), cross-checked against
[REQUIREMENTS_TRACEABILITY.md](REQUIREMENTS_TRACEABILITY.md) (A7). Per D-023 the
two PDFs were read in full on 2026-10-26, but the originals are **not** in this
checkout, so the address, deadline wording and submission format must be
re-verified against the primary brief before anything is sent.

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
  Coinbase Exchange API; a 180/180-bar historical snapshot was verified on
  2026-10-26 (recorded SHA-256 in
  [SUBMISSION_SUMMARY.md](SUBMISSION_SUMMARY.md)).
- **Forecast cutoff:** 00:00 UTC; features use completed bars and posts available
  by the cutoff only; the unfinished UTC day is dropped.
- **Horizons:** six targets `n+0` through `n+5` are implemented. The *meaning* of
  `n+0` still needs confirmation (Q2).
- **ML vs RL:** the brief's "machine learning / reinforcement learning" is treated
  as permitting the supervised ML path that is implemented (D-006).
- **News role:** by conservative default Tavily news is outlook context only and
  never a model feature; this still needs confirmation (Q4).
- **Security:** tokens are never committed to Git or placed in reports; a private
  credential-transfer channel is required (D-012, NFR3). The brief literally asks
  for tokens "by email", which conflicts with that rule and is raised in Q6.

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
| Q5 | Which X data source should be used? Please confirm the provider, licence/terms, specific Apify Actor ID or historical dataset, its input/output schema, text availability, timestamp semantics, and that it covers the most recent 180 days with ticker/cashtag/keyword searches. | No accepted, licensed 180-day post-level X corpus exists; the real sentiment-vs-price result depends entirely on it. | B1 / R2, R4, R5, R9, R10, A3, O6, O13 |
| Q6 | How should provider tokens and Actor IDs be delivered? The brief asks for them "by email"; our security rule forbids sending secrets in email/chat/Git. Please name an approved private channel and recipient for each secret, and confirm that non-secret Actor IDs/query config may be documented in the repo. | Unblocks credential provisioning without exposing secrets. | B2 / A2, O10, NFR3 |
| Q7 | What is the hard spend ceiling (USD) and per-run item cap for any paid Apify/Tavily/Exa operation? | Paid Actor launches cost money; the code refuses unauthorized paid calls (NFR4). | B3 / R2, NFR4, O13 |
| Q8 | What is the accepted final submission format and packet? Please confirm whether a Markdown evaluation report is sufficient or a PDF is additionally required, whether a video/screenshots are expected, and the delivery channel. Also re-confirm the recipient address in Q9. | Determines the exact artifacts to produce before submitting. | B7 / A7, A1 |
| Q9 | Please confirm the submission email recipient is `gilad@crowdwisdomtrading.com` (recorded from the brief) and state who should receive it. | Avoids sending to an unverified address. | B5 / A7 |

## 3. Provider / credential authorization checklist

Availability of a credential never implies authorization to spend. As of
2026-10-28 no provider credential is present in this environment (only empty
`.env.example` placeholders), no private transfer route is defined, and no paid
call is authorized. This is the exact checklist to satisfy before any live call.

| Provider | Purpose | Expected operation | May incur cost? | Required cap | Required approval |
| --- | --- | --- | --- | --- | --- |
| Apify (X corpus) | Obtain the accepted 180-day post-level X dataset | One bounded Actor run (ticker, cashtag, keyword queries), then profile and ingest | **Yes** — Actor runs are billed | Hard USD ceiling + per-run item cap (Q7) | Employer source approval (Q5) + user spend authorization + private token route (Q6) |
| Tavily (news) | Optional recent-news outlook context | One bounded, single-request `fetch-news --confirm-live-call` search | **Yes** — API usage is billed | Per-call USD cap (Q7) | Employer confirmation it is required (Q3) + user authorization + private key route (Q6) |
| Exa (news, optional) | Only used if the employer chooses it | One bounded news search | **Yes** if used | Per-call USD cap (Q7) | Only if actually selected (Q3/Q5) + private key route (Q6) |
| Coinbase (prices) | Reproducible public daily price snapshot | Free public `fetch-prices` re-fetch of the recorded 180-bar window | No (public endpoint) | n/a (bounded request) | Network allowlist to `api.exchange.coinbase.com`; no credential |
| Private credential channel | Transfer any token safely | Password-manager share / encrypted attachment | No | n/a | Employer-named channel and recipient (Q6) |

Engineering rule: no live Tavily/Exa/Apify/Coinbase request is made until the
matching row is fully approved, the cap is recorded, and the user explicitly
authorizes the call. Up to and including 2026-10-28, **no live provider call has
been made**; all provider coverage is mocked.

## 4. Ready-to-send email draft (NOT SENT)

**To:** `gilad@crowdwisdomtrading.com` (re-verify against the original brief — Q9)
**Subject:** X Sentiment Price Predictor — internship assignment deliverables and clarification request

> Hello,
>
> Please find the X Sentiment Price Predictor assignment deliverables below.
>
> **Repository:** <https://github.com/rajaryan1111/x-sentiment-price-predictor>
> **Assessment PR:** <https://github.com/rajaryan1111/x-sentiment-price-predictor/pull/14>
> **Verified working branch:** `arena/cf79e7b7-x-sentiment-price-predictor`
> **Documentation:** the submission summary, requirements audit, verification
> report, demo walkthrough and evaluation report (PDF or Markdown) are in the
> repository's `docs/` folder and `reports/btc-usd-180d/`.
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
- **GitHub links:** repository URL and PR #14 URL above; note the final verified
  code is on the Arena branch until the PR head is promoted per
  [PR14_PROMOTION.md](PR14_PROMOTION.md).
