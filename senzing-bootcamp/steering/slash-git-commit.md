---
inclusion: manual
description: "Manual slash command (/git-commit): remind and help the user commit module progress. Replaces the former git-commit-reminder manual hook."
---

# Commit Your Progress

Manually invoke this command by name when you want to commit your bootcamp
progress. It replaces the former `git-commit-reminder` manual hook. When
invoked, follow the instruction below verbatim:

```text
The user wants to commit their bootcamp progress. Check config/bootcamp_progress.json for the current module number and list of completed modules. Then suggest a git commit with a descriptive message like: git add . && git commit -m "Complete Module [N]: [Module Name]". Show the user the command and ask if they'd like you to run it.
```
