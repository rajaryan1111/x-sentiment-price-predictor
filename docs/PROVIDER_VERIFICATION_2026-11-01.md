# Provider verification — 2026-11-01

## Results

| Provider | Authentication/configuration | Live test | Historical capability | Limitations |
|---|---|---|---|---|
| Apify `apidojo/tweet-scraper` | Authenticated, non-run Actor metadata GET returned HTTP 200 and resolved the configured owner/name. `.env` is Git-ignored; all four expected settings loaded without printing values. Guessed API `input-schema` and `readme` subpaths returned 404; the public pages were inspected instead. | Not run, as required. No Actor launch, dataset read, or scraping credit used. | The public Actor README accepts `since:`/`until:` advanced-search terms and advertises an unlimited search range. This is date-filtered search, not a completeness guarantee: the same page warns that `until` can reduce results and X search/filtering may omit posts. | Free-plan API runs are disabled; the Actor says each query must return at least 50 posts, max one concurrent run and five batched queries. Listed price is $0.40/1,000 tweets. A full 3-query minimum would imply at least 150 returned rows ($0.06 in result charges), plus any required Apify plan; no account plan or spend was changed. |
| Tavily | `TAVILY_API_KEY` loaded through repository settings; no value displayed. | One finance search returned HTTP 200 and one normalized result. `published_at` was withheld because the provider timestamp was malformed. Retrieval time and URL were present (`finance.yahoo.com`); `source` was the generic `tavily` label. | Search date bounds apply to news results, not X posts. | Basic Search is documented as 1 credit per request. One request was made; account balance/usage after the call was not queried. Tavily lists $0.008/credit for pay-as-you-go. |
| Exa | `EXA_API_KEY` loaded through repository settings; no value displayed. | One `/search` request returned HTTP 200 and one normalized result, with publication time, retrieval time, source/author label (`Simon Mugo`) and URL (`www.investing.com`). | Search date bounds apply to news results, not X posts. | One request was made. Exa lists standard Search at $7/1,000 requests (about $0.007 for one) and free monthly credits; the account balance/actual deduction was not queried. |

### Apify input and output compatibility

The public Actor input schema documents `searchTerms`, `maxItems`, `sort`,
`tweetLanguage`, and `includeSearchTerms`. The following is the bounded input shape
for the repository's three required query modes; **it was inspected only and not
submitted**:

```json
{
  "searchTerms": [
    "BTC since:2026-05-05 until:2026-11-01",
    "$BTC since:2026-05-05 until:2026-11-01",
    "Bitcoin since:2026-05-05 until:2026-11-01"
  ],
  "maxItems": 150,
  "sort": "Latest",
  "tweetLanguage": "en",
  "includeSearchTerms": true
}
```

The public output example has `id`, `text`, `createdAt`, `likeCount`,
`retweetCount`, `viewCount`, and nested `author.followers`. The local
`normalize_apify_post` accepts these aliases and maps them to `XPostRecord`.
Retrieval time is set locally when an item is collected. It cannot be backdated:
posts fetched now do not become historically observable at earlier cutoffs.
Engagement/follower counts are current snapshots unless separately time-stamped.

Sources: [Actor README and pricing](https://apify.com/apidojo/tweet-scraper),
[Actor input schema](https://apify.com/apidojo/tweet-scraper/input-schema),
[Apify authenticated Get Actor API](https://docs.apify.com/api/v2/act-get),
[Tavily pricing](https://www.tavily.com/pricing), and
[Exa pricing](https://exa.ai/pricing).

### News/model boundary

`run --news-file` renders the normalized news as outlook context. News is not
passed to feature construction and does not change predictions or evaluation
metrics. Predictive sentiment still requires real, accepted X post records in
`--posts`; no such corpus is present. The complete live X-to-model path is therefore
**not reproducible yet**, even though the offline BTCUSDT price evaluation and the
two isolated news smoke calls are reproducible.

## Commands executed

Successful one-result smoke commands (outputs were written outside the repository
under `/var/folders/tg/7lnc6xmn7hdbbh6ms90fpjfw0000gn/T/xsentiment-provider-smoke-nwl1k9n8/`):

```bash
uv run python -m xsentiment fetch-news --provider tavily --topic finance --query 'Bitcoin BTC market news' --start-date 2026-10-30 --end-date 2026-11-01 --max-results 1 --out /var/folders/tg/7lnc6xmn7hdbbh6ms90fpjfw0000gn/T/xsentiment-provider-smoke-nwl1k9n8/tavily.jsonl --confirm-live-call
uv run python -m xsentiment fetch-news --provider exa --topic news --query 'Bitcoin BTC market news' --start-date 2026-10-30 --end-date 2026-11-01 --max-results 1 --out /var/folders/tg/7lnc6xmn7hdbbh6ms90fpjfw0000gn/T/xsentiment-provider-smoke-nwl1k9n8/exa.jsonl --confirm-live-call
```

The first Exa attempt failed locally with `TypeError` because the CLI passed the
Tavily-only `topic` argument to Exa; it failed before making an HTTP request. The
dispatch now passes `topic` only to Tavily, and the existing CLI test was tightened
to reject unexpected Exa arguments. The single successful Exa request above was the
only Exa provider request.

Validation commands:

```bash
uv run pytest -q tests/unit/test_fetch_news_cli.py::test_fetch_news_routes_exa_provider_and_date_bounds
uv run pytest -q
uv run ruff check .
uv run python scripts/validate_docs.py
uv run python scripts/validate_dataset_registry.py
```

On 2026-11-01, the full suite reported **220 passed**. The focused Exa routing test
and Ruff passed; documentation validation checked 109 links and 28 requirement
rows; dataset registry validation passed for 12 records.

## Changed files and next step

Changed: `src/xsentiment/main.py`, `tests/unit/test_fetch_news_cli.py`,
`README.md`, `DATA_POLICY.md`, `PHASES.md`, `PRD.md`,
`docs/EMPLOYER_CLARIFICATIONS.md`, `docs/FINAL_EXECUTION_STATUS_2026-11-01.md`,
`docs/FINAL_VERIFICATION_REPORT.md`, `docs/NEWS_SETUP.md`,
`docs/REQUIREMENTS_TRACEABILITY.md`, `submission/DATA_LIMITATIONS.md`,
`submission/EMPLOYER_EMAIL_DRAFT.md`, `submission/EXPERIMENT_METHODOLOGY.md`,
`submission/FINAL_EVALUATION_REPORT.md`, `submission/FINAL_HANDOFF.md`,
`submission/FINAL_SUBMISSION_CHECKLIST.md`, `submission/REMAINING_BLOCKERS.md`,
`submission/SUBMISSION_README.md`, and this report. No secrets or provider result
text were added to the repository. No commit or push was made.

Next, obtain a rights-cleared, employer-approved X export or explicit approval for
an Apify plan and spend limit. Then run one small approved coverage pilot, profile
the actual `createdAt` range and fields, and record real retrieval timestamps before
using any posts in point-in-time sentiment evaluation.
