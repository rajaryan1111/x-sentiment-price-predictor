# Execution checkpoint

This file is a recovery aid for interrupted work. It records the verified state,
the exact next safe commands, and the blockers. It is not a completion claim.

## Current verified state — 2026-11-01 (UTC)

- `origin/main` is `4ce17a50cd3f5e7fa346708b748a1d3652497aaf` (48 files, Phase 1
  scaffold). PR #14 head `848de0033f36341d2b85bf060aeeccc674686de5` contains
  `main` as a strict ancestor: 102 commits ahead, 0 behind, 112 files.
- PR #14 is OPEN, DRAFT and MERGEABLE. It was retargeted from
  `docs/canonical-source-of-truth` to **`main`** after the ancestry and secret
  checks. The diff against `main` is 87 files. CI runs `40799393484` (push) and
  `40799399662` (pull_request) succeeded on `848de00`. The PR is not merged.
- Local branch `feat/availability-basis-and-preflight` is at
  `346a18c253e587fefb5db413e7843684097a538e`, four commits on top of `848de00`.
  Code commit `4264469` adds the explicit availability basis, the offline Apify
  preflight and the bounded ingestion command; the tip `346a18c` records their
  documentation. It is committed locally and **not pushed**; push and merge await
  explicit authorization.
- A clean-copy run on 2026-11-01 at code `4264469` / branch tip `346a18c`
  (excluding the unrelated untracked `aicte-compliance-ai/` directory) passed 209
  tests, Ruff, compileall, the documentation validator, the dataset-registry
  validator and `git diff --check`.
  The working-tree copy with the unrelated directory present shows one
  environment-only docs-validator failure; that is not a code failure.
- The code now has two named availability bases. `observed` is the default and
  keeps `retrieved_at <= cutoff`. `archive_created_at` is opt-in, requires
  `--availability-note`, and records a look-ahead limitation in the manifest,
  report and outlook. See `DECISIONS.md` D-031, `DATA_POLICY.md` and
  `docs/PHASE_2_DATA_CONTRACT.md`.
- `docs/ACTOR_REVIEW.md` records the `apidojo/tweet-scraper` candidate and its
  unverified pricing/schema items. `config/apify_actor_input.example.json` is
  placeholder-only. `scripts/smoke_test_apify_x.py --validate-only` makes no
  network call and launches no paid run. `scripts/ingest_apify_x.py` runs one
  confirmed query under caps and writes normalized JSONL plus a sanitized manifest;
  it has only been tested with a fake adapter.
- No real X corpus, Actor ID, token, live provider call, employer answer, merge
  or submission email exists. The raw BTC price snapshot is present locally and
  ignored; its SHA-256 matches `reports/btc-usd-180d/manifest.json`.

## Current phase

