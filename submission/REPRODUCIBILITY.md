# Reproducibility guide

The repository supports a fully offline reproduction using clearly labelled synthetic inputs. Provider access is optional and gated. Never treat synthetic demo metrics as market evidence.

## 1. Extract or clone and install

For a Git clone with exact revision provenance:

```bash
git clone https://github.com/rajaryan1111/x-sentiment-price-predictor.git
cd x-sentiment-price-predictor
git checkout feat/availability-basis-and-preflight
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev,storage]'
```

For the submission ZIP, extract it and enter the single `x-sentiment-price-predictor/` directory. Install the same project extras from that directory. The ZIP intentionally has no `.git`; run manifests will therefore record `code_revision: unavailable` with a reason rather than inventing a SHA. The test suite supports this source-archive state.

No API key is needed for offline tests or the demo. `.env.example` contains placeholders; do not copy secrets into a tracked or packaged file.

## 2. Offline verification

Run from the repository root (Git clone or clean ZIP extraction):

```bash
python -m pytest -q -ra
python -m ruff check src tests scripts
python -m compileall -q src tests scripts
python scripts/validate_docs.py
python scripts/validate_dataset_registry.py
```

The provenance tests verify the exact Git SHA in a clone and an explicit unavailable state in a ZIP extraction. Current counts are in `FINAL_SUBMISSION_CHECKLIST.md` after the final run.

## 3. Reproduce the labelled synthetic demo

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

The output includes a manifest, metrics, per-row predictions, evaluation report, outlook and SVG chart. Run the pipeline twice into separate output directories and compare those six files byte-for-byte. The generated values are synthetic and must not be presented as historical market or sentiment results.

## 4. Safe Apify preflight (no request and no spend)

```bash
python scripts/smoke_test_apify_x.py \
  --input-json config/apify_actor_input.example.json --validate-only
```

Expected: `valid: true`, query modes `ticker`, `cashtag`, `keyword`, `network_call_made: false`, and `paid_run_launched: false`. This validates local shape only; it does not prove the candidate Actor accepts those inputs or terms.

A paid Actor run is blocked until an Actor and license are approved, actual billing is reviewed, item/USD caps are agreed, a secure credential channel is supplied, and the user explicitly authorizes the operation. See [APIFY_X_SETUP.md](../docs/APIFY_X_SETUP.md) and [REMAINING_BLOCKERS.md](REMAINING_BLOCKERS.md).

## 5. Historical real-price artifacts

The historical run under `reports/btc-usd-180d/` records 180 Coinbase BTC-USD daily bars and aggregate metrics from 2026-10-26. The raw price snapshot and `predictions.jsonl` are not in the repository or ZIP. The recorded MAE and strategy metrics can be inspected in the committed `metrics.json`; this is not enough to independently retrain or recompute those results from raw rows. A new price retrieval and evaluation would be a new run, not a reproduction of the committed raw snapshot.

## 6. Optional provider calls

`fetch-news` is the only Tavily live-capable path and requires an explicit confirmation flag. It was not called in this verification. Exa is not integrated. Apify live ingestion is also not performed. Do not configure a real key or run a paid command without employer approval, an agreed cost ceiling, and explicit user authorization.
