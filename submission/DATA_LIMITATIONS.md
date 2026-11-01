# Data limitations and external blockers

Every limitation below is already tracked in the canonical documents
([`docs/EXTERNAL_BLOCKERS.md`](../docs/EXTERNAL_BLOCKERS.md),
[`DATA_POLICY.md`](../DATA_POLICY.md),
[`docs/REQUIREMENTS_TRACEABILITY.md`](../docs/REQUIREMENTS_TRACEABILITY.md));
this page consolidates the ones that affect the submitted evidence.

## 1. No accepted X corpus — the central limitation

- No Apify Actor has been approved, licensed or run. Local configuration contains
  an Apify token and a candidate Actor ID, but that does not establish employer
  approval, licensing, a spend cap or an authorized private credential route
  (blockers R2, A2, B1–B3, O13). No live Actor run or paid X scrape has occurred.
- A Tavily key is locally configured, and the adapter exists, but no live Tavily
  request has been made. Exa is not implemented as a provider integration; its
  configuration placeholder is not evidence of working Exa support.
- The assessment-linked Google Doc was re-fetched on 2026-10-29 and is a
  12-entry dataset-*link* compilation, not a tweet corpus. Three candidate
  public listing/card metadata were checked, but no candidate rows were
  downloaded, rights-cleared or profiled (A3, A6, B10).
- The best registry snapshot predates the current 180-day window
  (≈2026-05-05 → 2026-11-01); older candidates end in 2019–2023 and ID-only
  corpora contain no text (B10).
- Consequences already visible in the results: all sentiment features are
  null, the sentiment-plus-price model is not identifiable (it degenerates to
  the price-only model), the chart's sentiment panels are labelled
  "unavailable", and the sentiment-versus-price question is unmeasured.

## 2. Point-in-time availability

- The pipeline's default `observed` basis requires `retrieved_at <= cutoff`.
  A historical archive collected today carries today's retrieval time, so it
  cannot silently become historical input. The project does not backdate
  retrieval, ever.
- `archive_created_at` is an opt-in, disclosure-noted retrospective basis
  (implemented and regression-tested) that treats event time as availability;
  it is not a leakage-safe historical backtest and it was dormant — no run in
  this submission uses it. Using it requires an explicit employer decision (B9).
- Current engagement counts (likes/reposts/views/followers) are preserved as
  metadata but excluded from historical features unless timestamped snapshots
  prove their values at a cutoff.

## 3. Convention and process clarifications awaiting the employer

| Item | Status |
| --- | --- |
| `n+0` target convention (B4) | working default: forecast the not-yet-completed close of day `n` at 00:00 UTC |
| Calendar deadline (A1, B5) | brief states both "one week" and "5–7 days"; no date may be inferred |
| Live Tavily news required? and news-as-feature? (B6) | adapter ready, gated CLI ready; news stays context-only unless formally revised |
| Submission format / channel / recipients (B7) | Markdown report exists; PDF not additionally produced because not confirmed |
| Private credential-transfer route (B2) | undefined; secrets never go through chat, Git or an email body |

## 4. Evidence-scope caveats

- 32 long days is a small strategy sample on a single asset and period;
  Sharpe/Sortino/drawdown are strategy statistics over one regime, not
  performance claims.
- The original assessment PDFs are absent from this checkout; requirement
  wording rests on the recorded transcription (with recorded SHA-256 hashes
  in the traceability matrix), and the re-read was not possible in the 2026-10-29/2026-11-01 audits.
- The committed price snapshot file is untracked (raw market data is kept out
  of Git); a fresh clone refetches it with `fetch-prices`, or the supplied
  deterministic synthetic demo demonstrates the software instead.
- CI green and 209 passing tests prove lint, validators and offline
  behavior only. They are not evidence of model quality, data access or
  profitability (NFR6, RULES.md §Reporting).
- All test fixtures and the offline demo are explicitly labelled synthetic;
  they never appear as market or model evidence.

## 5. What would unblock everything

1. Employer selects/authorizes one permitted X source, sets a hard item and
   USD spend cap, and names a private credential channel (B1–B3).
2. One bounded 7-day Apify pilot, then the capped 180-day ingestion
   (`scripts/ingest_apify_x.py`), each with a sanitized manifest.
3. The scripted offline pipeline then covers the rest automatically:
   normalize → profile → strict-mode features → six-horizon evaluation →
   chart, outlook, report, traceability updates.

Retrospective archive results, if ever approved, would additionally require:
an explicit disclosure note, `availability_basis` in the manifest, limitation
sentences in every applicable report, and language stating that historical
availability cannot be established and look-ahead bias cannot be excluded.
