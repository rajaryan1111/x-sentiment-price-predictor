# Demo script — x-sentiment-price-predictor

A 10-minute walkthrough for an evaluator or the employer, from install to
fictional-free conclusions. All commands are in
[REPRODUCIBILITY.md](REPRODUCIBILITY.md); this page adds the narrative.

## 1. What this project is (1 minute)

- Assignment: predict BTC-USD close price at multiple horizons and compare a
  price-only model with a sentiment-enhanced model built from X (Twitter)
  posts, evaluated honestly over 180 days.
- Status summary in one sentence: the entire software pipeline, validation
  stack and reporting apparatus are implemented and verify offline; the
  real X corpus cannot be collected yet because no approved source, token,
  Actor choice or spend cap exists (blockers B1–B3, B10). The empirically
  demonstrated dataset is a 180 day BTC-USD price record with **no** X
  posts, so the sentiment comparison is honestly reported as unmeasured.

## 2. Install and full offline verification (2–3 minutes)

```bash
git clone https://github.com/rajaryan1111/x-sentiment-price-predictor
cd x-sentiment-price-predictor
git checkout feat/availability-basis-and-preflight
python3.11 -m venv .venv && source .venv/bin/activate
python -m pip install -e '.[dev,storage]'

python -m pytest -q          # 209 offline tests at the 2026-11-01 verification; TEST_PLAN.md is authoritative
python -m ruff check src tests scripts
python scripts/validate_docs.py            # 28-row traceability matrix re-validates rules
python scripts/validate_dataset_registry.py
```

Point out: every number later shown comes from these same commands, not from
a saved notebook.

## 3. Deterministic end-to-end pipeline demo (3 minutes)

```bash
python scripts/make_offline_demo.py \
  --out reports/generated/offline-demo-inputs/prices.json \
  --posts-out reports/generated/offline-demo-inputs/posts.jsonl \
  --generated-at 2026-10-27T00:00:00+00:00
python -m xsentiment run --prices reports/generated/offline-demo-inputs/prices.json \
  --posts reports/generated/offline-demo-inputs/posts.jsonl \
  --out reports/generated/offline-demo --now 2026-07-30T00:00:00+00:00 \
  --input-note "synthetic offline demo from scripts/make_offline_demo.py"
```

Then open and narrate:

| File | Talking point |
| --- | --- |
| `reports/generated/offline-demo/manifest.json` | code revision, input hashes, library versions, consolidated availability basis — full replay |
| `…/evaluation-report.md` | the six-horizon × three-model table, warnings, per-fold rows, exclusions |
| `…/metrics.json` | MAE/RMSE per (model, horizon), sample counts, strategy metrics with fee/annualisation assumptions |
| `…/sentiment-vs-price.svg` | model comparison chart with an honest "sentiment-unavailable" panel on synthetic data |
| `…/predictions.jsonl` | one row per (cutoff, horizon, model), plus fold, exclusions, target values |
| `…/outlook.md` | the one-page outlook, refresh warnings included |

Emphasize: repeatedly running this demo produces identical artifacts — the
demo also demonstrates the strict post-availability guard, since posts are
restricted to their own historical window and the sentiment series is still
reported truthfully (as unavailable or sparse Hollander-Hinkle ICB).

## 4. Synthesis of a real 180-day price run (2 minutes)

```bash
python -m xsentiment fetch-prices --start 2026-04-29 --end 2026-10-26 \
  --out data/btc-usd-180d-snapshot.json
python -m xsentiment run --prices data/btc-usd-180d-snapshot.json \
  --out reports/regenerated-btc-usd-180d --now 2026-10-26T00:00:00+00:00
```

Point at the committed [reports/btc-usd-180d/evaluation-report.md](../reports/btc-usd-180d/evaluation-report.md)
and talk through the three headline facts:

1. **Naive beats both fitted models** (mean MAE 1828 vs 2265). A run
   claiming the fitted models beat naive would be a red flag — check fairness
   of splits instead.
2. **Sentiment adds nothing measurable yet** — because there are no posts
   (`sentiment_price == price_only` per horizon; metrics.json `warnings`).
   The single-solid-single row exists to make the missing-signal case
   inspectable, not to game numbers.
3. **Strategy metrics exist with assumptions** — fee rate, 365-day
   annualisation, 30-observation minimum for risk ratios; the `naive`
   strategy's Sharpe/Sortino are `null` with an explicit reason rather than
   fabricated.

## 5. Apify wiring without risk (1 minute)

```bash
python scripts/ingest_apify_x.py --help
python scripts/smoke_test_apify_x.py \
  --input-json config/apify_actor_input.example.json --validate-only   # zero-cost configuration check
```

Show [docs/APIFY_X_SETUP.md](../docs/APIFY_X_SETUP.md) and
[docs/ACTOR_REVIEW.md](../docs/ACTOR_REVIEW.md): the Actor, the pricing
review, bounded run limits, optional validate-only preflight, staged
ingestion once the token is handed over privately, and the hard rule that no
paid call is made until those are in place.

## 6. Close (1 minute)

- Hand over [SUBMISSION_README.md](SUBMISSION_README.md) and
  [REQUIREMENT_TRACEABILITY.md](REQUIREMENT_TRACEABILITY.md) so every claim
  lands on a file, a test or a run manifest.
- State the honest verdict: implementation and offline evidence are
  complete and reproducible; the empirical sentiment conclusion awaits the
  approved corpus — exactly as
  [DATA_LIMITATIONS.md](DATA_LIMITATIONS.md) and
  [docs/EXTERNAL_BLOCKERS.md](../docs/EXTERNAL_BLOCKERS.md) record.
- Do not promise the assignment is complete, and do not overstate what has
  been measured.
