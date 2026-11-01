# Reproducibility

Python 3.11+. Requires no API key for anything offline; every network-capable
command is explicit and gated.

## Setup

```bash
git clone https://github.com/rajaryan1111/x-sentiment-price-predictor.git
cd x-sentiment-price-predictor
git checkout feat/availability-basis-and-preflight   # evaluator branch; PR #14 alternative below
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev,storage]'
```

Copy `.env.example` to `.env` if you want configuration anywhere; all values
are placeholders. **Never put real tokens in `.env`-tracked files or in Git.**
Optional credentials (`APIFY_API_TOKEN`, `APIFY_ACTOR_ID`, `TAVILY_API_KEY`,
`EXA_API_KEY`) remain unset unless you have authorized sources.

## Verify the project first (about 1 minute)

```bash
python -m pytest -q                      # 209 offline tests at the 2026-11-01 verification; TEST_PLAN.md is authoritative
python -m ruff check src tests scripts
python -m compileall -q src tests scripts
python scripts/validate_docs.py          # links + 28-row traceability matrix
python scripts/validate_dataset_registry.py
git status --ignore-submodules -s        # should be clean (untracked local data only)
```

## Reproduce the labelled synthetic demo end to end

This proves the whole pipeline runs on your machine with no credentials:

```bash
python scripts/make_offline_demo.py \
  --out reports/generated/offline-demo-inputs/prices.json \
  --posts-out reports/generated/offline-demo-inputs/posts.jsonl \
  --generated-at 2026-10-27T00:00:00+00:00

python -m xsentiment run \
  --prices reports/generated/offline-demo-inputs/prices.json \
  --posts reports/generated/offline-demo-inputs/posts.jsonl \
  --out reports/generated/offline-demo \
  --now 2026-07-30T00:00:00+00:00 \
  --input-note "synthetic offline demo from scripts/make_offline_demo.py"
```

Six artefacts appear in `reports/generated/offline-demo/`:
`manifest.json` (code revision, input hashes, library versions, input
lineage), `metrics.json`, `predictions.jsonl`, `evaluation-report.md`,
`outlook.md` and `sentiment-vs-price.svg`. Run it twice; both runs must match
byte for byte.

## Reproduce the historical real-price run

The committed manifest in `reports/btc-usd-180d/` pins the run. The raw price
snapshot is intentionally not committed; refetch it:

```bash
python -m xsentiment fetch-prices \
  --start 2026-04-29 --end 2026-10-26 \
  --out data/btc-usd-180d-snapshot.json

python -m xsentiment run \
  --prices data/btc-usd-180d-snapshot.json \
  --out reports/regenerated-btc-usd-180d \
  --now 2026-10-26T00:00:00+00:00 \
  --input-note "refetch of the committed BTC-USD 180d snapshot"
```

`fetch-prices` needs outbound HTTPS to Coinbase. The committed manifest records
`provenance.price_snapshot_sha256` =
`09ce225a405aea390ae2f21c72634da1211a321aed1b39b52febfadf64083f75` for the
original 2026-10-26 snapshot. Your refetched file will NOT be byte-identical to
that hash: every snapshot embeds the UTC moment of its own fetch in
`fetched_at`, by design. Compare at the data level instead — the
2026-11-01 clean-environment verifier confirmed a fresh refetch is byte-equal to
a second refetch on `candles` (180/180 rows) and reproduced every committed
forecast metric exactly with `--now 2026-10-26T00:00:00+00:00`.Output writes to `reports/regenerated-btc-usd-180d/`; the original committed
report is never overwritten.

## Persisted-database path (R15)

```bash
python -m xsentiment persist \
  --prices <prices.json> --posts <posts.jsonl> \
  --database-url sqlite+aiosqlite:///./data/xsentiment.db
python -m xsentiment run --database-url sqlite+aiosqlite:///./data/xsentiment.db \
  --out reports/generated/persisted-run --now 2026-07-30T00:00:00+00:00
```

Writes are idempotent upserts; the manifest records
`input_source = persisted_storage`.

## News (optional, context only)

`fetch-news` is the only live-capable news command and performs exactly one
bounded call, gated behind `--confirm-live-call`; without an API key or the
flag it does nothing. Output JSONL feeds `run --news-file` offline; news never
enters model features.

```bash
TAVILY_API_KEY=<your-key> python -m xsentiment fetch-news \
  --query "Bitcoin" --out data/news.jsonl --confirm-live-call
python -m xsentiment run --prices <prices.json> --posts <posts.jsonl> \
  --news-file data/news.jsonl --out reports/generated/news-run
```

## Optional Apify X collection (blocked — never run without authorization)

Judge the wiring without spending anything:

```bash
python scripts/smoke_test_apify_x.py \
  --input-json config/apify_actor_input.example.json --validate-only    # no network call
```

Bounded ingestion — a real Actor run is prohibited until the employer selects
the Actor, reviews terms and prices, sets a hard item/USD cap and hands over
the token privately (B1/B3/B10; see
[docs/APIFY_X_SETUP.md](../docs/APIFY_X_SETUP.md) and
[docs/ACTOR_REVIEW.md](../docs/ACTOR_REVIEW.md)):

```bash
python scripts/ingest_apify_x.py \
  --actor "$APIFY_ACTOR_ID" \
  --q '$BTC OR BTC OR bitcoin' \
  --query-mode mixed --start 2026-05-05 --end 2026-11-01 \
  --max-items 10000 --max-spend-usd 50 --confirm-paid-run \
  --out data/x-posts-180d.jsonl --manifest data/x-posts-180d.manifest.json
```

The pipeline then continues automatically: normalize →
`python scripts/profile_local_x_dataset.py <jsonl>` → `xsentiment persist` →
`xsentiment run --database-url`. Once accepted posts are ingested this way,
the historical evaluation regenerates the four key artefacts honestly and the
sentiment comparison becomes measurable.
