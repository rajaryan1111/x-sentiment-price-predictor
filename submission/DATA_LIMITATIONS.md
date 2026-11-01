# Data limitations and external blockers

The full owner-assigned list is in [REMAINING_BLOCKERS.md](REMAINING_BLOCKERS.md); the 28-ID matrix is in [docs/REQUIREMENTS_TRACEABILITY.md](../docs/REQUIREMENTS_TRACEABILITY.md).

## X and sentiment

- No employer-approved Actor, accepted/license-cleared 180-day post corpus, or live X collection exists. Local configuration contains an Apify token entry and candidate Actor ID, but these do not confer approval, rights, a spend cap, or authorization. No paid Apify run occurred.
- The offline preflight validates only local input shape and lists ticker/cashtag/keyword modes. It does not confirm a real Actor's schema, terms, or historical coverage.
- No posts were supplied or scored in the committed historical price run. Sentiment features remain missing, the sentiment-plus-price model is unidentifiable, and the chart/outlook state this explicitly.
- The historical dataset-reference PDF and linked Google Doc list candidate sources, not an accepted post corpus. No candidate rows were downloaded, rights-cleared, or profiled as an approved dataset.

## News providers

- Tavily adapter/CLI are mocked-verified, gated, bounded, and context-only. A local key entry is configured but no live Tavily request was made.
- Exa is blank locally and is not integrated. No Exa request was made.

## Historical price metrics

The committed report/manifest/metrics describe a 180-candle BTC-USD run from 2026-04-29 through 2026-10-25 UTC. The raw snapshot and per-prediction rows are absent from this checkout. Current documents therefore label those results historical and cross-check their reported values against the aggregate metrics artifact; they do not claim fresh retraining or raw-row recalculation.

## Point-in-time and model limits

- Default availability uses first-observed time; retrospective archive event-time mode is explicit, opt-in, and disclosure-noted. No submitted run uses retrospective mode.
- `n+0` remains a documented engineering convention until the employer confirms the issue-time/target definition.
- The strategy metrics describe one short sample, one asset, and one period. They do not establish profitability or future performance.
- The deliverable chart is a generated SVG with empty sentiment panels labelled; there is no interactive web dashboard. The assignment asks for visual charts, which the SVG output supplies.

## Source and submission

The original assignment PDF and companion dataset-reference PDF were reviewed on 2026-11-01 from user-provided copies outside Git; hashes and page counts are recorded in the traceability matrix. They are not committed or included in the ZIP. The assignment specifies `gilad@crowdwisdomtrading.com`; the draft uses it and does not ask for reconfirmation. Mailbox ownership was not independently verified. No email was sent.
