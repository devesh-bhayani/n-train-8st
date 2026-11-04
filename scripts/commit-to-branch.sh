#!/usr/bin/env bash
# Copy a directory into a data branch and push it. Used by the GitHub Actions loggers,
# which call it repeatedly during a run (so it must be safe to call many times).
#
#   scripts/commit-to-branch.sh <branch> <source-dir> <dest-subdir> <commit message>
#
# Creates the branch (as an orphan) on first use. Files ending in .tmp (being written)
# are skipped. Retries the push with a rebase, because several runs can write at once.
set -euo pipefail
branch="$1"; src="$2"; dest="$3"; msg="$4"

if [ ! -d "$src" ] || [ -z "$(ls -A "$src")" ]; then
  echo "nothing to commit: $src is missing or empty"
  exit 0
fi

git config --global user.name "github-actions[bot]"
git config --global user.email "41898282+github-actions[bot]@users.noreply.github.com"

tmp="$(mktemp -d)"
wt="$tmp/branch"
cleanup() { git worktree remove --force "$wt" 2>/dev/null || true; rm -rf "$tmp"; }
trap cleanup EXIT

if git ls-remote --exit-code --heads origin "$branch" > /dev/null; then
  git fetch -q --depth=1 origin "$branch:refs/remotes/origin/$branch"
  git worktree add -q --detach "$wt" "refs/remotes/origin/$branch"
else
  git worktree add -q --orphan -b "$branch-$$" "$wt"
fi

mkdir -p "$wt/$dest"
cp -r "$src/." "$wt/$dest/"
find "$wt/$dest" -name '*.tmp' -delete
cd "$wt"
git add "$dest"
if git diff --cached --quiet; then
  echo "nothing new"
  exit 0
fi
git commit -q -m "$msg"

for i in 1 2 3 4 5; do
  if git push -q origin "HEAD:refs/heads/$branch"; then
    echo "pushed to $branch"
    exit 0
  fi
  sleep $((2 ** i))
  git fetch -q --depth=50 origin "$branch:refs/remotes/origin/$branch"
  git rebase -q "refs/remotes/origin/$branch"
done
echo "push failed after retries"
exit 1
