# Technical Design: enforce-visualization-step

## Overview

The agent skips Module 3 Step 9 (Web Service + Visualization) because no enforcement mechanism gates module completion on the `web_service` and `web_page` checkpoint entries in `config/bootcamp_progress.json`. The existing `enforce-visualization-offers` hook only checks whether a visualization was *offered* (via the tracker), not whether Step 9 was *executed* (via progress checkpoints). The `verify-demo-results` hook validates entity resolution results but does not check for web service artifacts.

## Root Cause

The module completion flow has no checkpoint gate for Step 9. When the agent finishes Steps 1–8, it can jump directly to Step 10 (Verification Report) and Step 11 (Cleanup) without executing Step 9. The Verification Report generation in Step 10 compiles results from `config/bootcamp_progress.json`, but nothing prevents it from running with missing `web_service`/`web_page` entries — it simply omits them or marks them as "skipped."

## Design

### Approach: New preToolUse Hook + Steering Reinforcement

The fix uses a two-layer enforcement strategy:

1. **New hook** (`gate-module3-visualization.kiro.hook`) — A `preToolUse` hook on `write` operations that detects when the agent is about to write Module 3 completion status without Step 9 checkpoints present, and blocks the write with corrective instructions.

2. **Steering reinforcement** — Add a mandatory gate marker (⛔) to Step 9 in `module-03-system-verification.md` and add explicit pre-completion validation logic to Step 10.

### Layer 1: Hook — `gate-module3-visualization.kiro.hook`

**Type:** `preToolUse` on `write` operations

**Trigger condition:** The agent is writing to `config/bootcamp_progress.json` AND the write content includes a Module 3 completion marker (e.g., adding `3` to `modules_completed` array, or setting `module_3_verification.status` to `"passed"`) AND the existing `config/bootcamp_progress.json` does NOT contain both `web_service.status: "passed"` and `web_page.status: "passed"` entries.

**Action when triggered:** Block the write and instruct the agent to load `module-03-phase2-visualization.md` and execute Step 9 before attempting module completion again.

**Skip-step exception:** If `config/bootcamp_progress.json` contains a `skipped_steps` entry for `"3.9"` (recorded via the skip-step protocol), the hook allows the completion write to proceed.

```json
{
  "name": "to gate Module 3 completion on visualization step",
  "version": "1.0.0",
  "description": "Prevents Module 3 from being marked complete unless Step 9 (Web Service + Visualization) checkpoints are present in bootcamp_progress.json, or the step was explicitly skipped via the skip-step protocol.",
  "when": {
    "type": "preToolUse",
    "toolTypes": ["write"]
  },
  "then": {
    "type": "askAgent",
    "prompt": "CHECK — Is this write updating `config/bootcamp_progress.json` to mark Module 3 as complete (adding 3 to modules_completed, or setting module_3_verification.status to 'passed')?\n\nIf NO (not a Module 3 completion write, or not writing to bootcamp_progress.json): output nothing. Proceed silently.\n\nIf YES: Read the CURRENT contents of `config/bootcamp_progress.json` and check TWO conditions:\n\nCONDITION A — Step 9 checkpoints exist:\n- `module_3_verification.checks.web_service.status` equals `\"passed\"`\n- `module_3_verification.checks.web_page.status` equals `\"passed\"`\n\nCONDITION B — Step 9 was explicitly skipped:\n- `skipped_steps` contains an entry with key `\"3.9\"`\n\nIf CONDITION A is true OR CONDITION B is true: output nothing. Proceed silently.\n\nIf NEITHER condition is met: STOP. Do NOT allow this write. Output exactly:\n\n⛔ BLOCKED: Module 3 cannot be marked complete — Step 9 (Web Service + Visualization) has not been executed. Load `module-03-phase2-visualization.md` and execute the full visualization step (generate web service, start server, verify 3 API endpoints, present URL to bootcamper). Only after web_service and web_page checkpoints show 'passed' can Module 3 be completed.\n\nDo not proceed with the write operation."
  }
}
```

### Layer 2: Steering Reinforcement

#### Change 1: Mark Step 9 as mandatory gate in `module-03-system-verification.md`

Add `⛔ MANDATORY` marker to Step 9 heading, matching the pattern used for Step 5 in Module 2:

```markdown
### Step 9: Web Service + Visualization Page

