# Module 3 Visualization No-Skip Bugfix Design

## Overview

Governing Rule 15 of the Senzing Bootcamp Power states: "In module 3, ALWAYS create the
visualization." The Module 3 visualization step (Step 9 — the ⛔ mandatory gate "Web Service +
Visualization") is meant to be unconditional. However, the current gate enforcement carries a
documented escape hatch — **CONDITION B** — that treats a `skipped_steps["3.9"]` entry in
`config/bootcamp_progress.json` as satisfying the gate. This directly contradicts both Governing
Rule 15 and the power's own `steering/skip-step-protocol.md` ("Mandatory gates (⛔) cannot be
skipped").

The fix is a **minimal, targeted removal of CONDITION B from the Module 3 Step 9 visualization gate
only.** After the fix, the gate is satisfied **exclusively by CONDITION A** — the real Step 9
checkpoints `module_3_verification.checks.web_service.status == "passed"` AND
`module_3_verification.checks.web_page.status == "passed"`. Any `skipped_steps["3.9"]` entry is
ignored **for this gate only**. Every other mandatory gate, the ordinary skip-step protocol for
non-mandatory steps, and all unrelated behavior remain untouched.

The fix spans eight enforcement and documentation surfaces that must stay mutually consistent. Four
of them — the three hook files plus the `steering/hook-registry-modules.md` mirror — are held
byte-consistent by CI via `sync_hook_registry.py --verify`, so the prompt text and `description`
fields must match the registry mirror exactly. The remaining four are the validation script, the
install summary, the dependency-gate config, and the skip-step protocol note.

## Glossary

- **Bug_Condition (C)**: The condition that triggers the bug — the Module 3 Step 9 visualization
  gate is crossed without checkpoints, yet a `skipped_steps["3.9"]` entry causes the gate to be
  (incorrectly) treated as satisfied. Formalized as `isBugCondition(X)` below.
- **Property (P)**: The desired behavior — when the visualization gate is crossed without
  checkpoints, the system blocks / reports a violation regardless of any `skipped_steps["3.9"]`
  entry. The skip can never satisfy this gate.
- **Preservation**: All non-buggy behavior that must remain unchanged — CONDITION A satisfying the
  gate, other mandatory gates honoring skips, non-mandatory skips, unrelated/non-Module-3 writes,
  hook schema/names/triggers, and CI staying green.
- **CONDITION A**: The legitimate satisfaction path — both Step 9 checkpoints
  (`module_3_verification.checks.web_service.status` and
  `module_3_verification.checks.web_page.status`) equal `"passed"`. **Preserved by this fix.**
- **CONDITION B**: The escape-hatch path being removed — a `skipped_steps` entry with key `"3.9"`
  treated as satisfying the visualization gate. **Removed by this fix (for the Module 3 Step 9 gate
  only).**
- **Visualization gate / Step 9 / "3.9"**: The ⛔ mandatory gate in `module-03-system-verification.md`
  for "Web Service + Visualization". The skip key is `"3.9"` (`{module}.{step}` form).
- **F**: The original (unfixed) gate-enforcement logic where CONDITION B satisfies the visualization
  gate.
- **F'**: The fixed logic where only CONDITION A satisfies the visualization gate.
- **`gate-module3-visualization`**: The `preToolUse`/`write` hook in
  `hooks/gate-module3-visualization.kiro.hook` that blocks Module 3 *completion* writes when Step 9
  is incomplete.
- **`enforce-mandatory-gate`**: The `preToolUse`/`write` hook in
  `hooks/enforce-mandatory-gate.kiro.hook` that blocks *advancement* of `current_step` past Step 9
  when incomplete.
- **`enforce-gate-on-stop`**: The `agentStop` hook in `hooks/enforce-gate-on-stop.kiro.hook` that
  emits a violation if the agent stops at/after Step 9 while it is incomplete.
- **`_check_gate`**: The function in `scripts/validate_mandatory_gates.py` that evaluates one
  `MandatoryGate` against progress and returns a `Violation | None`.
- **`NON_SKIPPABLE_GATES`**: A new module-level constant `{"3.9"}` introduced in
  `validate_mandatory_gates.py` to identify gates whose `skipped_steps` entry must NOT satisfy them.

## Bug Details

### Bug Condition

