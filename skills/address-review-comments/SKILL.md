---
name: address-review-comments
description: Use when asked to address, work through, or tackle open PR review comments on the current branch. Triggers on phrases like "address review comments", "work through the PR comments", "tackle review feedback".
allowed-tools: shell
---

# Address Review Comments

## Overview

Fetch all open PR review comments, categorize them by validity and effort, present the grouping for confirmation, then work through each category in order.

**Core principle:** Evaluate first, act second. Never blindly implement or dismiss.

## Model Strategy

Use a cheap, fast model (e.g. `claude-haiku-4.5`) for everything except non-trivial fixes:

| Step | Model |
|------|-------|
| Fetch + categorize comments (steps 1–2) | cheap (`claude-haiku-4.5`) |
| Present categorization + await confirmation (step 3) | cheap |
| Work through **invalid** threads (step 4) | cheap |
| Work through **trivial** threads (step 4) | cheap |
| Work through **valid (non-trivial)** threads (step 5) | **current (full) model** |
| Commit + push (step 6) | cheap |

To run a step with the cheap model, dispatch it via the `task` tool with `model: "claude-haiku-4.5"`.

## Workflow

```
1. [cheap] Fetch all open (unresolved) review threads for the PR on this branch
2. [cheap] Read every comment and categorize each into one of:
   - invalid, only respond    → concern is not valid; reply explaining why, resolve
   - valid but trivial, fix and respond → valid concern, small/obvious fix; fix + reply, resolve
   - valid, fix and respond   → valid concern requiring real work; fix + reply, resolve
3. [cheap] Present the full categorized list to the user and ask for confirmation
   (user may recategorize before proceeding)
4. [cheap] Work through invalid and trivial categories IN ORDER: invalid → trivial
   FOR EACH THREAD:
   a. Implement any code fixes
   b. Post a reply explaining what was done (or why the concern is invalid)
   c. Resolve the thread using GraphQL
5. [full model] Work through valid (non-trivial) threads, one at a time:
   a. Present your analysis and proposed action
   b. ASK: "Shall I proceed, or would you like a different approach?"
   c. On confirmation:
      - Implement the fix
      - Post a reply summarizing the changes
      - Resolve the thread using GraphQL
   d. Move to the next thread
6. [cheap] After all threads have been dealt with:
   a. Verify ALL threads show as resolved (query: isResolved == true)
   b. If any code changes were made, create a commit with all changes
   c. Present the commit description for approval
   d. If approved, push the commit
```

⚠️ **CRITICAL:** Every single thread (invalid, trivial, valid) must have:
1. A reply posted explaining what was done/why
2. The thread marked as resolved

Do NOT skip posting replies or resolving threads, even for trivial fixes.

## Fetching Comments

```bash
# Get PR number for current branch
PR=$(gh pr view --json number --jq '.number')

# List unresolved review threads (id, path, line, body, diff hunk)
gh pr view $PR --json reviewThreads \
  --jq '[.reviewThreads[] | select(.isResolved == false)] | reverse | .[]
        | "Thread \(.id)\nFile: \(.path // "general"):\(.line // "N/A")\nDiff:\n\(.comments[0].diffHunk)\nComment: \(.comments[0].body)\n---"'
```

## Resolving a Thread

After implementing a fix or posting a reply, resolve the thread via GraphQL:

```bash
gh api graphql -f query='
  mutation {
    resolveReviewThread(input: { threadId: "THREAD_ID" }) {
      thread { id isResolved }
    }
  }
'
```

## Replying to a Comment

```bash
# Get comment ID from thread
COMMENT_ID=$(gh pr view $PR --json reviewThreads \
  --jq '.reviewThreads[] | select(.id == "THREAD_ID") | .comments[0].databaseId')

gh api repos/{owner}/{repo}/pulls/comments/$COMMENT_ID/replies \
  -X POST -f body="YOUR REPLY"
```

Get `{owner}/{repo}` with: `gh repo view --json owner,name --jq '"\(.owner.login)/\(.name)"'`

## Categorization Presentation

Before acting, present the full grouped list:

```
**Invalid, only respond** (N)
1. [File: path:line] — [one-line summary of concern + why invalid]

**Valid but trivial, fix and respond** (N)
2. [File: path:line] — [one-line summary + proposed fix]

**Valid, fix and respond** (N)
3. [File: path:line] — [one-line summary + proposed fix approach]

Does this look right? Any recategorizations before I start?
  (You can refer to items by number, e.g. "move #2 to valid" or "skip #3")
```

## Per-Thread Prompt

When working each item:

````
**[Category] — File: path:line**

**Code context:**
```diff
[actual diffHunk from the review thread]
```

**Comment:**
> [verbatim comment body — copy exactly as written, do not paraphrase]

**Analysis:** [Why valid/invalid, what impact]
**Proposed action:** [Specific fix or reply text]

Shall I proceed?
````

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Implementing without asking | Always present categorization and confirm before acting |
| Resolving without acting | Only resolve after fix is made OR reply is posted |
| Dismissing valid concerns | If uncertain, lean toward implementing the fix |
| Addressing all at once | One thread at a time — wait for user confirmation each time |
| Skipping the categorization step | Always group and confirm first — user may disagree with your assessment |
| Not committing after finishing | Always commit and push all code changes once all threads are resolved |
| **Skipping replies on trivial/invalid threads** | **Every thread must have a reply posted and be marked resolved — not just non-trivial ones** |
| Delegating all work then not resolving | When using cheap model tasks for fixes, YOU must still post replies and resolve threads afterward |
| Verifying only code changes | Verify the PR shows 0 unresolved review threads before declaring done |
