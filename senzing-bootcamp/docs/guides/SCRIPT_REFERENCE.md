# Script Reference

All scripts are cross-platform Python and live in `senzing-bootcamp/scripts/`. Run them from your project root after the agent copies them during setup, or reference them directly from the power directory:

```text
python3 senzing-bootcamp/scripts/preflight.py            # Environment verification (primary)
python3 senzing-bootcamp/scripts/preflight.py --json     # Environment verification (JSON output)
python3 senzing-bootcamp/scripts/preflight.py --fix      # Environment verification with auto-fix
python3 senzing-bootcamp/scripts/status.py               # Check progress
python3 senzing-bootcamp/scripts/status.py --sync        # Sync progress to PROGRESS_TRACKER.md
python3 senzing-bootcamp/scripts/validate_module.py      # Validate current module completion
python3 senzing-bootcamp/scripts/validate_module.py --next 7  # Check if ready for module 7
python3 senzing-bootcamp/scripts/install_hooks.py        # Install hooks
python3 senzing-bootcamp/scripts/backup_project.py       # Backup project
python3 senzing-bootcamp/scripts/restore_project.py      # Restore from backup
python3 senzing-bootcamp/scripts/validate_commonmark.py  # Validate Markdown formatting
python3 senzing-bootcamp/scripts/validate_power.py       # Validate power integrity (cross-references, hooks, steering)
python3 senzing-bootcamp/scripts/measure_steering.py     # Update steering file token counts in steering-index.yaml
python3 senzing-bootcamp/scripts/measure_steering.py --check  # Verify stored token counts are within 10% of actual (CI mode)
python3 senzing-bootcamp/scripts/repair_progress.py      # Repair corrupted bootcamp_progress.json
python3 senzing-bootcamp/scripts/team_dashboard.py                    # Generate team progress dashboard (requires config/team.yaml)
python3 senzing-bootcamp/scripts/team_dashboard.py --output report.html  # Generate dashboard to custom path
python3 senzing-bootcamp/scripts/merge_feedback.py                    # Merge team feedback into one report
python3 senzing-bootcamp/scripts/merge_feedback.py --output report.md    # Merge feedback to custom path
python3 senzing-bootcamp/scripts/export_results.py                    # Export HTML report
python3 senzing-bootcamp/scripts/export_results.py --format zip       # Export ZIP with all artifacts
python3 senzing-bootcamp/scripts/export_results.py --modules 1,2,3    # Export specific modules only
python3 senzing-bootcamp/scripts/data_sources.py                     # View data source registry (table)
python3 senzing-bootcamp/scripts/data_sources.py --detail CUSTOMERS  # Show all fields for one source
python3 senzing-bootcamp/scripts/data_sources.py --summary           # Aggregate registry statistics
python3 senzing-bootcamp/scripts/rollback_module.py --module N           # Roll back a specific module
python3 senzing-bootcamp/scripts/rollback_module.py --module N --dry-run # Preview rollback without changes
python3 senzing-bootcamp/scripts/sync_hook_registry.py --write        # Regenerate hook-registry.md from .kiro.hook files
python3 senzing-bootcamp/scripts/sync_hook_registry.py --verify       # Verify hook registry matches hook files (CI mode)
python3 senzing-bootcamp/scripts/validate_dependencies.py             # Validate module dependency graph consistency
python3 senzing-bootcamp/scripts/lint_steering.py                     # Lint steering files for structural issues
python3 senzing-bootcamp/scripts/lint_steering.py --warnings-as-errors # Lint with warnings treated as errors
python3 senzing-bootcamp/scripts/lint_steering.py --skip-template     # Lint without template conformance checks
python3 senzing-bootcamp/scripts/split_steering.py --module 5         # Split large steering file into phase sub-files
python3 senzing-bootcamp/scripts/session_logger.py                    # Internal: append structured events to session log
python3 senzing-bootcamp/scripts/analyze_sessions.py config/session_log.jsonl          # Analyze session log (text table)
python3 senzing-bootcamp/scripts/analyze_sessions.py config/session_log.jsonl --format json  # Analyze session log (JSON)
python3 senzing-bootcamp/scripts/analyze_sessions.py config/session_log.jsonl --pretty       # Pretty-print log entries
python3 senzing-bootcamp/scripts/triage_feedback.py docs/feedback/SENZING_BOOTCAMP_POWER_FEEDBACK.md  # Parse feedback into spec skeletons
python3 senzing-bootcamp/scripts/triage_feedback.py --dry-run         # Preview triage without creating files
python3 senzing-bootcamp/scripts/progress_utils.py       # Internal: progress tracking utilities (used by other scripts)
python3 senzing-bootcamp/scripts/team_config_validator.py # Internal: validate config/team.yaml structure (used during onboarding)
python3 senzing-bootcamp/scripts/check_prerequisites.py  # DEPRECATED — use preflight.py instead
python3 senzing-bootcamp/scripts/preflight_check.py      # DEPRECATED — use preflight.py instead
```

Use `python` instead of `python3` on Windows.
