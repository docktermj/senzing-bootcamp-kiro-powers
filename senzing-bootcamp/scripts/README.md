# Senzing Bootcamp Scripts

Python CLI tools for the Senzing Bootcamp power. All scripts use stdlib only (no pip dependencies) except `validate_dependencies.py` which requires PyYAML.

Every script follows the same pattern: shebang, module docstring, `argparse` CLI with `main(argv=None)`, and `if __name__ == "__main__": main()` entry point.

For full usage details with flags and examples, see `docs/guides/SCRIPT_REFERENCE.md`.

## CI Validation Scripts

These run in the GitHub Actions pipeline on every PR.

| Script | Purpose |
|--------|---------|
| `validate_power.py` | Validate power internal consistency (files, frontmatter, structure) |
| `validate_commonmark.py` | Validate CommonMark compliance for all markdown files |
| `validate_dependencies.py` | Validate module dependency graph for internal consistency |
| `validate_prerequisites.py` | Validate module prerequisites alignment between dependency graph and steering |
| `validate_progress_ci.py` | Validate bootcamp_progress.json schema |
| `validate_mandatory_gates.py` | Validate mandatory gate checkpoints in bootcamp progress |
| `measure_steering.py` | Measure token counts for steering files and update steering-index.yaml |
| `sync_hook_registry.py` | Generate hook-registry.md from .kiro.hook JSON files |
| `lint_steering.py` | Lint steering files for structural consistency |

## User-Facing Scripts

These are run by bootcampers during the bootcamp.

| Script | Purpose |
|--------|---------|
| `status.py` | Show bootcamp progress (modules completed, current step) |
| `preflight.py` | Consolidated environment verification (SDK, database, dependencies) |
| `backup_project.py` | Create a timestamped backup of the bootcamp project |
| `restore_project.py` | Restore a project from a backup archive |
| `install_hooks.py` | Install bootcamp hooks into `.kiro/hooks/` |
| `export_results.py` | Export entity resolution results |
| `compare_results.py` | Compare ER statistics before/after mapping changes |
| `version.py` | Display the Senzing Bootcamp Power version |

## Utility Scripts

Used by the agent or for development/maintenance tasks.

| Script | Purpose |
|--------|---------|
| `repair_progress.py` | Repair bootcamp_progress.json by scanning for actual artifacts |
| `rollback_module.py` | Roll back a module's artifacts and progress state |
| `track_switcher.py` | Switch between bootcamp tracks (core/advanced) |
| `validate_module.py` | Validate module prerequisites and success criteria |
| `validate_data_files.py` | Validate data source files for format and encoding |
| `check_database.py` | Database health check (connectivity, tables, record counts) |
| `check_prerequisites.py` | DEPRECATED — use `preflight.py` instead |
| `data_sources.py` | Data source registry management |
| `record_export.py` | Record export utility |
| `verbosity.py` | Verbosity control logic |
| `session_logger.py` | Session event logging |
| `progress_utils.py` | Shared progress checkpoint utilities (imported by other scripts) |

## Analytics and Reporting Scripts

| Script | Purpose |
|--------|---------|
| `bootcamp_analytics.py` | Completion analytics with optional baseline comparison |
| `analyze_sessions.py` | Session analytics (duration, pacing, module timing) |
| `cord_metadata.py` | CORD data freshness metadata (use `get_sample_data` to download CORD datasets) |
| `visualize_dependencies.py` | Generate module dependency visualization |

## Steering and Content Management Scripts

| Script | Purpose |
|--------|---------|
| `split_steering.py` | Split large module steering files into phase-level sub-files |
| `validate_links.py` | Validate external URLs referenced in markdown files |

## Team and Collaboration Scripts

| Script | Purpose |
|--------|---------|
| `team_config_validator.py` | Validate team configuration files |
| `team_dashboard.py` | Generate team dashboard HTML |
| `merge_feedback.py` | Merge feedback from multiple bootcampers |
| `triage_feedback.py` | Automated feedback triage and categorization |

## Test Scripts

| Script | Purpose |
|--------|---------|
| `test_hooks.py` | Hook self-test (structural validation of all .kiro.hook files) |
| `test_dashboard.py` | Property-based and unit tests for the interactive HTML dashboard |