The bug manifests when the Module 3 Step 9 visualization gate is *crossed* (a write marks Module 3
complete, a write advances `current_step` past 9, an `agentStop` occurs at `current_module == 3` and
`current_step >= 9`, or `validate_mandatory_gates.py` evaluates the gate as crossed) AND the Step 9
checkpoints are NOT both `"passed"` AND a `skipped_steps["3.9"]` entry is present. In that state, all
four enforcement surfaces (three hooks + the validation script) treat CONDITION B as satisfying the
gate and allow the bootcamper / agent to bypass the visualization.

**Formal Specification:**

```
FUNCTION isBugCondition(X)
  INPUT: X = progress state + triggering operation for the Module 3 visualization gate
  OUTPUT: boolean

  // Step 9 checkpoints are NOT both passed (CONDITION A is false)
  checkpointsPassed ← (X.module_3_verification.checks.web_service.status = "passed")
                      AND (X.module_3_verification.checks.web_page.status = "passed")

  // The operation crosses / completes the Module 3 Step 9 gate
  gateCrossed ← X.operation marks Module 3 complete
                OR X.operation advances current_step past 9
                OR (X.current_module = 3 AND X.current_step >= 9 at agentStop)
                OR (validate evaluates the Module 3 Step 9 gate as crossed)

  // A skip entry exists for the visualization gate (CONDITION B is true)
  skipPresent ← "3.9" IN keys(X.skipped_steps)

  // Bug is triggered only when the gate is crossed without checkpoints
  // but a skip entry would (incorrectly) satisfy it
  RETURN gateCrossed AND (NOT checkpointsPassed) AND skipPresent
END FUNCTION
```

### Examples

- **Completion write + skip, no checkpoints (BUG)**: `bootcamp_progress.json` has
  `skipped_steps["3.9"]` present and `module_3_verification.checks.web_service` /
  `web_page` absent. A write adds `3` to `modules_completed`.
  *Expected:* `gate-module3-visualization` blocks the write.
  *Actual (F):* allowed (CONDITION B satisfies the gate). **Must block in F'.**
- **Advance write + skip, no checkpoints (BUG)**: `skipped_steps["3.9"]` present, no checkpoints, a
  write sets `current_step` to `10`.
  *Expected:* `enforce-mandatory-gate` blocks the write.
  *Actual (F):* allowed. **Must block in F'.**
- **agentStop at Step 9+ + skip, no checkpoints (BUG)**: `current_module == 3`,
  `current_step >= 9`, `skipped_steps["3.9"]` present, no checkpoints, agent stops.
  *Expected:* `enforce-gate-on-stop` emits the ⛔ violation.
  *Actual (F):* no output. **Must emit in F'.**
- **`validate_mandatory_gates.py` + skip, no checkpoints (BUG)**: progress past the gate with
  `skipped_steps["3.9"]` and no checkpoints.
  *Expected:* `_check_gate` returns a `Violation`.
  *Actual (F):* returns `None`. **Must report a violation in F'.**
- **Checkpoints present (NOT a bug — CONDITION A)**: `web_service.status == "passed"` and
  `web_page.status == "passed"`. Gate satisfied in both F and F'. **Preserved.**
- **Other mandatory gate skipped (NOT a bug)**: a `skipped_steps` entry for some gate other than
  `"3.9"`. The skip continues to satisfy that gate in both F and F'. **Preserved.**

## Expected Behavior

### Preservation Requirements

**Unchanged Behaviors:**

- **CONDITION A still satisfies the gate** — when both Step 9 checkpoints are `"passed"`, the gate
  is satisfied (no block, no violation) in F and F'. *(Requirement 3.1)*
- **Other mandatory gates still honor skips** — `validate_mandatory_gates.py` continues to treat a
  matching `skipped_steps` entry as satisfying any mandatory gate **other than** `"3.9"`.
  *(Requirements 3.2, 3.3)*
- **Non-mandatory step skips still work** — bootcamper-initiated skips of non-⛔ steps via the
  skip-step protocol continue to be honored and allow advancement. *(Requirement 3.2)*
- **Non-Module-3 / unrelated writes remain a no-op** — writes that don't target
  `config/bootcamp_progress.json`, don't mark Module 3 complete, and don't advance `current_step`
  past 9 produce no hook output. *(Requirement 3.4)*
