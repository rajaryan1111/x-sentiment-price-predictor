# Historical social-text dataset sources

This registry is transcribed from the user-provided **Historical Twitter/X Datasets — Verified Download Links** PDF (compiled 21 October 2026). The PDF says its entries were checked against live pages on that date. We have captured the PDF's links and claims, but have **not independently re-verified the current provider pages, current availability, or license terms**. The machine-readable registry records this explicitly as `independent_verification.status = not-reverified` with a checked date and next action; the validator rejects a missing or unknown verification record.

The assessment-linked Google Doc was retrieved on 2026-10-26; its exported text matches the PDF's 12 entries. The document is a dataset-link compilation, not a tweet corpus. Uploaded local files were also inspected: the 90-day samples are numeric tweet IDs only; the date/count files are summaries; the available archives are an air-quality CSV and MQTT sensor JSON; `Manuscript.pdf` is a StockTwits paper. No uploaded file contains X post text.

Machine-readable source of truth: [`data/registry/historical_twitter_x_datasets.json`](../data/registry/historical_twitter_x_datasets.json).

## Selection guidance for this project

1. **Do not download all datasets.** Some are multi-gigabyte, one reported corpus is 44.9 GB, and StockTwits is reported as 71+ GB.
2. Start with a small, relevant candidate such as **Crypto & Stock Tweets (Hugging Face)** for a mixed-domain exploration, or **Tweets about the Top Companies (2015–2020)** for equity-specific exploration. For a Bitcoin-only experiment, consider the 2025–2026 Bitcoin corpus only after inspecting its schema and pinning a snapshot.
3. The PDF itself has one numeric inconsistency for Crypto & Stock Tweets: its stated total is 8.02M, while the listed stock and crypto subcounts sum to 8.37M. The registry preserves the stated total but flags it; do not use the count until the live dataset card is checked. These are candidates, not a declaration that any dataset is already downloaded, clean, licensed for every use, or ready for training. Inspect timestamps, schema, coverage, duplicates, language, asset/symbol mapping, missingness, bot/spam risks and source provenance before using it.
4. **StockTwits is not X/Twitter.** It may be useful as a separate comparative dataset, but never merge it into an X-only dataset without explicit platform labels and a documented research design.
5. Tweet-ID-only datasets are not full-text datasets. Hydration is subject to platform access, redistribution rules, deletion/protection and the terms of the source.
6. Sentiment140's license is marked “Other” in the PDF. Do not use or redistribute it until its actual license is checked.
7. The registry's license/access text is a source-document summary, not legal advice. Re-check the current source page before downloading or using any dataset, particularly for commercial work.

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
