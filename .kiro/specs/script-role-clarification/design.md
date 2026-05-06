# Design: Script Role Clarification

## Overview

With 28 scripts in `senzing-bootcamp/scripts/`, some have overlapping names or unclear boundaries. This design clarifies each script's role, updates documentation, and adds cross-references.

## Current Script Inventory (by category)

### Status & Validation

- `status.py` — Project health dashboard (progress, data sources, hooks)
- `preflight.py` — Pre-session environment checks
- `validate_power.py` — CI: validates power structure and manifest
- `validate_module.py` — Validates a specific module's steering file structure
- `validate_commonmark.py` — CI: validates Markdown compliance
- `validate_data_files.py` — Validates data source files (format, encoding)
- `validate_dependencies.py` — CI: validates module-dependencies.yaml (uses PyYAML)

### Progress Management

- `progress_utils.py` — Library: progress file read/write/validate (not a CLI tool)
- `repair_progress.py` — Fixes corrupted bootcamp_progress.json
- `rollback_module.py` — Reverts a module's progress and artifacts
- `restore_project.py` — Restores from a backup archive

### Data Management

- `data_sources.py` — Data source registry CLI (table, detail, summary views)
- `export_results.py` — Exports bootcamp artifacts to HTML/ZIP
- `backup_project.py` — Creates timestamped project backups

### Hooks & Configuration

- `install_hooks.py` — Installs hook files into the workspace
- `sync_hook_registry.py` — CI: verifies hook-registry.md matches hook files
- `team_config_validator.py` — Validates team.yaml configuration

### Analysis & Reporting

- `analyze_sessions.py` — Session analytics: per-module summary, confusion ranking
- `session_logger.py` — Library: appends log entries to session_log.jsonl
- `merge_feedback.py` — Merges multiple feedback files into one report
- `triage_feedback.py` — Categorizes and prioritizes feedback entries

### Steering Maintenance

- `lint_steering.py` — Lints steering files for style/structure issues
- `measure_steering.py` — Measures token counts, updates steering-index.yaml
- `split_steering.py` — Splits large steering files into phases

### Dashboards

- `team_dashboard.py` — Team progress overview (multi-member tracking)
- `test_dashboard.py` — Test suite results dashboard (CI/dev use)

### Utilities

- `verbosity.py` — Library: verbosity level helpers

## Identified Overlaps and Clarifications

### team_dashboard.py vs test_dashboard.py

These serve different audiences and purposes:

- `team_dashboard.py` — For team leads: shows per-member module progress, completion rates, active sessions
- `test_dashboard.py` — For developers/maintainers: shows test suite pass/fail rates, coverage, recent failures

**Action**: Rename is not needed — the names are distinct. Add clear one-line descriptions to `--help` and SCRIPT_REFERENCE.md.

### status.py vs analyze_sessions.py

- `status.py` — Current state snapshot (what's happening now)
- `analyze_sessions.py` — Historical analysis (what happened over time)

**Action**: Add "See Also" cross-references in `--help` output.

### validate_power.py vs validate_module.py vs validate_commonmark.py

- `validate_power.py` — Whole-power structural validation (CI)
- `validate_module.py` — Single module steering validation
- `validate_commonmark.py` — Markdown syntax validation (CI)

**Action**: Document the validation hierarchy in SCRIPT_REFERENCE.md.

### session_logger.py vs analyze_sessions.py

- `session_logger.py` — Write-only library (appends entries)
- `analyze_sessions.py` — Read-only CLI (analyzes entries)

**Action**: Mark `session_logger.py` as a library (not a standalone CLI) in documentation.

## Design Decisions

1. **No consolidation needed** — After audit, no scripts are truly redundant. The overlaps are complementary (write vs read, current vs historical, team vs dev).
2. **Documentation-first approach** — Update SCRIPT_REFERENCE.md with categories, one-line purposes, and cross-references.
3. **--help improvements** — Add "See Also" lines to related scripts.
4. **Library marking** — Scripts that are libraries (not CLI tools) get a note in docs: `progress_utils.py`, `session_logger.py`, `verbosity.py`.

## Files Modified

- `senzing-bootcamp/docs/guides/SCRIPT_REFERENCE.md` — Reorganize with categories and cross-references
- `senzing-bootcamp/POWER.md` — Update "Useful Commands" section if needed
- Individual scripts — Add "See Also" to argparse epilog where relevant
