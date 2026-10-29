# Final verification report

**Verification context:** checks were run on 2026-10-29 on branch
`feat/sentiment-features-and-forecasting`, first on the working tree based on
`fa69d53f70535dec03dd7f48c1c0d212b565e336` plus the documentation/registry
changes, then again from a detached clean worktree at the released commit
`9b0698f86267973a220c914ac0802a5bba171374`. Application code remains
`d8016610aa7ebf82263413c48b1164e4a64d13df`; the release commit adds documentation,
registry evidence and its registry test only. PR #14 and CI were live queried at
that released head. Historical source review is distinguished from the current
documentation and registry checks.

## Code verification and current documentation checks (2026-10-29)

The full suite and source-oriented quality gates were run on 2026-10-29 against
the working tree at HEAD `fa69d53` plus the documentation, registry and
registry-test changes that became commit `9b0698f`. Application code remains
code commit `d801661`; the change set includes the updated registry test and
documentation-count validation. Earlier wording revisions briefly tripped the
count guard; those claims were corrected before the final run. The final results
for this exact state are listed below.

- `.venv/bin/python -m pytest -q` -> **187 passed in 3.77s** (run on 2026-10-29
  against the current local documentation/registry changes).
- The focused Apify/Tavily/news CLI/pipeline regressions previously passed **64
  tests** (run on 2026-10-29 against application source commit `d801661`).
- `.venv/bin/ruff check src tests scripts` -> all checks passed.
- `.venv/bin/python -m compileall -q src tests scripts` -> exit 0.
- `.venv/bin/python scripts/validate_dataset_registry.py` -> 12 records
  structurally valid; no URL, license, download or data-quality claim is implied.
- `.venv/bin/python scripts/validate_docs.py` -> passed: 103 relative Markdown
  links, 22 test-count claims, and 28 requirement rows (11 complete, 14 partial,
  2 externally blocked, 1 needing clarification).
- `.venv/bin/python -m pytest tests/unit/test_dataset_registry.py tests/unit/test_docs_validation.py -q`
  -> focused registry/docs tests passed on the final local state (2026-10-29).
- `git diff --check` -> clean on the final local changes.

A fresh two-run CLI demonstration was generated from a previously absent output
root at `reports/generated/final-submit-verify-2026-10-29/`. It produced 210 synthetic daily bars, 209 synthetic posts,
6 folds, 2,160 predictions and 18 finite metric rows across horizons `n+0` through
`n+5` for naive, price-only and sentiment-plus-price models. Each run has six
non-empty artefacts; all six were byte-identical between runs:

| Artefact | Size | SHA-256 |
| --- | ---: | --- |
| `evaluation-report.md` | 7,926 bytes | `e7b9015f07bcbdad1000c51744371979af21a88191017566958f8202e356f8ca` |
| `outlook.md` | 3,041 bytes | `a4ef193ac43e1f17572550278efe1287eb55587d02e9f9f0afead21d516a5c64` |
| `sentiment-vs-price.svg` | 17,647 bytes | `852633606e1236fda94fc2b4c6868637af345c201bc6d95800c4e07ab7c285bc` |
| `manifest.json` | 5,691 bytes | `71a63b8d4f477b4f22e23e0b208300407c18c5004b24a54df9b098387c052aa0` |
| `metrics.json` | 6,983 bytes | `b7cf3accde0ef8f25749e2f509923502d9ba97a84e38d3b121e955093c79502f` |
| `predictions.jsonl` | 454,597 bytes | `2885a7399911e29019cdda31bd1b8f9b396798abb280cebf9c35ab7b76f3a5a4` |

Synthetic metrics are only software/reproducibility evidence; they do not establish
real-world forecast value.

The prior 2026-10-29 inspection recorded APIFY_TOKEN, APIFY_API_TOKEN,
TAVILY_API_KEY and EXA_API_KEY absent from the process environment and project-local
`.env` files (presence only; values were never read or printed). No live provider
request was made. This current pass inspected `.env.example` placeholders and
implementation/configuration but did not re-read credential values.

