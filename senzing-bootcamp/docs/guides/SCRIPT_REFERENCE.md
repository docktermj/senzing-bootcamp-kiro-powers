# Script Reference

All scripts are cross-platform Python (3.11+, stdlib only) and live in `senzing-bootcamp/scripts/`. Run them from your project root. Use `python` instead of `python3` on Windows.

## Status and Validation

| Script | Purpose |
| --- | --- |
| `status.py` | Project health dashboard — current module, progress, data sources, hooks |
| `preflight.py` | Pre-session environment checks — Python version, Senzing install, disk space |
| `validate_power.py` | CI: validates power structure, cross-references, hooks, and steering |
| `validate_module.py` | Validates a specific module's steering file structure and readiness |
| `validate_commonmark.py` | CI: validates Markdown compliance across all .md files |
| `validate_data_files.py` | Validates data source files for format, encoding, and structure |
| `validate_dependencies.py` | CI: validates module-dependencies.yaml graph consistency (uses PyYAML) |

### Validation Hierarchy

These three validators operate at different scopes:

- `validate_power.py` — whole-power structural validation (runs all checks)
- `validate_module.py` — single module steering validation (focused check)
- `validate_commonmark.py` — Markdown syntax validation only (no semantic checks)

```text
python3 senzing-bootcamp/scripts/status.py
python3 senzing-bootcamp/scripts/status.py --sync
python3 senzing-bootcamp/scripts/preflight.py
python3 senzing-bootcamp/scripts/preflight.py --json
python3 senzing-bootcamp/scripts/preflight.py --fix
python3 senzing-bootcamp/scripts/validate_module.py
python3 senzing-bootcamp/scripts/validate_module.py --next 7
python3 senzing-bootcamp/scripts/validate_power.py
python3 senzing-bootcamp/scripts/validate_commonmark.py
python3 senzing-bootcamp/scripts/validate_data_files.py
python3 senzing-bootcamp/scripts/validate_dependencies.py
```

## Progress Management

| Script | Purpose |
| --- | --- |
| `repair_progress.py` | Fixes corrupted `bootcamp_progress.json` by reconstructing from artifacts |
| `rollback_module.py` | Reverts a module's progress and removes its artifacts |
| `restore_project.py` | Restores the entire project from a timestamped backup archive |

```text
python3 senzing-bootcamp/scripts/repair_progress.py
python3 senzing-bootcamp/scripts/rollback_module.py --module N
python3 senzing-bootcamp/scripts/rollback_module.py --module N --dry-run
python3 senzing-bootcamp/scripts/restore_project.py
```

See Also: `backup_project.py` creates the archives that `restore_project.py` restores.

## Data Management

| Script | Purpose |
| --- | --- |
| `data_sources.py` | Data source registry CLI — table view, detail view, summary statistics |
| `export_results.py` | Exports bootcamp artifacts to HTML report or ZIP archive |
| `backup_project.py` | Creates timestamped project backups for safe rollback |

```text
python3 senzing-bootcamp/scripts/data_sources.py
python3 senzing-bootcamp/scripts/data_sources.py --detail CUSTOMERS
python3 senzing-bootcamp/scripts/data_sources.py --summary
python3 senzing-bootcamp/scripts/export_results.py
python3 senzing-bootcamp/scripts/export_results.py --format zip
python3 senzing-bootcamp/scripts/export_results.py --modules 1,2,3
python3 senzing-bootcamp/scripts/backup_project.py
```

## Hooks and Configuration

| Script | Purpose |
| --- | --- |
| `install_hooks.py` | Installs hook files from the power into the workspace |
| `sync_hook_registry.py` | CI: verifies hook-registry.md matches actual hook files |

```text
python3 senzing-bootcamp/scripts/install_hooks.py
python3 senzing-bootcamp/scripts/sync_hook_registry.py --verify
python3 senzing-bootcamp/scripts/sync_hook_registry.py --write
```

## Analysis and Reporting

| Script | Purpose |
| --- | --- |
| `analyze_sessions.py` | Session analytics — per-module summary, confusion ranking, time tracking |
| `merge_feedback.py` | Merges multiple feedback files into one consolidated report |
| `triage_feedback.py` | Categorizes and prioritizes feedback entries into spec skeletons |

```text
python3 senzing-bootcamp/scripts/analyze_sessions.py config/session_log.jsonl
python3 senzing-bootcamp/scripts/analyze_sessions.py config/session_log.jsonl --format json
python3 senzing-bootcamp/scripts/analyze_sessions.py config/session_log.jsonl --pretty
python3 senzing-bootcamp/scripts/merge_feedback.py
python3 senzing-bootcamp/scripts/merge_feedback.py --output report.md
python3 senzing-bootcamp/scripts/triage_feedback.py docs/feedback/SENZING_BOOTCAMP_POWER_FEEDBACK.md
python3 senzing-bootcamp/scripts/triage_feedback.py --dry-run
```

See Also: `session_logger.py` (library) writes the log entries that `analyze_sessions.py` reads.

## Steering Maintenance

| Script | Purpose |
| --- | --- |
| `lint_steering.py` | Lints steering files for style, structure, and template conformance |
| `measure_steering.py` | Measures token counts, updates steering-index.yaml, simulates budget |
| `split_steering.py` | Splits large steering files into phase sub-files for incremental loading |

```text
python3 senzing-bootcamp/scripts/lint_steering.py
python3 senzing-bootcamp/scripts/lint_steering.py --warnings-as-errors
python3 senzing-bootcamp/scripts/lint_steering.py --skip-template
python3 senzing-bootcamp/scripts/measure_steering.py
python3 senzing-bootcamp/scripts/measure_steering.py --check
python3 senzing-bootcamp/scripts/measure_steering.py --simulate
python3 senzing-bootcamp/scripts/split_steering.py --module 5
```

## Dashboards

| Script | Purpose | Audience |
| --- | --- | --- |
| `team_dashboard.py` | Team progress overview — per-member module completion and active sessions | Team leads |

```text
python3 senzing-bootcamp/scripts/team_dashboard.py
python3 senzing-bootcamp/scripts/team_dashboard.py --output report.html
```

See Also: `status.py` shows individual progress; `analyze_sessions.py` shows historical analytics.

## Libraries (not standalone CLI tools)

These scripts are imported by other scripts or the agent — they are not intended to be run directly from the command line.

| Script | Purpose |
| --- | --- |
| `progress_utils.py` | Progress file read/write/validate — used by status, repair, rollback scripts |
| `session_logger.py` | Appends structured log entries to `config/session_log.jsonl` |
| `verbosity.py` | Verbosity level helpers — used by the agent for output formatting |
| `team_config_validator.py` | Validates `config/team.yaml` structure — used during team onboarding |
| `test_dashboard.py` | Test suite results formatting — used by CI for pass/fail reporting |
| `check_prerequisites.py` | DEPRECATED — superseded by `preflight.py` |