- **Hook schema, names, and triggers unchanged** — each hook keeps its trigger type/events
  (`preToolUse`/`toolTypes:["write"]` for `gate-module3-visualization` and `enforce-mandatory-gate`;
  `agentStop` for `enforce-gate-on-stop`), its `name` field (the "to ..." form), and a valid JSON
  schema (`name`, `version`, `when`, `then`). *(Requirement 3.5)*
- **CI stays green** — `sync_hook_registry.py --verify`, `validate_commonmark.py`, and
  `measure_steering.py --check` all continue to pass; the three hook files stay byte-consistent with
  the `hook-registry-modules.md` mirror, CommonMark stays valid, and steering token budgets stay in
  limits. *(Requirement 3.6)*
- **Everything unrelated stays untouched** — any hook, script, steering file, or config not tied to
  the Module 3 visualization gate is unchanged. *(Requirement 3.7)*

**Scope:**

All inputs where `isBugCondition(X)` is false should be completely unaffected by this fix. This
includes:

- States where the Step 9 checkpoints are both `"passed"` (CONDITION A).
- Skips of any gate other than the Module 3 Step 9 visualization gate.
- Skips of non-mandatory steps.
- Writes unrelated to Module 3 completion or step-9 advancement.

> **Note:** The expected correct behavior for buggy inputs is defined in Property 1 of the
> Correctness Properties section. This Expected Behavior section focuses on what must NOT change.

## Hypothesized Root Cause

Based on the bug analysis, the root cause is a single design decision replicated across four
enforcement surfaces plus four documentation/config surfaces:

