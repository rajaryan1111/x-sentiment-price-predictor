# Final evaluation report — 2026-11-01

## Scope and evidence limits

This report records the artifacts and verification available on the final submission branch. The original assignment and companion dataset-reference PDF were reviewed in full from user-provided copies; the source file names, page counts, and SHA-256 values are in [the requirement traceability matrix](../docs/REQUIREMENTS_TRACEABILITY.md). They are not in Git or the ZIP.

The committed BTC-USD evaluation artifacts are historical outputs from 2026-10-26. They contain a manifest, aggregate `metrics.json`, rendered report, outlook, and SVG, but the raw 180-day price snapshot and `predictions.jsonl` are absent from this checkout. This audit cross-checked reported numbers against the committed metrics artifact and verified arithmetic summaries where possible; it did **not** refetch market data, retrain the models, or recompute MAE and strategy returns from raw rows. The values below must therefore be read as results recorded in those committed artifacts, not a fresh independent evaluation.

No accepted X posts or scored sentiment observations are present. The sentiment-plus-price model is not identifiable in that historical run. No sentiment improvement is claimed.

## Requirement-by-requirement status

Detailed acceptance criteria, evidence, and blockers for all 28 IDs are in [REQUIREMENTS_TRACEABILITY.md](../docs/REQUIREMENTS_TRACEABILITY.md). This table maps the source brief's major deliverables to those IDs.

| Original assignment requirement | Status | Evidence and remaining gap |
| --- | --- | --- |
| Python ML/RL pipeline | COMPLETE (supervised ML interpretation) | Implemented CLI pipeline, baseline comparisons and tests; the brief permits ML or RL and does not define an RL environment. |
| X scraping with ticker, cashtag and keyword searches over the latest 180 days | BLOCKED | Offline Apify adapter, local input preflight and bounded ingest exist; preflight confirms all three query modes without network or spend. No approved Actor, licensed corpus, live run, or coverage profile exists. |
| Same-period historical prices | COMPLETE (historical record) | The committed manifest/metrics record 180/180 Coinbase BTC-USD daily candles for 2026-04-29 through 2026-10-25 UTC. The raw snapshot is not in the repository, so this audit did not independently revalidate the rows. |
| Post text, timestamps/UTC offsets, engagement and follower counts | PARTIAL | Normalization contracts and fixture tests exist; no real provider payload has been checked for actual field availability or semantics. |
| Join price and X data in a database | COMPLETE (offline implementation) | Versioned storage, idempotent writes and leakage-safe joins are implemented and fixture-tested; populating with accepted real X records remains blocked by source/data approval. |
| Recent relevant news with Tavily | PARTIAL | Bounded, explicitly gated adapter and offline JSONL path are mocked-tested. No live Tavily request or news snapshot was made. |
| Sentiment and price-only features | PARTIAL | VADER, aggregates, price features and explicit missing-sentiment behavior are implemented and fixture-tested. No accepted post text was scored. |
| Forecast `n+0` through `n+5` | PARTIAL | Six horizon models/targets exist and are tested. Meaning of `n+0` remains a working convention pending employer clarification. |
| Walk-forward out-of-sample validation | PARTIAL | Five expanding folds with a five-row purge and baseline comparisons are implemented. Historical aggregate metrics exist, but no fresh retraining from raw rows was possible and sentiment is absent. |
| Visual matrix of sentiment change against price | PARTIAL | Dependency-free SVG has price, sentiment-level and sentiment-change panels; empty panels state that sentiment is unavailable. The historical artifact has no real sentiment curve. |
| One-page sentiment outlook | PARTIAL | Generator and page contract are tested; historical outlook clearly reports zero scored posts and no news context. A real sentiment outlook cannot be produced without data. |
| Evaluation report with Sharpe, Sortino and max drawdown | COMPLETE as an artifact; current recalculation PARTIAL | Markdown report and metrics artifact state the strategy assumptions and values, with undefined ratios explained. Raw prices/predictions are absent, so the metrics are not freshly recomputed here. |
| Repository, evaluation report and reproducibility materials | PARTIAL (prepared, not delivered) | Final branch, package, report, demo and reproduction instructions are prepared; email delivery and any employer-required additional materials remain outstanding. |
| Provider credentials and Actor IDs | BLOCKED | The brief asks for credentials used. Local Apify/Tavily entries are configured but are not employer-approved; Exa is blank and not integrated. A secure private channel and employer approval are missing. |
| Submission timing and any extra video/format | BLOCKED | Brief says both “within 1 week” and “5–7 days” but gives no calendar date; it does not specify a video. Employer must clarify deadline and any extra deliverables. |

The exhaustive matrix statuses currently aggregate to 11 verified complete, 14 partial, 2 blocked by external dependency, and 1 requiring clarification. “Complete” for software does not mean the real-data experiment is complete.

## Historical recorded BTC-USD metrics

The committed `reports/btc-usd-180d/metrics.json` records 180 BTC-USD daily candles from 2026-04-29 through 2026-10-25 UTC; 0 posts and 0 scored posts; 5 expanding walk-forward folds; 100 evaluation samples per model and horizon; and 1,800 model/horizon prediction evaluations (3 × 6 × 100). The raw candles and per-row predictions are not committed.

| Model | Mean MAE across six horizons (USD) | Relative to naive |
| --- | ---: | ---: |
| Naive persistence | 1,828.36 | baseline |
| Price-only ridge | 2,264.62 | 23.86% higher MAE |
| Sentiment-plus-price ridge | 2,264.62 | identical to price-only; no sentiment observations |

The historical metrics artifact records the price-only strategy at +10.91% cumulative net return, Sharpe 1.807, Sortino 3.979, maximum drawdown 4.08%, and 32/100 long days. It records the unconditional long benchmark at +6.11%, Sharpe 0.752, Sortino 1.377, and 10.33% maximum drawdown. These are sample-specific backtest statistics, not expected or guaranteed future returns. The naive strategy made no trades, so its risk ratios are undefined.

## Verification status

The final exact-working-tree test, lint, compile, documentation, registry, preflight, clean-extraction, ZIP, and CI results are recorded in [FINAL_HANDOFF.md](FINAL_HANDOFF.md) and [FINAL_SUBMISSION_CHECKLIST.md](FINAL_SUBMISSION_CHECKLIST.md). Historical Actions runs are not used as proof for a newer commit.

## Final verdict

**READY WITH DISCLOSED EXTERNAL BLOCKERS.** Locally achievable software, offline verification, documentation, and packaging are prepared. Real X collection and sentiment evaluation, approved credentials/source terms, any paid run, and the employer's remaining decisions cannot be completed without external authorization and data.
