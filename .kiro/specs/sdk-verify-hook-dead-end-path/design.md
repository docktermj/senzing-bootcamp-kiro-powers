# SDK Verify Hook Dead-End Path Bugfix Design

## Overview

The Module 2 (SDK Setup) verification hook `senzing-bootcamp/hooks/verify-sdk-setup.kiro.hook` runs after edits to configuration or database files. When verification fails, the hook's `then.prompt` failure-guidance text instructs the bootcamper to run `python3 senzing-bootcamp/scripts/preflight.py`. That path does not resolve from the bootcamper's project workspace: `preflight.py` lives inside the power repository, but the hook prompt executes in the bootcamper's installed project, where the power is installed elsewhere. Following the suggestion produces a "No such file or directory" error — a remediation dead end that erodes trust at the worst moment.

The verification logic itself is correct; it properly detects a missing `database/G2C.db` or `config/engine_config.json`. The defect is isolated to the recommended remediation command path inside the failure-guidance text. The script the bootcamper actually has in their workspace is the generated `src/scripts/verify_sdk.py`, created during Module 2 after the engine config is produced.

The fix is a minimal, single-string edit to the hook's `then.prompt`: replace the unresolvable `python3 senzing-bootcamp/scripts/preflight.py` recommendation with `python3 src/scripts/verify_sdk.py`, a path that resolves within the bootcamper's workspace. All other hook behavior — trigger patterns, Module 2 gating, the verification checks performed, and correct detection/reporting of genuine failures — must remain byte-for-byte identical.

## Glossary

- **Bug_Condition (C)**: The condition that triggers the bug — the failure-guidance text recommends a remediation command whose script path does not resolve from the bootcamper's project workspace.
- **Property (P)**: The desired behavior — the failure-guidance text recommends a remediation command whose script path exists and resolves within the bootcamper's workspace.
- **Preservation**: All hook behavior other than the recommended remediation path — trigger patterns, Module 2 gating, verification checks, and genuine-failure detection/reporting — that must remain unchanged by the fix.
- **`verify-sdk-setup.kiro.hook`**: The hook file at `senzing-bootcamp/hooks/verify-sdk-setup.kiro.hook` that re-verifies SDK setup after config/database edits during Module 2.
- **`then.prompt`**: The askAgent prompt string in the hook that contains the verification instructions and the failure-guidance remediation recommendation.
- **`recommendedScriptPath`**: The script path embedded in the remediation command suggested by the failure-guidance text.
- **Bootcamper workspace**: The user's installed project where the hook prompt executes; the power repository is installed elsewhere and is not addressable via relative paths like `senzing-bootcamp/...`.
- **`src/scripts/verify_sdk.py`**: The generated verification script that exists in the bootcamper's workspace after the engine config is created in Module 2; the correct remediation target.

## Bug Details

### Bug Condition

The bug manifests when the verification hook reports a failure and its failure-guidance text recommends a remediation command. The recommended command (`python3 senzing-bootcamp/scripts/preflight.py`) references a script path that does not resolve from the bootcamper's project workspace, because the power — and its `scripts/preflight.py` — is installed outside the bootcamper's project.

**Formal Specification:**
```
FUNCTION isBugCondition(X)
  INPUT: X of type FailureGuidanceText
  OUTPUT: boolean

  RETURN X.recommendsCommand
         AND NOT pathResolvesInBootcamperWorkspace(X.recommendedScriptPath)
END FUNCTION
```

Concrete instance: the current prompt recommends `python3 senzing-bootcamp/scripts/preflight.py`. The path `senzing-bootcamp/scripts/preflight.py` does not resolve in the bootcamper's workspace, so `isBugCondition` returns true.

### Examples

