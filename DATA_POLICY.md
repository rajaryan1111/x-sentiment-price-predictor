# Data Policy
This is an engineering policy, not legal advice or proof of license approval.

## Principles
Use only sources accessible through documented, permitted routes. A URL, dataset card or registry entry is not proof of current rights. Review current terms before collection, hydration, processing, retention, training or redistribution. If access or rights are unclear, mark the source blocked. Preserve platform identity: StockTwits is not X. Never bypass access controls or hydrate IDs unless permitted.

## Price source
Default is Coinbase Exchange public BTC-USD daily candles. Record provider/endpoint, product, granularity, UTC interval, retrieval time, code revision and coverage profile. Public availability does not guarantee future API behavior or completeness.

## X source
Required target is asset-related X posts over 180 days using an approved Apify/provider route. Before collection verify Actor identity, input/output schema, platform, terms, query support, charges, plan limits, max results and actual 180-day reach. No live Actor has been selected/run and no real X corpus is accepted. Do not assume free credits make an Actor free; no paid run without explicit budget approval.

## Historical datasets
Start with the assessment-linked resource if access is obtained; inspect actual contents, platform, schema, license/terms, version, text availability and event-time coverage. Registry entries are candidates only. ID-only files contain no text; older corpora cannot by themselves meet a recent 180-day window. Uploaded date/count and ID-list files do not provide post-level text. Uploaded 90-day-samples.zip and archive (2).zip have not been inspected internally; their contents, schema and rights are unverified.

## News
Tavily is named for recent relevant news. Default use is context for the outlook, not predictive features. Record URL, headline, publication time when available, retrieval time and query. Exa appears in the submission checklist but its runtime role is unresolved.

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
- Required 180-day event-time coverage measured.
- Missing IDs/text/timestamps, duplicates, invalid timestamps and engagement availability profiled.
- Provenance and hash/run ID recorded.
- Point-in-time availability assessed and limitations stated.
- Cost is zero or within explicit approval.
- No raw content or secret committed.
Until evidenced, a source remains a candidate, not an accepted training dataset.
