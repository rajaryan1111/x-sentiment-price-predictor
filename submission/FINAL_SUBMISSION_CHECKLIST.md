# Final submission checklist — 2026-11-01

## Repository and source audit

- [x] Repository remote is `https://github.com/rajaryan1111/x-sentiment-price-predictor.git`.
- [x] Target branch is `feat/availability-basis-and-preflight`; final SHA and remote/PR sync are reported in the release handoff.
- [x] Original assessment PDFs were re-read from user-provided copies; hashes/page counts are recorded in `docs/REQUIREMENTS_TRACEABILITY.md`.
- [x] All 28 requirement IDs have current evidence, status and external dependency.
- [x] No force-push, history rewrite, merge to `main`, email or external submission.

## Data and evaluation

- [x] Real X status is explicit: 0 accepted posts, 0 scored posts, no 180-day corpus.
- [x] Apify actor `apidojo/tweet-scraper` is identified; current Free plan prohibits API runs; no Actor run or purchase was made.
- [x] One bounded Tavily finance search and one bounded Exa news search were live-checked; see the provider verification report for timestamp/source results.
- [x] Exa CLI dispatch fixed and regression-tested after a pre-network TypeError was found; no Apify run was launched.
- [x] 180 Binance Vision BTCUSDT bars cover 2026-05-05 to 2026-10-31 UTC; 36 published archive checksums matched, with no missing or duplicate dates.
- [x] Six horizons, five folds, 100 OOS samples per model/horizon, 1,800 prediction rows, and the defined price-only strategy were freshly recomputed.
- [x] Price-only is worse than naive on mean MAE; no sentiment or profitability claim is made.
- [x] Binance Vision data and derived outputs have attribution/share-alike notices and are non-commercial only. Quote is USDT, not USD.
- [x] Old Coinbase-derived reports were removed from the current tree after terms review; Git history remains unchanged.

## Verification on the reviewed source tree

| Check | Result |
| --- | --- |
| Full pytest suite | Current count and command: [TEST_PLAN.md](../TEST_PLAN.md). |
| Ruff | Pass |
| Python compilation | Pass |
| Documentation validation | Pass: 102 relative links, 5 test-count claims, 28 requirement rows |
| Dataset registry validation | Pass: 12 records structurally valid |
| Apify validate-only preflight | Pass; no network call and no paid run |
| Binance archive builder | Pass: 36 published checksum matches, 180 complete bars |
| Fresh walk-forward evaluation | Pass: 5 folds, 6 horizons, per-row predictions and risk metrics |
| Clean extraction, secret scan and final ZIP integrity | Pass: final package verification reports exact file count, size and digest in output handoff |
| GitHub Actions for final pushed SHA | Checked after normal push; exact Actions link is in final response |

## Package

- [x] Package includes source, tests, canonical docs, reproducibility guide, all permitted Binance source archives/checksums, evaluation artifacts, offline HTML dashboard, one-page outlook and demo script.
- [x] Package excludes `.git`, `.env`, secrets, private databases, caches, virtual environments and unrelated files.
- [x] Assessment PDFs are not copied into the package.
- [x] Package path: `outputs/x-sentiment-price-predictor-submission.zip` in this Codex task.
- [x] SHA-256 and archive entry count are recorded in the adjacent `.sha256` file and final handoff.

## External blockers and submission

- [x] Remaining decisions and exact employer actions are listed in `REMAINING_BLOCKERS.md`.
- [x] Email draft is prepared but unsent; no credentials are included.
- [x] Final verdict: **SUBMISSION READY WITH EXTERNAL BLOCKERS**. Real X sentiment and exact BTC-USD acceptance remain external dependencies.