- **Dead end on missing database**: A bootcamper in Module 2 edits `config/senzing_config.yaml`, verification fails (missing `database/G2C.db`), the hook says "suggest running: python3 senzing-bootcamp/scripts/preflight.py". Expected: a runnable remediation command. Actual: `python3: can't open file 'senzing-bootcamp/scripts/preflight.py': [Errno 2] No such file or directory`.
- **Missing engine config**: A bootcamper edits `config/bootcamp_preferences.yaml`, verification fails because `config/engine_config.json` is absent, the hook recommends the unresolvable preflight path. Expected: a path that exists. Actual: dead-end "No such file or directory".
- **Database edit**: A bootcamper edits `database/G2C.db`, verification fails, the recommended preflight command cannot be executed from the workspace. Expected: a runnable script. Actual: dead end.
- **Edge case (expected behavior, must be preserved)**: A bootcamper edits a config file while NOT in Module 2 — the hook produces no output, so no remediation text is emitted and the bug condition does not apply.

## Expected Behavior

### Preservation Requirements

**Unchanged Behaviors:**
- The hook SHALL CONTINUE TO run verification when a config or database file is edited and the bootcamper is in Module 2, checking that `database/G2C.db` exists and is accessible and that the Senzing engine can initialize with the current config (Requirement 3.1).
- The hook SHALL CONTINUE TO detect and present genuine failures correctly, e.g., a missing `database/G2C.db` or `config/engine_config.json` (Requirement 3.2).
- The hook SHALL CONTINUE TO produce no output when the bootcamper is NOT in Module 2 (Requirement 3.3).
- The hook SHALL CONTINUE TO trigger on edits to `config/senzing_config.*`, `config/bootcamp_preferences.yaml`, and `database/*.*` (Requirement 3.4).
- The hook JSON schema integrity SHALL be preserved: required fields `name`, `version`, `description`, `when` (with `when.type` = `fileEdited`), and `then` (with `then.type` = `askAgent` and `then.prompt`) remain valid and well-formed.

**Scope:**
All inputs that do NOT trigger the bug condition (i.e., where the failure-guidance text is not being emitted with an unresolvable remediation path) should be completely unaffected by this fix. This includes:
- The trigger/pattern-matching behavior of the hook (when it fires).
- The Module 2 gating logic (run vs. produce no output).
- The verification checks performed and the detection/reporting of genuine failures.
- The hook's `name`, `version`, `description`, and `when` block.

**Note:** The actual expected correct behavior for buggy inputs is defined in the Correctness Properties section (Property 1). This section focuses on what must NOT change.

## Hypothesized Root Cause

Based on the bug description, the cause is well-isolated:

1. **Hardcoded power-relative path in failure guidance**: The `then.prompt` ends with "suggest running: python3 senzing-bootcamp/scripts/preflight.py". The `senzing-bootcamp/...` prefix is a path relative to the power repository, not the bootcamper's installed project, so it cannot resolve when the prompt executes in the bootcamper's workspace.

2. **Authoring-context vs. execution-context mismatch**: The prompt was written from the perspective of the power repo (where `scripts/preflight.py` exists), but it executes in the bootcamper's project (where it does not). The remediation target was never re-pointed to a workspace-resident script.

3. **Recommending a script that is not part of the shipped user artifacts**: `preflight.py` is a power-internal script, not one of the generated artifacts a bootcamper produces. The verification artifact the bootcamper actually owns is `src/scripts/verify_sdk.py`, generated after the engine config is created in Module 2.

The verification detection logic is not implicated — only the literal remediation command string in `then.prompt`.

## Correctness Properties

Property 1: Bug Condition - Remediation Path Resolves In Workspace