⛔ MANDATORY GATE — This step cannot be skipped without explicit bootcamper request via the skip-step protocol. The visualization is the "wow moment" of Module 3.
```

#### Change 2: Add pre-completion validation to Step 10

Insert a validation check at the beginning of Step 10 (Verification Report Generation) that explicitly verifies Step 9 checkpoints before compiling the report:

```markdown
**Pre-report validation:** Before compiling the Verification Report, confirm that `config/bootcamp_progress.json` contains BOTH `web_service` and `web_page` checkpoint entries under `module_3_verification.checks`. If either entry is missing or has `"status": "failed"`:
- If missing: STOP. Do not generate the report. Return to Step 9 and execute it fully by loading `module-03-phase2-visualization.md`.
- If failed: Include the failure in the report and proceed (failed is different from skipped/missing — it means the step was attempted).
```

#### Change 3: Update Success Criteria

The existing success criteria already mention "All 8 verification checks report 'passed' status" but the checks list in Step 10 mentions "8 verification checks" while there are actually 10 checkpoint entries (including web_service and web_page). Clarify:

```markdown
## Success Criteria

Module 3 is considered successfully complete when ALL of the following are true:

- All 10 verification checkpoint entries report "passed" status (mcp_connectivity, truthset_acquisition, sdk_initialization, code_generation, build_compilation, data_loading, results_validation, database_operations, web_service, web_page)
```

### Layer 3: Hook Registry Update

Add the new hook to `hook-categories.yaml` under module 3:

```yaml
  3:
    - enforce-visualization-offers
    - gate-module3-visualization
    - verify-demo-results
```

## Files Changed

| File | Change |
|------|--------|
| `senzing-bootcamp/hooks/gate-module3-visualization.kiro.hook` | NEW — preToolUse hook gating Module 3 completion |
| `senzing-bootcamp/hooks/hook-categories.yaml` | ADD `gate-module3-visualization` to module 3 list |
| `senzing-bootcamp/steering/module-03-system-verification.md` | ADD ⛔ MANDATORY marker to Step 9; ADD pre-report validation to Step 10; UPDATE success criteria count |

## Interaction with Existing Hooks

- **`enforce-visualization-offers`** (agentStop): Unchanged. Continues to check whether visualizations were *offered*. The new hook checks whether Step 9 was *executed*. They are complementary.
- **`verify-demo-results`** (postTaskExecution): Unchanged. Validates entity resolution results (Steps 6–8). Does not overlap with Step 9 enforcement.
- **`module-completion-celebration`** (postTaskExecution): Unchanged. Fires after completion is recorded. The new hook fires *before* the completion write, preventing premature celebration.
- **Skip-step protocol**: Honored. If the bootcamper explicitly skips Step 9 via the protocol (recorded in `skipped_steps["3.9"]`), the hook allows completion to proceed.

## Scope Boundaries

- This fix applies ONLY to Module 3. Other modules' completion criteria are not affected (requirement 3.3).
- The `enforce-visualization-offers` hook behavior for modules 5, 7, 8 is unchanged (requirement 3.4).
- If Module 3 Steps 1–8 have failures, the existing failure-blocking logic in Step 10 handles that independently (requirement 3.2).

## Testing Considerations

- Verify the hook blocks completion when `web_service`/`web_page` checkpoints are absent
- Verify the hook allows completion when both checkpoints show `"passed"`
- Verify the hook allows completion when `skipped_steps["3.9"]` exists
- Verify the hook produces no output for non-Module-3 completion writes
- Verify the hook produces no output for writes to files other than `bootcamp_progress.json`
