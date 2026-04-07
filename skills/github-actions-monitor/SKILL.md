---
name: github-actions-monitor
description: >
  Monitor GitHub Actions for the current repository. Use when asked about:
  active or running CI jobs; recent failures or broken builds; why a specific
  job failed; CI status; workflow errors or logs.
allowed-tools: shell
---

## GitHub Actions Monitor

Three scripts are available in this skill's directory. Always run them from
inside the repository you want to inspect.

---

### a) Active Jobs

Show all currently running, queued, or waiting workflow runs:

```bash
bash <skill-base-dir>/active-jobs.sh
```

Present the results as a concise table or list grouped by status. Note how
long jobs have been running and flag anything that looks unexpectedly slow.

---

### b) Recent Failed Jobs

List the most recent failed runs and their individual failed job IDs:

```bash
bash <skill-base-dir>/failed-jobs.sh [limit]
```

- `limit` is optional — how many failed runs to inspect (default: 5)

The output includes:
- The **run ID** and workflow name
- Each failed **job ID** and its name
- A direct **log URL** for each failed job

Present this as a scannable list. Highlight patterns — e.g. if the same job
keeps failing, or multiple jobs in one run all failed. Always show the Job IDs
clearly since they're needed for the next step.

---

### c) Explain a Job Failure

Fetch full details and logs for a specific job and explain what went wrong:

```bash
bash <skill-base-dir>/explain-job.sh <job-id> [max-lines]
```

- `job-id`: the numeric Job ID from the failed-jobs output
- `max-lines`: optional log line limit (default: 300)

The script outputs:
1. Job metadata: name, status, which steps failed, timestamps
2. The tail of the job's raw log output

After running the script, provide:

1. **Root cause** — what specifically caused the failure (error message,
   assertion, missing dependency, etc.)
2. **Which step failed** — the step name and why it failed
3. **Fix suggestion** — a concrete, actionable recommendation
4. **Confidence** — note if the logs are truncated and more context may help

If the logs reference a specific file and line number, suggest using `@` to
include that file for deeper analysis.