Priority 1 (PR #14 integration) is prepared: the PR is retargeted to `main` and
mergeable with green CI. Priority 2 (offline engineering) is complete for the
availability basis and Apify preflight. The remaining work is external or needs
authorization:

1. Push the local commit and/or merge PR #14 — explicit authorization required.
2. Answer B9 (availability basis) and B10 (stale registry snapshot) and approve
   one X source, a paid plan, a hard spend cap and a private credential route.
3. Run the 7-day pilot, then the bounded 180-day ingestion, then the real
   sentiment-versus-price evaluation.
4. Resolve the employer questions in `docs/EMPLOYER_CLARIFICATIONS.md` (Q1–Q11).
5. Reconcile the real-data report and submission packet only after the real run.

## External blockers

- B1/B3: no approved X source, Actor, paid plan or spend cap.
- B2: no private credential-transfer route.
- B4: `n+0` convention unconfirmed.
- B5: exact calendar deadline unconfirmed.
- B6: whether live Tavily news is required, and whether news may be a feature.
- B7: final submission format and recipient confirmation.
- B9: explicit retrospective-availability decision (the code is ready, but no
  real run uses it).
- B10: the strongest registry snapshot predates the current 180-day window.
- The original assessment PDFs and `CWT_ASSIGNMENT_AUDIT.md` are absent from this
  checkout; requirement wording rests on the recorded transcription.

No live provider call is authorized.

## Pending tasks

1. Push `346a18c` to `feat/sentiment-features-and-forecasting` and let CI run on
   the exact SHA — only after explicit push authorization.
2. Merge PR #14 with a merge commit — only after explicit merge authorization.
3. Close or annotate PRs #9–#13 only with patch-equivalence evidence. #9–#11 are
   fully contained in `848de00`; #12/#13 have 5 and 9 non-contained commits, so
   they must not be closed without a content review.
4. Run the bounded real-data pilot once B1–B3/B9 and credentials are approved.
5. Regenerate the real report, chart and outlook; update the traceability matrix
   with measured evidence.
6. Re-run the full QA and prepare the unsent submission packet.

## Recovery history (2026-10-28)

- Initial local HEAD in the first recovery: `5af5bc7a50c4b56edc1efe3aae4fce2501bdc656`.
- Initial remote Arena head: `8bc4f7ffc45ece3402060578fe14aa5c4a89bef7`.
- The initial working tree was byte-for-byte identical to remote commit
  `8bc4f7f` but was uncommitted. It was preserved in a named safety stash, then
  the local Arena branch was fast-forwarded with `git merge --ff-only` to
  `8bc4f7f`. No reset, force-push, branch switch, history rewrite or PR merge was
  performed. The repository was unshallowed to restore full ancestry.
- A fresh Python 3.11.2 `.venv` was created with `.[dev,storage,analysis]`.
- Four Arena-only checkpoints were then committed and pushed, ending at
  `15478906bbc2cb6c5806f366141b5cd35cac0523`.

## Completed tasks (cumulative)

- Recovered and preserved the uncommitted final tree; aligned the local branch.
- Re-fetched and verified all relevant remote refs, PR metadata and CI runs.
- Re-audited all 28 requirement IDs against actual source paths, tests and
  artefacts; no primary PDF was available, so all rows remain `T*`.
- Verified price validation, timestamp contracts, point-in-time alignment,
  sentiment/price features, six horizon targets, walk-forward evaluation,
  baselines, risk metrics, chart/outlook/report generation and storage.
- Hardened the Tavily response ceiling and caller-note redaction; added streaming
  and offline network-isolation regressions.
- Implemented and tested the explicit availability basis (D-031) and the offline
  Apify input preflight; added the actor review page and placeholder input.
- Retargeted PR #14 to `main` after verifying ancestry and a clean diff.
- Updated `TEST_PLAN.md`, README, canonical docs, `DECISIONS.md` (D-031),
  `DATA_POLICY.md`, the data contract, the traceability matrix, the external
  blockers and the employer clarifications (Q10/Q11).

## Latest verification evidence

On 2026-11-01 at local commit `4264469`, a clean copy passed 209 tests, Ruff,
compileall, the documentation validator (all links and 28 requirement rows valid),
the dataset-registry validator (12 records) and `git diff --check`. These results do not cover live providers, real X data or
model quality. Exact commands are in `FINAL_VERIFICATION_REPORT.md`. No live
provider request was made.

## Exact next commands

```bash
# Verify the live PR state before quoting a SHA.
gh pr view 14 --repo rajaryan1111/x-sentiment-price-predictor \
  --json baseRefName,headRefOid,mergeable,mergeStateStatus,isDraft

# Reproduce the 2026-11-01 checks in a clean copy (no unrelated nested project).
rsync -a --exclude aicte-compliance-ai --exclude .git --exclude .venv \
  --exclude .pytest_cache --exclude .ruff_cache --exclude __pycache__ \
  --exclude .qa-clean ./ .qa-clean/
cd .qa-clean
PYTHONPATH="$PWD/src" ../.venv/bin/python -m pytest -q
PYTHONPATH="$PWD/src" ../.venv/bin/python -m ruff check src tests scripts
PYTHONPATH="$PWD/src" ../.venv/bin/python scripts/validate_docs.py
PYTHONPATH="$PWD/src" ../.venv/bin/python scripts/validate_dataset_registry.py
PYTHONPATH="$PWD/src" ../.venv/bin/python -m compileall -q src tests scripts
git -C .. diff --check
```

Do not merge PR #14, push the local commit, or change its draft status without
explicit authorization. Do not run a paid Actor without an approved source,
budget and credential route.