## Clean-checkout reproduction of the released commit (2026-10-29)

The released commit `9b0698f86267973a220c914ac0802a5bba171374` was checked out
detached into a separate temporary worktree with no copied `.env`, no ignored
inputs and a fresh virtual environment built with Python 3.11.15. The host's
default `python3` is 3.9, below the project's `requires-python`, so it was not
used; the first setup attempt with it failed for that reason and is not counted
as a project failure. In the clean tree the documented commands then produced:

- `python3.11 -m venv .venv && .venv/bin/python -m pip install -e '.[dev,storage]'`
  -> succeeded.
- `.venv/bin/python -m pytest -q` -> **187 passed** on 2026-10-29 at commit
  `9b0698f`.
- `.venv/bin/ruff check src tests scripts` -> all checks passed.
- `.venv/bin/python scripts/validate_dataset_registry.py` -> 12 records valid.
- `.venv/bin/python scripts/validate_docs.py` -> passed: 102 relative Markdown
  links, 19 test-count claims outside `TEST_PLAN.md`, 28 matrix rows.
- `scripts/make_offline_demo.py` followed by `python -m xsentiment run` -> 210
  synthetic bars, 209 synthetic posts, six artefacts and finite metrics for
  `n+0`..`n+5`; all labelled synthetic.
- `git status --short --branch` -> clean before those ignored outputs were written.
- The same suite was re-run on Python 3.12.4 in a separate temporary virtual
  environment at the final tree -> 187 tests passed on 2026-10-29 and Ruff was
  clean, matching the README's stated 3.11/3.12 support.

The temporary worktree and its generated outputs were removed after the run, so
this is a recorded reproduction rather than a committed artefact. It shows the
delivered tree needs no undocumented local file; it adds no real X data,
provider evidence or real-market result.

## Previous local verification (2026-10-28; code commit d801661)

The prior complete local code verification was run on 2026-10-28 for the
22-file change set committed as `d8016610aa7ebf82263413c48b1164e4a64d13df`.
The live PR query on 2026-10-29 found pushed head
`fa69d53f70535dec03dd7f48c1c0d212b565e336`; CI runs `40787633232` and
`40787639350` succeeded on that exact SHA before the current local edits. The
historical 2026-10-28 code results below remain separate from current local checks.

- Focused regressions on 2026-10-28:
  `.venv/bin/python -m pytest -q tests/unit/test_apify_x.py tests/unit/test_tavily_news.py tests/unit/test_fetch_news_cli.py tests/unit/test_pipeline.py`
  -> **64 passed in 1.86s** on 2026-10-28.
- Full suite on 2026-10-28: `.venv/bin/python -m pytest -q` -> **187 passed in 4.06s**,
  0 failed, 0 skipped, 0 xfailed. The result matches the authoritative collection
  count in `TEST_PLAN.md`. While correcting this report's wording, several
  intermediate full-suite runs each failed only the documentation count validator
  (stale counts, then newly added counts that still lacked a date qualifier); after
  the date-scoped wording corrections, this final full run passed.
- Ruff: `.venv/bin/ruff check src tests scripts` -> all checks passed.
  Compile: `.venv/bin/python -m compileall -q src tests scripts` -> exit 0.
  Registry: `.venv/bin/python scripts/validate_dataset_registry.py` -> 12 records
  valid. Docs: `.venv/bin/python scripts/validate_docs.py` -> 104 relative Markdown
  links, 20 test-count claims inspected, 28 requirement rows: 11 complete,
  14 partial, 0 not implemented, 2 externally blocked, 1 needing clarification.
  `git diff --check` -> clean.
