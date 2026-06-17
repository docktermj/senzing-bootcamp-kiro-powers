# Module 5 Mapping Workflow Guidance Bugfix Design

## Overview

Module 5 (Data Quality & Mapping) Phase 2 guides the bootcamper through a per-source
`mapping_workflow` run. Two points in that guidance are brittle:

1. **Unexecutable hard gate on 404 validation scripts.** The MCP server's `mapping_workflow`
   advertises three validation scripts and the Phase 2 guidance treats the verbatim-fidelity
   check (`sz_verbatim_check.py`) as a hard blocking gate and requires the routing-coverage
   report (`sz_routing_report.py`). Both currently return HTTP 404, while `sz_json_analyzer.py`
   is still hosted (HTTP 200). When the gated scripts are unavailable, the bootcamper is blocked
   or confused with no confirmed inline fallback.

2. **No forward guidance after the Step 5 menu.** After Step 4 approval, `mapping_workflow`
   returns Step 5 (`detect_environment`) with a four-option menu (skip / test_load / load+resolve
   / done). The guidance relays no recommendation or next action, so the bootcamper hits a dead
   end mid-module.

The fix is **power-side only** — re-hosting the missing scripts is a server-side concern outside
the power's control. The fix makes the Module 5 Phase 2 guidance resilient by (a) degrading the
verbatim-fidelity and routing-coverage checks to optional/best-effort when their scripts are
unavailable while proceeding with the hosted `sz_json_analyzer.py`, and (b) explicitly handling
the Step 5 menu by surfacing that Steps 5–8 are optional sandbox validation, recommending a skip
when multiple sources remain, and continuing to the next unmapped source.

The affected guidance lives in `senzing-bootcamp/steering/module-05-phase2-data-mapping.md` (and
the optional Step 5–8 path in `senzing-bootcamp/steering/module-05-phase3-test-load.md`), with the
companion user doc at `senzing-bootcamp/docs/modules/MODULE_5_DATA_QUALITY_AND_MAPPING.md`. The fix
is steering/documentation text only — no Python or runtime code changes.

## Glossary

- **Bug_Condition (C)**: The condition that triggers the bug — either (a) a required mapping
  validation script (`sz_verbatim_check.py` or `sz_routing_report.py`) is unavailable (HTTP 404 /
  no working inline fallback) while the guidance still treats its check as required, or (b) the
  Step 5 `detect_environment` menu is returned and the guidance provides no recommendation or next
  action.
- **Property (P)**: The desired guidance behavior — unavailable validation scripts are treated as
  optional/best-effort and the workflow proceeds using `sz_json_analyzer.py`; the Step 5 menu is
  explained, a skip is recommended when sources remain, and the next unmapped source is started.
- **Preservation**: Existing Module 5 behavior that must remain unchanged — `sz_json_analyzer.py`
  validation, the normal `mapping_workflow` progression and Step 4 approval, the explicit
  `test_load` / `load+resolve` paths, and deferral of the real load to Module 6.
- **mapping_workflow**: The Senzing MCP server tool that drives the per-source mapping run through
  numbered steps, including Step 4 (generate/validate) and Step 5 (`detect_environment` menu).
- **sz_json_analyzer.py**: The hosted (HTTP 200) validation script performing structural +
  Entity-Specification validation. The primary mapping validation, available today.
- **sz_verbatim_check.py**: The verbatim-fidelity validation script, currently HTTP 404.
- **sz_routing_report.py**: The routing-coverage report script, currently HTTP 404.
- **Step 5 menu (`detect_environment`)**: The four-option menu returned after Step 4 approval —
  skip / test_load / load+resolve / done — gating the optional Phase 3 (Steps 5–8) sandbox
  validation.

## Bug Details

### Bug Condition

The bug manifests at two points in a per-source `mapping_workflow` run. First, when Step 4
validation requires the verbatim-fidelity check or the routing-coverage report but their scripts
return HTTP 404 (and no working inline fallback exists), the guidance still treats those checks as
required — the verbatim-fidelity check as a hard "do NOT proceed" gate — leaving the workflow
blocked. Second, when `mapping_workflow` returns the Step 5 `detect_environment` menu after Step 4
approval, the guidance provides no recommendation or next action, leaving the bootcamper at a dead
end mid-module.

