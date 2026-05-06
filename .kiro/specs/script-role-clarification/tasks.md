# Tasks: Script Role Clarification

## Task 1: Audit scripts and confirm categorization

- [x] 1.1 Read all scripts in `senzing-bootcamp/scripts/` and verify the categorization in the design document is accurate
- [x] 1.2 Identify any scripts not listed in the design (added after design was written) and categorize them
- [x] 1.3 Confirm which scripts are libraries vs CLI tools by checking for `if __name__ == "__main__"` or `main()` entry points

## Task 2: Update SCRIPT_REFERENCE.md

- [x] 2.1 Reorganize `senzing-bootcamp/docs/guides/SCRIPT_REFERENCE.md` into the six categories: Status & Validation, Progress Management, Data Management, Hooks & Configuration, Analysis & Reporting, Steering Maintenance, Dashboards, Utilities
- [x] 2.2 Add a one-line purpose statement for each script
- [x] 2.3 Mark library scripts (`progress_utils.py`, `session_logger.py`, `verbosity.py`) with a "Library — not a standalone CLI" note
- [x] 2.4 Add "See Also" cross-references between related scripts (status.py ↔ analyze_sessions.py, team_dashboard.py ↔ test_dashboard.py, validate_power.py ↔ validate_module.py ↔ validate_commonmark.py)
- [x] 2.5 Add a "Validation Hierarchy" subsection explaining the relationship between the three validate scripts

## Task 3: Add See Also to script --help outputs

- [x] 3.1 Add epilog text to `status.py` argparse: "See Also: analyze_sessions.py (historical analytics), preflight.py (environment checks)"
- [x] 3.2 Add epilog text to `analyze_sessions.py` argparse: "See Also: status.py (current state), session_logger.py (log entry library)"
- [x] 3.3 Add epilog text to `team_dashboard.py` argparse: "See Also: test_dashboard.py (test results), status.py (individual progress)"
- [x] 3.4 Add epilog text to `test_dashboard.py` argparse: "See Also: team_dashboard.py (team progress)"
- [x] 3.5 Add epilog text to `rollback_module.py` argparse: "See Also: restore_project.py (full backup restore), backup_project.py (create backups)"

## Task 4: Update POWER.md Useful Commands section

- [x] 4.1 Review the "Useful Commands" section in `senzing-bootcamp/POWER.md` and ensure all CLI scripts are listed with accurate descriptions
- [x] 4.2 Remove any references to library scripts from the "Useful Commands" section (they're not user-facing commands)

## Task 5: Validate

- [x] 5.1 Run `python3 senzing-bootcamp/scripts/validate_commonmark.py` on modified markdown files
- [x] 5.2 Verify all modified scripts still pass their existing tests: `pytest senzing-bootcamp/tests/ -v`
- [x] 5.3 Verify `--help` output renders correctly for modified scripts