- Previous two-run synthetic offline CLI demo, output root
  `reports/generated/final-verify-2026-10-28-82883/` (ignored by Git): generator
  command `scripts/make_offline_demo.py --generated-at 2026-10-27T00:00:00+00:00`,
  followed by two `python -m xsentiment run` commands with identical inputs and
  `--now 2026-07-30T00:00:00+00:00`. It generated 210 labelled synthetic price
  bars, 209 labelled synthetic posts, six non-empty artefacts per run, six
  walk-forward folds, 2,160 predictions, and 18 finite horizon/model metric rows.
  The emitted horizons are `n+0`..`n+5`; models are `naive`, `price_only`, and
  `sentiment_price`. All six output files matched byte-for-byte between runs:
  report SHA-256 `9204315aaca110532306db8e6db74a231022f57db7ed7428762f336192a196d6`,
  outlook `a4ef193ac43e1f17572550278efe1287eb55587d02e9f9f0afead21d516a5c64`,
  chart `852633606e1236fda94fc2b4c6868637af345c201bc6d95800c4e07ab7c285bc`,
  manifest `209900c3e79422c5abbe50c56bbc4bc2f68abd55f10a3f93bfadbe5c75e89268`,
  metrics `b7cf3accde0ef8f25749e2f509923502d9ba97a84e38d3b121e955093c79502f`,
  and predictions `2885a7399911e29019cdda31bd1b8f9b396798abb280cebf9c35ab7b76f3a5a4`.
  These synthetic outcomes are software/reproducibility evidence only; no real
  forecasting conclusion follows.
- `data/` contains the dataset registry but no raw BTC price snapshot or
  post-text X corpus; the historical BTC evaluation artifacts are under
  `reports/btc-usd-180d/`. APIFY_TOKEN, APIFY_API_TOKEN, TAVILY_API_KEY and
  EXA_API_KEY were checked for presence only; all are unset. No live provider
  call was made.

## Prior environment details for code commit d801661

- Python: **3.11.15**, existing project `.venv`; confirmed and reused.
- The shell's bare `python` is unavailable; use `.venv/bin/python`.
- No packages were installed and no environment was recreated.
- CI installs `.[dev,storage]` on Python 3.11; the local environment has analysis extras.

## Historical checkpoint records (earlier than d801661)

The historical 167-test run and earlier environment details below describe checkpoint
`8bc4f7f` only; they are dated evidence, not proof for this local revision.

## 2. Mandatory verification results

All results in this historical section were produced on **2026-10-28 at code checkpoint `8bc4f7f`**
with the hardening changes applied; they do not describe the delivered commit `d801661`.

- Full suite on 2026-10-28 at code checkpoint `8bc4f7f`: `python -m pytest -q`
  -> **167 passed in 5.20s**, 0 failed, 0 skipped, 0 xfailed. `TEST_PLAN.md`
  is the authoritative current count and `test_docs_validation.py` checks it
  against actual collection.
- Targeted Tavily adapter: `pytest tests/unit/test_tavily_news.py -q` -> **13
  passed in 0.13s** on 2026-10-28 at code checkpoint `8bc4f7f`.
- Targeted gated news CLI: `pytest tests/unit/test_fetch_news_cli.py -q` -> **9
  passed in 0.67s** on 2026-10-28 at code checkpoint `8bc4f7f`.
- Offline demo integration: `pytest tests/integration/test_offline_demo.py -q` ->
  **5 passed in 1.21s** on 2026-10-28 at code checkpoint `8bc4f7f`.
- Network-isolation regression alone:
  `pytest tests/integration/test_offline_demo.py::test_offline_demo_run_makes_no_network_connection -q`
  -> **1 passed in 0.48s** on 2026-10-28 at code checkpoint `8bc4f7f`.

Other required commands:

```text
ruff check src tests scripts -> All checks passed!
python -m compileall -q src tests scripts -> COMPILEALL_OK
git diff --check -> CLEAN
```

