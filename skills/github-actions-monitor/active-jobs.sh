#!/usr/bin/env bash
# Shows currently active (in_progress, queued, waiting) workflow runs.
# Usage: active-jobs.sh

set -euo pipefail

REPO=$(gh repo view --json nameWithOwner -q '.nameWithOwner' 2>/dev/null || true)
if [[ -z "$REPO" ]]; then
  echo "Error: not inside a GitHub repository directory." >&2
  exit 1
fi

echo "### Active Workflow Runs — $REPO"
echo ""

FOUND=0

for STATUS in in_progress queued waiting; do
  RUNS=$(gh run list --repo "$REPO" --status="$STATUS" --limit=20 \
    --json databaseId,displayTitle,workflowName,status,event,updatedAt,url 2>/dev/null)

  COUNT=$(echo "$RUNS" | jq 'length')
  if [[ "$COUNT" -gt 0 ]]; then
    FOUND=1
    LABEL="${STATUS//_/ }"
    echo "#### ${LABEL^} ($COUNT)"
    echo "$RUNS" | jq -r '.[] |
      "  Run \(.databaseId) | \(.workflowName) — \(.displayTitle)\n  Event: \(.event) | Updated: \(.updatedAt)\n  \(.url)\n"'
  fi
done

if [[ "$FOUND" -eq 0 ]]; then
  echo "No active workflow runs found."
fi
