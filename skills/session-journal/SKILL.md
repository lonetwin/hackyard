---
name: session-journal
description: Creates blog-post style journal entries from Copilot CLI session history. Use when asked to "journal today's sessions", "write my dev journal for yesterday", "summarize my sessions from [date]", "create a journal entry for [timeframe]", or "journal the last N days".
allowed-tools: shell, ask_user, task
---

# Session Journal Skill

This skill queries your Copilot CLI session history and writes formatted markdown journal entries, one per session, aggregated into a daily index.

## Step 1 — Parse the timeframe

Determine the time window from the user's message using this table. Both values must be formatted as `YYYY-MM-DDTHH:MM:SS` (no timezone suffix).

| User says | `from_iso` | `to_iso` |
|-----------|-----------|---------|
| (nothing / default) | now minus 24 hours | now |
| "today" | today at `00:00:00` | now |
| "yesterday" | yesterday at `00:00:00` | yesterday at `23:59:59` |
| "last N days" | N days ago at `00:00:00` | now |
| "YYYY-MM-DD to YYYY-MM-DD" | first date at `00:00:00` | last date at `23:59:59` |

Use the `bash` tool to get the current date/time if needed: `date '+%Y-%m-%dT%H:%M:%S'`

## Step 2 — Resolve journal directory

Check if the `JOURNAL_DIR` environment variable is set:

```bash
echo "${JOURNAL_DIR:-~/src/journal}"
```

Expand `~` to the absolute home directory path. Store this as the journal directory for all subsequent file operations.

## Step 3 — Query session data

Run the query script and capture its output:

```bash
python3 <skill-base-dir>/query-sessions.py "<from_iso>" "<to_iso>"
```

Replace `<skill-base-dir>` with `~/.copilot/skills/session-journal`.

If the command exits non-zero, report the stderr message to the user and stop.

## Step 4 — Check for sessions

Parse the JSON output. If the `sessions` array is empty, tell the user:

> "No Copilot CLI sessions found between `<from_iso>` and `<to_iso>`."

Then stop — do not proceed to model selection.

## Step 5 — Ask user to choose the writing model

Use the `ask_user` tool with:

- **question:** "Which model should write the journal entries?"
- **choices:**
  - `claude-haiku-4.5` *(recommended — fast and cheap)*
  - `gemini-3.5-flash`
  - `gpt-5.4-mini`
  - Current session model (whatever model is running now)

Map the choice to a model ID for the `task` tool:
- `claude-haiku-4.5` → `"claude-haiku-4.5"`
- `gemini-3.5-flash` → `"gemini-3.5-flash"`
- `gpt-5.4-mini` → `"gpt-5.4-mini"`
- Current session model → omit the `model` field from the `task` call

## Step 6 — Dispatch writing sub-agent

Use the `task` tool with `agent_type: "general-purpose"` and the chosen model. The prompt must include the full session JSON inline.

**Prompt template** (substitute `JOURNAL_DIR` and `SESSION_JSON` before dispatching):

---

You are writing developer journal entries. Your output will be saved as markdown files.

**Journal directory:** `JOURNAL_DIR`

**Session data:**
```json
SESSION_JSON
```

---

### For each session: write a per-session markdown file

**Step A — Determine the output path:**

- Date: the `YYYY-MM-DD` portion of `created_at`
- Slug: take the first checkpoint's `title` (if non-empty), else `summary`, else `session-<first-8-chars-of-id>`. Slugify: lowercase, replace spaces/punctuation with hyphens, truncate to 50 chars. Prepend the date: `YYYY-MM-DD-<slug>`.
- Path: `JOURNAL_DIR/YYYY-MM-DD/YYYY-MM-DD-<slug>.md`
- If a file at that path already exists on disk, **overwrite** it — always regenerate to pick up the latest turn data.
- If two sessions produce the same slug, append `-2`, `-3`, etc.

**Step B — Write the file:**

```markdown
---
date: <created_at value>
repository: <repository>
branch: <branch>
session_id: <id>
model: <the model name you are currently using>
tags:
  - <3 to 5 lowercase keyword tags derived from checkpoint titles, overviews, and technical_details>
refs:
  <for each item in the refs array — omit this key entirely if refs is empty>
  - type: <ref_type>
    <if ref_type is "commit": add `sha: <ref_value>` and, if repository is set, add `url: https://github.com/<repository>/commit/<ref_value>`>
    <if ref_type is "pr" or "issue": add `url: <ref_value>` (it will already be a URL)>
    title: "<short human description if inferrable, else omit>"
---

# <First checkpoint title, or session summary, or "Session <first-8-chars-of-id>">

## Overview
<Narrative synthesised from the full conversation — checkpoint overviews and all turns. Write as many paragraphs as needed to tell the story of the session without losing relevant detail. Preserve specific references: numbers, environment variables, config file names, command names, file paths, error messages, and anything quoted in backticks are likely significant — weave them into the narrative naturally. Do NOT copy conversation verbatim or list checkpoint titles; synthesise into flowing prose that captures what was being done, why, and what was found or decided. The goal is a readable narrative, not an exhaustive transcript.>

## What Was Done
<Bullet list from work_done fields across all checkpoints. Be specific. Skip bullets that are empty.>

## Technical Details
<Narrative from technical_details fields. Omit this section entirely if all technical_details values are empty strings.>

## Files Changed
<Use this hierarchy — default to omitting the section:>
<• If the prose summary conveys the idea without code: omit this section entirely (default).>
<• If a short excerpt (≤15 lines) from a file makes the entry significantly clearer: include as a fenced code block with a comment `# from <relative-path>`. Only do this if the file was edited (tool_name="edit" or "create").>
<• Copy a file only if it IS the primary artefact (e.g. a new config, script, spec) AND a snippet is inadequate. Criteria: tool_name="edit"/"create", inside repo directory, not a lock/build/generated file. Max 2 copies. Copy to JOURNAL_DIR/YYYY-MM-DD/files/<basename> and link as [`basename`](./files/basename).>

## Links
<One line per ref: "PR #N: <url>", "Commit `<sha[:7]>`: <url>", "Issue #N: <url>". Omit this section if refs is empty.>

## Next Steps
<From the last checkpoint's next_steps field. Omit this section if empty.>
```

---

### Write/update the daily index file

**Path:** `JOURNAL_DIR/YYYY-MM-DD/index.md`

**If the file already exists:**
1. Read it and parse the `sessions` YAML frontmatter array.
2. Skip any session IDs already in the array.
3. Append new sessions to BOTH the frontmatter array and the prose list.

**If the file does not exist:**
Create it fresh with this format:

```markdown
---
date: YYYY-MM-DD
sessions:
  - id: <session_id>
    file: <filename.md>
    title: "<session title>"
    time: "HH:MM"
---

# Dev Journal — <Day of week, D Month YYYY>

## Sessions
- HH:MM [<session title>](./<filename.md>) — `<repository>` on `<branch>`
```

(`time` is the 24h HH:MM from `created_at`; one line per session ordered by `created_at` ascending)

---

### Report back

When done, respond with a summary:
- Sessions journalled: N
- Files written: list of relative paths from journal root
- Links captured: list any PR/issue/commit refs found

---

## Step 7 — Relay results to user

Take the sub-agent's summary and present it to the user in a clean format, listing the files written and any notable links captured.
