# Bugfix Requirements Document

## Introduction

Governing Rule 15 of the Senzing Bootcamp Power states: "In module 3, ALWAYS create the
visualization." The Module 3 visualization step (Step 9 — the ⛔ mandatory gate "Web Service +
Visualization") is intended to be unconditional. However, the current gate enforcement contains a
documented escape hatch: a `skipped_steps["3.9"]` entry in `config/bootcamp_progress.json` is
treated as satisfying the gate ("CONDITION B"). This lets an agent bypass the visualization gate
even though the power's own `steering/skip-step-protocol.md` declares that mandatory gates (⛔)
cannot be skipped.

This bug spans seven enforcement and documentation surfaces that must stay mutually consistent
(four of them — the three hook files plus the `steering/hook-registry-modules.md` mirror — are held
byte-consistent by CI via `sync_hook_registry.py --verify`):

1. `senzing-bootcamp/hooks/gate-module3-visualization.kiro.hook`
2. `senzing-bootcamp/hooks/enforce-mandatory-gate.kiro.hook`
3. `senzing-bootcamp/hooks/enforce-gate-on-stop.kiro.hook`
4. `senzing-bootcamp/steering/hook-registry-modules.md` (mirror of the three hooks above)
5. `senzing-bootcamp/scripts/validate_mandatory_gates.py` (`_check_gate`, skip-key handling)
6. `senzing-bootcamp/scripts/install_hooks.py` (gate summary wording: "or skipped")
7. `senzing-bootcamp/config/module-dependencies.yaml` (gate `3->4` "or explicitly skipped" text)
8. `senzing-bootcamp/steering/skip-step-protocol.md` (consistency note for Step 9)

The fix removes the "CONDITION B" (explicit-skip) branch from the Module 3 visualization gate so
that **only actual Step 9 checkpoints (CONDITION A) can satisfy the gate**, while preserving every
other mandatory gate and the ordinary skip-step protocol for non-mandatory steps.

The impact of the bug: a bootcamper (or an agent acting on their behalf) can mark Module 3 complete,
advance `current_step` past 9, or end a turn past Step 9 — all without ever building or presenting
the visualization — simply by writing a `skipped_steps["3.9"]` entry. This silently violates
Governing Rule 15.

## Bug Analysis

### Current Behavior (Defect)

When a `skipped_steps["3.9"]` entry is present in `config/bootcamp_progress.json` and the Step 9
checkpoints (`module_3_verification.checks.web_service.status` and
`module_3_verification.checks.web_page.status`) are NOT both `"passed"`, the system treats the
Module 3 visualization gate as satisfied.

1.1 WHEN a write marks Module 3 complete (adds 3 to `modules_completed` or sets
`module_3_verification.status` to `"passed"`) AND the Step 9 checkpoints are not both `"passed"` AND
`skipped_steps` contains key `"3.9"` THEN the `gate-module3-visualization` hook allows the write
(CONDITION B is treated as satisfying the gate).

1.2 WHEN a write advances `current_step` to 10 or higher AND the Step 9 checkpoints are not both
`"passed"` AND `skipped_steps` contains key `"3.9"` THEN the `enforce-mandatory-gate` hook allows
the write (CONDITION B is treated as satisfying the gate).

1.3 WHEN the agent stops with `current_module` equal to 3 and `current_step` greater than or equal
to 9 AND the Step 9 checkpoints are not both `"passed"` AND `skipped_steps` contains key `"3.9"`
THEN the `enforce-gate-on-stop` hook produces no violation output (CONDITION B is treated as
satisfying the gate).

1.4 WHEN `validate_mandatory_gates.py` checks the Module 3 Step 9 visualization gate AND the Step 9
checkpoints are missing AND `skipped_steps` contains key `"3.9"` THEN `_check_gate` returns `None`
(no violation), treating the bootcamper skip as satisfying the mandatory gate.

1.5 WHEN documentation describes the Module 3 visualization gate THEN the system states that the gate
may be satisfied by an explicit skip — the `gate-module3-visualization` hook `description` says "or
the step was explicitly skipped via the skip-step protocol"; the `enforce-mandatory-gate` hook
`description` says "and no skipped_steps entry exists"; `install_hooks.py` summarizes the gate as
"Blocks Module 3 completion until visualization step is done or skipped"; and
`module-dependencies.yaml` gate `3->4` requires "System verification passed or explicitly skipped by
bootcamper".

### Expected Behavior (Correct)

The Module 3 visualization gate (Step 9) can be satisfied ONLY by the real Step 9 checkpoints. Any
`skipped_steps["3.9"]` entry is ignored for this specific gate; the visualization can never be opted
out of.

2.1 WHEN a write marks Module 3 complete (adds 3 to `modules_completed` or sets
`module_3_verification.status` to `"passed"`) AND the Step 9 checkpoints are not both `"passed"` THEN
the `gate-module3-visualization` hook SHALL block the write regardless of whether `skipped_steps`
contains key `"3.9"` (only CONDITION A — checkpoints present — satisfies the gate).

2.2 WHEN a write advances `current_step` to 10 or higher AND the Step 9 checkpoints are not both
`"passed"` THEN the `enforce-mandatory-gate` hook SHALL block the write regardless of whether
`skipped_steps` contains key `"3.9"` (only CONDITION A satisfies the gate).

2.3 WHEN the agent stops with `current_module` equal to 3 and `current_step` greater than or equal
to 9 AND the Step 9 checkpoints are not both `"passed"` THEN the `enforce-gate-on-stop` hook SHALL
emit the mandatory-gate violation output regardless of whether `skipped_steps` contains key `"3.9"`
(only CONDITION A satisfies the gate).

