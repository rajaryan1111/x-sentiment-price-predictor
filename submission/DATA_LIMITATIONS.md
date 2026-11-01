# Data limitations and external blockers

See [REMAINING_BLOCKERS.md](REMAINING_BLOCKERS.md), the
[28-ID requirement matrix](../docs/REQUIREMENTS_TRACEABILITY.md), and the
[current execution status](../docs/FINAL_EXECUTION_STATUS_2026-11-01.md).

## X and sentiment

- No accepted recent X corpus exists in this checkout: 0 posts accepted and 0
  scored. Synthetic fixtures remain test-only and are never represented as posts.
- Apify actor `61RPP7dywgiy0JPD0` resolves to `apidojo/tweet-scraper`, but current
  Free-plan policy prohibits its API use. No Actor run was launched. A permitted
  export or explicit paid-plan/source approval and spend cap is required.
- The linked dataset document is a list of candidate links, not a tweet corpus.
  Available public candidates do not establish current 180-day coverage or terms.

## Price source and license

- Current report uses 180 Binance Vision BTCUSDT Spot daily bars (USDT quote) from
  2026-05-05 through 2026-10-31 UTC. All 36 source ZIP checksums match; there are
  no missing dates or duplicates. Source archives, snapshot, predictions and
  derived report artifacts are in `reports/btcusdt-180d/`.
- Binance Vision data and derivatives are CC BY-NC-SA 4.0, with attribution and
  same-license obligations and non-commercial use only. This is not exact BTC-USD.
- Coinbase Market Data terms restrict model training/validation/benchmarking and
  redistribution of derived works without written consent. No Coinbase data was
  fetched in this execution; earlier derived artifacts are removed from the current
  tree but remain in prior Git history.

## News providers

- Tavily is bounded, dated, live-checked once and context-only. Its one-result smoke
  response had a malformed publication timestamp, which the adapter withheld.
- Exa adapter and CLI are implemented and tested; one bounded live request returned
  one dated result with source metadata. See the provider verification report for
  costs and the ongoing-use limitation.

## Model and display limits

- With no posts, sentiment features are missing and the sentiment candidate is
  unidentifiable. The price-only candidate's mean MAE is worse than naive; no
  accuracy or profitability claim is made.
- The generated HTML dashboard is offline and non-interactive; empty sentiment panels are
  labelled. The deterministic synthetic demo is for software behavior only.
- The `n+0` convention remains an employer-unconfirmed default. The PDF also gives
  conflicting relative deadlines; the exact calendar due date must be clarified.

The recipient printed in the assessment is `gilad@crowdwisdomtrading.com` and has
not been independently mailbox-verified. The final message and delivery status are
recorded in the external release handoff.