`scripts/validate_docs.py` and `scripts/validate_dataset_registry.py` outputs at
code checkpoint `8bc4f7f` (before the employer-clarifications document was added;
later re-runs after that document verified all relative links — the exact link
count grows with each new doc — and 16 test-count claims, all OK):

```text
Checked 69 relative Markdown links across the repository.
Checked 14 test-count claims outside TEST_PLAN.md.
Requirement status counts from the matrix:
  Verified complete: 13
  Partially complete: 12
  Not implemented: 0
  Blocked by external dependency: 2
  Needs clarification: 1
  TOTAL: 28
OK: documentation links, requirement IDs and matrix rows are valid.
Note: this checks documentation structure only, not implementation evidence.
OK: validated 12 dataset records in .../data/registry/historical_twitter_x_datasets.json
Note: structural validation does not verify URLs, licenses, downloads, or data quality.
```

## 3. CLI and news integration verification

`python -m xsentiment --help` lists exactly `fetch-prices`, `fetch-news`,
`persist` and `run`. `fetch-news --help` lists `--query`, `--max-results`
(1..20), `--out` and the mandatory `--confirm-live-call`; there is no
`--api-key` argument. `--help` made no provider request.

The mocked-transport tests verify:

- no adapter construction without `--confirm-live-call`;
- graceful missing-credential handling and environment-only `TAVILY_API_KEY`;
- non-empty query ≤400 chars and result bounds 1..20;
- exactly one mocked HTTP request, no automatic retry;
- streaming response ceiling enforced before the whole body is buffered;
- normalized JSONL with title, URL, publication time or explicit note, retrieval
  time, source, provider, payload hash, query and context line;
- credential redaction in provider errors and caller-supplied input notes;
- `run --news-file` remains context-only and leaves `predictions.jsonl` and
  `metrics.json` byte-identical to a matching run without news.

No live Tavily, Exa, Apify or Coinbase request was made.

## 4. Offline end-to-end reproducibility

A prior two-run offline CLI demonstration was recorded on 2026-10-28 at
`reports/generated/final-verify-2026-10-28-82883/`. The commands below describe
that historical run; its artifact hashes are listed in the *Previous local
verification (2026-10-28; code commit d801661)* section above. The fresh 2026-10-29
demo and hashes are recorded separately at the start of this report:

```bash
python scripts/make_offline_demo.py \
  --out reports/generated/final-verify-2026-10-28-82883/inputs/prices.json \
  --posts-out reports/generated/final-verify-2026-10-28-82883/inputs/posts.jsonl \
  --generated-at 2026-10-27T00:00:00+00:00

python -m xsentiment run \
  --prices reports/generated/final-verify-2026-10-28-82883/inputs/prices.json \
  --posts reports/generated/final-verify-2026-10-28-82883/inputs/posts.jsonl \
  --out reports/generated/final-verify-2026-10-28-82883/run-a \
  --now 2026-07-30T00:00:00+00:00 \
  --input-note "synthetic offline demo from scripts/make_offline_demo.py"
```

The same `run` command was repeated into `run-b` with only `--out` changed.
Observed results:

- 210 labelled synthetic daily bars and 209 labelled synthetic posts.
- Two complete six-artefact run directories, each with non-empty files:
  `evaluation-report.md` (7,924 bytes), `outlook.md` (3,041),
  `sentiment-vs-price.svg` (17,647), `manifest.json` (5,689),
  `metrics.json` (6,983) and `predictions.jsonl` (454,597).
- 6 walk-forward folds; 2,160 out-of-sample prediction records matching the
  manifest; horizons `n+0`..`n+5`; models `naive`, `price_only`,
  `sentiment_price`; 18 finite per-horizon metric rows.
- Manifest `input_lineage` records `synthetic = True`, `source_platforms =
  ['synthetic']`, schema identity, windows, retrieval reason and query-mode hash.
