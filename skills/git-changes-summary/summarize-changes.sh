#!/usr/bin/env bash
# Summarizes git changes since a given date or commit SHA.
# Usage: summarize-changes.sh [date|commit-sha]
#   date examples: "yesterday", "2026-04-01", "3 days ago", "last week"
#   commit example: a1b2c3d
# Defaults to changes since yesterday.

set -euo pipefail

ARG="${1:-yesterday}"

# Resolve the base commit
if [[ "$ARG" =~ ^[0-9a-f]{7,40}$ ]]; then
  # Treat as a commit SHA - base is its parent
  BASE="${ARG}^"
  LABEL="since commit ${ARG:0:7}"
else
  # Treat as a date - find the last commit strictly before that date
  BASE=$(git log --before="$ARG" --format="%H" -1)
  if [[ -z "$BASE" ]]; then
    echo "No commits found before '$ARG' — showing full history." >&2
    BASE=$(git rev-list --max-parents=0 HEAD)
  fi
  LABEL="since $ARG"
fi

RANGE="${BASE}..HEAD"
COMMIT_COUNT=$(git log "$RANGE" --oneline --no-merges | wc -l | tr -d ' ')

if [[ "$COMMIT_COUNT" -eq 0 ]]; then
  echo "No commits found $LABEL."
  exit 0
fi

echo "### Git Changes $LABEL ($COMMIT_COUNT commits)"
echo ""

echo "#### Commits"
git log "$RANGE" --oneline --no-merges
echo ""

echo "#### Files Changed"
git diff "$RANGE" --stat
echo ""

echo "#### Full Diff"
git diff "$RANGE"
