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

### `status.py` Flags

| Flag | Description |
| --- | --- |
| `--sync` | Sync progress with workspace artifacts |
| `--step` | Show step-level progress for the current module |

```text
python3 senzing-bootcamp/scripts/status.py
python3 senzing-bootcamp/scripts/status.py --sync
python3 senzing-bootcamp/scripts/status.py --step
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
| `compose_hook_prompts.py` | CI: composes the Module 3 gate-hook prompts from shared fragments and verifies on-disk sync |

```text
python3 senzing-bootcamp/scripts/install_hooks.py
python3 senzing-bootcamp/scripts/sync_hook_registry.py --verify
python3 senzing-bootcamp/scripts/sync_hook_registry.py --write
python3 senzing-bootcamp/scripts/compose_hook_prompts.py --verify
python3 senzing-bootcamp/scripts/compose_hook_prompts.py --write
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

## Additional Validation

| Script | Purpose |
| --- | --- |
| `validate_prerequisites.py` | CI: validates module prerequisite documentation matches dependency graph |
| `validate_progress_ci.py` | CI: validates bootcamp_progress.json.example schema |
| `validate_mandatory_gates.py` | CI: validates all ⛔ mandatory gates have proper checkpoint instructions |
| `validate_links.py` | Validates external URLs in markdown files are reachable |
| `validate_governance_rules.py` | CI: validates each governing rule is wired to its enforcement point(s) via `governance-rules.yaml` |
| `validate_yaml_schemas.py` | CI: validates top-level key structure of the authoritative YAML config files |
| `validate_preferences_ci.py` | CI: validates `bootcamp_preferences.yaml` schema (uses a built-in sample when no file exists) |
| `validate_behavior_rules.py` | Validates steering content against the four agent behavior rules (`--check`) |
| `validate_completion_artifacts.py` | Validates journal/recap structure and consistency with the progress file |

```text
python3 senzing-bootcamp/scripts/validate_prerequisites.py
python3 senzing-bootcamp/scripts/validate_progress_ci.py
python3 senzing-bootcamp/scripts/validate_mandatory_gates.py
python3 senzing-bootcamp/scripts/validate_links.py
python3 senzing-bootcamp/scripts/validate_links.py --dry-run
python3 senzing-bootcamp/scripts/validate_links.py --timeout 10
python3 senzing-bootcamp/scripts/validate_governance_rules.py
python3 senzing-bootcamp/scripts/validate_yaml_schemas.py
python3 senzing-bootcamp/scripts/validate_preferences_ci.py
python3 senzing-bootcamp/scripts/validate_behavior_rules.py
python3 senzing-bootcamp/scripts/validate_completion_artifacts.py --progress config/bootcamp_progress.json --journal docs/bootcamp_journal.md --recap docs/bootcamp_recap.md
```

## Data Tools

| Script | Purpose |
| --- | --- |
| `compare_results.py` | Compares ER statistics before/after mapping changes (diff + quality assessment) |
| `bootcamp_analytics.py` | Session analytics — module timing, question counts, error frequency |
| `cord_metadata.py` | Displays metadata for CORD sample datasets (Las Vegas, London, Moscow) — use `get_sample_data` to download |
| `check_database.py` | Checks Senzing database health — entity count, record count, data sources |
| `record_export.py` | Exports records from the Senzing database in various formats |
| `visualize_dependencies.py` | Generates a visual dependency graph of module relationships |

```text
python3 senzing-bootcamp/scripts/compare_results.py --baseline <file> --current <file>
python3 senzing-bootcamp/scripts/bootcamp_analytics.py
python3 senzing-bootcamp/scripts/bootcamp_analytics.py --compare
python3 senzing-bootcamp/scripts/cord_metadata.py
python3 senzing-bootcamp/scripts/check_database.py
python3 senzing-bootcamp/scripts/record_export.py --format jsonl
python3 senzing-bootcamp/scripts/visualize_dependencies.py
```

## Track Management