1. **CONDITION B escape hatch in the three hooks**: Each of `gate-module3-visualization`,
   `enforce-mandatory-gate`, and `enforce-gate-on-stop` includes a branch that treats
   `skipped_steps["3.9"]` as satisfying the ⛔ gate ("If CONDITION A is true OR CONDITION B is
   true: produce no output"). This is the primary defect — the gate should be unconditional.

2. **Generic skip short-circuit in `validate_mandatory_gates.py`**: `_check_gate` short-circuits to
   `return None` whenever `skip_key = f"{gate.module}.{gate.step}"` is present in `skipped_steps`.
   This generic rule (correct for ordinary mandatory gates) wrongly also exempts the `"3.9"`
   visualization gate.

3. **Documentation/config asserting skippability**: The hook `description` fields, the
   `install_hooks.py` summary line ("...is done or skipped"), and `module-dependencies.yaml` gate
   `3->4` ("System verification passed or explicitly skipped by bootcamper") all *describe* the
   gate as skippable, reinforcing the wrong behavior and keeping the mirror/registry consistent with
   it.

4. **Missing explicit non-skippable note for Step 9**: `skip-step-protocol.md` states mandatory
   gates can't be skipped in general, but does not call out Step 9 specifically, leaving room for
   the CONDITION B interpretation.

The fix removes the CONDITION B branch from the gate (surfaces 1), special-cases `"3.9"` in
`_check_gate` so the skip short-circuit is bypassed for that gate only (surface 2), and reconciles
the documentation/config wording (surfaces 3–4) so all eight surfaces consistently present the Step
9 visualization as unconditional.

## Correctness Properties

Property 1: Bug Condition — Visualization Gate Cannot Be Satisfied By A Skip

_For any_ input where the bug condition holds (`isBugCondition(X)` returns true) — i.e., the Module 3
Step 9 visualization gate is crossed, the Step 9 checkpoints are not both `"passed"`, and a
`skipped_steps["3.9"]` entry is present — the fixed logic SHALL block the write (the three hooks
emit their ⛔ block/violation output) and SHALL report a violation (`validate_mandatory_gates.py`
`_check_gate` returns a `Violation`), regardless of the `skipped_steps["3.9"]` entry. Only CONDITION
A (both checkpoints `"passed"`) can satisfy the gate, and the documentation across all eight surfaces
SHALL state that the Step 9 visualization cannot be skipped.

**Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5**

Property 2: Preservation — All Non-Buggy Inputs Unchanged

_For any_ input where the bug condition does NOT hold (`isBugCondition(X)` returns false), the fixed
logic SHALL produce the same result as the original logic (`F(X) = F'(X)`), preserving: CONDITION A
satisfying the gate (3.1); non-mandatory step skips being honored (3.2); other mandatory gates
continuing to honor their `skipped_steps` entries (3.3); non-Module-3 / unrelated writes remaining a
no-op (3.4); hook trigger types/events, `name` fields, and JSON schema validity (3.5); CI checks
(`sync_hook_registry.py --verify`, `validate_commonmark.py`, `measure_steering.py --check`) staying
green (3.6); and all unrelated hooks/scripts/steering/config staying untouched (3.7).

**Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7**

## Fix Implementation

### Changes Required

Assuming the root cause analysis is correct, eight surfaces change. The three hook files and the
`hook-registry-modules.md` mirror must be updated **together and byte-consistently** (CI runs
`sync_hook_registry.py --verify`). The cleanest path is to edit the three `.kiro.hook` files and the
`module-03` section of the registry mirror, then run `python senzing-bootcamp/scripts/sync_hook_registry.py`
to regenerate/verify the mirror rather than hand-aligning byte-for-byte — but either way, verify with
`--verify` before completing.

---

#### 1. `senzing-bootcamp/hooks/gate-module3-visualization.kiro.hook`

**Change A — `description` field (req 2.5):**

- *Before:* `"Prevents Module 3 from being marked complete unless Step 9 (Web Service +
  Visualization) checkpoints are present in bootcamp_progress.json, or the step was explicitly
  skipped via the skip-step protocol."`
- *After:* `"Prevents Module 3 from being marked complete unless Step 9 (Web Service +
  Visualization) checkpoints are present in bootcamp_progress.json. Step 9 is an unconditional ⛔
  mandatory gate and cannot be skipped."`

**Change B — prompt CONDITION B removal (req 2.1):**

- Remove the entire `CONDITION B — Step 9 was explicitly skipped:` block and its
  `- `skipped_steps` contains an entry with key `"3.9"`` line.
- Change the satisfaction line from `If CONDITION A is true OR CONDITION B is true: produce no
  output at all. Do nothing.` to a checkpoints-only form, e.g.:
  `If CONDITION A is true: produce no output at all. Do nothing.`
- Change `If NEITHER condition is met:` to `If CONDITION A is not met:`.
- Optionally relabel "CONDITION A — Step 9 checkpoints exist:" to simply describe the single
  remaining checkpoints requirement (keep the `web_service` / `web_page` `"passed"` checks
  verbatim so the preservation checkpoint-structure assertions still hold).

#### 2. `senzing-bootcamp/hooks/enforce-mandatory-gate.kiro.hook`

**Change A — `description` field (req 2.5):**

- *Before:* `"Blocks step advancement past a ⛔ mandatory gate step in bootcamp_progress.json when
  the corresponding checkpoint is missing and no skipped_steps entry exists. ..."`
- *After:* drop the "and no skipped_steps entry exists" clause, e.g. `"Blocks step advancement past
  a ⛔ mandatory gate step in bootcamp_progress.json when the corresponding checkpoint is missing.
  Step 9 is unconditional and cannot be satisfied by a skip. ..."` (retain the remaining sentence
  about firing BEFORE advancement).

**Change B — prompt CONDITION B removal (req 2.2):**

- Remove the `CONDITION B — Step 9 was explicitly skipped by the bootcamper:` block and its
  `"3.9"` line.
- Change `If CONDITION A is true OR CONDITION B is true: produce no output at all. Do nothing. The
  mandatory gate has been satisfied.` to the checkpoints-only form.
- Change `If NEITHER condition is met:` to `If CONDITION A is not met:`. Keep the ⛔ BLOCKED output
  text and the `web_service`/`web_page` `"passed"` checks verbatim.

#### 3. `senzing-bootcamp/hooks/enforce-gate-on-stop.kiro.hook`

**Change — prompt CONDITION B removal (req 2.3):**

- Remove the `CONDITION B — Step 9 was explicitly skipped by the bootcamper:` block and its
  `"3.9"` line.
- Change `If CONDITION A is true OR CONDITION B is true: produce no output. The mandatory gate is
  satisfied.` to the checkpoints-only form.
- Change `If NEITHER condition is met:` to `If CONDITION A is not met:`. Keep the ⛔ MANDATORY GATE
  VIOLATION output text verbatim. (This hook's `description` does not mention skipping, so it needs
  no description change.)

#### 4. `senzing-bootcamp/steering/hook-registry-modules.md` (mirror)

**Change — mirror the three hooks above (reqs 2.5, 3.6):**

- In the Module 3 section, update the `enforce-gate-on-stop`, `enforce-mandatory-gate`, and
  `gate-module3-visualization` prompt code-fences and their `- description:` lines to match the
  edited `.kiro.hook` files exactly. Prefer regenerating via
  `python senzing-bootcamp/scripts/sync_hook_registry.py`, then confirm with `--verify`.

#### 5. `senzing-bootcamp/scripts/validate_mandatory_gates.py`

**Change — special-case the `"3.9"` gate in `_check_gate` (reqs 2.4, 3.3):**

- Add a module-level constant near `_MODULE3_STEP9_CHECKPOINTS`:

  ```python
  # Mandatory gates whose checkpoints CANNOT be bypassed by a skipped_steps entry.
  # The Module 3 Step 9 visualization gate ("3.9") is unconditional (Governing Rule 15).
  NON_SKIPPABLE_GATES = {"3.9"}
  ```

- In `_check_gate`, guard the existing skip short-circuit so it is bypassed for non-skippable gates:

  ```python
  # Check if skipped_steps entry exists (bootcamper-initiated skip)
  skipped_steps = progress.get("skipped_steps", {})
  skip_key = f"{gate.module}.{gate.step}"
  if skip_key in skipped_steps and skip_key not in NON_SKIPPABLE_GATES:
      return None
  ```

  This preserves the skip behavior for every other mandatory gate (req 3.3) while ensuring the
  `"3.9"` gate continues past the short-circuit to the checkpoint check, where a missing checkpoint
  yields a `Violation` (req 2.4). No other logic in the function changes; the existing message,
  checkpoint loop, and `module_N_verification` lookup are preserved.

#### 6. `senzing-bootcamp/scripts/install_hooks.py`

**Change — gate summary line (req 2.5):**

- *Before:* `"Blocks Module 3 completion until visualization step is done or skipped"`
- *After:* `"Blocks Module 3 completion until visualization step is done"`
  (drop "or skipped"; this is the third tuple element for `gate-module3-visualization.kiro.hook`).

#### 7. `senzing-bootcamp/config/module-dependencies.yaml`

**Change — gate `3->4` requires text (req 2.5):**

- *Before:* `- "System verification passed or explicitly skipped by bootcamper"`
- *After:* a single requires entry that no longer presents the visualization as skippable, e.g.
  `- "System verification passed, including the Step 9 web service + visualization (cannot be
  skipped)"`. Keep the list-of-strings YAML schema valid (single quoted string under `requires:`).
  > Tradeoff note: the two unit tests that currently assert `"explicitly skipped"` in this gate text
  > must be updated to the new wording (see Testing Strategy → Unit Tests). Module-level skip
  > behavior for Module 3 (the `skip_if` field on module 3) is a different mechanism and is left
  > unchanged.

#### 8. `senzing-bootcamp/steering/skip-step-protocol.md`

**Change — explicit Step 9 note (req 2.5):**

- The Constraints section already states "Mandatory gates (⛔) cannot be skipped." Add an explicit
  clause naming Step 9, e.g.: "In particular, the Module 3 Step 9 (Web Service + Visualization) gate
  is unconditional per Governing Rule 15 — a `skipped_steps["3.9"]` entry is ignored by the
  visualization gate and never satisfies it." Keep CommonMark valid (req 3.6) and the existing
  Constraints bullets intact.

## Testing Strategy

### Validation Approach

Two phases: first surface counterexamples that demonstrate the bug on the UNFIXED code (exploration
/ fix-checking authored to fail before the fix), then verify the fix works and preserves existing
behavior (preservation authored to pass before and after). New property-based test files live in
`senzing-bootcamp/tests/` and follow `python-conventions.md` (pytest + Hypothesis, stdlib +
Hypothesis only, class-based, `st_`-prefixed strategies, `@settings(max_examples=20)`,
`from __future__ import annotations`, type hints using `X | None` and lowercase generics).

A shared domain model mirrors `isBugCondition` from `bugfix.md`:

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

`validate_mandatory_gates.py` is imported via the `sys.path` manipulation pattern from
`python-conventions.md`.

### Exploratory Bug Condition Checking

**Goal**: Surface counterexamples that demonstrate the bug BEFORE implementing the fix; confirm or
refute the root-cause analysis (CONDITION B escape hatch). If refuted, re-hypothesize.

**Test Plan**: Parse the three hook files (and exercise `validate_mandatory_gates._check_gate`) and
assert that CONDITION B / `skipped_steps["3.9"]` no longer satisfies the visualization gate. Run on
UNFIXED code to observe failures.

**Test Cases** (will fail on unfixed code):

1. **Gate hook has no CONDITION B**: `gate-module3-visualization.kiro.hook` prompt does NOT contain
   "CONDITION B" nor a `skipped_steps["3.9"]` satisfaction branch.
2. **Enforce-mandatory-gate has no CONDITION B**: same assertion for
   `enforce-mandatory-gate.kiro.hook`.
3. **Enforce-gate-on-stop has no CONDITION B**: same assertion for `enforce-gate-on-stop.kiro.hook`.
4. **`_check_gate` reports a violation under skip**: for a progress state with `current_step > 9`,
   no `web_service`/`web_page` checkpoints, and `skipped_steps["3.9"]` present, `_check_gate`
   returns a non-`None` `Violation`.
5. **Edge case — documentation wording**: hook `description` fields, `install_hooks.py` summary,
   and `module-dependencies.yaml` gate `3->4` no longer present the gate as skippable.

**Expected Counterexamples**: On unfixed code, the hooks still contain CONDITION B and `_check_gate`
returns `None` for the skip+no-checkpoint state — confirming CONDITION B is the escape hatch.

### Fix Checking

**Goal**: Verify that for all inputs where the bug condition holds, the fixed logic blocks / reports
a violation.

**Pseudocode:**

```
FOR ALL X WHERE isBugCondition(X) DO
  result := F'(X)
  ASSERT result = BLOCKED                 // hooks emit the ⛔ block/violation output
  ASSERT result.violation_reported = true // validate_mandatory_gates returns a Violation
END FOR
```

Implemented in `test_module3_visualization_no_skip_exploration.py` (Property 1) — authored to FAIL
on the unfixed code (CONDITION B still present) and PASS after the fix.

### Preservation Checking

**Goal**: Verify that for all inputs where the bug condition does NOT hold, the fixed logic behaves
identically to the original.

**Pseudocode:**

```
FOR ALL X WHERE NOT isBugCondition(X) DO
  ASSERT F(X) = F'(X)
END FOR
```

**Testing Approach**: Property-based testing is recommended for preservation because it generates
many cases across the input domain, catches edge cases manual tests miss, and gives strong
guarantees that behavior is unchanged for all non-buggy inputs.

**Test Plan**: Observe behavior on UNFIXED code first (CONDITION A satisfying the gate, other gates
honoring skips, non-mandatory skips, non-Module-3 no-ops, hook schema/triggers), then encode those
as properties in `test_module3_visualization_no_skip_preservation.py` (Property 2) — authored to
PASS on unfixed code.

**Test Cases**:

1. **CONDITION A preservation (3.1)**: when both Step 9 checkpoints are `"passed"`, the gate is
   satisfied (no block, no `_check_gate` violation) — true on unfixed and fixed code.
2. **Other-gate skip preservation (3.3)**: `_check_gate` still returns `None` when a non-`"3.9"`
   mandatory gate has a matching `skipped_steps` entry (use a synthetic `MandatoryGate` with a
   different module/step).
3. **Non-mandatory skip preservation (3.2)**: skip-step protocol structure for non-⛔ steps is
   intact and honored.
4. **Non-Module-3 / unrelated no-op (3.4)**: the three hooks' prompts still short-circuit to "no
   output" for writes that don't mark Module 3 complete or advance `current_step` past 9.
5. **Hook schema/name/trigger preservation (3.5)**: each hook keeps `name`, `version`, `when`,
   `then`; `gate-module3-visualization` and `enforce-mandatory-gate` stay `preToolUse` +
   `toolTypes:["write"]`; `enforce-gate-on-stop` stays `agentStop`; `name` fields keep the "to ..."
   form.
6. **Structural / snapshot checks on unrelated regions**: assert that unrelated hooks, scripts,
   steering, and config bytes are unchanged (req 3.7).

### Unit Tests

- **Invert** `tests/test_mandatory_gate_preservation.py::test_gate_hook_checks_both_conditions` — it
  currently asserts both "CONDITION A" and "CONDITION B" are present; update to assert "CONDITION B"
  is ABSENT (and CONDITION A still present). (Path:
  `senzing-bootcamp/tests/test_mandatory_gate_preservation.py`.)
- **Invert** `tests/test_mandatory_gate_preservation.py::test_existing_gate_hook_accepts_skipped_steps_entry`
  — currently asserts the gate hook references `skipped_steps`/`"3.9"`; update to assert the
  visualization gate hook no longer accepts a `"3.9"` skip (no CONDITION B branch).
- **Update** `tests/test_module3_default_on_unit.py::test_gate_3_4_explicitly_skipped` — currently
  asserts `"explicitly skipped"` is in gate `3->4` text; update to the new non-skippable wording.
- **Update** `tests/test_system_verification_unit.py` (gate `3->4` requires text) — same change from
  `"explicitly skipped"` to the new wording.
- **Review/align** `tests/test_mandatory_gate_exploration.py` — it models the bug condition and
  references `skipped_steps["3.9"]`; reconcile so its assertions remain consistent with the fixed
  CONDITION-A-only gate (these existing tests verify hook/script existence and the ⛔ marker, which
  remain valid).
- All of the above are **updated/inverted, not deleted.**

### Property-Based Tests

- `test_module3_visualization_no_skip_exploration.py` (Property 1 / Fix Checking): generates
  `GateState` inputs satisfying `is_bug_condition`, parses the three hook files, and exercises
  `_check_gate`; asserts CONDITION B / `skipped_steps["3.9"]` no longer satisfies the gate.
  Authored to FAIL on unfixed code.
- `test_module3_visualization_no_skip_preservation.py` (Property 2 / Preservation): generates
  non-buggy `GateState` inputs and progress states; asserts CONDITION A still satisfies the gate,
  other gates still honor skips, non-mandatory skips work, non-Module-3 writes are no-ops, hook
  schema/triggers/names are unchanged, and unrelated regions are byte-stable. Authored to PASS on
  unfixed code.

### Integration Tests

- Run `python senzing-bootcamp/scripts/sync_hook_registry.py --verify` — confirms the three hook
  files stay byte-consistent with the `hook-registry-modules.md` mirror (req 3.6).
- Run `python senzing-bootcamp/scripts/validate_commonmark.py` — confirms steering/markdown
  (including the updated `skip-step-protocol.md` and mirror) stays valid CommonMark (req 3.6).
- Run `python senzing-bootcamp/scripts/measure_steering.py --check` — confirms steering token
  budgets stay within limits after the registry/protocol edits (req 3.6).
- Run `python senzing-bootcamp/scripts/validate_mandatory_gates.py` against representative progress
  fixtures: (a) skip + no checkpoints past the gate → exits non-zero with a violation; (b)
  checkpoints present → exits 0; (c) other-gate skip → still honored.
- Run the existing mandatory-gate test suites
  (`senzing-bootcamp/tests/test_mandatory_gate_preservation.py`,
  `test_mandatory_gate_exploration.py`) plus the two updated unit suites to confirm no regressions.

## Security & Convention Compliance

- **Hook JSON schema valid (req 3.5)**: all three edited hooks retain `name`, `version`, `when`,
  `then`; CONDITION B removal only deletes prompt text, not structural fields. The
  `preToolUse`/`toolTypes:["write"]` hooks are modified (not removed) — this is the explicit
  approved scope of the fix.
- **No hardcoded MCP server URLs**: no surface in this fix introduces an MCP server URL or any
  external URL; the power's `mcp.json` remains the single source of truth.
- **No prompt-injection / no security-bypass instructions**: edits remove an escape hatch and
  tighten enforcement; no user-input interpolation is added to any hook prompt.
- **stdlib-only Python (tech.md / python-conventions.md)**: the `validate_mandatory_gates.py` change
  uses only stdlib; new test files use only pytest + Hypothesis + stdlib.
- **No PII / no real data**: test fixtures use synthetic progress states only.
- **Requirement alignment**: Property 1 validates Expected Behavior clauses 2.1–2.5; Property 2
  validates Preservation clauses 3.1–3.7 — matching the EARS requirements in `bugfix.md`.
