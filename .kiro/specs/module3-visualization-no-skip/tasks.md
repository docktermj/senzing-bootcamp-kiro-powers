# Implementation Plan

## Overview

This bugfix removes the **CONDITION B** escape hatch from the Module 3 Step 9 ("Web Service +
Visualization") ⛔ mandatory gate so the gate is satisfied **only** by CONDITION A — both Step 9
checkpoints (`module_3_verification.checks.web_service.status` and
`module_3_verification.checks.web_page.status`) equal to `"passed"`. A `skipped_steps["3.9"]` entry
is ignored for this gate only; every other mandatory gate, the ordinary skip-step protocol for
non-mandatory steps, and all unrelated behavior remain untouched.

The fix spans eight enforcement and documentation surfaces that must stay mutually consistent. Four
of them — the three `.kiro.hook` files plus the `steering/hook-registry-modules.md` mirror — are
held byte-consistent by CI via `sync_hook_registry.py --verify`, so the registry mirror is
regenerated after the hook edits land.

Two new property-based test files (pytest + Hypothesis, stdlib + Hypothesis only, per
`python-conventions.md`) validate the fix: an exploration suite (Property 1 — Fix Checking) authored
to FAIL on the unfixed code (CONDITION B still present), and a preservation suite (Property 2 —
Preservation Checking) authored to PASS on the unfixed code. A shared domain model mirrors
`isBugCondition` from `bugfix.md`:

```python
@dataclass
class GateState:
    checkpoints_passed: bool
    skip_present: bool
    operation: str  # "complete" | "advance" | "stop" | "validate"

def is_bug_condition(x: GateState) -> bool:
    gate_crossed = x.operation in {"complete", "advance", "stop", "validate"}
    return gate_crossed and (not x.checkpoints_passed) and x.skip_present
```

## Tasks

- [x] 1. Write bug condition exploration test (Fix Checking)
  - **Property 1: Bug Condition** - Visualization Gate Cannot Be Satisfied By A Skip
  - **CRITICAL**: This test MUST FAIL on unfixed code (CONDITION B still present) — failure confirms the bug exists
  - **DO NOT attempt to fix the test or the code when it fails**
  - **NOTE**: This test encodes the expected behavior — it will validate the fix when it passes after implementation
  - **GOAL**: Surface counterexamples demonstrating that CONDITION B / `skipped_steps["3.9"]` currently satisfies the Module 3 Step 9 visualization gate
  - **Scoped PBT Approach**: For the deterministic hook-content assertions, scope to the concrete three hook files; use Hypothesis only to enumerate the bug-condition input space (`gate crossed AND NOT checkpoints_passed AND skip_present`)
  - Create `senzing-bootcamp/tests/test_module3_visualization_no_skip_exploration.py`
  - Per `python-conventions.md`: `from __future__ import annotations`, class-based organization, type hints (`X | None`, `list[str]`), `st_`-prefixed strategies, `@settings(max_examples=20)`, stdlib + Hypothesis only
  - Define the `GateState` dataclass `{ checkpoints_passed: bool, skip_present: bool, operation: str }` and `is_bug_condition(x) -> bool` mirroring the `isBugCondition` pseudocode in `bugfix.md`
  - Add `st_gate_state()` composite strategy drawing `checkpoints_passed` (booleans), `skip_present` (booleans), and `operation` (`"complete" | "advance" | "stop" | "validate"`)
  - Import `validate_mandatory_gates` via the `sys.path` manipulation pattern from `python-conventions.md` (`_SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"`)
  - **Test 1 — Gate hook has no CONDITION B**: parse `senzing-bootcamp/hooks/gate-module3-visualization.kiro.hook` and assert its prompt contains NO `"CONDITION B"` and no `skipped_steps["3.9"]` satisfaction branch
  - **Test 2 — Enforce-mandatory-gate has no CONDITION B**: same assertion for `senzing-bootcamp/hooks/enforce-mandatory-gate.kiro.hook`
  - **Test 3 — Enforce-gate-on-stop has no CONDITION B**: same assertion for `senzing-bootcamp/hooks/enforce-gate-on-stop.kiro.hook`
  - **Test 4 — `_check_gate` reports a violation under skip**: for a progress state with `current_step > 9`, no `web_service`/`web_page` checkpoints, and `skipped_steps["3.9"]` present, assert `validate_mandatory_gates._check_gate` returns a non-`None` `Violation` for the Module 3 Step 9 gate
  - **Property test**: for every `GateState` where `is_bug_condition(x)` holds, assert the fixed logic blocks/reports a violation (the three hooks carry no CONDITION B branch AND `_check_gate` returns a `Violation` for the equivalent progress state)
  - **DO NOT** hardcode any MCP server URL in the test (security hook blocks it)
  - Run on UNFIXED code: `pytest senzing-bootcamp/tests/test_module3_visualization_no_skip_exploration.py`
  - **EXPECTED OUTCOME**: Test FAILS (correct — the three hooks still contain CONDITION B and `_check_gate` returns `None` for the skip + no-checkpoint state)
  - Document counterexamples found (e.g., "gate-module3-visualization prompt still contains CONDITION B and a `skipped_steps[\"3.9\"]` branch"; "`_check_gate` returns None for current_step=10 with skipped_steps[\"3.9\"] and no checkpoints")
  - Mark task complete when the test is written, run, and the failure is documented
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

- [x] 2. Write preservation property tests (BEFORE implementing fix)
  - **Property 2: Preservation** - All Non-Buggy Inputs Unchanged
  - **IMPORTANT**: Follow observation-first methodology — observe behavior on UNFIXED code, snapshot it, then assert it is preserved
  - **IMPORTANT**: Write these tests BEFORE implementing the fix
  - Create `senzing-bootcamp/tests/test_module3_visualization_no_skip_preservation.py`
  - Per `python-conventions.md`: `from __future__ import annotations`, class-based organization, type hints (`X | None`, `list[str]`), `st_`-prefixed strategies, `@settings(max_examples=20)`, stdlib + Hypothesis only
  - Reuse `GateState`, `is_bug_condition`, and `st_gate_state()` (import or redefine); import `validate_mandatory_gates` via the `sys.path` pattern
  - **Observation phase**: snapshot via SHA-256 the UNFIXED unrelated regions — hooks/scripts/steering/config not tied to the Module 3 visualization gate — and the unchanged structural fields of the three edited hooks (`name`, `version`, `when`, `then`)
  - **Test — CONDITION A preservation (3.1)**: when both Step 9 checkpoints are `"passed"`, the gate is satisfied (no `_check_gate` violation) — true on unfixed and fixed code
  - **Test — Other-gate skip preservation (3.3)**: `_check_gate` still returns `None` for a NON-`"3.9"` mandatory gate with a matching `skipped_steps` entry (use a synthetic `MandatoryGate` with a different module/step, e.g. `3.3`)
  - **Test — Non-mandatory skip preservation (3.2)**: skip-step protocol structure for non-⛔ steps is intact and honored (skips other than `"3.9"` allow advancement)
  - **Test — Non-Module-3 / unrelated no-op (3.4)**: the three hooks' prompts still short-circuit to "no output" for writes that don't target `config/bootcamp_progress.json`, don't mark Module 3 complete, and don't advance `current_step` past 9
  - **Test — Hook schema/name/trigger preservation (3.5)**: each hook keeps `name`, `version`, `when`, `then`; `gate-module3-visualization` and `enforce-mandatory-gate` stay `preToolUse` + `toolTypes:["write"]`; `enforce-gate-on-stop` stays `agentStop`; `name` fields keep the "to ..." form
  - **Test — Snapshot of unrelated regions (3.7)**: assert the SHA-256 of unrelated hooks/scripts/steering/config bytes is unchanged from the baseline
  - **PBT — Non-bug-condition equivalence (`F(X) = F'(X)`)**: for every `GateState` where `NOT is_bug_condition(x)`, assert the fixed logic produces the same result as the baseline
  - **DO NOT** hardcode any MCP server URL in the test (security hook blocks it)
  - Run on UNFIXED code: `pytest senzing-bootcamp/tests/test_module3_visualization_no_skip_preservation.py`
  - **EXPECTED OUTCOME**: Tests PASS (this confirms the baseline behavior to preserve)
  - Mark task complete when tests are written, run, and passing on unfixed code
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7_

- [x] 3. Fix — remove CONDITION B from the Module 3 Step 9 visualization gate

  - [x] 3.1 Remove CONDITION B from `gate-module3-visualization.kiro.hook`
    - Edit `senzing-bootcamp/hooks/gate-module3-visualization.kiro.hook` (prompt + `description`)
    - Prompt: remove the entire `CONDITION B — Step 9 was explicitly skipped:` block and its `skipped_steps["3.9"]` line; change the satisfaction line from `If CONDITION A is true OR CONDITION B is true: produce no output...` to the checkpoints-only form `If CONDITION A is true: produce no output at all. Do nothing.`; change `If NEITHER condition is met:` to `If CONDITION A is not met:`
    - Keep the CONDITION A checkpoint checks verbatim (the `web_service` / `web_page` `"passed"` checks) so preservation checkpoint-structure assertions still hold
    - `description`: change "...or the step was explicitly skipped via the skip-step protocol." to "...Step 9 is an unconditional ⛔ mandatory gate and cannot be skipped."
    - _Bug_Condition: isBugCondition(X) where gateCrossed (Module 3 complete) AND NOT checkpointsPassed AND "3.9" IN skipped_steps_
    - _Expected_Behavior: gate-module3-visualization SHALL block the write regardless of skipped_steps["3.9"] — only CONDITION A satisfies the gate (Property 1)_
    - _Preservation: CONDITION A checkpoint checks, hook schema/name/trigger, and unrelated prompt regions unchanged (Property 2)_
    - _Requirements: 2.1, 2.5_

  - [x] 3.2 Remove CONDITION B from `enforce-mandatory-gate.kiro.hook`
    - Edit `senzing-bootcamp/hooks/enforce-mandatory-gate.kiro.hook` (prompt + `description`)
    - Prompt: remove the `CONDITION B — Step 9 was explicitly skipped by the bootcamper:` block and its `"3.9"` line; change `If CONDITION A is true OR CONDITION B is true: produce no output...` to the checkpoints-only form; change `If NEITHER condition is met:` to `If CONDITION A is not met:`. Keep the ⛔ BLOCKED output text and the `web_service`/`web_page` `"passed"` checks verbatim
    - `description`: drop the "and no skipped_steps entry exists" clause (e.g. "Blocks step advancement past a ⛔ mandatory gate step in bootcamp_progress.json when the corresponding checkpoint is missing. Step 9 is unconditional and cannot be satisfied by a skip. ..."); retain the sentence about firing BEFORE advancement
    - _Bug_Condition: isBugCondition(X) where gateCrossed (current_step advanced past 9) AND NOT checkpointsPassed AND "3.9" IN skipped_steps_
    - _Expected_Behavior: enforce-mandatory-gate SHALL block the write regardless of skipped_steps["3.9"] — only CONDITION A satisfies the gate (Property 1)_
    - _Preservation: ⛔ BLOCKED output text, checkpoint checks, hook schema/name/trigger unchanged (Property 2)_
    - _Requirements: 2.2, 2.5_

  - [x] 3.3 Remove CONDITION B from `enforce-gate-on-stop.kiro.hook`
    - Edit `senzing-bootcamp/hooks/enforce-gate-on-stop.kiro.hook` (prompt only — its `description` does not mention skipping, so no description change is needed)
    - Prompt: remove the `CONDITION B — Step 9 was explicitly skipped by the bootcamper:` block and its `"3.9"` line; change `If CONDITION A is true OR CONDITION B is true: produce no output...` to the checkpoints-only form; change `If NEITHER condition is met:` to `If CONDITION A is not met:`. Keep the ⛔ MANDATORY GATE VIOLATION output text verbatim
    - _Bug_Condition: isBugCondition(X) where gateCrossed (current_module=3 AND current_step>=9 at agentStop) AND NOT checkpointsPassed AND "3.9" IN skipped_steps_
    - _Expected_Behavior: enforce-gate-on-stop SHALL emit the ⛔ violation regardless of skipped_steps["3.9"] — only CONDITION A satisfies the gate (Property 1)_
    - _Preservation: ⛔ MANDATORY GATE VIOLATION output text, hook schema/name/trigger unchanged (Property 2)_
    - _Requirements: 2.3_

  - [x] 3.4 Regenerate the registry mirror `hook-registry-modules.md` to match the three edited hooks
    - Update `senzing-bootcamp/steering/hook-registry-modules.md` Module 3 section so the `gate-module3-visualization`, `enforce-mandatory-gate`, and `enforce-gate-on-stop` prompt code-fences and `- description:` lines match the edited `.kiro.hook` files exactly
    - Prefer regenerating via `python senzing-bootcamp/scripts/sync_hook_registry.py`, then confirm with `python senzing-bootcamp/scripts/sync_hook_registry.py --verify`
    - **NOTE**: This task depends on 3.1–3.3 being complete (the mirror must reflect the final hook bytes)
    - _Bug_Condition: documentation mirror still presented the gate as skippable (CONDITION B wording mirrored from hooks)_
    - _Expected_Behavior: mirror reflects the unconditional gate; `sync_hook_registry.py --verify` passes (Property 1 req 2.5)_
    - _Preservation: byte-consistency between hooks and mirror; CI `sync_hook_registry.py --verify` stays green (Property 2 req 3.6)_
    - _Requirements: 2.5, 3.6_

  - [x] 3.5 Special-case the `"3.9"` gate in `validate_mandatory_gates.py`
    - Edit `senzing-bootcamp/scripts/validate_mandatory_gates.py`
    - Add a module-level constant `NON_SKIPPABLE_GATES = {"3.9"}` near `_MODULE3_STEP9_CHECKPOINTS`
    - In `_check_gate`, guard the existing skip short-circuit: `if skip_key in skipped_steps and skip_key not in NON_SKIPPABLE_GATES: return None`
    - No other logic changes; the existing message, checkpoint loop, and `module_N_verification` lookup are preserved (a missing `"3.9"` checkpoint now yields a `Violation`)
    - _Bug_Condition: isBugCondition(X) where validate evaluates the Module 3 Step 9 gate crossed AND NOT checkpointsPassed AND "3.9" IN skipped_steps_
    - _Expected_Behavior: _check_gate SHALL return a Violation for the "3.9" gate regardless of skipped_steps["3.9"] (Property 1 req 2.4)_
    - _Preservation: every other mandatory gate continues to honor its skipped_steps entry (Property 2 req 3.3)_
    - _Requirements: 2.4, 3.3_

  - [x] 3.6 Update the gate summary line in `install_hooks.py`
    - Edit `senzing-bootcamp/scripts/install_hooks.py`: change the `gate-module3-visualization.kiro.hook` summary tuple element from "Blocks Module 3 completion until visualization step is done or skipped" to "Blocks Module 3 completion until visualization step is done" (drop "or skipped")
    - _Bug_Condition: install summary described the gate as satisfiable by a skip ("or skipped")_
    - _Expected_Behavior: summary states the gate is satisfied only by completing the visualization (Property 1 req 2.5)_
    - _Preservation: all other install summary lines unchanged (Property 2 req 3.7)_
    - _Requirements: 2.5_

  - [x] 3.7 Update the gate `3->4` requires text in `module-dependencies.yaml`
    - Edit `senzing-bootcamp/config/module-dependencies.yaml` gate `3->4`: change `- "System verification passed or explicitly skipped by bootcamper"` to a requires entry that no longer presents the visualization as skippable, e.g. `- "System verification passed, including the Step 9 web service + visualization (cannot be skipped)"`
    - Keep the list-of-strings YAML schema valid (single quoted string under `requires:`); leave the module-level `skip_if` mechanism on module 3 unchanged
    - _Bug_Condition: dependency-gate config described the gate as "explicitly skipped by bootcamper"_
    - _Expected_Behavior: gate 3->4 text presents the Step 9 visualization as non-skippable (Property 1 req 2.5)_
    - _Preservation: YAML stays valid; module-level skip_if and other gates unchanged (Property 2 req 3.7)_
    - _Requirements: 2.5_

  - [x] 3.8 Add an explicit Step 9 non-skippable note to `skip-step-protocol.md`
    - Edit `senzing-bootcamp/steering/skip-step-protocol.md` Constraints section: add a clause naming Step 9, e.g. "In particular, the Module 3 Step 9 (Web Service + Visualization) gate is unconditional per Governing Rule 15 — a `skipped_steps[\"3.9\"]` entry is ignored by the visualization gate and never satisfies it."
    - Keep CommonMark valid and the existing Constraints bullets intact
    - _Bug_Condition: protocol stated mandatory gates can't be skipped generally but did not call out Step 9, leaving room for the CONDITION B interpretation_
    - _Expected_Behavior: protocol explicitly states Step 9 is unconditional and skipped_steps["3.9"] is ignored (Property 1 req 2.5)_
    - _Preservation: existing Constraints bullets and CommonMark validity unchanged (Property 2 reqs 3.6, 3.7)_
    - _Requirements: 2.5_

  - [x] 3.9 Update/invert the existing tests that assert the OLD behavior (do NOT delete)
    - **Invert** `senzing-bootcamp/tests/test_mandatory_gate_preservation.py::test_gate_hook_checks_both_conditions` — currently asserts both "CONDITION A" and "CONDITION B" are present; update to assert "CONDITION B" is ABSENT (and CONDITION A still present)
    - **Invert** `senzing-bootcamp/tests/test_mandatory_gate_preservation.py::test_existing_gate_hook_accepts_skipped_steps_entry` — currently asserts the gate hook references `skipped_steps`/`"3.9"`; update to assert the visualization gate hook no longer accepts a `"3.9"` skip (no CONDITION B branch)
    - **Update** `senzing-bootcamp/tests/test_module3_default_on_unit.py::test_gate_3_4_explicitly_skipped` — update the `"explicitly skipped"` assertion to the new non-skippable gate `3->4` wording
    - **Update** `senzing-bootcamp/tests/test_system_verification_unit.py` — update the gate `3->4` requires-text assertion from `"explicitly skipped"` to the new wording
    - **Reconcile** `senzing-bootcamp/tests/test_mandatory_gate_exploration.py` references to `skipped_steps["3.9"]` so its assertions remain consistent with the fixed CONDITION-A-only gate (the existence/⛔-marker checks remain valid)
    - All of the above are **updated/inverted, not deleted**
    - _Bug_Condition: existing tests encoded the CONDITION B / "explicitly skipped" behavior as correct_
    - _Expected_Behavior: existing tests assert the unconditional gate (CONDITION B absent, "3.9" skip not accepted, new gate 3->4 wording) (Property 1 reqs 2.1, 2.4, 2.5)_
    - _Preservation: existence/⛔-marker checks and unrelated assertions remain intact; other-gate skip behavior still asserted (Property 2 req 3.3)_
    - _Requirements: 2.1, 2.4, 2.5, 3.3_

  - [x] 3.10 Verify bug condition exploration test now passes
    - **Property 1: Expected Behavior** - Visualization Gate Cannot Be Satisfied By A Skip
    - **IMPORTANT**: Re-run the SAME test from task 1 — do NOT write a new test
    - The test from task 1 encodes the expected behavior; when it passes, CONDITION B is confirmed removed from all three hooks and `_check_gate` reports a violation under the skip + no-checkpoint state
    - Run `pytest senzing-bootcamp/tests/test_module3_visualization_no_skip_exploration.py`
    - **EXPECTED OUTCOME**: Test PASSES (confirms the bug is fixed across the three hooks and `validate_mandatory_gates.py`)
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

  - [x] 3.11 Verify preservation tests still pass
    - **Property 2: Preservation** - All Non-Buggy Inputs Unchanged
    - **IMPORTANT**: Re-run the SAME tests from task 2 — do NOT write new tests
    - Run `pytest senzing-bootcamp/tests/test_module3_visualization_no_skip_preservation.py`
    - **EXPECTED OUTCOME**: Tests PASS (confirms no regressions — CONDITION A still satisfies the gate, other mandatory gates still honor skips, non-mandatory skips honored, non-Module-3 writes remain no-ops, hook schema/triggers/names unchanged, unrelated regions byte-stable)
    - Confirm all tests still pass after the fix (no regressions)
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7_

- [x] 4. Checkpoint - Ensure all tests pass
  - Run the two new suites: `pytest senzing-bootcamp/tests/test_module3_visualization_no_skip_exploration.py senzing-bootcamp/tests/test_module3_visualization_no_skip_preservation.py`
  - Run the updated existing suites: `pytest senzing-bootcamp/tests/test_mandatory_gate_preservation.py senzing-bootcamp/tests/test_mandatory_gate_exploration.py senzing-bootcamp/tests/test_module3_default_on_unit.py senzing-bootcamp/tests/test_system_verification_unit.py`
  - Run CI validators: `python senzing-bootcamp/scripts/sync_hook_registry.py --verify`, `python senzing-bootcamp/scripts/validate_commonmark.py`, `python senzing-bootcamp/scripts/measure_steering.py --check`
  - Run `python senzing-bootcamp/scripts/validate_mandatory_gates.py` against representative progress fixtures: (a) skip + no checkpoints past the gate → violation / non-zero exit; (b) checkpoints present → exit 0; (c) other-gate skip → still honored
  - Confirm no MCP server URL was introduced into any edited surface
  - Ensure all tests pass; ask the user if questions arise.
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7_

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1", "2"] },
    { "id": 1, "tasks": ["3.1", "3.2", "3.3", "3.5", "3.6", "3.7", "3.8", "3.9"] },
    { "id": 2, "tasks": ["3.4"] },
    { "id": 3, "tasks": ["3.10", "3.11"] },
    { "id": 4, "tasks": ["4"] }
  ]
}
```

- **Wave 0** — `[1, 2]`: the exploration suite (must FAIL on unfixed code) and the preservation suite (must PASS on unfixed code) are authored against the unfixed baseline and can run in parallel.
- **Wave 1** — `[3.1, 3.2, 3.3, 3.5, 3.6, 3.7, 3.8, 3.9]`: all touch distinct files and are independent — 3.1/3.2/3.3 edit the three distinct hook files, 3.5/3.6 edit distinct scripts, 3.7 edits the config, 3.8 edits the steering protocol, and 3.9 edits the existing test files.
- **Wave 2** — `[3.4]`: the registry mirror regeneration depends on the final bytes of the three edited hooks (3.1–3.3), so it runs after wave 1.
- **Wave 3** — `[3.10, 3.11]`: verification re-runs the unchanged task 1 / task 2 suites after the fix lands.
- **Wave 4** — `[4]`: the final checkpoint runs all suites and CI validators after verification.

## Notes

- Tests use pytest + Hypothesis (property-based testing), stdlib + Hypothesis only, in `senzing-bootcamp/tests/` per `tech.md` and `python-conventions.md`.
- The exploration test (task 1) is authored to FAIL on unfixed code (CONDITION B still present) — this confirms the bug across the three hooks and `validate_mandatory_gates.py`.
- The preservation test (task 2) is authored to PASS on unfixed code — this captures baseline behavior to preserve. After the fix (tasks 3.1–3.9), both suites PASS.
- The three `.kiro.hook` files and the `hook-registry-modules.md` mirror are held byte-consistent by CI (`sync_hook_registry.py --verify`); 3.4 regenerates the mirror after 3.1–3.3.
- `NON_SKIPPABLE_GATES = {"3.9"}` special-cases only the Module 3 Step 9 gate in `_check_gate`; every other mandatory gate continues to honor its `skipped_steps` entry (req 3.3).
- No MCP server URL is introduced into any hook, script, steering file, config, or test (security hook blocks it; the power's `mcp.json` remains the single source of truth).
- Existing tests in task 3.9 are updated/inverted, never deleted.
