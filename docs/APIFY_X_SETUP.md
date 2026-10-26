# Apify X ingestion setup

## Before any run

1. Choose an Actor in your Apify account and verify its current terms, pricing model, input schema, data retention rules and ability to collect the target BTC-related posts over the requested 180-day window using **ticker, cashtag and keyword searches**.
2. Check the Actor's output dataset in the Apify console using a tiny test first. Confirm stable post IDs, original creation timestamps (with UTC/EST offset information), actual text, likes, reposts, views, author follower counts and nested author fields. Field aliases supported by this adapter are common conventions, not a guarantee of a particular Actor's schema.
3. Agree on a maximum spend. The adapter sends Apify run options for `maxItems`, `maxTotalChargeUsd` and `timeout`. Apify documents these as run options; actual billing behavior depends on the Actor's pricing model/account. Do not rely on these controls instead of checking the Actor's pricing.
4. Never put an API token in the URL, code, JSON input file or Git. Configure `APIFY_API_TOKEN` in your private local environment or secret manager and `APIFY_ACTOR_ID` with the reviewed actor ID.

## Input configuration and query modes

Actor input schemas vary, so there is deliberately no universal default query payload. Create a **local, untracked** JSON file using the input schema shown by the reviewed Actor. Keep query dates explicitly bounded to the desired 180-day window and include the three search modes required by the brief: the asset ticker (for example `BTC`), the cashtag (for example `$BTC`) and relevant keywords (for example `Bitcoin`). Verify with the Actor's own documentation that the selected input fields actually implement all three modes; do not assume that one search field covers them. Do not include credentials in the payload.

Example shell configuration:

```bash
export APIFY_API_TOKEN='set-locally-without-sharing-it'
export APIFY_ACTOR_ID='owner~reviewed-actor-name'
```

Do not paste the token into chat or commit it. Prefer setting it through your own shell/secret manager rather than storing it in a tracked file.

## Adapter behavior

`ApifyXAdapter.run_and_fetch(...)` is explicit and never runs merely by importing the module. The caller must supply the Actor input plus an item cap, dollar cap and timeout. The initial POST is not automatically retried because a network timeout may leave a paid run's result ambiguous. In that case, inspect the Apify console before another attempt.

The adapter:
- passes the token as a Bearer header, never as a query parameter;
- applies explicit run item, cost and timeout options;
- caps response-body size and result item count;
- unwraps the documented `data` envelope for run responses while reading dataset items as the documented JSON array;
- normalizes common tweet ID/text/date/engagement field names;
- requires real ID, text and timezone-aware event timestamp;
- preserves engagement fields as null when the Actor did not return them;
- records retrieval time separately from event time;
- leaves sentiment unscored (null) until a separately specified sentiment model is configured;
- does not persist raw posts automatically.

No live Apify run is included in CI. Tests use mocked HTTP responses and incur no provider costs. A green test suite does not certify the Actor's current availability, legal terms, historical reach, or actual output schema.
