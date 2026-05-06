# Requirements: Script Role Clarification

## Overview

Some scripts (`team_dashboard.py`, `test_dashboard.py`) appear to overlap in purpose. This feature clarifies and documents the distinct role of each script, consolidating where appropriate and updating `SCRIPT_REFERENCE.md` to eliminate confusion.

## Requirements

1. Audit all 28 scripts in `senzing-bootcamp/scripts/` and identify pairs or groups with overlapping functionality
2. For each overlap identified, determine whether to: (a) consolidate into one script with subcommands, (b) rename for clarity, or (c) document the distinction
3. The `docs/guides/SCRIPT_REFERENCE.md` is updated with a clear one-line purpose statement for each script, organized by category (status/validation, progress management, data management, hooks/config, analysis/reporting, utilities)
4. Scripts that are genuinely redundant are consolidated — the deprecated script is removed and its functionality merged into the surviving script
5. If `team_dashboard.py` and `test_dashboard.py` serve different audiences (team leads vs developers), their names and descriptions make this distinction explicit
6. Each script's `--help` output includes a "See Also" line referencing related scripts (e.g., `status.py --help` mentions `analyze_sessions.py` for historical data)
7. The `POWER.md` "Useful Commands" section is updated to reflect any renames or consolidations
8. No script behavior changes — only naming, documentation, and potential consolidation of truly redundant code

## Non-Requirements

- This does not add new script functionality
- This does not change script interfaces (arguments, exit codes) unless consolidating
- This does not affect CI pipeline commands (those are updated if scripts are renamed)
