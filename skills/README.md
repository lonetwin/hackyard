# Skills for your AI REPL thingy

* [address-review-comments](./address-review-comments/) - Use to work through (unresolved) PR review comments for the branch you're on currently

  Example invocation:
  - let's address this PR's review comments

* [github-changes-summary](./git-changes-summary/) - Summarizes changes since a given date of commit. Relies on the `git log` + `git diff` commands instead of forcing the LLM figure it out each time.

  Example invocation:
  - Show me the changes in this repo since yesterday

* [github-actions-monitor](./github-actions-monitor/) - Uses the [gh](https://cli.github.com/) to query github actions jobs as well as debug any failed runs.

  Example invocations:
  - List out the active jobs
  - List out the 3 most recent failed runs in the CI workflow
  - What went wrong with run id 24090589644 ?

* [session-journal](./session-journal) - a daily journal of your Github Copilot sessions. Stores these in the path specified by `$JOURNAL_DIR`  (defaults to `~/src/journal` -- update this default directly in the `SKILL.mc` file)
  > [!TIP]
  > 
  > The file [viewer.html](./session-journal/viewer.html) has a simple
  > self-contained viewer for the entires. Use `python -m http.server` in
  > `$JOURNAL_DIR` to view these at localhost:8000

  Example invocations:
  - journal today's sessions
  - write my dev journal for yesterday
  - summarize my sessions from [date]
  - create a journal entry for [timeframe]
  - journal the last N days
