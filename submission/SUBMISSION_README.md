# X Sentiment Price Predictor — submission packet

**Repository:** https://github.com/rajaryan1111/x-sentiment-price-predictor
**Branch:** `feat/availability-basis-and-preflight`
**Recipient in assignment PDF:** `gilad@crowdwisdomtrading.com` (not independently mailbox-verified)
**Submission state:** final package and email are handled after the verified PR release gates; check the external release handoff for the final send and delivery status.

## Packet contents

| File | Purpose |
| --- | --- |
| [FINAL_HANDOFF.md](FINAL_HANDOFF.md) | Repository state, verification evidence, package location and verdict |
| [FINAL_SUBMISSION_CHECKLIST.md](FINAL_SUBMISSION_CHECKLIST.md) | Exact final checks and submission readiness |
| [FINAL_EVALUATION_REPORT.md](FINAL_EVALUATION_REPORT.md) | Requirement coverage and historical result summary |
| [REMAINING_BLOCKERS.md](REMAINING_BLOCKERS.md) | External dependencies, owners and required actions |
| [PACKAGE_MANIFEST.md](PACKAGE_MANIFEST.md) | Included components and exclusions |
| [DEMO_SCRIPT.md](DEMO_SCRIPT.md) | Honest evaluator walkthrough |
| [REPRODUCIBILITY.md](REPRODUCIBILITY.md) | Clean clone/ZIP setup, offline checks and demo |
| [EMPLOYER_EMAIL_DRAFT.md](EMPLOYER_EMAIL_DRAFT.md) | Prepared email using the address printed in the assignment |
| [RESULTS.md](RESULTS.md) and [DATA_LIMITATIONS.md](DATA_LIMITATIONS.md) | Recorded metrics and evidence limits |
| [EXPERIMENT_METHODOLOGY.md](EXPERIMENT_METHODOLOGY.md) | Modeling and evaluation conventions |

The full 28-ID traceability matrix and detailed engineering evidence are in `docs/REQUIREMENTS_TRACEABILITY.md`.

## What the software does

The package includes a checked Binance Vision BTCUSDT dataset and evaluation,
configurable X/Apify preflight and ingestion, Tavily and Exa contextual-news
adapters, point-in-time sentiment/price features, six-horizon supervised forecasts,
naive and price-only baselines, purged walk-forward evaluation, strategy risk
metrics, database persistence and joins, an offline HTML dashboard and SVG visualization, a one-page outlook,
offline tests, and safe preflight tooling.

## What the evidence does not show

- No accepted or licensed 180-day X corpus or scored real sentiment is present.
- No Apify run or Coinbase request was made. One bounded request each to Tavily and Exa was made; see the [provider verification report](../docs/PROVIDER_VERIFICATION_2026-11-01.md).
- The fresh Binance Vision evaluation includes its source archives/checksums, exact snapshot and per-row predictions. Its quote currency is USDT, not USD.
- Binance data and derived report files are CC BY-NC-SA 4.0, attributed and non-commercial only.
- The original assessment PDFs were reviewed from user-provided copies outside the repository; they are neither committed nor included in the ZIP.
- The email send and external delivery status are recorded in the external release handoff.

**Verdict:** SUBMISSION READY WITH EXTERNAL BLOCKERS. See the handoff and blocker list for exact next actions.
