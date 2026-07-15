---
inclusion: manual
description: "Manual slash command (/backup-project): run the project backup on request. Replaces the former backup-project-on-request manual hook."
---

# Back Up Your Project

Manually invoke this command by name when you want to back up your project. It
replaces the former `backup-project-on-request` manual hook. When invoked,
follow the instruction below verbatim:

```text
The user wants to back up their project. Run the backup script: python3 scripts/backup_project.py (on Linux/macOS) or python scripts/backup_project.py (on Windows). Create the backups/ directory first if it doesn't exist.
```
