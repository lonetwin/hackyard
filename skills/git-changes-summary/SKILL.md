---
name: git-changes-summary
description: Summarizes git changes since a given date or commit. Use when asked to summarize recent changes, write a standup update, generate a changelog, or explain what has changed in the codebase recently.
allowed-tools: shell
---

## Git Changes Summary

When asked to summarize recent changes, use the `summarize-changes.sh` script from this skill's directory.

### Running the script

```bash
bash <skill-base-dir>/summarize-changes.sh [date|commit-sha]
```

- **No argument** — changes since yesterday (default)
- **Date string** — e.g. `"2026-04-01"`, `"3 days ago"`, `"last week"` (any format accepted by `git log --before`)
- **Commit SHA** — e.g. `a1b2c3d` — summarizes changes since that specific commit

### Presenting the summary

After running the script, produce a summary in this structure:

1. **Overview** — one sentence: how many commits, how many files, the date range
2. **What changed** — group changes by theme:
   - New features or functionality
   - Bug fixes
   - Refactoring or code quality
   - Tests
   - Config, tooling, or dependencies
3. **Notable changes** — call out anything particularly significant, risky, or surprising
4. **Most affected files** — list the top 3–5 files with a brief note on why each changed

Keep the summary tight enough for a standup or PR description by default. If the user asks for more detail, expand each section.
