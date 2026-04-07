#!/usr/bin/env bash
# Fetches details and logs for a specific GitHub Actions job ID.
# Usage: explain-job.sh <job-id> [max-lines]
#   job-id:    the numeric job ID shown by failed-jobs.sh
#   max-lines: how many lines of logs to include (default: 300)

set -euo pipefail

JOB_ID="${1:?Usage: explain-job.sh <job-id> [max-lines]}"
MAX_LINES="${2:-300}"

REPO=$(gh repo view --json nameWithOwner -q '.nameWithOwner' 2>/dev/null || true)
if [[ -z "$REPO" ]]; then
  echo "Error: not inside a GitHub repository directory." >&2
  exit 1
fi

echo "### Job Details — Job $JOB_ID ($REPO)"
echo ""

# Metadata: name, conclusion, step summary
gh api "repos/$REPO/actions/jobs/$JOB_ID" --jq '
{
  name:         .name,
  conclusion:   .conclusion,
  status:       .status,
  started_at:   .started_at,
  completed_at: .completed_at,
  html_url:     .html_url,
  failed_steps: [.steps[] | select(.conclusion == "failure") | {number: .number, name: .name}],
  all_steps:    [.steps[] | {number: .number, name: .name, conclusion: .conclusion}]
}' | jq .

echo ""
echo "### Logs (last $MAX_LINES lines)"
echo ""

# Fetch logs — the API returns plain text
gh api "repos/$REPO/actions/jobs/$JOB_ID/logs" 2>/dev/null | tail -"$MAX_LINES" \
  || {
    echo "(API log fetch failed — falling back to run view)"
    gh run view --job="$JOB_ID" --repo "$REPO" --log 2>/dev/null | tail -"$MAX_LINES"
  }
