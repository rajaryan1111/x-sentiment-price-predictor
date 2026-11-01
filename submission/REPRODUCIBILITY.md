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

The output includes a manifest, metrics, per-row predictions, evaluation report, outlook, SVG chart and standalone offline `dashboard.html`. The integration suite repeats the pipeline and compares deterministic outputs. The generated values are synthetic and must not be presented as historical market or sentiment results.

## 4. Safe Apify preflight (no request and no spend)

```bash
python scripts/smoke_test_apify_x.py \
  --input-json config/apify_actor_input.example.json --validate-only
```

Expected: `valid: true`, query modes `ticker`, `cashtag`, `keyword`, `network_call_made: false`, and `paid_run_launched: false`. This validates local shape only; it does not prove the candidate Actor accepts those inputs or terms.

A paid Actor run is blocked until an Actor and license are approved, actual billing is reviewed, item/USD caps are agreed, a secure credential channel is supplied, and the user explicitly authorizes the operation. See [APIFY_X_SETUP.md](../docs/APIFY_X_SETUP.md) and [REMAINING_BLOCKERS.md](REMAINING_BLOCKERS.md).

## 5. Reproduce the licensed BTCUSDT evaluation

The directory `reports/btcusdt-180d/source/` includes the 36 official Binance
Vision archive ZIPs and their published `.CHECKSUM` sidecars. These data and all
derived files are CC BY-NC-SA 4.0, attributed to Binance Vision and non-commercial
only; see `reports/btcusdt-180d/ATTRIBUTION.md`.

```bash
python scripts/build_binance_snapshot.py \
  --archives-dir reports/btcusdt-180d/source \
  --start 2026-05-05 --end 2026-11-01 \
  --out /tmp/btcusdt-180d-snapshot.json

python -m xsentiment run \
  --prices /tmp/btcusdt-180d-snapshot.json \
  --asset BTCUSDT \
  --out /tmp/btcusdt-180d-run \
  --min-train 60 --test-size 20 --embargo 5
```

This is BTCUSDT (USDT quote), not exact BTC-USD. It contains no X posts and cannot
measure sentiment contribution. The exact generated input and outputs, including the offline HTML dashboard, from the
verified run are also included under `reports/btcusdt-180d/`.

## 6. Optional provider calls

`fetch-news` selects Tavily or Exa and requires an explicit `--confirm-live-call`
flag. One dated Tavily finance request was performed using existing free allowance;
it returned five results without publication dates. Exa has no configured key and
is only mock-verified. No Apify Actor run was performed; the current account Free
plan forbids API use. Do not run a paid collection without employer approval and an
explicit cap.
