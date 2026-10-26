# X Sentiment Price Predictor

Research pipeline to evaluate whether timestamped X sentiment adds predictive value beyond price-only baselines for a selected asset.

> **Current status:** Architecture scaffold only. This repository does not yet claim live ingestion, trained forecasts, backtest results, Sharpe ratio, Sortino ratio, or maximum drawdown.

## Historical dataset registry

The curated inventory from the supplied historical Twitter/X dataset PDF is recorded in [`data/registry/historical_twitter_x_datasets.json`](data/registry/historical_twitter_x_datasets.json), with selection, licensing, provenance, point-in-time, and hydration caveats in [`docs/data-sources.md`](docs/data-sources.md). These are source references only: no corpus is bundled or automatically downloaded. Validate the inventory offline with `python scripts/validate_dataset_registry.py`.

## Architecture

- `src/xsentiment/config/`: validated environment-backed settings.
- `src/xsentiment/ingestion/`: provider-neutral data contracts, shared bounded async HTTP/retry boundary, and replaceable X, price and optional news adapters.
- `src/xsentiment/storage/`: database lifecycle, project-owned schema base and repository interface.
- `src/xsentiment/features/`: sentiment aggregation and price features.
- `src/xsentiment/models/`: price-only baseline and candidate forecasting interfaces.
- `src/xsentiment/validation/`: temporal validation and leakage guards.
- `src/xsentiment/backtesting/`: backtesting and risk metrics.
- `src/xsentiment/reporting/`: report payloads and report assembly.
- `dashboard/`: future presentation layer.
- `tests/`: offline unit tests and later provider/database contract tests.

## Shared infrastructure patterns adapted from GraphOne

The following patterns are being reused/adapted: replaceable source adapters; single HTTP boundary with bounded concurrency and response-size caps; transient-only retries with jitter; environment-backed validated settings; async SQLAlchemy engine/session lifecycle; project-separated model and repository layers; and tests that can run without live providers.

GraphOne's AI-news orchestration, business-domain ORM entities, storage tables, and application runtime are deliberately **not** copied. The source-specific adapter implementations will be written against this project's actual X and price provider contracts.

## Setup

Python 3.11+ is targeted. Create a virtual environment, then install the package with development and storage dependencies:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev,storage]"
cp .env.example .env
pytest
ruff check src tests
```

These setup commands are scaffold-level; external provider ingestion and full application execution are not implemented yet.

## Data integrity and evaluation rules

- Retain source IDs, event timestamps, retrieval timestamps, and provenance.
- Keep credentials, raw private X exports, and large generated datasets out of Git.
- Enforce point-in-time availability; use chronological/walk-forward evaluation, never random train/test splits for time series.
- Compare sentiment-augmented models against simple price-only baselines.
- Only publish performance metrics derived from out-of-sample strategy returns with disclosed transaction costs, annualization, return convention, and trading assumptions.
- Treat Tavily/Exa results as context/provenance unless the approved specification explicitly allows them as model features.
- Never label fixtures or synthetic examples as live provider data.

## Branch strategy

- `main`: stable integration.
- `setup/project-scaffold`: skeleton and reusable infrastructure.
- `feat/ingestion`: provider adapters and ingestion contracts.
- `feat/modeling`: features and forecast models.
- `feat/evaluation`: walk-forward evaluation and backtesting.
- `feat/dashboard-reporting`: charts and assessment report.

Feature work should be merged through review after offline tests pass.

## Scope boundary

The ten canonical requirements/architecture files are intentionally not created in this scaffold commit. They will be added in the next step and treated as the source of truth for implementation decisions.
