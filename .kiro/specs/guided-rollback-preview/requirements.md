# Requirements: Guided Rollback with Diff Preview

## Overview

`rollback_module.py` exists but operates without showing the bootcamper what will change. This feature adds a preview mode that shows what files will be removed/reverted and what progress entries will be cleared before executing, building confidence in using rollback as a learning tool.

## Requirements

1. The `rollback_module.py` script gains a `--preview` flag (also aliased as `--dry-run`) that shows what would change without making any modifications
2. The preview output includes: files that would be deleted (with sizes), files that would be reverted to a previous state (if backups exist), progress entries that would be cleared from `bootcamp_progress.json`, data source registry entries that would be removed from `config/data_sources.yaml`
3. The preview output is formatted as a summary table similar to `git diff --stat`: file path, action (delete/revert/clear), and size impact
4. When `rollback_module.py` is run without `--preview`, it now shows the preview first and asks for confirmation before proceeding (unless `--yes` flag is provided for non-interactive use)
5. The agent uses the preview output when the bootcamper asks about rollback: it runs `rollback_module.py --preview` and presents the results conversationally before asking "Want me to proceed with the rollback?"
6. The preview identifies irreversible actions (files with no backup) and marks them with a warning indicator
7. If a backup exists for the module (from `backup_project.py`), the preview shows the backup timestamp and path
8. The `--preview` output includes a "Safety Assessment": how many files are backed up vs not, whether the rollback is fully reversible
9. The steering file `module-completion.md` (which handles rollback offers) is updated to instruct the agent to always run preview before confirming rollback
10. Exit code for `--preview` is always 0 (it's informational), regardless of what would be rolled back
11. The preview respects the same module dependency logic as the actual rollback — if rolling back Module 5 would invalidate Module 6 artifacts, the preview warns about downstream impact

## Non-Requirements

- This does not add new backup functionality (that's `backup_project.py`)
- This does not change what rollback actually does — only adds visibility before execution
- This does not provide undo-after-rollback capability