_For any_ failure-guidance text where the bug condition holds (isBugCondition returns true — the text recommends a remediation command whose path does not resolve in the bootcamper's workspace), the fixed hook's `then.prompt` SHALL recommend a remediation command whose script path exists and resolves within the bootcamper's project workspace (`src/scripts/verify_sdk.py`), and SHALL NOT recommend the unresolvable `senzing-bootcamp/scripts/preflight.py` path, so that following the suggestion does not produce a "No such file or directory" dead end.

**Validates: Requirements 2.1, 2.2**

Property 2: Preservation - Verification, Gating, and Trigger Behavior Unchanged

_For any_ input where the bug condition does NOT hold (isBugCondition returns false), the fixed hook SHALL produce the same result as the original hook, preserving: the verification checks performed in Module 2 (`database/G2C.db` accessible, engine initializes with current config), correct detection/reporting of genuine failures, the no-output behavior when not in Module 2, the trigger patterns `config/senzing_config.*`, `config/bootcamp_preferences.yaml`, and `database/*.*`, and the hook JSON schema (`name`, `version`, `description`, `when.type` = `fileEdited`, `then.type` = `askAgent`, `then.prompt`).

**Validates: Requirements 3.1, 3.2, 3.3, 3.4**

## Fix Implementation

### Changes Required

Assuming our root cause analysis is correct:

**File**: `senzing-bootcamp/hooks/verify-sdk-setup.kiro.hook`

**Function/Field**: `then.prompt`

**Specific Changes**:
1. **Repoint the remediation path**: Replace the trailing phrase `suggest running: python3 senzing-bootcamp/scripts/preflight.py` with `suggest running: python3 src/scripts/verify_sdk.py`.
   - `src/scripts/verify_sdk.py` is the generated verification script that exists in the bootcamper's workspace after the engine config is created in Module 2.
   - The path is workspace-relative and resolves where the prompt executes.

2. **Preserve all other prompt text verbatim**: The verification instructions (Module 2 gating, the `database/G2C.db` accessibility check, the engine-initialization check, the "produce no output" branch, and "If verification fails, present the error and") remain unchanged. Only the final remediation command path is altered.

3. **Leave the `when` block untouched**: `when.type` stays `fileEdited`; `when.patterns` stays `["config/senzing_config.*", "config/bootcamp_preferences.yaml", "database/*.*"]`.

4. **Leave schema fields untouched**: `name`, `version`, `description`, and `then.type` (`askAgent`) are unchanged; the file remains valid JSON conforming to the hook schema (`name`, `version`, `when`, `then` present).

5. **No new files, no MCP URL changes, no new dependencies**: The fix is a single-string edit. No hardcoded MCP URLs are introduced, and the `mcp.json` single-source-of-truth rule is respected.

**Resulting `then.prompt` (target):**
```
A configuration or database file was modified. If the bootcamper is in Module 2 (SDK Setup), run a quick verification: check that database/G2C.db exists and is accessible, and that the Senzing engine can initialize with the current config. If not in Module 2, produce no output. If verification fails, present the error and suggest running: python3 src/scripts/verify_sdk.py
```

## Testing Strategy

### Validation Approach

The testing strategy follows a two-phase approach: first, surface a counterexample that demonstrates the bug on the unfixed hook file, then verify the fix works correctly and preserves existing behavior. Tests that validate the real hook file are placed in the repo-root `tests/` directory (per the workspace structure rule: hook tests validating real hook files go in repo-root `tests/`, not `senzing-bootcamp/tests/`). They load the hook via `hook_test_helpers.load_hook` and assert against `then.prompt` and the hook schema. Tests are class-based and use Hypothesis with `@settings(max_examples=20)`.

### Exploratory Bug Condition Checking

**Goal**: Surface a counterexample that demonstrates the bug BEFORE implementing the fix. Confirm or refute the root cause (the `then.prompt` recommends an unresolvable `senzing-bootcamp/scripts/preflight.py` path). If we refute, we will need to re-hypothesize.

**Test Plan**: Write a test that loads `verify-sdk-setup.kiro.hook` and inspects `then.prompt`. Assert that the recommended remediation path resolves in a bootcamper workspace (i.e., does not contain the power-relative `senzing-bootcamp/scripts/preflight.py`). Run on the UNFIXED hook to observe the failure and confirm the dead-end path.

**Test Cases**:
1. **No power-relative remediation path**: Assert `then.prompt` does not contain `senzing-bootcamp/scripts/preflight.py` (will fail on unfixed code).
2. **Workspace-resolvable remediation path present**: Assert `then.prompt` contains `src/scripts/verify_sdk.py` (will fail on unfixed code).
3. **Remediation command is still recommended**: Assert `then.prompt` still contains a `python3 ...` remediation suggestion (passes before and after; ensures we do not remove guidance entirely).
4. **Edge case — no `senzing-bootcamp/`-prefixed script path anywhere in prompt**: Assert no `senzing-bootcamp/scripts/` substring remains (may fail on unfixed code).

**Expected Counterexamples**:
- The unfixed `then.prompt` contains `senzing-bootcamp/scripts/preflight.py`, demonstrating the unresolvable path.
- Possible causes: hardcoded power-relative path, authoring-vs-execution context mismatch, recommending a power-internal script not present in the bootcamper workspace.

### Fix Checking

**Goal**: Verify that for all inputs where the bug condition holds, the fixed hook produces the expected behavior (a workspace-resolvable remediation path).

**Pseudocode:**
```
FOR ALL X WHERE isBugCondition(X) DO
  result := emitFailureGuidance_fixed(X)
  ASSERT result.recommendsCommand
     AND pathResolvesInBootcamperWorkspace(result.recommendedScriptPath)
END FOR
```

Concrete expectation: after the fix, `then.prompt` recommends `python3 src/scripts/verify_sdk.py`, which exists in the bootcamper workspace, so following the suggestion does not produce a "No such file or directory" error.

### Preservation Checking

**Goal**: Verify that for all inputs where the bug condition does NOT hold, the fixed hook produces the same result as the original hook.

**Pseudocode:**
```
FOR ALL X WHERE NOT isBugCondition(X) DO
  ASSERT F(X) = F'(X)
END FOR
```

Where **F** is the original hook behavior (before the fix) and **F'** is the fixed hook behavior (after updating the recommended remediation path).

**Testing Approach**: Property-based testing is recommended for preservation checking because:
- It generates many test cases automatically across the input domain.
- It catches edge cases that manual unit tests might miss.
- It provides strong guarantees that behavior is unchanged for all non-buggy inputs.

**Test Plan**: Capture the original hook's invariant fields (schema fields, `when` block, and the non-remediation portion of `then.prompt`) and assert they are byte-for-byte identical after the fix. The only permitted delta is the single remediation path substring.

**Test Cases**:
1. **Trigger patterns preserved**: Assert `when.patterns` equals exactly `["config/senzing_config.*", "config/bootcamp_preferences.yaml", "database/*.*"]`.
2. **Module 2 gating preserved**: Assert `then.prompt` still contains the "If the bootcamper is in Module 2 (SDK Setup)" gating and the "If not in Module 2, produce no output" branch.
3. **Verification checks preserved**: Assert `then.prompt` still contains "database/G2C.db exists and is accessible" and "the Senzing engine can initialize with the current config".
4. **Genuine-failure reporting preserved**: Assert `then.prompt` still contains "If verification fails, present the error".
5. **Schema integrity preserved**: Assert the hook has required fields `name`, `version`, `description`, `when`, `then`; `when.type` == `fileEdited`; `then.type` == `askAgent`; `then.prompt` is a non-empty string; the file parses as valid JSON.
6. **Prompt diff is exactly the remediation path**: Assert the only difference between the original and fixed `then.prompt` is the substring `senzing-bootcamp/scripts/preflight.py` → `src/scripts/verify_sdk.py`.

### Unit Tests

- Assert the unfixed `then.prompt` contains `senzing-bootcamp/scripts/preflight.py` (baseline/counterexample) and the fixed `then.prompt` does not.
- Assert the fixed `then.prompt` contains `src/scripts/verify_sdk.py`.
- Assert the hook still parses as valid JSON and retains required schema fields after the edit.
- Assert `when.type` is `fileEdited` and `when.patterns` is unchanged.

### Property-Based Tests

- Over a generated set of trigger patterns and module contexts, assert that the fixed hook's non-remediation behavior fields (schema fields, `when` block, gating/verification phrases) are invariant relative to the original.
- Over generated path-resolution checks, assert the recommended remediation path never matches the power-relative `senzing-bootcamp/scripts/...` form and always matches a workspace-relative form (`src/scripts/verify_sdk.py`).
- Generate "not in Module 2" and "in Module 2" contexts and assert the gating instructions remain present and unchanged.

### Integration Tests

- Validate the hook against the repo's hook-schema conformance suite (e.g., `test_hook_schema_conformance.py`) to confirm the edited file still passes structural validation.
- Validate the hook against the structural/standards suites (`test_hook_structural_validation.py`, `test_hook_prompt_standards.py`) to confirm no regression in prompt standards.
- Confirm the hook registry sync (`sync_hook_registry.py --verify`) still passes, since `name`, `version`, and `when` are unchanged.
