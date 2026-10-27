# Safe PR #14 promotion procedure

**Purpose:** move the verified Arena-branch work into the existing PR #14 head
branch with a normal, non-forced fast-forward. This document is for an authorized
user working in a normal clone. It is **not** a command to run from the restricted
Arena session, which may push only to
`arena/cf79e7b7-x-sentiment-price-predictor`.

**Repository:** <https://github.com/rajaryan1111/x-sentiment-price-predictor>
**PR:** <https://github.com/rajaryan1111/x-sentiment-price-predictor/pull/14>
**Base:** `docs/canonical-source-of-truth`
**PR head branch:** `feat/sentiment-features-and-forecasting`

## Verified state on 2026-10-28

- PR #14 head / feature branch: `5af5bc7a50c4b56edc1efe3aae4fce2501bdc656`.
- PR base: `36b7b486bb60b54f3f19201f2e548b11e5f93197`.
- Arena branch verified code checkpoint: `8bc4f7ffc45ece3402060578fe14aa5c4a89bef7`,
  with the final documentation/security checkpoint added afterwards.
- Full ancestry: PR base is an ancestor of the feature branch; the feature branch
  is an ancestor of the Arena branch. No merge commit is needed.
- GitHub branch API reported `protected=false` for the feature branch and zero
  repository rulesets. Re-check before pushing; a changed protection rule may
  require a maintainer with bypass rights.
- CI on the Arena branch is green. PR #14's current green check belongs to its
  older head and must be rerun after the head branch advances.

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
  '+refs/heads/main:refs/remotes/origin/main' \
  '+refs/heads/arena/cf79e7b7-x-sentiment-price-predictor:refs/remotes/origin/arena/cf79e7b7-x-sentiment-price-predictor' \
  '+refs/heads/feat/sentiment-features-and-forecasting:refs/remotes/origin/feat/sentiment-features-and-forecasting' \
  '+refs/heads/docs/canonical-source-of-truth:refs/remotes/origin/docs/canonical-source-of-truth'

FEAT=origin/feat/sentiment-features-and-forecasting
ARENA=origin/arena/cf79e7b7-x-sentiment-price-predictor
BASE=origin/docs/canonical-source-of-truth

git rev-parse "$FEAT" "$ARENA" "$BASE"
git merge-base --is-ancestor "$BASE" "$FEAT"
git merge-base --is-ancestor "$FEAT" "$ARENA"
```

The last two commands must exit zero. If either fails, stop: the graph has
diverged and a fast-forward is not safe.

## Step 2 — confirm the feature branch has not unexpectedly advanced

```bash
EXPECTED_FEAT=5af5bc7a50c4b56edc1efe3aae4fce2501bdc656
ACTUAL_FEAT=$(git rev-parse "$FEAT")
test "$ACTUAL_FEAT" = "$EXPECTED_FEAT" || {
  echo "STOP: feature branch is now $ACTUAL_FEAT, not $EXPECTED_FEAT" >&2
  exit 1
}

COUNTS=$(git rev-list --left-right --count "$FEAT...$ARENA")
LEFT=${COUNTS%%$'\t'*}
RIGHT=${COUNTS##*$'\t'}
echo "feat-only=$LEFT arena-only=$RIGHT"
test "$LEFT" -eq 0 || { echo "STOP: feature branch has diverged" >&2; exit 1; }
test "$RIGHT" -ge 1 || { echo "STOP: arena branch is not ahead" >&2; exit 1; }

git log --oneline --decorate "$FEAT..$ARENA"
git diff --check "$FEAT..$ARENA"
git diff --stat "$FEAT..$ARENA"
```

`LEFT` must be exactly `0`. `RIGHT` is the number of new commits to promote; it
will be at least one. `git diff --check` must be clean. The diff should contain
only the verified implementation, tests, CI configuration and documentation
changes described in the submission package.

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

## Step 4 — fast-forward and push normally

```bash
if git show-ref --verify --quiet refs/heads/feat/sentiment-features-and-forecasting; then
  git switch feat/sentiment-features-and-forecasting
  git merge --ff-only "$FEAT"
else
  git switch --create feat/sentiment-features-and-forecasting --track "$FEAT"
fi

git merge --ff-only "$ARENA"
git status --short --branch
git push origin feat/sentiment-features-and-forecasting
```

`git merge --ff-only` cannot create a merge commit; it only moves the branch
pointer to a descendant. A normal `git push` will be rejected if someone advanced
the remote branch in the meantime. If that happens, re-fetch and restart at Step
1 instead of forcing.

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

PR #14 should now report the same head SHA as the remote feature branch. Both the
push event and the pull-request event may trigger the CI workflow because
`.github/workflows/ci.yml` contains `feat/**` in its push and pull-request branch
filters. Wait for the checks attached to the new head, not the older check on
`5af5bc7`.

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
