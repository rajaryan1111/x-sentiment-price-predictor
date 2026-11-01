# Context-only news providers

News results are optional context for the one-page outlook. They are not model
features. `fetch-news` is an explicit live operation; it requires
`--confirm-live-call`, reads credentials only from the environment or ignored
`.env`, makes one bounded request, applies the response-size limit, and never
automatically retries.

## Tavily

Set `TAVILY_API_KEY`, then run one bounded search:

```bash
python -m xsentiment fetch-news \
  --provider tavily \
  --topic finance \
  --query "Bitcoin BTC market news" \
  --start-date 2026-10-26 --end-date 2026-11-01 \
  --max-results 5 --out data/news-context.jsonl \
  --confirm-live-call
```

The date range is inclusive UTC calendar dates. Tavily's
`include_published_date` and `filter_by_published_date` fields are requested when
using a range. Missing or timezone-less result dates stay null; do not infer a
publication time from titles or URLs.

## Exa

Set `EXA_API_KEY` and choose `--provider exa`. The adapter uses the official
`POST https://api.exa.ai/search` contract with category `news`, typed response
validation, optional published-date bounds, timeout and response-size limits, and
the `x-api-key` header. It uses no answer synthesis or result-page extraction.
No Exa key was available for live verification in the current audit.

## Offline handoff

Both providers write the same normalized JSONL shape with publication timestamp or
an explicit unavailable note, retrieval time, provider, source, sanitized URL and
payload hash. Consume it with `xsentiment run --news-file PATH`; this path makes no
network call. A provider response missing publication dates remains useful context,
but it cannot be claimed as publication-dated or used as a point-in-time feature.

Official API references:

- [Tavily Search API](https://docs.tavily.com/documentation/api-reference/endpoint/search)
- [Exa Search API](https://exa.ai/docs/reference/search)
