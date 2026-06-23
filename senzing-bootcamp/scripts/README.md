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
| `validate_governance_rules.py` | Validate governing rules are wired to their enforcement points (`governance-rules.yaml`) |
| `validate_yaml_schemas.py` | Validate top-level key structure of the authoritative YAML config files |
| `validate_preferences_ci.py` | Validate `bootcamp_preferences.yaml` schema (validates a built-in sample when no file exists) |
| `eval_conversations.py` | Conversational-eval harness — run scripted transcripts against behavioral rules |
| `compose_hook_prompts.py` | Compose the Module 3 gate-hook prompts from shared fragments (`--write` / `--verify`) |
| `generate_power_docs.py` | Regenerate the volatile POWER.md sections from sources (`--write` / `--verify`) |

### POWER.md Documentation Generator

`generate_power_docs.py` regenerates the four volatile sections of `POWER.md`
(MCP tools, hooks, steering files, modules) in place between marker comments,
preserving all hand-written prose. It mirrors the `--write` / `--verify` pattern
of `sync_hook_registry.py`.

Regenerate the sections in place (default mode):

```bash
python3 senzing-bootcamp/scripts/generate_power_docs.py --write
```

Verify the committed `POWER.md` matches what the generator would produce (used
in CI; exits non-zero on drift and prints the regeneration command):

```bash
python3 senzing-bootcamp/scripts/generate_power_docs.py --verify
```

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
| `assess_entry_point.py` | Recommend where to begin/resume by scanning produced artifacts and SDK availability |
| `organize_mapping_files.py` | Route `mapping_workflow` output files into the correct project subdirectories |
| `parse_business_problem.py` | Derive Module 7 query requirements from `docs/business_problem.md` |
| `optimize_steering.py` | Split/compress always-on steering files and sync `steering-index.yaml` |
| `validate_behavior_rules.py` | Check steering content against the four agent behavior rules |
| `validate_completion_artifacts.py` | Validate journal/recap structure and consistency with progress |
| `preferences_utils.py` | Preferences schema + minimal YAML parser/validator (imported by other scripts) |
| `volume_utils.py` | Record-volume parsing, tier classification, and guidance (imported by other scripts) |
| `hook_prompt_fragments.py` | Single-source shared Module 3 gate-hook prompt fragments (imported by `compose_hook_prompts.py`) |

## Analytics and Reporting Scripts

| Script | Purpose |
|--------|---------|
| `bootcamp_analytics.py` | Completion analytics with optional baseline comparison |
| `analyze_sessions.py` | Session analytics (duration, pacing, module timing) |
| `cord_metadata.py` | CORD data freshness metadata (use `get_sample_data` to download CORD datasets) |
| `visualize_dependencies.py` | Generate module dependency visualization |
| `progress_dashboard.py` | Generate a self-contained HTML progress dashboard at `docs/progress/dashboard.html` |
| `generate_graduation_certificate.py` | Generate a graduation certificate in Markdown and HTML |
| `generate_artifact_inventory.py` | Generate the "Complete Artifact Inventory" graduation-report section — every artifact grouped by phase with why-it-matters notes and carry-forward/leave-behind tags, derived from progress + files on disk |
| `generate_recap_pdf.py` | Render `docs/bootcamp_recap.md` to a PDF (optional `fpdf2`; keeps Markdown if absent) |
| `generate_completion_summary.py` | Build a module completion summary in Markdown (optional PDF via `fpdf2`) |

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