| Script | Purpose |
| --- | --- |
| `track_switcher.py` | Switches between Core Bootcamp and Advanced Topics tracks |

```text
# Dry-run (the DEFAULT): print the computed switch as JSON without writing
python3 senzing-bootcamp/scripts/track_switcher.py --from core_bootcamp --to advanced_topics --progress config/bootcamp_progress.json

# Apply the switch (writes config/bootcamp_progress.json)
python3 senzing-bootcamp/scripts/track_switcher.py --from advanced_topics --to core_bootcamp --progress config/bootcamp_progress.json --apply
```

`--from`, `--to`, and `--progress` are all required. Without `--apply` the script is a dry-run; pass `--apply` to write the change.

## Generators and Tools

| Script | Purpose |
| --- | --- |
| `eval_conversations.py` | CI: runs scripted transcript fixtures against behavioral rules (runtime-behavior eval) |
| `assess_entry_point.py` | Recommends where to begin/resume by scanning produced artifacts and SDK availability |
| `parse_business_problem.py` | Derives Module 7 query requirements from `docs/business_problem.md` |
| `organize_mapping_files.py` | Routes `mapping_workflow` output files into the correct project subdirectories |
| `optimize_steering.py` | Splits/compresses always-on steering files and syncs `steering-index.yaml` (`--check`, `--dry-run`) |
| `progress_dashboard.py` | Generates a self-contained HTML progress dashboard at `docs/progress/dashboard.html` |
| `generate_graduation_certificate.py` | Generates a graduation certificate in Markdown and HTML |
| `generate_artifact_inventory.py` | Generates the "Complete Artifact Inventory" graduation-report section — every artifact grouped by phase with why-it-matters notes and carry-forward/leave-behind tags, derived from progress + files on disk |
| `generate_recap_pdf.py` | Renders `docs/bootcamp_recap.md` to PDF (optional `fpdf2`; keeps Markdown when absent) |
| `generate_completion_summary.py` | Builds a module completion summary in Markdown (optional PDF via `fpdf2`) |

```text
python3 senzing-bootcamp/scripts/eval_conversations.py
python3 senzing-bootcamp/scripts/assess_entry_point.py
python3 senzing-bootcamp/scripts/parse_business_problem.py --file docs/business_problem.md
python3 senzing-bootcamp/scripts/organize_mapping_files.py --source <dir> --project-root . --dry-run
python3 senzing-bootcamp/scripts/optimize_steering.py --check
python3 senzing-bootcamp/scripts/progress_dashboard.py
python3 senzing-bootcamp/scripts/generate_graduation_certificate.py
python3 senzing-bootcamp/scripts/generate_artifact_inventory.py
python3 senzing-bootcamp/scripts/generate_recap_pdf.py --input docs/bootcamp_recap.md
python3 senzing-bootcamp/scripts/generate_completion_summary.py
```

## Libraries (not standalone CLI tools)

These scripts are imported by other scripts or the agent — they are not intended to be run directly from the command line.

| Script | Purpose |
| --- | --- |
| `progress_utils.py` | Progress file read/write/validate — used by status, repair, rollback scripts |
| `session_logger.py` | Appends structured log entries to `config/session_log.jsonl` |
| `verbosity.py` | Verbosity level helpers — used by the agent for output formatting |
| `version.py` | Version parsing and validation — used by validate_power.py for semver checks |
| `team_config_validator.py` | Validates `config/team.yaml` structure — used during team onboarding |
| `test_dashboard.py` | Test suite results formatting — used by CI for pass/fail reporting |
| `test_hooks.py` | Hook testing utilities — used by the test suite for hook validation |
| `preferences_utils.py` | Preferences schema, minimal YAML parser, and validator — used by `validate_preferences_ci.py` |
| `volume_utils.py` | Record-volume parsing, tier classification, and Module 6 guidance generation |
| `hook_prompt_fragments.py` | Single-source shared Module 3 gate-hook prompt fragments — expanded by `compose_hook_prompts.py` |
