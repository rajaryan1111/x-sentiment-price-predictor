# Employer clarifications and authorization gates

**Status (2026-11-01):** no employer answers or submission delivery are recorded. The original assignment PDF was re-opened and read in full from a user-provided copy in Downloads; the companion historical-dataset PDF was also reviewed. Both are outside Git and excluded from the ZIP. The source names, page counts, and verified hashes are in [REQUIREMENTS_TRACEABILITY.md](REQUIREMENTS_TRACEABILITY.md). The PDF specifies the recipient `gilad@crowdwisdomtrading.com`; this address is copied into the unsent draft and is not independently mailbox-verified. No address reconfirmation is requested.

## Confirmed from the assignment source

- The assignment requests BTC/asset-related X posts from the most recent 180 days, searched by ticker, cashtag, and keywords; same-period prices; timestamp alignment and the listed post metadata; Tavily news; sentiment/price features; forecasts `n+0` through `n+5`; walk-forward evaluation; visual output; a one-page outlook; and an evaluation report containing Sharpe, Sortino, and maximum drawdown.
- The submission page gives `gilad@crowdwisdomtrading.com` and asks for a repository link, provider credentials/Actor IDs used, and a PDF or Markdown evaluation report.
- It gives both “within 1 week” and “5–7 days” without an absolute due date.
- Security policy for this project forbids putting credentials in Git, chat, package files, or plaintext email. Employer-provided secure transfer instructions are needed if credentials are required.

## Decisions still requiring an external answer

| Question | Why it remains open | Owner / needed action |
| --- | --- | --- |
| What is the exact calendar deadline and timezone? | The source gives two relative durations but no receipt date or absolute due date. | Employer: provide the due date and timezone. |
| What precisely does `n+0` mean? | The implementation's working default is the unfinished close for day `n`, issued at 00:00 UTC; the source does not define the cutoff convention. | Employer: confirm or specify the target and issue time. |
| Is Binance Vision BTCUSDT (USDT quote) acceptable, or is exact BTC-USD required? | The reproducible report uses Binance Vision data under CC BY-NC-SA 4.0, non-commercial/share-alike terms. Coinbase terms restrict ML use and derived-report redistribution without written consent. | Employer: accept the disclosed USDT proxy or provide/approve a rights-cleared BTC-USD source. |
| Is a live Tavily request mandatory? May news affect model features? | The brief asks for recent news to complement sentiment but separately limits model inputs to sentiment and price. The safe current policy keeps news as outlook context only. | Employer: state whether live news is required and whether the feature policy should change. |
| Which X source/Actor and terms should be used? | No approved Actor, license, matching 180-day corpus, or live payload profile exists. `61RPP7dywgiy0JPD0` is only a candidate configured locally. | Employer: approve a provider/Actor or dataset, terms, fields, query modes, and 180-day coverage. |
| What is the hard item and USD spend cap? | The adapter has local caps, but they do not verify Actor pricing or authorize a paid run. | Employer: specify per-run item and spend ceilings; user must authorize any paid run. |
| How should required provider credentials be transferred? | Local presence is not approval. Secrets must not be sent by plaintext email or included in the ZIP. | Employer: name an approved private channel and recipient. |
| Is Exa required for ongoing use? | The brief names Tavily in project scope and mentions Exa only on the submission page. A bounded Exa request has now been smoke-tested once. | Employer: clarify ongoing provider requirements and any allowed credit/spend limit. |
| Is a video or any format beyond the requested repository and Markdown/PDF report required? | The source does not specify a demo/video attachment. A demo script exists; no video is claimed. | Employer: specify any additional deliverables and delivery channel. |
| May retrospective archive creation time be used as availability time? | This can introduce look-ahead bias. The implemented default is leakage-safe observed availability; archive mode is opt-in and disclosed. | Employer: explicitly approve or reject the disclosed retrospective assumption. |

## Provider status verified locally

Configuration was checked on 2026-11-01 without printing secret values. The ignored local `.env` has the Apify token, candidate Actor ID, Tavily key, and Exa key configured. `.env.example` contains placeholders only. This does not establish employer approval, licensing, permission to spend, or a secure credential-transfer route.

- **Apify:** configured ID resolves to `apidojo/tweet-scraper`; adapter and preflight tests exist. Current account Free-plan rules block API Actor runs. No live run, paid scrape, accepted X post, or 180-day X profile exists.
- **Tavily:** bounded adapter, date/topic controls, explicit CLI gate and offline JSONL handoff are mocked-tested. One live dated finance request returned one result with a malformed publication timestamp withheld.
- **Exa:** official `/search` adapter, typed response envelope, date filters, bounds, and mock tests exist. One live request returned one result with publication and source metadata; the shared CLI dispatch was corrected and regression-tested.
- **Prices:** a fresh 180-row Binance Vision BTCUSDT snapshot and evaluation, with source archives/checksums and per-row predictions, are included. Values are USDT, not USD, and derivatives are non-commercial CC BY-NC-SA 4.0.

## Submission draft

The unsent email is in [EMPLOYER_EMAIL_DRAFT.md](../submission/EMPLOYER_EMAIL_DRAFT.md). It uses the source-specified recipient, identifies the final branch and report, describes current evidence and limitations, states that no paid Apify run was made, and asks only for unresolved employer decisions. No email has been sent.