2.4 WHEN `validate_mandatory_gates.py` checks the Module 3 Step 9 visualization gate AND the Step 9
checkpoints are missing THEN `_check_gate` SHALL report a violation regardless of whether
`skipped_steps` contains key `"3.9"`, while continuing to honor `skipped_steps` for all other
mandatory gates.

2.5 WHEN documentation describes the Module 3 visualization gate THEN the system SHALL state that the
gate cannot be skipped — the three hook `description` fields, the `hook-registry-modules.md` mirror,
the `install_hooks.py` summary line, the `module-dependencies.yaml` gate `3->4` text, and
`skip-step-protocol.md` SHALL all reflect that the Step 9 visualization is unconditional and cannot
be opted out of.

### Unchanged Behavior (Regression Prevention)

3.1 WHEN the Step 9 checkpoints `module_3_verification.checks.web_service.status` and
`module_3_verification.checks.web_page.status` are both `"passed"` (CONDITION A) THEN the system SHALL
CONTINUE TO treat the Module 3 visualization gate as satisfied and allow completion/advancement
without any violation output.

3.2 WHEN a bootcamper skips a NON-mandatory step via the skip-step protocol (any `skipped_steps`
entry other than the Module 3 Step 9 visualization gate) THEN the system SHALL CONTINUE TO honor the
skip and allow advancement.

3.3 WHEN `validate_mandatory_gates.py` checks any mandatory gate OTHER THAN the Module 3 Step 9
visualization gate AND a matching `skipped_steps` entry exists THEN `_check_gate` SHALL CONTINUE TO
treat that skip as satisfying the gate (no violation).

3.4 WHEN a write does not target `config/bootcamp_progress.json`, or does not mark Module 3 complete,
or does not advance `current_step` past 9 THEN the three hooks SHALL CONTINUE TO produce no output
(non-Module-3 / unrelated writes remain a no-op).

3.5 WHEN the hooks are loaded by the framework THEN each hook SHALL CONTINUE TO have unchanged
trigger types/events (`preToolUse` with `toolTypes: ["write"]` for `gate-module3-visualization` and
`enforce-mandatory-gate`; `agentStop` for `enforce-gate-on-stop`), unchanged `name` fields (the "to
..." form), and a valid hook JSON schema (`name`, `version`, `when`, `then`).

3.6 WHEN CI runs `sync_hook_registry.py --verify`, `validate_commonmark.py`, and
`measure_steering.py --check` THEN all three SHALL CONTINUE TO pass (the hook files and the
`hook-registry-modules.md` mirror remain byte-consistent, CommonMark stays valid, steering token
budgets stay within limits).

3.7 WHEN any hook, script, steering file, or config unrelated to the Module 3 visualization gate is
considered THEN it SHALL CONTINUE TO be untouched by this fix.

## Bug Condition Derivation

### Definitions

- **F**: The original (unfixed) gate-enforcement logic — hooks, `validate_mandatory_gates.py`, and
  the associated documentation, where a `skipped_steps["3.9"]` entry (CONDITION B) satisfies the
  Module 3 visualization gate.
- **F'**: The fixed logic where only the real Step 9 checkpoints (CONDITION A) satisfy the Module 3
  visualization gate, and `skipped_steps["3.9"]` is ignored for this gate.
- **X**: A `bootcamp_progress.json` state (plus the triggering operation: a completion write, a
  `current_step` advance, an `agentStop`, or a `validate_mandatory_gates` evaluation).

### Bug Condition Function

```pascal
FUNCTION isBugCondition(X)
  INPUT: X = progress state + triggering operation for the Module 3 visualization gate
  OUTPUT: boolean

  // Step 9 checkpoints are NOT both passed
  checkpointsPassed ← (X.module_3_verification.checks.web_service.status = "passed")
                      AND (X.module_3_verification.checks.web_page.status = "passed")

  // The operation crosses / completes the Module 3 Step 9 gate
  gateCrossed ← X.operation marks Module 3 complete
                OR X.operation advances current_step past 9
                OR (X.current_module = 3 AND X.current_step >= 9 at agentStop)
                OR (validate evaluates the Module 3 Step 9 gate as crossed)

  // A skip entry exists for the visualization gate
  skipPresent ← "3.9" IN keys(X.skipped_steps)

  // Bug is triggered only when the gate is crossed without checkpoints
  // but a skip entry would (incorrectly) satisfy it
  RETURN gateCrossed AND (NOT checkpointsPassed) AND skipPresent
END FUNCTION
```

### Property: Fix Checking

For every input that triggers the bug, the fixed logic must block / report a violation — the skip
entry must never satisfy the visualization gate.

```pascal
// Property: Fix Checking — Visualization gate cannot be satisfied by a skip
FOR ALL X WHERE isBugCondition(X) DO
  result ← F'(X)
  ASSERT result = BLOCKED        // hooks emit the ⛔ block/violation output
  ASSERT result.violation_reported = true   // validate_mandatory_gates returns a Violation
END FOR
```

In F (original), `isBugCondition(X)` inputs are ALLOWED (CONDITION B satisfies the gate). In F'
(fixed), the same inputs are BLOCKED.

### Property: Preservation Checking

For every input that does NOT trigger the bug, the fixed logic must behave identically to the
original.

```pascal
// Property: Preservation Checking — all non-buggy inputs unchanged
FOR ALL X WHERE NOT isBugCondition(X) DO
  ASSERT F(X) = F'(X)
END FOR
```

This covers, among others:

- **CONDITION A satisfied** (`checkpointsPassed = true`): gate allowed in both F and F' (req 3.1).
- **Other mandatory gates** with a matching `skipped_steps` entry: skip still satisfies them in both
  F and F' (req 3.3).
- **Non-mandatory step skips**: honored in both F and F' (req 3.2).
- **Unrelated / non-Module-3 writes**: no-op in both F and F' (req 3.4).
