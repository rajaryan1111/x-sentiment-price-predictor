# X Sentiment Price Predictor

Research project for reproducible asset-price forecasting that evaluates whether timestamped X sentiment adds predictive value beyond price-only baselines.

> **Status:** Architecture scaffold only. No live ingestion, trained model, forecast, backtest, Sharpe ratio, Sortino ratio, or drawdown result is claimed yet.

## Design principles

- Separate ingestion, normalization, feature engineering, forecasting, validation, backtesting, and presentation.
- Preserve source identifiers, timestamps, retrieval time, and provenance for every external record.
- Enforce point-in-time feature availability and chronological/walk-forward evaluation to avoid leakage.
- Compare against transparent price-only baselines before claiming sentiment adds value.
- Keep credentials and private/raw datasets out of version control.
- Keep provider-specific APIs behind replaceable adapters.

## Planned package layout

- `src/xsentiment/config/`: environment-backed settings.
- `src/xsentiment/ingestion/`: provider interfaces and X, prices, and news adapters.
- `src/xsentiment/storage/`: database lifecycle, schema and repositories.
- `src/xsentiment/features/`: sentiment aggregation and price features.
- `src/xsentiment/models/`: baseline and forecast interfaces.
- `src/xsentiment/validation/`: time-aware split and leakage checks.
- `src/xsentiment/backtesting/`: strategy simulation and risk metrics.
- `src/xsentiment/reporting/`: output contracts and report assembly.
- `dashboard/`: future visualization application.
- `tests/`: offline unit tests and contract tests.
- `reports/`: generated reports (no secrets or private data).

## Quick start

Python 3.11+ is the initial target. The scaffold and dependencies will be finalized in the project setup phase.

```bash
cp .env.example .env
# Fill only credentials you are authorized to use.
python -m pip install -e ".[dev]"
pytest
```

The commands above describe the intended workflow; execution and provider integration will be enabled in subsequent implementation phases.

## Branching

- `main`: stable integration branch.
- `setup/project-scaffold`: repository structure, shared infrastructure patterns, and tooling.
- `feat/ingestion`: provider adapters and data contracts.
- `feat/modeling`: features, baselines, and forecasting.
- `feat/evaluation`: walk-forward validation and backtesting.
- `feat/dashboard-reporting`: charts, outlook, and reports.

Feature branches should be based on `main` and merged through pull requests after tests pass.

## Data and research integrity

Never commit API credentials, access tokens, raw X exports, proprietary datasets, or large generated artifacts. Do not label fixture/demo data as live data. Forecast horizons and return definitions must be explicitly documented. Backtest performance metrics must be calculated from timestamped out-of-sample strategy returns and disclose costs and assumptions.

## GraphOne reuse note

This project adapts architectural patterns from `rajaryan1111/graphone-intelligence-pipeline` (adapter interfaces, bounded HTTP/retry behavior, environment configuration, async database lifecycle, repositories, validation, and tests). It does not copy GraphOne's unrelated business entities, AI-news orchestration, or domain-specific runtime.