- Outlook passes `check_outlook_page`; chart includes the day-over-day change
  panel; report and outlook explicitly label the inputs as synthetic.
- `run-a/predictions.jsonl` and `run-b/predictions.jsonl` are byte-identical;
  the two `metrics.json` files are also byte-identical.
- A separate regression blocks sockets and HTTP client methods during a real
  offline `run`, proving the documented workflow makes no network request.

Synthetic mean MAEs from this run were naive `547.2070833333329`, price-only
`265.3802434060445` and sentiment-price `265.4125671799008`. They demonstrate
software operation only and are **not** BTC-USD or X evidence. Generated paths
under `reports/generated/` are ignored by Git.

## 5. Historical real-price artefact consistency

The committed `reports/btc-usd-180d/` artefacts were cross-checked:

```text
HISTORICAL_ARTIFACT_CONSISTENCY_OK
mean_mae {'naive': 1828.3636, 'price_only': 2264.618261845033,
          'sentiment_price': 2264.618261845033}
folds 5 predictions 1800
```

The check recomputed each model's mean MAE from the 18 committed per-horizon
metric rows, confirmed metric samples sum to the manifest's 1,800 predictions,
and confirmed the rounded MAE and risk values appear in the Markdown report. The
raw 180-bar price snapshot and `predictions.jsonl` are not committed; the sandbox
network allowlist excludes Coinbase, so this is an internal consistency check of
historical artefacts, not a live re-fetch.

On that historical sample, naive MAE was **$1,828.36**, price-only ridge
**$2,264.62** and sentiment-price identical to price-only because there were zero
posts. No sentiment improvement is claimed.

## 6. Secret and generated-file review

- Added-line secret scan of the diff from `8bc4f7f`:
  `NO_ADDED_REAL_SECRET_PATTERNS`. The only `tvly-...` strings are the fixed
  mock key `tvly-mock-key-not-real` in tests and a documentation reference to it.
- `git ls-files reports/generated | wc -l` -> `0`; generated datasets, demo
  inputs and prediction dumps are not committed.
- `.env.example` contains empty placeholders only; no `.env` is tracked.
- `git diff --check` -> `CLEAN`.

## 7. GitHub delivery and CI

Remote refs and PR #14 were queried live on 2026-10-29:

```text
local branch      feat/sentiment-features-and-forecasting
local HEAD        9b0698f86267973a220c914ac0802a5bba171374 (= remote feature)
working tree      clean; the 19 documentation/registry files were committed and
                  pushed as 9b0698f, then verified in a detached clean worktree
code revision     d8016610aa7ebf82263413c48b1164e4a64d13df  <- delivered change set
                  (followed by documentation-only commits on the same branch)
remote feature    9b0698f86267973a220c914ac0802a5bba171374
remote Arena      c0cd3c113c71a25d02ebf9931b6d7b2f42b5109f  (unchanged)
remote base       36b7b486bb60b54f3f19201f2e548b11e5f93197
PR #14            OPEN, DRAFT, MERGEABLE, base docs/canonical-source-of-truth,
                  head = tip of feat/sentiment-features-and-forecasting
```

The feature branch contains both the base and Arena branches. The initial
promotion was a normal fast-forward (`5af5bc7..d801661`); subsequent docs-only
commits increased the feature-vs-Arena count. The final documentation/registry
reconciliation was then committed as `9b0698f` and pushed by ordinary
fast-forward (`fa69d53..9b0698f`). No force, history rewrite, base change or
draft-state change was used.

The released head `9b0698f86267973a220c914ac0802a5bba171374` passed both attached
CI runs: `40795420005` (push) and `40795425900` (pull_request), each `test`
conclusion `SUCCESS` on that exact SHA. Earlier heads remain historical for
their own commits: `fa69d53` passed `40787633232`/`40787639350`, code revision
`d801661` passed `40616497449`/`40616501268`, `5c91603` passed
`40622384336`/`40622378634`, and older runs `40398880548`/`40398888540` (head
`5af5bc7`) and `40570468109` (Arena `c0cd3c1`) apply only to those commits.

