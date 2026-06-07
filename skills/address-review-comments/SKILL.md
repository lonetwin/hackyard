---
name: address-review-comments
description: Use when asked to address, work through, or tackle open PR review comments on the current branch. Triggers on phrases like "address review comments", "work through the PR comments", "tackle review feedback".
allowed-tools: shell
---

# Address Review Comments

## Overview

Fetch all open PR review comments, categorize them by validity and effort, present the grouping for confirmation, then work through each category in order.

**Core principle:** Evaluate first, act second. Never blindly implement or dismiss.

## Workflow

```
1. Fetch all open (unresolved) review threads for the PR on this branch
2. Read every comment and categorize each into one of:
   - invalid, only respond    → concern is not valid; reply explaining why, resolve
   - valid but trivial, fix and respond → valid concern, small/obvious fix; fix + reply, resolve
   - valid, fix and respond   → valid concern requiring real work; fix + reply, resolve
3. Present the full categorized list to the user and ask for confirmation
   (user may recategorize before proceeding)
4. Work through categories IN ORDER: invalid → trivial → valid
5. For each thread (one at a time):
   a. Present your analysis and proposed action
   b. ASK: "Shall I proceed, or would you like a different approach?"
   c. On confirmation: act (implement and/or reply), then resolve thread
   d. Move to the next thread
```

## Fetching Comments

```bash
# Get PR number for current branch
PR=$(gh pr view --json number --jq '.number')

# List unresolved review threads (id, path, line, body)
gh pr view $PR --json reviewThreads \
  --jq '[.reviewThreads[] | select(.isResolved == false)] | reverse | .[]
        | "Thread \(.id)\nFile: \(.path // "general"):\(.line // "N/A")\nComment: \(.comments[0].body)\n---"'
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
- [File: path:line] — [one-line summary of concern + why invalid]

**Valid but trivial, fix and respond** (N)
- [File: path:line] — [one-line summary + proposed fix]

**Valid, fix and respond** (N)
- [File: path:line] — [one-line summary + proposed fix approach]

Does this look right? Any recategorizations before I start?
```

## Per-Thread Prompt

When working each item:

```
**[Category] — File: path:line**
> [quoted comment body]

**Analysis:** [Why valid/invalid, what impact]
**Proposed action:** [Specific fix or reply text]

Shall I proceed?
```

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Implementing without asking | Always present categorization and confirm before acting |
| Resolving without acting | Only resolve after fix is made OR reply is posted |
| Dismissing valid concerns | If uncertain, lean toward implementing the fix |
| Addressing all at once | One thread at a time — wait for user confirmation each time |
| Skipping the categorization step | Always group and confirm first — user may disagree with your assessment |
