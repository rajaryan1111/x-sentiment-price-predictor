# Evaluator demo script (5–7 minutes)

## Before the demo

Clone the final branch and install the project using the commands in [REPRODUCIBILITY.md](REPRODUCIBILITY.md). No credentials are needed. Keep the repository README, [requirement matrix](../docs/REQUIREMENTS_TRACEABILITY.md), and the historical evaluation report open.

## 0:00–0:45 — State the research question

Explain that the assignment asks whether X sentiment improves multi-horizon price forecasting beyond price-only baselines. The implementation is ready to evaluate that question, but there are no accepted X posts in the measured historical run, so there is no sentiment result or improvement claim.

## 0:45–1:30 — Show the design and leakage rules

Show `ARCHITECTURE.md`, `DATA_POLICY.md`, and `MODEL_PLAN.md`. Highlight UTC cutoffs, completed prices, distinct event/observed times, purged chronological folds, and missing sentiment remaining null. News is kept out of model features under the current conservative interpretation.

## 1:30–2:15 — Show local verification

Run:

```bash
python -m pytest -q -ra
python -m ruff check src tests scripts
python scripts/validate_docs.py
python scripts/validate_dataset_registry.py
```

Read exact counts from `FINAL_SUBMISSION_CHECKLIST.md`. These checks verify offline behavior and project consistency, not live provider access or forecast profitability.

## 2:15–3:00 — Demonstrate safe data handling

Run the offline demo input generator and the Apify preflight from `REPRODUCIBILITY.md`. Point out that the demo labels its data synthetic. The preflight reports ticker, cashtag, and keyword modes while confirming that it made no network call and launched no paid Actor.

## 3:00–4:00 — Run the synthetic pipeline

Use the `xsentiment run` command from the reproducibility guide. Show the generated `manifest.json`, `metrics.json`, `predictions.jsonl`, `evaluation-report.md`, `outlook.md`, and `sentiment-vs-price.svg`. State clearly that demo numbers and posts are synthetic software fixtures, not evidence about BTC or X.

## 4:00–5:00 — Show the historical result with its limits

Open `reports/btc-usd-180d/evaluation-report.md` and `metrics.json`. Explain that these committed artifacts record 180 BTC-USD candles, zero X posts, and zero scored posts. The stored aggregate metrics show naive mean MAE $1,828.36 and price-only mean MAE $2,264.62; sentiment-plus-price is identical because no sentiment was available. The raw snapshot and per-prediction rows are not in the package, so this audit did not recalculate those historical results from raw inputs.

## 5:00–6:00 — Show the visualization and one-page outlook

Open the committed SVG and `outlook.md`. The price panel has historical values; sentiment panels explicitly say no scored posts are available. Do not replace these empty states with synthetic numbers. The deliverable is generated report/chart output, not an interactive web dashboard.

## 6:00–7:00 — State external blockers and close

Show `REMAINING_BLOCKERS.md`. Explain that a permitted X source, 180-day corpus, employer-approved terms and cost ceiling, secure credential channel, and several convention decisions are still needed. No paid Apify scrape or live news request was executed. No email was sent.
