# Final handoff — 2026-11-01

## Repository and review

- Repository: https://github.com/rajaryan1111/x-sentiment-price-predictor
- Final branch: `feat/availability-basis-and-preflight`
- PR #14: https://github.com/rajaryan1111/x-sentiment-price-predictor/pull/14
  (keep open as draft; no merge to `main`)
- The implementation commits are in PR #14, and the PR source branch is advanced
  only by normal fast-forward. The exact final commit SHA, green checks, package
  digest and delivery status are recorded in the external release handoff generated
  after verification. No force-push or history rewrite was performed.

## Current evidence

The current report is freshly recomputed from 180 Binance Vision Spot BTCUSDT daily
bars covering 2026-05-05 through 2026-10-31 UTC. All 36 source ZIPs matched the
published checksums; there are no missing dates or duplicates. The package contains
the source ZIPs/checksums, normalized snapshot, manifest, metrics, per-row
predictions, report, one-page outlook, offline HTML dashboard and SVG chart.

The quote currency is USDT, not USD. Source data and derived artifacts are
CC BY-NC-SA 4.0, attributed to Binance Vision and non-commercial only. Across five
walk-forward folds and 100 OOS samples per horizon, naive mean MAE is 1,824.23 USDT
and price-only mean MAE is 2,378.50 USDT. There were zero accepted X posts and zero
scored posts; sentiment contribution is not identifiable. The price-only strategy
reports Sharpe 1.124, Sortino 2.431 and maximum drawdown 5.885%; these are
sample-specific research metrics, not performance claims.

One bounded Tavily finance search and one bounded Exa news search were live-checked.
Tavily returned one result with a malformed publication timestamp, withheld by the
adapter; Exa returned one result with publication and source metadata. The Exa CLI
dispatch was fixed and regression-tested. Apify authentication and Actor metadata
were verified, but no Actor scraping run was launched and no scraping credits were
used. Free-plan restrictions and incomplete historical search coverage remain
limitations. No Coinbase data was fetched in this execution. See
[provider verification](../docs/PROVIDER_VERIFICATION_2026-11-01.md).

## Verification

The current count is 228 tests, recorded in [TEST_PLAN.md](../TEST_PLAN.md); Ruff
and Python compilation passed; documentation validation and dataset registry
validation passed for 28 requirements and 12 records respectively; Apify preflight reported
`valid: true`, `network_call_made: false`, `paid_run_launched: false`. The clean
package extraction, secret scan and exact pushed-commit CI result are release checks
recorded in the final response and package checksum sidecar.

## Package and employer materials

- Evaluation PDF: [FINAL_EVALUATION_REPORT.pdf](FINAL_EVALUATION_REPORT.pdf)
- ZIP: `outputs/x-sentiment-price-predictor-submission.zip`
- SHA-256 sidecar: the adjacent `.sha256` file; exact digest and entry count are in
  the external release handoff. The Gmail connector cannot attach files, so the
  curated ZIP requires a separate delivery method.
- Attribution and package details: [PACKAGE_MANIFEST.md](PACKAGE_MANIFEST.md) and
  `reports/btcusdt-180d/ATTRIBUTION.md`.
- Email: the final message is sent only after the verified PR head, green CI,
  integrity-checked PDF/ZIP, and accurate limitations pass the release gates. No
  credentials are included.

## Remaining external work

See [REMAINING_BLOCKERS.md](REMAINING_BLOCKERS.md). Employer decisions or access
are needed for a rights-cleared 180-day X corpus/Actor, the exact USD versus USDT
price source, any Exa live requirement, the `n+0` convention, the absolute deadline,
and a secure credential channel. Do not use the Binance-derived report commercially.

## Verdict

**SUBMISSION READY WITH EXTERNAL BLOCKERS.** Locally achievable provider, modeling,
evaluation, documentation, test, and package work has been completed. The mandatory
real X sentiment experiment and exact BTC-USD acceptance cannot be claimed complete
without external source approval and data.
