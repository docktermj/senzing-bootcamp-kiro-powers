---
inclusion: manual
---

# Phase-Level Steering Loading

Some large modules (currently 1, 3, 5, 6, 8, 9, 10, and 11) are split into phase-level sub-files. When entering a split module:

1. Check `steering-index.yaml` — if the module entry has a `root` and `phases` map (instead of a simple filename), it is a split module.
2. Load the root file first (contains preamble, prerequisites, and phase manifest).
3. Read `current_step` from `config/bootcamp_progress.json`. If `current_step` is a sub-step identifier (e.g., `"5.3"` or `"7a"`), extract the parent step number (the integer portion before the dot or letter — `"5.3"` → `5`, `"7a"` → `7`) via `parse_parent_step` and use that for phase lookup. If `current_step` is an integer, use it directly. Find the phase whose `step_range` in `steering-index.yaml` contains the resolved step number.
4. Load only the sub-file for the current phase.
5. On phase transition (when `current_step` crosses a phase boundary), unload the previous phase's sub-file before loading the next phase's sub-file.
6. If a sub-file cannot be found at the expected path, fall back to loading the root file and log a warning that the sub-file is missing.

## Session Resume with Split Modules

When resuming a session mid-module via `session-resume.md`, the agent reads `current_step` from `bootcamp_progress.json` (Step 1). If the current module has a `phases` entry in `steering-index.yaml`, use `current_step` to determine the phase and load only that sub-file instead of the full module. When `current_step` is a sub-step identifier (e.g., `"5.3"` or `"7a"`), use the parent step number (via `parse_parent_step`) for `step_range` matching — the sub-step suffix does not affect phase selection. If `current_step` is absent or the resolved step number doesn't fall within any phase's `step_range`, load the root file only.
