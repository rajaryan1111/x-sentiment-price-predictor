# Safe PR #14 promotion procedure

**Promotion status: COMPLETED on 2026-10-28.** The verified work was committed
as `d8016610aa7ebf82263413c48b1164e4a64d13df` and pushed to
`feat/sentiment-features-and-forecasting` with a normal non-forced fast-forward
(`5af5bc7..d801661`). PR #14 now evaluates that exact SHA and its CI is green.
No force-push, history rewrite, base change, draft-state change or merge occurred.
The procedure below is retained as the record of how it was done and as the safe
repeat path if the head ever needs to advance again.

**Purpose:** move verified Arena-branch work into the existing PR #14 head
branch with a normal, non-forced fast-forward. The earlier assumption that this
session could push only to the Arena branch was tested and disproven; the plain
push to the feature branch succeeded from here.

**Repository:** <https://github.com/rajaryan1111/x-sentiment-price-predictor>
**PR:** <https://github.com/rajaryan1111/x-sentiment-price-predictor/pull/14>
**Base:** `docs/canonical-source-of-truth`
**PR head branch:** `feat/sentiment-features-and-forecasting`

## Verified state on 2026-10-28 (after promotion)

- Remote feature / PR #14 head: `d8016610aa7ebf82263413c48b1164e4a64d13df`
  (equals local HEAD; working tree clean).
- PR base `docs/canonical-source-of-truth`:
  `36b7b486bb60b54f3f19201f2e548b11e5f93197`.
- Remote Arena branch: `c0cd3c113c71a25d02ebf9931b6d7b2f42b5109f` (unchanged by
  this promotion; Arena CI run `40570468109` remains valid for that SHA).
- PR #14 metadata: OPEN, DRAFT, MERGEABLE.
- Fresh CI on the delivered head, both `success`:
  run `40616497449` (push) and run `40616501268` (pull_request) —
  <https://github.com/rajaryan1111/x-sentiment-price-predictor/actions/runs/40616497449>
  and <https://github.com/rajaryan1111/x-sentiment-price-predictor/actions/runs/40616501268>.
  Older runs `40398880548`/`40398888540` (head `5af5bc7`) are historical only.
- Ancestry rechecked after the push: base is an ancestor of feature, Arena is an
  ancestor of feature, and `git rev-list --left-right --count feature...arena`
  returns `1 0` (feature strictly ahead, no divergence).
- GitHub branch API reported `protected=false` for the feature branch and zero
  repository rulesets, which is why the plain fast-forward push was accepted.

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
# Reconfirm PR metadata rather than assuming the remembered feature SHA is current.
EXPECTED_FEAT=d8016610aa7ebf82263413c48b1164e4a64d13df
ACTUAL_FEAT=$(git rev-parse "$FEAT")
test "$ACTUAL_FEAT" = "$EXPECTED_FEAT" || {
  echo "STOP: feature branch is now $ACTUAL_FEAT, not the verified $EXPECTED_FEAT" >&2
  echo "Re-inspect PR #14, review the new commits, then update EXPECTED_FEAT only if safe." >&2
  exit 1
}

COUNTS=$(git rev-list --left-right --count "$FEAT...$ARENA")
LEFT=${COUNTS%%$'\t'*}
RIGHT=${COUNTS##*$'\t'}
echo "feat-only=$LEFT arena-only=$RIGHT"
# Promotion already happened, so the current state is feat-only=1 arena-only=0:
# feature contains Arena. The arena -> feature fast-forward run on 2026-10-28 was
# valid only while feat-only was 0 and arena-only was >= 1. If either guard does
# not hold now, push nothing; re-derive the direction from the two live SHAs.
test "$LEFT" -eq 1 && test "$RIGHT" -eq 0 || {
  echo "STOP: refs no longer match the recorded post-promotion state" >&2
  echo "Inspect $FEAT and $ARENA before deciding anything." >&2
  exit 1
}

git log --oneline --decorate "$ARENA..$FEAT"
git diff --check "$ARENA..$FEAT"
git diff --stat "$ARENA..$FEAT"
```

The only feature-only commit should be the verified delivery commit `d801661`
listed above. `git diff --check` must be clean, and the diff should contain only
the verified implementation, tests, CI configuration and documentation changes
described in the submission package. Pre-promotion, the equivalent check was
`feat-only=0` with `arena-only >= 1`, and `git diff --check "$FEAT..$ARENA"`.

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

PR #14 should now report the same head SHA as the remote feature branch — for the
2026-10-28 promotion it reported `d8016610aa7ebf82263413c48b1164e4a64d13df`.
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
