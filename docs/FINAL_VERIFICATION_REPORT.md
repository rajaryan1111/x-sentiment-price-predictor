# Final verification report

**Local verification context:** 2026-10-28, Python 3.11.15, branch
`feat/sentiment-features-and-forecasting`, base HEAD
`c0cd3c113c71a25d02ebf9931b6d7b2f42b5109f` plus modified, uncommitted files.
This HEAD identifies the base revision only; there is no commit SHA for these edits.
The remote Arena ref remains at that base SHA, and the working changes have not
been pushed or run in GitHub Actions.

## Current local verification (2026-10-28)

This verification applies to the working tree based on HEAD
`c0cd3c113c71a25d02ebf9931b6d7b2f42b5109f`, branch
`feat/sentiment-features-and-forecasting`, with 22 modified tracked files and no
untracked source files. The changes are uncommitted; no GitHub Actions run covers
this tree. The exact local content is checked below; historical checkpoint results
remain separate.

- Focused regressions on 2026-10-28:
  `.venv/bin/python -m pytest -q tests/unit/test_apify_x.py tests/unit/test_tavily_news.py tests/unit/test_fetch_news_cli.py tests/unit/test_pipeline.py`
  -> **64 passed in 1.86s**.
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
- Two-run synthetic offline CLI demo, output root
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
- `data/` contains the BTC price snapshot and registry, no post-text X corpus.
  APIFY_TOKEN, APIFY_API_TOKEN, TAVILY_API_KEY and EXA_API_KEY were checked for
  presence only; all are unset. No live provider call was made.

## 1. Environment

- Python: **3.11.15**, existing project `.venv`; confirmed and reused.
- The shell's bare `python` is unavailable; use `.venv/bin/python`.
- No packages were installed and no environment was recreated.
- CI installs `.[dev,storage]` on Python 3.11; the local environment has analysis extras.

## Historical checkpoint records

The historical 167-test run and earlier environment details below describe checkpoint
`8bc4f7f` only; they are dated evidence, not proof for this local revision.

## 2. Mandatory verification results

All results in this historical section were produced on **2026-10-28 at code checkpoint `8bc4f7f`**
with the hardening changes applied; they do not describe the current uncommitted tree.

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

The documented commands were executed from a clean output directory. This is the
same run whose SHA-256 hashes are listed under *Current local verification
(2026-10-28)* above; rerunning it on 2026-10-28 reproduced every hash exactly:

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

Remote refs were fetched and the current PR was queried on 2026-10-28:

```text
local branch      feat/sentiment-features-and-forecasting
local HEAD        c0cd3c113c71a25d02ebf9931b6d7b2f42b5109f + uncommitted changes
remote Arena      c0cd3c113c71a25d02ebf9931b6d7b2f42b5109f
remote feature    5af5bc7a50c4b56edc1efe3aae4fce2501bdc656
remote base       36b7b486bb60b54f3f19201f2e548b11e5f93197
PR #14            OPEN, DRAFT, base docs/canonical-source-of-truth,
                  head feat/sentiment-features-and-forecasting at 5af5bc7...
```

The feature branch is an ancestor of the Arena branch, and the base is an
ancestor of feature. `git rev-list --left-right --count
origin/feat/sentiment-features-and-forecasting...origin/arena/cf79e7b7-x-sentiment-price-predictor`
returned `0 7`. This confirms the remote commit series is fast-forwardable, but
the current uncommitted changes are not yet part of that candidate.
`gh pr checks 14` currently shows passing `test` jobs for the PR head commit
`5af5bc7a50c4b56edc1efe3aae4fce2501bdc656` (runs `40398880540` and
`40398888540`). These checks do not cover Arena `c0cd3c1` or this local work.
GitHub API reports the feature branch unprotected, Arena unprotected, zero
repository rulesets. Nevertheless, this execution context is explicitly restricted
to the Arena push target; do not push to the feature branch from here.

Prior successful CI evidence exists for Arena commit `c0cd3c1` as reported in the
prior checkpoint, but the interrupted security/documentation changes have not
been committed or run by CI. No push, commit, PR update, PR draft-state change or
merge was made during this resumed pass. The current worktree is on the local
feature-named branch, but the environment's push policy is Arena-only; there is
no final commit SHA for these edits.

The safe promotion procedure for an authorized normal clone remains in
[PR14_PROMOTION.md](PR14_PROMOTION.md); it must use the final Arena SHA after
these working changes are committed and pushed. PR #14 remains draft and was not
merged.

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
- Raw historical price snapshot is not committed and could not be refetched in
  this network-restricted sandbox.
- PR #14's head cannot be advanced from this restricted session; an authorized
  normal clone must run `docs/PR14_PROMOTION.md`.
- Static typing is not configured as a CI gate; no claim of mypy-clean code is
  made. The defined offline checks and CI are the release gates.
- CI proves offline code health only; it cannot prove data access, licence,
  model quality, profitability or employer acceptance.

## 9. Submission artifacts

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
- `reports/generated/final-verify-2026-10-28-82883/` — the verified two-run
  artefact set recorded under *Current local verification (2026-10-28)* and in
  section 4 (hashes above were re-reproduced).
- `reports/generated/final-audit-2026-10-28.D0dgOZ/`,
  `reports/generated/final-resume-2026-10-28/` and
  `reports/generated/resume-audit-2026-10-28/` ignored synthetic demo artefacts
  from prior runs (their hashes remain historical until refreshed).
