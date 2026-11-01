# Apify X Actor review

**Status: candidate review only. No Actor is selected, approved or run.** This page
records what was observed on 2026-11-01 and the exact checks that remain before a
paid collection. Store pages and prices can change; re-check them in the console.

## Minimum contract

An acceptable Actor must provide:

- stable post IDs, original post text, and timezone-aware creation timestamps;
- usable ticker, cashtag and keyword search modes over an explicit historical range;
- at least 180 days of reach for Bitcoin-related queries;
- available likes, reposts and author follower counts, with missing values left null;
- a documented pricing model, free/paid plan requirements and retention terms;
- an input schema that the local adapter can pass through unchanged.

## Candidate: `apidojo/tweet-scraper` (Tweet Scraper V2)

Observed on the public store page on 2026-11-01:

| Item | Observed value | Verification still needed |
|---|---|---|
| Actor ID | `apidojo/tweet-scraper` | Confirm it resolves in the account console |
| Price | From $0.40 per 1,000 tweets | Confirm the account's actual price and plan |
| Free plan | Demo mode only: 5 runs/month, 10 items per run, no API | Confirm on the account |
| Query input | `searchTerms` supports advanced search, including `since:`/`until:` | Test one 7-day query |
| Minimum result | Each query must return at least 50 tweets | Confirm with a pilot |
| Output fields | `id`, `url`, `text`, `createdAt`, `likeCount`, `retweetCount`, `author.followers` | Confirm `viewCount` and any offset fields on a real item |
| Historical range | Store page advertises a search data range; recall is not guaranteed | Measure daily coverage in a pilot |
| Limits | Max 1 concurrent run; no single-tweet or conversation scraping | Confirm for the planned run |

Source: <https://apify.com/apidojo/tweet-scraper>

The public output example shows an RFC-2822-style `createdAt` value with a UTC
offset and nested `author` fields. The local adapter already accepts common aliases
for IDs, text, timestamps, counts and author followers, but aliases are not a
schema guarantee. A real item must be inspected before a full run.

## Other candidates

The store lists alternatives such as `xquik/x-tweet-scraper` with per-row pricing.
They were not reviewed in detail and are not recommended here. Any alternative must
pass the same contract and a pilot. Do not infer an Actor ID from an adapter or a
blog post.

## Required review before a paid run

- [ ] Actor ID resolves in the account; owner and last-modified date recorded.
- [ ] Pricing, plan requirement, free-tier limits and retention terms recorded.
- [ ] Input schema captured from the Actor's own Input tab.
- [ ] Output schema captured from one 10-item paid smoke test.
- [ ] Ticker, cashtag and keyword queries each return usable rows.
- [ ] A 7-day pilot measures posts/day, field completeness, duplicates and actual spend.
- [ ] A hard USD cap and item cap are approved in writing.
- [ ] The source's terms are accepted for collection, retention and reporting.
- [ ] The availability basis is decided before the full run (see `DATA_POLICY.md`).

## Cost planning

At the observed $0.40 per 1,000 tweets, data cost alone is roughly $0.80 for 2,000
posts, $4.00 for 10,000 and $20.00 for 50,000. The Apify plan price is separate and
must be confirmed in the console. A 7-day pilot is the cheapest way to measure
recall and true cost before committing to the full 180-day window.

## What a green preflight does not prove

`scripts/smoke_test_apify_x.py --validate-only` proves only that a local JSON file
satisfies the project contract. It does not prove the Actor is available, that the
queries return enough rows, that the historical window is covered, that the fields
match, or that the price is correct.
