# Submission package manifest

The ZIP is a source-based package built from the reviewed `feat/availability-basis-and-preflight` worktree. It contains tracked repository files only, under one `x-sentiment-price-predictor/` root directory. The exact entry count and integrity result are recorded in `FINAL_SUBMISSION_CHECKLIST.md` after the ZIP is built.

| Top-level component | Included content | Why it is included |
| --- | --- | --- |
| Project root | README, pyproject, `.env.example`, canonical PRD/architecture/design/data/model/test/rules/phase/decision docs | Setup, configuration shape, engineering design, policies and project state. `.env.example` contains placeholders only. |
| `.github/` | CI workflow | Reproducible automated verification configuration. |
| `src/xsentiment/` | CLI, adapters, validation, feature/model/evaluation pipeline, persistence, reporting | Required implementation. |
| `scripts/` | Safe preflight, bounded ingestion command, offline demo, local profilers and validators | Reproduction and operational workflows. The paid ingestion script remains gated. |
| `tests/` | Unit and offline integration tests | Evidence for local behavior, safety gates, data contracts, evaluation and artifact reproducibility. No live paid integration test is included. |
| `docs/` | Source-checked requirements, traceability, provider setup, data contract, limitations and technical audit records | Requirement evidence and context; historical records are dated and must not be read as current-state CI evidence. |
| `data/registry/` | Curated historical dataset reference metadata | Reproducible dataset inventory; no downloaded post corpus. |
| `reports/btcusdt-180d/` | 180-row BTCUSDT snapshot, 36 source archive ZIPs and checksum sidecars, manifest, aggregate/per-horizon metrics, 1,800 predictions, Markdown report/outlook, SVG, attribution/license | Recomputed reproducible price-only evaluation; USDT quote, Binance Vision CC BY-NC-SA 4.0, non-commercial only. |
| `submission/` | Final checklist, handoff, package manifest, blockers, evaluation, demo, reproducibility, results, limitations and unsent email draft | Evaluator-facing packet and precise handoff. |
| `dashboard/` and pipeline `dashboard.html` | Offline dashboard scope and generated dashboard | Self-contained HTML embeds the generated SVG and reports sample counts, forecast metrics, risk metrics, source freshness, licensing, and honest empty sentiment states. |

## Exclusions

- `.git` and all Git history
- `.env`, tokens, keys, passwords, and other secret values
- local databases, model binaries, virtual environments, Python/cache/build artifacts
- unlicensed/raw X datasets and temporary logs; the Binance Vision archive is included only under its non-commercial CC BY-NC-SA 4.0 terms and attribution
- original assessment PDFs (reviewed from user-provided copies; not copied into Git or ZIP)
- unrelated files and prior ad-hoc output-directory artifacts

The root folder is rebuilt from a clean allow-listed Git archive plus this release's reviewed changes. The final ZIP is inspected for integrity, secrets, forbidden paths, duplicate/stale output artifacts, and consistent structure before handoff.
