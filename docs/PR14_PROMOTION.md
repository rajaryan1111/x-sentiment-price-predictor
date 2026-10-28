# Safe PR #14 promotion procedure

**Code promotion status: COMPLETED on 2026-10-28.** The verified work was committed
as `d8016610aa7ebf82263413c48b1164e4a64d13df` and pushed to
`feat/sentiment-features-and-forecasting` with a normal non-forced fast-forward
(`5af5bc7..d801661`). PR #14's head branch contains it. Documentation-only
reconciliation commits were subsequently pushed by normal fast-forward. At the
full PR inspection before this documentation-only update, head
`6a41980943b000326e3b3cabe331a392e63410a3` had fresh push and pull-request CI
runs `40784385769` and `40784392125`, both passed. No force-push, history rewrite,
base change, draft-state change or merge occurred. The procedure below is retained as the record of how it was done and as the safe
repeat path if the head ever needs to advance again.

**Purpose:** move verified Arena-branch work into the existing PR #14 head
branch with a normal, non-forced fast-forward. The earlier assumption that this
session could push only to the Arena branch was tested and disproven; the plain
push to the feature branch succeeded from here.

**Repository:** <https://github.com/rajaryan1111/x-sentiment-price-predictor>
**PR:** <https://github.com/rajaryan1111/x-sentiment-price-predictor/pull/14>
**Base:** `docs/canonical-source-of-truth`
**PR head branch:** `feat/sentiment-features-and-forecasting`

## Verified state on 2026-10-29 (recorded metadata inspection)

- Remote feature / PR #14 head at the recorded metadata inspection:
  `6a41980943b000326e3b3cabe331a392e63410a3`, containing code revision
  `d8016610aa7ebf82263413c48b1164e4a64d13df` and later docs-only commits. Check
  GitHub again before using this procedure.
- PR base `docs/canonical-source-of-truth`:
  `36b7b486bb60b54f3f19201f2e548b11e5f93197`.
- Remote Arena branch: `c0cd3c113c71a25d02ebf9931b6d7b2f42b5109f`.
- PR #14 metadata: OPEN, DRAFT, MERGEABLE.
- CI on that inspected head, both successful: run `40784385769` and run
  `40784392125` —
  <https://github.com/rajaryan1111/x-sentiment-price-predictor/actions/runs/40784385769>
  and <https://github.com/rajaryan1111/x-sentiment-price-predictor/actions/runs/40784392125>.
  Earlier runs `40783061034`/`40783064118` belong to head `2d5e2f7`;
  `40622384336`/`40622378634` belong to `5c91603`; and
  `40616497449`/`40616501268` belong to `d801661`. Older runs
  `40398880548`/`40398888540` and `40570468109` are historical for their
  respective SHAs.
- At the recorded ancestry inspection, the base and Arena
  were ancestors of feature; feature-vs-Arena was `5 0` after documentation-only
  commits. No force push,
  history rewrite, base change, PR-ready change or merge occurred.
- Documentation updates through inspected head `6a41980` passed the offline
  verification gates on 2026-10-29; fresh CI passed on that head (runs
  `40784385769`, `40784392125`). These results are tied to that SHA; inspect the
  live PR head and attached checks before making a new CI claim.

## Do not

- Do not run `git push --force`, `git reset --hard`, `git rebase`, or
  `gh pr merge 14`.
- Do not push to `main` or `docs/canonical-source-of-truth`.
- Do not open a duplicate PR unless the fast-forward is impossible and a
  maintainer explicitly approves replacing PR #14.
- Do not place API keys in shell history, commands, files or chat.

## Step 1 — fetch and verify refs

Run from a clean, authorized clone with a normal `origin` refspec:

```bash
git fetch origin \
  '+refs/heads/arena/cf79e7b7-x-sentiment-price-predictor:refs/remotes/origin/arena/cf79e7b7-x-sentiment-price-predictor' \
  '+refs/heads/feat/sentiment-features-and-forecasting:refs/remotes/origin/feat/sentiment-features-and-forecasting' \
  '+refs/heads/docs/canonical-source-of-truth:refs/remotes/origin/docs/canonical-source-of-truth'

FEAT=origin/feat/sentiment-features-and-forecasting
ARENA=origin/arena/cf79e7b7-x-sentiment-price-predictor
BASE=origin/docs/canonical-source-of-truth

git rev-parse "$FEAT" "$ARENA" "$BASE"
git merge-base --is-ancestor "$BASE" "$FEAT"
```

The base-ancestry check must exit zero. Next inspect whether Arena is already
contained in the feature branch:

```bash
git merge-base --is-ancestor "$ARENA" "$FEAT" && echo 'Arena is contained in feature'
git rev-list --left-right --count "$FEAT...$ARENA"
```

If Arena is not an ancestor of feature, do not assume a fast-forward direction;
inspect the graph and diffs before deciding anything. Never push the base branch.

## Step 2 — confirm the feature branch has not unexpectedly advanced

