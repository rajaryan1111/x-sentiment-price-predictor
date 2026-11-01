# Employer email draft — NOT SENT

**To:** gilad@crowdwisdomtrading.com
**Subject:** X Sentiment Price Predictor — internship assignment deliverables

Hello Gilad,

I have prepared the X Sentiment Price Predictor repository and evaluation materials for the internship assignment.

- **Repository:** https://github.com/rajaryan1111/x-sentiment-price-predictor
- **Branch:** https://github.com/rajaryan1111/x-sentiment-price-predictor/tree/feat/availability-basis-and-preflight
- **Evaluation report:** `submission/FINAL_EVALUATION_REPORT.md` on that branch
- **Reproducibility and demo:** `submission/REPRODUCIBILITY.md` and `submission/DEMO_SCRIPT.md`
- **CI:** current successful run and exact SHA are listed in [the final handoff](FINAL_HANDOFF.md).

The repository implements a reproducible BTC-USD daily forecasting pipeline for six horizons (`n+0` through `n+5`), price and sentiment feature handling, naive/price-only/sentiment-plus-price model comparison, purged walk-forward evaluation, strategy risk metrics, database persistence and joins, chart/report generation, and bounded Apify and Tavily integrations with offline tests.

The committed historical price report records 180 BTC-USD daily candles and zero accepted X posts or scored sentiment posts. In that artifact, naive persistence has mean MAE $1,828.36 and the price-only ridge model $2,264.62. The sentiment-plus-price result is identical to price-only because sentiment was unavailable; it is not evidence that sentiment improves prediction. The report's historical metric artifacts are included, but the raw price snapshot and prediction rows are not in the repository, so this audit did not independently recompute those values from raw records.

Current local verification is offline. No live Apify Actor was run and no paid scrape or live Tavily/Exa request was made. Exa is not integrated. The local Apify/Tavily credential entries are not employer-approved access, and no secret is included in the repository or package. To complete the real sentiment comparison, please confirm an approved X source/Actor and license, 180-day/query coverage, an item and USD spend cap, whether live Tavily news and Exa are required, and the intended `n+0` convention. If credentials are needed, please provide an approved secure private channel; I will not send secrets in plaintext email.

The assignment states both “within 1 week” and “5–7 days” without an absolute date. Please provide the due date and timezone, and let me know if a video or additional format is required. The address above is the recipient printed in the assignment PDF; I have not independently verified mailbox ownership.

This is a prepared draft only. **No email has been sent.**

Thank you,

Raj Aryan
