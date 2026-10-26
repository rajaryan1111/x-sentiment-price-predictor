# X Sentiment Price Predictor

Research pipeline to evaluate whether timestamped X sentiment adds predictive value beyond price-only baselines for a selected asset.

> **Current status:** Architecture scaffold and dataset registry are present. **Phase 1 requirements are closed as a documented baseline.** Working defaults: BTC-USD, daily (`1d`) UTC bars, forecasts of the closes at `n` through `n+5` made at the start of UTC day `n`, and Coinbase Exchange public BTC-USD candles as the price-source default. See [Phase 1 requirements](docs/PHASE_1_REQUIREMENTS.md) for the assumptions, source-backed limitations and Phase 2 readiness gates. The historical dataset Google Doc was not accessible during this session; its contents/rights remain unverified, and provider/Actor checks must pass before live ingestion or training. This repository does not yet claim live ingestion, trained forecasts, backtest results, Sharpe ratio, Sortino ratio, or maximum drawdown.

## Requirements first

Read [docs/PHASE_1_REQUIREMENTS.md](docs/PHASE_1_REQUIREMENTS.md) before implementation. It maps the assessment brief to requirements, acceptance criteria, documented working defaults, external readiness gates, scope boundaries, data-integrity rules and a traceability matrix. BTC-USD and daily bars are the selected project choices; UTC cutoff, Coinbase candles and close-price horizons are implementation defaults rather than employer-confirmed requirements. External data access, provider behavior, source terms and any employer clarification must be checked before live ingestion or evaluation.

## Phase 2 data-ingestion status

The Coinbase adapter and point-in-time data primitives are implemented. The user-run UTC 180-day BTC-USD profile returned 180/180 daily bars with no missing or duplicate bars in the checked range. A configurable Apify adapter and mocked tests are present, but no live Actor has been selected or run. For a no-cost path, see [Phase 2 no-cost data plan](docs/PHASE_2_NO_COST_DATA_PLAN.md) and use [the local X dataset profiler](scripts/profile_local_x_dataset.py) on an accessible local CSV/JSONL file. The profiler prints schema/coverage metadata only and deliberately does not certify point-in-time backtest readiness. Phase 2 remains partial until a real, permitted X dataset is profiled and coverage is evidenced. See [Phase 2 progress](docs/PHASE_2_PROGRESS.md) and [Apify X setup and run caps](docs/APIFY_X_SETUP.md). The latest implementation is tracked in [draft PR #10](https://github.com/rajaryan1111/x-sentiment-price-predictor/pull/10).

## Historical dataset registry

The curated inventory from the supplied historical Twitter/X dataset PDF is recorded in [data/registry/historical_twitter_x_datasets.json](data/registry/historical_twitter_x_datasets.json), with selection, licensing, provenance, point-in-time, and hydration caveats in [docs/data-sources.md](docs/data-sources.md). These are source references only: no corpus is bundled or automatically downloaded. Validate the inventory offline with `python scripts/validate_dataset_registry.py`.

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