**Formal Specification:**
```
FUNCTION isBugCondition(input)
  INPUT: input of type WorkflowState {
           step: integer,                 // current mapping_workflow step
           scriptAvailability: map,       // script name -> available (bool)
           menuReturned: boolean          // Step 5 detect_environment menu surfaced
         }
  OUTPUT: boolean

  // Aspect A: unexecutable hard gate on an unavailable validation script
  gateBlocked := input.step == 4
                 AND ( NOT input.scriptAvailability['sz_verbatim_check.py']
                       OR NOT input.scriptAvailability['sz_routing_report.py'] )

  // Aspect B: Step 5 menu returned with no forward guidance
  deadEnd := input.step == 5 AND input.menuReturned == true

  RETURN gateBlocked OR deadEnd
END FUNCTION
```

### Examples

- **Verbatim gate blocks (Aspect A):** At Step 4, `sz_verbatim_check.py` returns HTTP 404. Expected:
  the verbatim-fidelity check is announced as skipped (script unavailable) and the workflow proceeds
  using `sz_json_analyzer.py`. Actual: the guidance treats it as a hard gate ("Do NOT proceed until
  it passes") and the workflow stalls.
- **Routing report blocks (Aspect A):** At Step 4, `sz_routing_report.py` returns HTTP 404. Expected:
  the routing-coverage check is announced as skipped and the workflow proceeds. Actual: the guidance
  still requires running it, with no defined path to complete validation.
- **Step 5 dead end (Aspect B):** After Step 4 approval, `mapping_workflow` returns the
  `detect_environment` menu (skip / test_load / load+resolve / done). Expected: the guidance explains
  Steps 5–8 are optional sandbox validation, recommends a skip when sources remain, and continues to
  the next unmapped source. Actual: no recommendation is relayed; the bootcamper stops.
- **Edge — all scripts hosted (not a bug):** At Step 4 with `sz_verbatim_check.py`,
  `sz_routing_report.py`, and `sz_json_analyzer.py` all returning HTTP 200, all three checks run as
  before. `isBugCondition` returns false and behavior is preserved.

## Expected Behavior

### Preservation Requirements

**Unchanged Behaviors:**
- When `sz_json_analyzer.py` is available, structural + Entity-Specification validation continues to
  run as the primary mapping validation (3.1).
- When the verbatim-fidelity and routing-coverage scripts ARE available (hosted or via a working
  inline fallback), their checks continue to run as before (3.2).
- The normal `mapping_workflow` progression — per-source mapping and Step 4 approval — continues
  unchanged (3.3).
- When the bootcamper explicitly chooses `test_load` or `load+resolve` at the Step 5 menu, the
  guidance continues to follow that path (Phase 3 Steps 5–8) as before (3.4).
- The production load continues to be deferred to Module 6 (3.5).

**Scope:**
All inputs that do NOT satisfy the bug condition should be completely unaffected by this fix. This
includes:
- Step 4 runs where all three validation scripts are hosted (HTTP 200).
- The Step 5 menu when the bootcamper explicitly selects `test_load` or `load+resolve`.
- Every mapping_workflow step other than the Step 4 validation gate and the Step 5 menu.

**Note:** The expected correct behavior for buggy inputs is defined in the Correctness Properties
section (Property 1 and Property 2). This section captures what must NOT change.

## Hypothesized Root Cause

Based on the bug description, the most likely issues are:

1. **Hard-gate framing in Phase 2 validation guidance**: The Step 4 validation guidance frames the
   verbatim-fidelity check as a mandatory "do NOT proceed until it passes" gate, with no conditional
   branch for "script unavailable (HTTP 404)."
   - `sz_verbatim_check.py` and `sz_routing_report.py` are advertised at Step 1 and required at
     Step 4, but both currently return HTTP 404.
   - No confirmed inline fallback is documented, so an unavailable script has no defined off-ramp.

2. **Missing availability/degradation branch**: The guidance does not distinguish "check failed" from
   "check could not run because the script is unavailable," so it cannot degrade verbatim-fidelity and
   routing-coverage to optional/best-effort while continuing with the hosted `sz_json_analyzer.py`.

3. **No Step 5 menu handling**: The guidance does not interpret the `detect_environment` menu output.
   It neither labels Steps 5–8 as optional sandbox validation nor maps the four options to a
   recommendation.

4. **No multi-source continuation logic**: When unmapped sources remain, the guidance does not
   recommend skipping the per-source test load (real load deferred to Module 6) or automatically
   advance to the next unmapped source.

## Correctness Properties

Property 1: Bug Condition - Resilient Validation When Scripts Are Unavailable

_For any_ Step 4 validation where the verbatim-fidelity script (`sz_verbatim_check.py`) or the
routing-coverage script (`sz_routing_report.py`) is unavailable (HTTP 404 / no working inline
fallback), the fixed guidance SHALL treat the affected check as optional/best-effort, inform the
bootcamper it is being skipped because the script is unavailable, and proceed using the hosted
`sz_json_analyzer.py` (structural + Entity-Specification validation) without blocking the mapping
workflow.

**Validates: Requirements 2.1, 2.2, 2.3**

Property 2: Bug Condition - Forward Guidance After the Step 5 Menu

_For any_ Step 5 `detect_environment` menu returned after Step 4 approval, the fixed guidance SHALL
state that Steps 5–8 are optional sandbox validation and explain the available choices; and when one
or more unmapped sources remain, it SHALL recommend skipping the per-source test load (noting the
real load happens in Module 6) and automatically continue to the next unmapped source.

**Validates: Requirements 2.4, 2.5**

Property 3: Preservation - Normal Mapping Workflow Unchanged

_For any_ input where the bug condition does NOT hold (all validation scripts hosted, or the
bootcamper explicitly chooses `test_load` / `load+resolve`), the fixed guidance SHALL produce the
same result as the original guidance, preserving `sz_json_analyzer.py` validation, the
verbatim-fidelity and routing-coverage checks when their scripts are available, the normal
`mapping_workflow` progression and Step 4 approval, the explicit Phase 3 paths, and deferral of the
real load to Module 6.

**Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5**

## Fix Implementation

### Changes Required

Assuming our root cause analysis is correct, the fix updates steering guidance (and the companion
user doc) only — no runtime/code changes.

**File**: `senzing-bootcamp/steering/module-05-phase2-data-mapping.md`

**Section**: Step 4 (Map / validate) and the Step 5 transition into Phase 3

**Specific Changes**:

1. **Add an availability-aware validation branch at Step 4**: Replace the hard "do NOT proceed until
   verbatim-fidelity passes" framing with conditional guidance:
   - If `sz_verbatim_check.py` is available → run the verbatim-fidelity check as before.
   - If unavailable (HTTP 404 / no working inline fallback) → announce it is being skipped because the
     script is unavailable, treat it as optional/best-effort, and continue.

2. **Degrade the routing-coverage report the same way**: If `sz_routing_report.py` is available → run
   it as before; if unavailable → announce skip, treat as optional/best-effort, continue.

3. **Anchor validation on the hosted analyzer**: State explicitly that `sz_json_analyzer.py`
   (structural + Entity-Specification validation) is the primary mapping validation and is sufficient
   to proceed when the verbatim/routing scripts are unavailable.

4. **Add explicit Step 5 menu handling**: When `mapping_workflow` returns the `detect_environment`
   menu, explain that Steps 5–8 are optional sandbox validation and describe the four options
   (skip / test_load / load+resolve / done).

5. **Add multi-source continuation guidance**: When one or more unmapped sources remain, recommend
   skipping the per-source test load (note the real load happens in Module 6) and automatically
   continue to the next unmapped source. Preserve the explicit `test_load` / `load+resolve` paths
   when the bootcamper chooses them.

**File**: `senzing-bootcamp/steering/module-05-phase3-test-load.md`

**Change**: Cross-reference the Step 5 menu handling so that explicitly chosen `test_load` /
`load+resolve` paths still enter Phase 3 (Steps 21–26 / workflow steps 5–8) unchanged.

**File**: `senzing-bootcamp/docs/modules/MODULE_5_DATA_QUALITY_AND_MAPPING.md`

**Change**: Update the companion user doc so its description of Phase 2 validation and the Step 5
decision matches the resilient guidance (optional/best-effort checks, optional Steps 5–8, skip
recommendation when sources remain).

## Testing Strategy

### Validation Approach

The testing strategy follows a two-phase approach: first, surface counterexamples that demonstrate
the bug on the unfixed guidance, then verify the fix produces resilient behavior and preserves
existing behavior. Because the artifact under test is steering/documentation guidance, tests assert
on the presence/absence of the required guidance branches and the conditions under which they apply,
rather than on executable runtime output.

### Exploratory Bug Condition Checking

**Goal**: Surface counterexamples that demonstrate the bug BEFORE implementing the fix. Confirm or
refute the root cause analysis. If we refute, we will need to re-hypothesize.

**Test Plan**: Inspect the unfixed Module 5 Phase 2 guidance for (a) a conditional branch that
degrades verbatim-fidelity / routing-coverage to optional when their scripts are unavailable, and
(b) explicit Step 5 `detect_environment` menu handling with a recommendation and next action. Assert
these branches are present; on unfixed guidance these assertions fail, demonstrating the bug.

**Test Cases**:
1. **Verbatim gate degradation** (will fail on unfixed code): Assert the Step 4 guidance contains an
   "if `sz_verbatim_check.py` unavailable → skip as optional, proceed" branch.
2. **Routing report degradation** (will fail on unfixed code): Assert the Step 4 guidance contains an
   "if `sz_routing_report.py` unavailable → skip as optional, proceed" branch.
3. **Analyzer-anchored validation** (will fail on unfixed code): Assert the guidance names
   `sz_json_analyzer.py` as the primary validation sufficient to proceed when the others are absent.
4. **Step 5 menu handling** (will fail on unfixed code): Assert the guidance explains Steps 5–8 as
   optional sandbox validation and recommends a skip + next-source continuation when sources remain.

**Expected Counterexamples**:
- The unfixed guidance frames verbatim-fidelity as a hard gate with no unavailability branch.
- The unfixed guidance has no `detect_environment` menu handling.
- Possible causes: hard-gate framing, missing degradation branch, missing Step 5 interpretation,
  missing multi-source continuation logic.

### Fix Checking

**Goal**: Verify that for all inputs where the bug condition holds, the fixed guidance produces the
expected behavior.

**Pseudocode:**
```
FOR ALL input WHERE isBugCondition(input) DO
  result := module5Guidance_fixed(input)
  ASSERT expectedBehavior(result)
  // gateBlocked inputs: verbatim/routing degraded to optional, proceed via sz_json_analyzer.py
  // deadEnd inputs: Steps 5-8 explained as optional, skip recommended, next source started
END FOR
```

### Preservation Checking

**Goal**: Verify that for all inputs where the bug condition does NOT hold, the fixed guidance
produces the same result as the original guidance.

**Pseudocode:**
```
FOR ALL input WHERE NOT isBugCondition(input) DO
  ASSERT module5Guidance_original(input) = module5Guidance_fixed(input)
END FOR
```

**Testing Approach**: Property-based testing is recommended for preservation checking because:
- It generates many workflow-state inputs automatically across the input domain (every step, every
  combination of script availability, and both explicit Step 5 choices).
- It catches edge cases that manual unit tests might miss (e.g., partially available scripts).
- It provides strong guarantees that behavior is unchanged for all non-buggy inputs.

**Test Plan**: Observe behavior on the unfixed guidance for non-bug inputs — all scripts hosted, and
explicit `test_load` / `load+resolve` selections — then write property-based tests capturing that
behavior and assert the fixed guidance matches.

**Test Cases**:
1. **Analyzer validation preservation**: Observe that `sz_json_analyzer.py` structural +
   Entity-Specification validation runs on unfixed guidance when available, then verify this continues
   after the fix (3.1).
2. **Available-scripts preservation**: Observe that verbatim-fidelity and routing-coverage checks run
   when their scripts are hosted, then verify this continues after the fix (3.2).
3. **Progression + Step 4 approval preservation**: Observe the normal per-source `mapping_workflow`
   progression and Step 4 approval on unfixed guidance, then verify it is unchanged (3.3).
4. **Explicit Phase 3 path preservation**: Observe that explicit `test_load` / `load+resolve`
   selections enter Phase 3 Steps 5–8, then verify this continues after the fix (3.4, 3.5).

### Unit Tests

- Assert the Step 4 guidance includes the verbatim-fidelity unavailability (skip-as-optional) branch.
- Assert the Step 4 guidance includes the routing-coverage unavailability (skip-as-optional) branch.
- Assert the guidance names `sz_json_analyzer.py` as the primary validation that allows the workflow
  to proceed when the other scripts are absent.
- Assert the Step 5 `detect_environment` guidance labels Steps 5–8 optional and enumerates the four
  options.
- Assert the guidance recommends a skip and next-source continuation when unmapped sources remain.

### Property-Based Tests

- Generate `WorkflowState` inputs across all steps and every combination of script availability;
  assert that whenever `isBugCondition` holds via Aspect A, the fixed guidance degrades the affected
  check and proceeds via `sz_json_analyzer.py`.
- Generate Step 5 states with varying numbers of remaining unmapped sources; assert the recommendation
  is "skip + continue" when sources remain and the menu is always explained.
- Generate non-bug inputs (all scripts hosted, or explicit `test_load` / `load+resolve` choice) and
  assert the fixed guidance equals the original guidance (preservation).

### Integration Tests

- Full Phase 2 flow with `sz_verbatim_check.py` and `sz_routing_report.py` at HTTP 404 and
  `sz_json_analyzer.py` at HTTP 200: confirm the workflow completes validation and reaches Step 4
  approval without blocking.
- Step 4 → Step 5 transition with multiple unmapped sources: confirm the menu is explained, a skip is
  recommended, and the next unmapped source is started.
- Step 5 with an explicit `test_load` / `load+resolve` selection: confirm the flow enters Phase 3
  Steps 5–8 unchanged and the real load remains deferred to Module 6.
