# Skills for your AI REPL thingy

* [github-actions-monitor](./git-changes-summary/) - Summarizes changes since a given date of commit. Relies on the `git log` + `git diff` commands instead of forcing the LLM figure it out each time.

  Example invocation:
  - Show me the changes in this repo since yesterday"

* [github-actions-monitor](./github-actions-monitor/) - Uses the [gh](https://cli.github.com/) to query github actions jobs as well as debug any failed runs.

  Example invocations:
  - List out the active jobs
  - List out the 3 most recent failed runs in the CI workflow
  - What went wrong with run id 24090589644 ?
