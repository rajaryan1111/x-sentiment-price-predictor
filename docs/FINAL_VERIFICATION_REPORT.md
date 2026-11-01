# Final verification report — 2026-11-01

## Local verification

The full source-tree verification was run on the execution changes:

| Check | Result |
| --- | --- |
| `uv run pytest -q -ra` | See the current count in [TEST_PLAN.md](../TEST_PLAN.md); this report follows the 2026-11-01 run. |
| `uv run ruff check src tests scripts` | Pass |
| `uv run python -m compileall -q src tests scripts` | Pass |
| `uv run python scripts/validate_docs.py` | Pass: 102 relative links, 4 test-count claims, 28 matrix rows |
| `uv run python scripts/validate_dataset_registry.py` | Pass: 12 records structurally valid |
| Apify `--validate-only` preflight | `valid: true`; `network_call_made: false`; `paid_run_launched: false` |
| Binance archive build | 36 published checksum matches; 180 complete, unique daily rows |
| Full price-only pipeline | 5 folds; six horizons; 100 OOS samples per model/horizon; 1,800 per-row predictions |

The local test count matches the authoritative count in `TEST_PLAN.md`. Adapter
tests use mocked HTTP and do not reach provider endpoints. The one explicitly
authorized live Tavily request is documented separately in the final execution
status; it yielded five results without publication timestamps. Exa is not live
verified and no Apify Actor was run.

## Data and model result

The source snapshot is Binance Vision Spot BTCUSDT, USDT quote, 2026-05-05 through
2026-10-31 UTC. Source archives and published SHA-256 sidecars are packaged. There
are no accepted or scored X posts. Mean MAE is 1,824.23 USDT for naive persistence
and 2,378.50 USDT for price-only ridge; the candidate sentiment model is identical
without sentiment and cannot establish an effect. Price-only strategy risk metrics
are Sharpe 1.124, Sortino 2.431 and maximum drawdown 5.885%. All Binance-derived
results are CC BY-NC-SA 4.0, attributed and non-commercial only.

## Release checks

The final ZIP is built from the reviewed final branch. ZIP integrity, clean
extraction, forbidden-file/secret scans, archive entry count, checksum sidecar, and
GitHub Actions for the exact pushed SHA are release gates. Their exact output paths,
digest and Actions link are returned in the final handoff. Historical CI runs are
not used as evidence for a newer SHA.

## External constraints

Current Apify Free-plan rules prohibit Actor API use. Coinbase Market Data terms
prohibit ML evaluation and derived-artifact redistribution without written consent;
no Coinbase data was used in this execution and its former derived result files were
removed from the current tree. The exact BTC-USD pair, real X dataset, any Exa live
call, employer `n+0` convention, deadline and private credential channel remain
external decisions. See [FINAL_EXECUTION_STATUS](FINAL_EXECUTION_STATUS_2026-11-01.md).
