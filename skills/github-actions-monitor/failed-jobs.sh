#!/usr/bin/env bash
# Lists recent failed workflow runs and their individual failed jobs with IDs and log URLs.
# Usage: failed-jobs.sh [limit]
#   limit: number of failed runs to inspect (default: 5)

set -euo pipefail

LIMIT="${1:-5}"

REPO=$(gh repo view --json nameWithOwner -q '.nameWithOwner' 2>/dev/null || true)
if [[ -z "$REPO" ]]; then
  echo "Error: not inside a GitHub repository directory." >&2
  exit 1
fi

echo "### Recent Failed Jobs — $REPO (last $LIMIT failed runs)"
echo ""

RUNS=$(gh run list --repo "$REPO" --status=failure --limit="$LIMIT" \
  --json databaseId,displayTitle,workflowName,updatedAt,url)

RUN_COUNT=$(echo "$RUNS" | jq 'length')
if [[ "$RUN_COUNT" -eq 0 ]]; then
  echo "No failed runs found."
  exit 0
fi

echo "$RUNS" | jq -c '.[]' | while IFS= read -r RUN; do
  RUN_ID=$(echo "$RUN" | jq -r '.databaseId')
  WORKFLOW=$(echo "$RUN" | jq -r '.workflowName')
  TITLE=$(echo "$RUN" | jq -r '.displayTitle')
  UPDATED=$(echo "$RUN" | jq -r '.updatedAt')

  echo "#### Run $RUN_ID — $WORKFLOW: $TITLE"
  echo "Updated: $UPDATED"
  echo "Run URL: $(echo "$RUN" | jq -r '.url')"
  echo ""

  FAILED_JOBS=$(gh run view "$RUN_ID" --repo "$REPO" --json jobs \
    2>/dev/null | jq '[.jobs[] | select(.conclusion == "failure")]')

  JOB_COUNT=$(echo "$FAILED_JOBS" | jq 'length')
  if [[ "$JOB_COUNT" -eq 0 ]]; then
    echo "  (no individual failed jobs found)"
  else
    echo "$FAILED_JOBS" | jq -r '.[] |
      "  Job ID:  \(.databaseId)\n  Name:    \(.name)\n  Log URL: \(.url)\n"'
  fi
done
