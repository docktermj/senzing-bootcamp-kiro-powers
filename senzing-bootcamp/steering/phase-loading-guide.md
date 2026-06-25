---
inclusion: manual
---

# Phase-Level Steering Loading

Some large modules (currently 1, 3, 5, 6, 7, 8, 9, 10, and 11) are split into phase-level sub-files.

For every split module the root file is a thin **router**: it provides navigation and overview content (preamble, prerequisites, and the phase manifest) and is the entry point the agent loads first. The substantive numbered workflow steps do not live in the router root — they reside in the phase sub-files. Loading the root tells the agent which phase file to load for the bootcamper's current step.

When entering a split module:

1. Check `steering-index.yaml` — if the module entry has a `root` and `phases` map (instead of a simple filename), it is a split module.
2. Load the root file first (contains preamble, prerequisites, and phase manifest).
3. Read `current_step` from `config/bootcamp_progress.json` and resolve the phase **sub-step-aware**. A step's key is `(parent_integer, suffix)`: the leading digits, then the part after them (`""` for a bare integer, which sorts below lettered sub-steps, so `(4, "") < (4, "a")`). A phase's `step_range` `[lo, hi]` contains a step when `key(lo) <= key(step) <= key(hi)`. Select the single phase whose range contains the step. For integer-only ranges this reduces to plain integer comparison, and `parse_parent_step` reduces a sub-step identifier to its parent integer. When ranges use lettered sub-steps (Module 7 phase2a `["4a","4c"]`, phase2b `["4d","4e"]` — both parent integer 4), the suffix DOES select the phase.
4. Load only the sub-file for the current phase.
5. On phase transition (when `current_step` crosses a phase boundary), unload the previous phase's sub-file before loading the next.
6. If a sub-file cannot be found at the expected path, fall back to the root file and log a warning that the sub-file is missing.

## Dedicated Router Roots (Modules 1, 7, and 11)

Modules 1, 7, and 11 previously used the root file as both the router and the first phase. Each now has a dedicated thin router root whose phase-1 content was moved into a new phase sub-file. The load-root-first then resolve-phase then load-matching-phase behavior is unchanged; only the file names differ. Resolve the phase from `current_step` using the same sub-step-aware `(parent_integer, suffix)` matching, then load the matching phase file:

- **Module 1** — router root `module-01-business-problem.md`; phases:
  - `module-01-phase1-discovery.md` (`step_range` `[1, 9]`)
  - `module-01-phase2-document-confirm.md` (`step_range` `[10, 18]`)
- **Module 7** — router root `module-07-query-visualize-discover.md`; phases:
  - `module-07-phase1-query-visualize.md` (`step_range` `[1, "3d"]`)
  - `module-07-phase2-discover.md` (`step_range` `["4a", "4c"]`)
  - `module-07-phase2b-discover.md` (`step_range` `["4d", "4e"]`)
- **Module 11** — router root `module-11-deployment.md`; phases:
  - `module-11-phase1-packaging.md` (`step_range` `[1, 12]`)
  - `module-11-phase2-deploy.md` (`step_range` `[13, 15]`)

## Session Resume with Split Modules

When resuming mid-module via `session-resume.md`, the agent reads `current_step` (Step 1). If the current module has a `phases` entry, use the same sub-step-aware `(parent_integer, suffix)` matching to pick the phase and load only that sub-file: for integer-ranged modules a sub-step identifier reduces to its parent integer (via `parse_parent_step`); for sub-step-ranged modules (Module 7) the suffix selects the phase. If `current_step` is absent or resolves outside every `step_range`, load the root file only.
