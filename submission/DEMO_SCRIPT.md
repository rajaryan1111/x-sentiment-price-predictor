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

Open `reports/btcusdt-180d/evaluation-report.md`, `metrics.json`, `predictions.jsonl`, and `outlook.md`. Explain that these files record 180 Binance Vision BTCUSDT bars (USDT quote), zero X posts, five walk-forward folds, and 100 OOS samples per horizon. Naive mean MAE is 1,824.23 USDT; price-only is 2,378.50 USDT (30.38% worse); sentiment-plus-price is identical because no sentiment was scored. The raw source archives, published checksums and exact snapshot are included. These data-derived files are CC BY-NC-SA 4.0 and non-commercial only.

## 5:00–6:00 — Show the visualization and one-page outlook

Open `reports/btcusdt-180d/dashboard.html`, `sentiment-vs-price.svg`, and `outlook.md` for the committed measured run. The dashboard is standalone and offline. Sentiment panels explicitly say no scored posts are available. Do not replace these empty states with synthetic numbers.

## 6:00–7:00 — State external blockers and close

Show `REMAINING_BLOCKERS.md`. Explain that a permitted X source, 180-day corpus, employer-approved terms and cost ceiling, secure credential channel, and several convention decisions are still needed. No paid Apify scrape was executed. Final email and delivery status are recorded in the external release handoff.