PR #14 was advanced by non-forced fast-forward; no merge or draft-state change
was made. The live query after the push reports it OPEN, DRAFT and MERGEABLE,
with base `36b7b486bb60b54f3f19201f2e548b11e5f93197` and pushed head
`9b0698f86267973a220c914ac0802a5bba171374`, whose two attached checks succeeded.
The working tree matches that head.

## 8. Known limitations and external blockers

- No original assignment PDFs are present in this checkout. Recorded page counts
  and hashes from 2026-10-26 are used; exact primary-source wording was not
  re-verified here.
- No accepted licensed 180-day X corpus, Apify Actor, credential, spend cap or
  private credential-transfer route. R2 and the real sentiment comparison remain
  blocked.
- No live Tavily/Exa authorization; news CLI behaviour is mocked-verified only.
- Employer clarifications are absent for the `n+0` convention, exact deadline,
  live-news requirement, news feature policy and final submission format/email.
- The raw historical price snapshot is untracked and therefore absent from a
  fresh clone; it is present in this working copy and reproduced the committed
  metrics exactly (section 7.1). Re-fetching it needs network access to Coinbase.
- The live PR inspection found PR #14 OPEN/DRAFT/MERGEABLE at head
  `9b0698f86267973a220c914ac0802a5bba171374`; runs `40795420005` and
  `40795425900` passed on that exact head. Any later pushed change requires its
  own fresh CI before being described as green.
- Static typing is not configured as a CI gate; no claim of mypy-clean code is
  made. The defined offline checks and CI are the release gates.
- CI proves offline code health only; it cannot prove data access, licence,
  model quality, profitability or employer acceptance.

## 7.1 Real-price reproduction from the local snapshot (2026-10-29)

The committed historical report was generated on 2026-10-26 from a public
Coinbase snapshot. That file is untracked (`.gitignore` covers `/data/*`) but
present in this working copy at
`data/btc-usd-daily-2026-04-29_2026-10-25.json`, with SHA-256
`09ce225a405aea390ae2f21c72634da1211a321aed1b39b52febfadf64083f75` — identical
to the hash recorded in `reports/btc-usd-180d/manifest.json`. It holds 180 BTC-USD
daily candles for 2026-04-29..2026-10-25 UTC and carries no synthetic marker.

Re-running the pipeline at `e22da11`:

```bash
python -m xsentiment run \
  --prices data/btc-usd-daily-2026-04-29_2026-10-25.json \
  --out reports/generated/repro-price-2026-10-29 \
  --now 2026-10-26T00:00:00+00:00
```

reproduced the committed results exactly:

- `metrics.json` compared field-by-field against `reports/btc-usd-180d/metrics.json`:
  **0 differences** — same folds, 1,800 predictions, every per-horizon metric,
  strategy statistic and warning.
- Mean MAE: naive `$1,828.36`, price-only `$2,264.62`, sentiment-plus-price
  `$2,264.62` (identical, because zero posts were scored).
- Strategy: 32 long days, +10.91% cumulative net return, Sharpe 1.807, Sortino
  3.979, maximum drawdown 4.08%.
- The regenerated report body differs only by provenance fields added after the
  original run (snapshot metadata, code revision, two extra limitation bullets).

This is real public price data reproduced on the final commit. It is **not** X
data and says nothing about sentiment value. The regenerated artefacts sit in the
ignored `reports/generated/` tree and are not committed; a fresh clone must
re-fetch the snapshot with `fetch-prices` because the raw file is untracked.

## 8.1 Final acceptance decision (2026-10-29)

The dimensions are reported separately on purpose: a green test suite or a green
PR does not close the data, model-quality, credential or delivery gates.

