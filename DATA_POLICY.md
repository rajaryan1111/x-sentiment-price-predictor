# Data Policy
This is an engineering policy, not legal advice or proof of license approval.

## Principles
Use only sources accessible through documented, permitted routes. A URL, dataset card or registry entry is not proof of current rights. Review current terms before collection, hydration, processing, retention, training or redistribution. If access or rights are unclear, mark the source blocked. Preserve platform identity: StockTwits is not X. Never bypass access controls or hydrate IDs unless permitted.

## Price source
Default is Coinbase Exchange public BTC-USD daily candles. Record provider/endpoint, product, granularity, UTC interval, retrieval time, code revision and coverage profile. Public availability does not guarantee future API behavior or completeness.

## X source
Required target is asset-related X posts over the most recent 180 days using an approved Apify/provider route, with ticker, cashtag and keyword searches. Before collection verify Actor identity, input/output schema, platform, terms, query support for all three modes, available fields (text, timestamps, likes, reposts, views, author followers), charges, plan limits, max results and actual 180-day reach. No live Actor has been selected/run and no real X corpus is accepted. Do not assume free credits make an Actor free; no paid run without explicit budget approval.

## Historical datasets
The assessment-linked Google Doc was retrieved on 2026-10-26; it is a 12-entry dataset-link compilation matching the companion PDF, not a tweet corpus. Start by selecting a candidate and inspecting its actual contents, platform, schema, license/terms, version, text availability and event-time coverage. Registry entries are candidates only. ID-only files contain no text; older corpora cannot by themselves meet a recent 180-day window. The uploaded files were inspected on 2026-10-26: `90-day-samples.zip` contains numeric tweet IDs only; the historical sample, date-tweet-id and statistics files contain IDs or date/count summaries; `archive.zip` is an air-quality CSV; the available `archive (1).zip` is MQTT sensor JSON; `archive (2).zip` is absent; `Manuscript.pdf` is a StockTwits paper. No uploaded file contains post-level X text, and none is an accepted dataset.

## News
Tavily is the named source for the most recent and relevant news. Default use is context for the outlook, not predictive features, because the brief says the model uses sentiment and price only. Record URL, headline, publication time when available, retrieval time and query. Exa appears only in the submission line and token request; it is optional unless actually used or employer-required.

## Provenance manifest
Record source/platform/provider and URL; dataset version or non-secret run ID; query and UTC range; retrieval timestamp; code revision; license review status/date/restrictions; SHA-256 hash when a snapshot is retained; schema version; sanitized counts/missingness/duplicates/time range; transformations/exclusions; and whether historical availability is known. Never include secrets.

## Point-in-time and engagement
created_at is event time; retrieved_at is when first observed. Never backdate retrieval. Old posts downloaded today are not automatically valid historical features. Only records with defensible availability evidence may enter a historical cutoff. Current likes/reposts/views/follower counts are not historical predictors unless time-stamped snapshots prove their values at cutoff.

## Security, retention and cost
Keep raw datasets, private exports, hydrated text, cookies and secrets out of Git. Use ignored local paths or approved private storage; honor retention/deletion terms. Share credentials only through a verified employer-approved private channel. Bound items, timeout and spend; use a small schema test first; no automatic retries of non-idempotent paid launches.

## What is committed to the repository
Committed: sanitized reports, charts, outlook pages, metrics, manifests and non-secret configuration. Every real run records input SHA-256 hashes, counts and the library versions used. Post text is never written into a committed artefact, and bulk generated prediction dumps stay out of Git (see D-021). Optional news files are operator-supplied context only; the news text never becomes a model feature.

## Source acceptance checklist
- Platform/source identity and access route verified.
- Current terms reviewed for collection, training, storage, retention and reporting.
- Actual schema and text availability inspected.
- Required 180-day event-time coverage measured, with ticker, cashtag and keyword query modes documented.
- Missing IDs/text/timestamps, duplicates, invalid timestamps and engagement availability profiled.
- Provenance and hash/run ID recorded.
- Point-in-time availability assessed and limitations stated.
- Cost is zero or within explicit approval.
- No raw content or secret committed.
Until evidenced, a source remains a candidate, not an accepted training dataset.
