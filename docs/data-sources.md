# Historical social-text dataset sources

This registry is transcribed from the user-provided **Historical Twitter/X Datasets — Verified Download Links** PDF (compiled 21 October 2026). The PDF says its entries were checked against live pages on that date. On 2026-10-29, three candidate listings were partially rechecked at their public metadata/card level; the other registry entries, current rights and full row contents remain unverified. The machine-readable registry records `independent_verification.status = partially-reverified` with scope, date and next action; the validator rejects a missing or unknown verification record.

The assessment-linked Google Doc's full text export was retrieved on 2026-10-29; it contains 12 dataset entries and is a dataset-link compilation, not a tweet corpus. It says it was compiled 2026-10-21 and that entries were verified against live pages then; that statement is the document author's claim, not this project's current verification. The companion PDF and assignment PDF are not present in this checkout, so their previously recorded 2026-10-26 full review and hashes cannot be re-opened here. The current Google Doc's visible title and description are not the source text; the text-export endpoint was read. Uploaded local files were previously inventoried in repository notes, but no such raw files are present in the current checkout. No accepted post-level X corpus is present.

Machine-readable source of truth: [`data/registry/historical_twitter_x_datasets.json`](../data/registry/historical_twitter_x_datasets.json).

## Candidate source checks (2026-10-29)

These are page/card and metadata checks only. No bulk dataset was downloaded, no rows were profiled, and no source was approved for this project. Public availability and an uploader-selected license label are not proof of the uploader's rights in the underlying X posts or of permission for this project's collection, retention, training or redistribution.

| Candidate | Source claims and observed page metadata | What it does not establish | Current decision |
| --- | --- | --- | --- |
| [Bitcoin Tweets Dataset (2025–2026), Kaggle](https://www.kaggle.com/datasets/pokeash/bitcoin-tweets-dataset-20252026) | The accessible Kaggle dataset metadata reports CC0, about 2.10 GB, version 1 last updated 2026-03-04. Its description says X posts from 2025 “to present”, filtered by Bitcoin-related keywords; lists `text`, `date`, `user_followers`, profile fields, hashtags, source and retweet flag. | No exact observed row date range or current 180-day coverage; the page's “to present” claim is not validated against rows. No likes/reposts/views fields are listed. User follower count is not shown to be a historical point-in-time snapshot. Not BTC-USD pair-specific; input query modes are not the assignment's live ticker/cashtag/keyword collection. The listing version predates the requested recent window at the time checked. | Most relevant candidate to ask the employer about, but not an accepted data source. Requires written rights/use approval and authorized download/profile of timestamp range, schema, duplicates, missingness and point-in-time semantics. |
| [Crypto & Stock Tweets, Hugging Face](https://huggingface.co/datasets/StephanAkkerman/crypto-stock-tweets) | Public ungated repository; dataset card declares CC-BY-4.0 and combines ten sources. Card states 8,024,269 rows (including 4,820,915 Bitcoin tweets); repository metadata identifies the CSV and a 2023-12-22 revision. | Dataset-server schema has only `text` and `url`, without structured timestamp, author or engagement columns; a date embedded in sample text is not a reliable timestamp field. No current 180-day coverage. Card's total conflicts with its stated subcounts (2,624,314 + 5,748,725 = 8,373,039), and it says original-source terms apply without establishing each source's rights. | Does not meet the recent 180-day data/metadata requirement; not accepted. |
| [Tweets about the Top Companies (2015–2020), Kaggle](https://www.kaggle.com/datasets/omermetinn/tweets-about-the-top-companies-from-2015-to-2020) | Accessible Kaggle metadata reports CC0 and last update 2020-11-26; uploader describes >3M tweets for Amazon, Apple, Google, Microsoft and Tesla with author, date, text, comments, likes and retweets. | Equity-only topic and old date window, not BTC-USD or recent 180 days; actual row-level schema and coverage were not downloaded/profiled. CC0 label alone does not establish rights over underlying content. | Not a match for this BTC task. |

The linked Google Doc also lists older Bitcoin collections, ID-only corpora, StockTwits and other sources. None of the source-list text constitutes downloaded post data or a validated current-window profile. For the sources above, primary pages checked were the Kaggle metadata endpoints and Hugging Face card/API/first-rows schema linked in their names; they describe uploader claims, not legal clearance.

## Selection guidance for this project

1. **Do not download all datasets.** Some are multi-gigabyte, one reported corpus is 44.9 GB, and StockTwits is reported as 71+ GB.
2. No candidate has been selected or accepted. If a historical corpus is desired, ask the employer to approve the Bitcoin 2025–2026 Kaggle dataset (or name another source) and confirm a permitted, bounded download; do not treat it as meeting the recent window until actual rows show coverage.
3. The CC0/CC-BY labels are source statements. Confirm who owns or can license the underlying content, current applicable platform terms, commercial/research use, retention and redistribution rights before processing. This is not legal advice. In particular, the [X Developer Policy](https://docs.x.com/developer-terms/policy#content-redistribution) restricts redistribution of X Content; any permitted use of historical third-party corpora needs its own review.
4. **StockTwits is not X/Twitter.** Do not merge it into an X-only cohort.
5. Tweet-ID-only datasets are not full-text datasets. Hydration is subject to platform access, redistribution rules, deletion/protection and the terms of the source.
6. The registry's license/access text is a source-document summary, not legal advice. Re-check current source pages and written terms before downloading or using any dataset, particularly for commercial work.

## Reproducibility and point-in-time safety

- Keep a local record of the provider URL, dataset version/snapshot, retrieval date, file hashes, schema, license review, and transformation version.
- Keep raw files and hydrated content out of Git. Store data only in local ignored paths or approved storage.
- Preserve source ID, original event timestamp (timezone-aware), retrieval timestamp and provenance. Do not substitute retrieval time for event time.
- Before creating daily/hourly sentiment, use only posts available by that forecast cutoff. Deduplicate and aggregate within a clearly defined window.
- Join sentiment and prices on explicit time windows and asset mapping. Use chronological/walk-forward validation; no random split and no future sentiment leakage.
- Compare a price-only baseline against the sentiment-augmented model. Do not report performance metrics until they are calculated on out-of-sample data with assumptions disclosed.

## Registry validation

Run offline validation from the repository root:

```bash
python scripts/validate_dataset_registry.py
pytest
ruff check src tests scripts
```

The validator checks registry structure and consistency only: platform and text-availability vocabulary, ISO verification dates, date ordering, positive record counts, ID-only hydration caveats, a sane "recommended" flag, and the explicit independent-verification record. It does not download files or certify provider claims.