| Dimension | Status | Evidence and exact remaining action |
| --- | --- | --- |
| Engineering correctness | **Implemented and locally verified within the documented scope** | 187 tests passed on 2026-10-29 at commit `9b0698f`, along with Ruff, compileall, both validators and the registry/docs tests; credentials, URL sanitization and publication-time rules have regression coverage. Scope exclusions are stated in the canonical documents. |
| Automated verification | **Green for the released commit** | Local and clean-checkout suite runs at `9b0698f`; CI runs `40795420005` and `40795425900` succeeded on that SHA. Coverage is offline/fixture based. |
| Real-data ingestion | **Partial: public prices only** | The historical run used 180 public Coinbase BTC-USD daily bars and zero X posts; the untracked snapshot is present and reproduced the committed metrics exactly at `e22da11`. Action: approved X source/Actor, licence, spend cap and credentials. |
| Genuine model evaluation | **Partial and negative for the price-only model** | Per-horizon MAE/RMSE for `n+0`..`n+5`, plus Sharpe, Sortino and max drawdown for the predeclared strategy, reproduced exactly at `e22da11` (section 7.1). Price-only mean MAE ($2,264.62) is worse than naive ($1,828.36); the sentiment model is not identifiable with zero scored posts. No sentiment claim is made. Action: run it on accepted X data. |
| Provider reproducibility | **Not achieved** | Apify, Tavily and Exa are mocked or configuration-only; no Actor ID, no live call, no credentials and no approved credential channel. Action: select an Actor, record its ID, authorize one bounded call per provider and publish non-secret identifiers. |
| GitHub release readiness | **Draft PR only; not merged** | PR #14 is OPEN, DRAFT and MERGEABLE at `9b0698f`, both checks green, no review approval and no merge. Action: employer/owner decision to merge; nothing is force-pushed. |
| Submission package readiness | **Substantially assembled, not sendable as final** | Report, traceability matrix, audit, demo script, reproduction commands and an unsent email draft exist. Missing: real sentiment metrics, provider identifiers, a secure credential channel, confirmed deadline and confirmed format. |
| Actual delivery confirmation | **None** | No email was sent, no employer response exists and the recipient address is unconfirmed against the original brief. |

Therefore the project is **not fully submission-ready**: the engineering and offline
verification gates are satisfied, while real-data, provider, format/deadline and
delivery gates are only closable by the employer or by explicit authorization.

## 9. Submission artifacts and verified paths

- `README.md`
- `docs/SUBMISSION_SUMMARY.md`
- `docs/FINAL_REQUIREMENTS_AUDIT.md`
- `docs/FINAL_VERIFICATION_REPORT.md`
- `docs/DEMO_WALKTHROUGH.md`
- `docs/EXECUTION_CHECKPOINT.md`
- `docs/EXTERNAL_BLOCKERS.md`
- `docs/EMPLOYER_CLARIFICATIONS.md` — consolidated questions, provider
  authorization checklist and unsent ready-to-send email draft
- `docs/PR14_PROMOTION.md`
- `docs/REQUIREMENTS_TRACEABILITY.md`
- `reports/btc-usd-180d/` committed historical real-price artefacts
- `reports/generated/final-submit-verify-2026-10-29/` — fresh two-run artefact
  set with sizes and SHA-256 values recorded above; these ignored generated
  artefacts remain local and are not tracked in Git.
- Clean-checkout reproduction at `9b0698f` (temporary detached worktree, removed
  after the run) — results recorded in the section above.
- `reports/generated/final-verify-2026-10-28-82883/` — prior ignored two-run
  synthetic demonstration artifacts (historical evidence; unchanged).
- `reports/generated/final-audit-2026-10-28.D0dgOZ/`,
  `reports/generated/final-resume-2026-10-28/` and
  `reports/generated/resume-audit-2026-10-28/` ignored synthetic demo artefacts
  from prior runs (their hashes remain historical until refreshed).
