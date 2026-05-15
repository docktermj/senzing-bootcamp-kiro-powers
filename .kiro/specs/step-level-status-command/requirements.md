# Requirements: Step-Level Status Command

## Overview

Add step-level detail to `status.py` so bootcampers can quickly see not just which module they're in, but which step within that module, providing quick orientation without asking the agent.

## Requirements

1. Add a `--step` or `--detail` flag to `scripts/status.py` that shows step-level progress
2. When `--step` is used, read `step_history` from `config/bootcamp_progress.json` and display the last completed step for the current module
3. Display format: "Module N: [Name] — Step X of Y completed" (where Y comes from the module's steering file step count in `steering-index.yaml` phase step_range)
4. If `current_step` is set (integer or sub-step string like "5.3"), display it as the active step
5. Show timestamp of last step completion from `step_history[module].updated_at`
6. Handle edge cases: no step history (display "Not started"), null current_step (display "Between steps"), sub-step identifiers (display "Step 5.3")
7. The output must work on all platforms (Linux, macOS, Windows) with no third-party dependencies
8. Update POWER.md "Useful Commands" section to document the new flag
9. Update `docs/guides/SCRIPT_REFERENCE.md` if it exists
10. Write tests for the new flag covering: no progress file, empty step history, active step, completed module, sub-step identifiers