```bash
# Reconfirm PR metadata rather than assuming the remembered feature SHA is current.
# The head moves with every documentation commit, so compare the local tip against
# the live PR head instead of hard-coding a SHA that this commit would invalidate.
PR_HEAD=$(gh pr view 14 --repo rajaryan1111/x-sentiment-price-predictor \
  --json headRefOid --jq '.headRefOid')
ACTUAL_FEAT=$(git rev-parse "$FEAT")
test "$ACTUAL_FEAT" = "$PR_HEAD" || {
  echo "STOP: local feature tip $ACTUAL_FEAT differs from PR #14 head $PR_HEAD" >&2
  echo "Fetch and re-inspect before deciding anything." >&2
  exit 1
}

COUNTS=$(git rev-list --left-right --count "$FEAT...$ARENA")
LEFT=${COUNTS%%$'\t'*}
RIGHT=${COUNTS##*$'\t'}
echo "feat-only=$LEFT arena-only=$RIGHT"
# After promotion, Arena should be an ancestor of feature and arena-only must be 0.
# The feature-only count can grow as PR documentation or code advances.
git merge-base --is-ancestor "$ARENA" "$FEAT" && test "$RIGHT" -eq 0 || {
  echo "STOP: feature no longer contains the recorded Arena base" >&2
  echo "Inspect both refs and the complete diff before deciding anything." >&2
  exit 1
}

git log --oneline --decorate "$ARENA..$FEAT"
git diff --check "$ARENA..$FEAT"
git diff --stat "$ARENA..$FEAT"
```

The feature-only commits include the verified code delivery `d801661` plus
subsequent documentation commits; the exact count is not a fixed guard. Review
`git log --oneline "$ARENA..$FEAT"`, `git diff --check "$ARENA..$FEAT"`, and
`git diff --stat "$ARENA..$FEAT"`. Do not advance anything unless the reviewed
diff is intended and all local gates pass.

## Step 3 — verify branch rules and local cleanliness

```bash
gh api repos/rajaryan1111/x-sentiment-price-predictor/branches/feat%2Fsentiment-features-and-forecasting \
  --jq '"protected=\(.protected) sha=\(.commit.sha)"'
gh api repos/rajaryan1111/x-sentiment-price-predictor/rulesets --jq 'rulesets=\(length)'

git status --short --branch
```

The working tree must be clean. On 2026-10-28 the branch endpoint reported
`protected=false` and the ruleset list was empty; re-check because settings can
change. If a new rule blocks direct pushes, ask a maintainer with bypass rights to
run the fast-forward or approve the push through GitHub's normal UI.

## Step 4 — advance the PR branch only when there is a reviewed descendant

Promotion of the previously audited Arena change set is complete; do not repeat
it. For a future, separately reviewed candidate commit, first verify it descends
from the live feature tip and contains the intended base, then fast-forward only:

```bash
FEATURE=origin/feat/sentiment-features-and-forecasting
CANDIDATE=<reviewed-local-commit>
git merge-base --is-ancestor "$FEATURE" "$CANDIDATE"
git merge-base --is-ancestor "$BASE" "$CANDIDATE"
git diff --check "$FEATURE..$CANDIDATE"
git diff --stat "$FEATURE..$CANDIDATE"
# Review the complete diff, run local gates, then:
git switch feat/sentiment-features-and-forecasting
git merge --ff-only "$CANDIDATE"
git push origin feat/sentiment-features-and-forecasting
```

Never blindly merge Arena into feature. If someone advanced the remote branch,
normal push rejects; fetch and re-inspect, without forcing.

## Step 5 — verify the PR head and fresh CI

```bash
git ls-remote origin refs/heads/feat/sentiment-features-and-forecasting

gh pr view 14 \
  --json number,state,isDraft,headRefName,headRefOid,baseRefName,mergeable,mergeStateStatus,url

RUN=$(gh run list --branch feat/sentiment-features-and-forecasting --limit 1 \
  --json databaseId --jq '.[0].databaseId')
gh run watch "$RUN" --exit-status
gh pr checks 14
```

PR #14 should report the same head SHA as the remote feature branch. Record the
live SHA returned by GitHub at the time of the check; documentation commits also
advance the branch tip.
Both the push event and the pull-request event trigger the CI workflow because
`.github/workflows/ci.yml` contains `feat/**` in its push and pull-request branch
filters; both runs were observed green. Wait for the checks attached to the new
head, not the older check on `5af5bc7`.

Only after CI is green, optionally mark the draft ready:

```bash
gh pr ready 14
```

Do **not** merge the PR without explicit approval.

## If divergence is detected

If `git merge-base --is-ancestor "$FEAT" "$ARENA"` fails, or `LEFT` is not zero,
do not force-push and do not create a merge commit here. Report both SHAs:
`git rev-parse "$FEAT" "$ARENA"`, then let a maintainer decide whether to rebase
the Arena work, cherry-pick it, or open a replacement PR from the Arena branch.
The current repository is designed to avoid rewriting the existing PR history.
