# Write-Gate Noise Cleanup Bugfix Design

## Overview

This bugfix targets two residual visible-noise defects related to the `write-policy-gate` hook. Defect 1 removes a stale onboarding section ("0a. Why You May See 'Rejected'/'Accepted' Messages") that describes an intercept-then-retry write cycle that no longer occurs. Defect 2 reinforces agent-side steering to explicitly prohibit narration when re-invoking after an internal-file pass-through, eliminating occasional leaks like "Internal progress file — re-invoking silently." The fix is purely subtractive (remove stale content) and additive (add a steering rule) — no hook security behavior changes.

## Glossary

- **Bug_Condition (C)**: The condition that triggers visible noise — either the stale onboarding note is presented, or the agent narrates during an internal-file pass-through re-invoke
- **Property (P)**: The desired behavior — no stale/unwanted write-gate-related output reaches the bootcamper
- **Preservation**: Legitimate write-gate rejections still produce corrective output; all other onboarding content unchanged; hook security behavior unchanged
- **onboarding-flow.md**: The steering file at `senzing-bootcamp/steering/onboarding-flow.md` that defines the onboarding sequence
- **agent-behavior-rules.md**: The steering file at `senzing-bootcamp/steering/agent-behavior-rules.md` containing agent behavior rules
- **write-policy-gate.json**: The PreToolUse hook at `senzing-bootcamp/hooks/write-policy-gate.json` that enforces write policies
- **INTERNAL-FILE PASS-THROUGH**: The first-evaluated rule in write-policy-gate that silently passes writes to routine power-managed files (progress, preferences, etc.)

## Bug Details

### Bug Condition

The bug manifests in two independent scenarios where the bootcamper sees write-gate-related output that should not be visible:

1. During onboarding, the agent presents section "0a" which describes a "Rejected" → "Accepted" intercept-then-retry cycle that no longer occurs in practice.
2. When the write-policy-gate passes through a write to a routine internal file, the agent occasionally emits narration (e.g., "Internal progress file — re-invoking silently.") instead of producing zero tokens.

**Formal Specification:**
```
FUNCTION isBugCondition(input)
  INPUT: input of type WriteGateOutputEvent
         (kind, note_present, is_passthrough, target_path,
          not_guards_hold, emitted_tokens)
  OUTPUT: boolean

  // Defect 1: stale onboarding "Rejected/Accepted" reassurance note is shown
  staleOnboardingNote :=
        input.kind = "onboarding_preamble"
    AND input.note_present = TRUE

  // Defect 2: agent narrates instead of staying silent on internal-file pass-through
  narratedSilentReinvoke :=
        input.kind = "write_gate_passthrough"
    AND input.is_passthrough = TRUE
    AND input.target_path IS a routine power-managed internal file
    AND input.not_guards_hold = TRUE
    AND input.emitted_tokens != EMPTY

  RETURN staleOnboardingNote OR narratedSilentReinvoke
END FUNCTION
```

### Examples

- **Defect 1 — stale note shown**: Agent presents onboarding; bootcamper sees "During setup and throughout the bootcamp, you may occasionally see a pair of messages like 'Rejected creation of ...' followed immediately by 'Accepted edits to ...'." This describes behavior that no longer occurs.
- **Defect 2 — narration on pass-through**: Agent writes to `config/bootcamp_progress.json`; write-policy-gate intercepts; agent emits "Internal progress file — re-invoking silently." before re-issuing the write. Expected: zero visible tokens.
- **Defect 2 — variant**: Agent writes to `config/bootcamp_preferences.yaml`; write-policy-gate intercepts; agent emits "Updating preferences silently." Expected: zero visible tokens.
- **Non-bug (preservation)**: Agent writes Senzing SQL; write-policy-gate blocks and produces corrective output — this is correct behavior that must be preserved.

## Expected Behavior

### Preservation Requirements

**Unchanged Behaviors:**
- All legitimate write-gate rejections (Senzing SQL, compound `.question_pending` questions, feedback-file overwrite/in-place modification, external paths, root-blocked placements) continue to produce their documented visible corrective output
- Non-internal-file question validation on `config/.question_pending` is unchanged
- The `write-policy-gate` hook's `preToolUse` trigger, `toolTypes` (`fs_write|str_replace|fs_append`), INTERNAL-FILE PASS-THROUGH rule, and all NOT-guards remain unchanged
- All other onboarding content (setup preamble, MCP health check, version display, directory structure, team detection, prerequisite checks) is presented unchanged
- The write-policy-gate hook file itself is not modified

**Scope:**
All inputs that do NOT involve the stale onboarding note or internal-file pass-through narration should be completely unaffected by this fix. This includes:
- All legitimate write-gate blocking and corrective output
- Mouse/keyboard interactions with the bootcamp
- All onboarding steps other than section 0a
- Hook evaluation logic and security behavior

## Hypothesized Root Cause

Based on the bug description, the most likely issues are:

1. **Stale Documentation (Defect 1)**: The "0a" section in `onboarding-flow.md` was added when the intercept-then-retry cycle was visible to bootcampers. Subsequent fixes (silent-hook-architecture, hook-silent-fast-path, suppress-policy-pass-output) eliminated the visible "Rejected"/"Accepted" messages, but the explanatory note was never removed. The section is now inaccurate and constitutes noise.

2. **Insufficient Agent-Side Steering (Defect 2)**: The `write-policy-gate.json` hook prompt already mandates "produce ZERO tokens" for internal-file pass-through. However, the agent occasionally generates narration anyway because no agent behavior rule in `agent-behavior-rules.md` explicitly reinforces the zero-token requirement. The hook fires at the PreToolUse level, but the agent's general behavior steering lacks a matching prohibition that would prevent it from narrating during the re-invoke. Adding an explicit rule in `agent-behavior-rules.md` will close this gap by giving the agent a second, steering-level instruction that reinforces the hook's mandate.

3. **Test Assertions Codify the Stale Section (Defect 1)**: Tests in `tests/test_write_policy_gate_integration.py` (lines 372–456) assert that section 0a exists and has specific properties. The test in `senzing-bootcamp/tests/test_onboarding_question_ownership.py` includes the 0a heading in `_EXPECTED_HEADINGS`. These tests must be updated to reflect the removal.

## Correctness Properties

Property 1: Bug Condition - No Stale/Unwanted Write-Gate Output

_For any_ output event where the bug condition holds (isBugCondition returns true), the fixed system SHALL produce no visible write-gate-related noise to the bootcamper: the stale "Rejected/Accepted" onboarding note SHALL be absent from onboarding content, and internal-file pass-through re-invokes SHALL emit zero visible tokens.

**Validates: Requirements 2.1, 2.2**

Property 2: Preservation - Legitimate Gate Behavior and Other Onboarding Unchanged

_For any_ output event where the bug condition does NOT hold (isBugCondition returns false), the fixed system SHALL produce exactly the same behavior as the original system, preserving all legitimate write-gate rejections with their corrective output, all non-internal-file question validation, the hook's security behavior, and all other onboarding content.

**Validates: Requirements 3.1, 3.2, 3.3, 3.4**

## Fix Implementation

### Changes Required

Assuming our root cause analysis is correct:

**File**: `senzing-bootcamp/steering/onboarding-flow.md`

**Change**: Remove section "0a. Why You May See 'Rejected'/'Accepted' Messages"

**Specific Changes**:
1. **Remove stale section**: Delete the entire `## 0a. Why You May See "Rejected"/"Accepted" Messages` section (heading and all body content through the end of the section, stopping before `## 0b. MCP Health Check`). This removes approximately 12 lines of stale content.

---

**File**: `senzing-bootcamp/steering/agent-behavior-rules.md`

**Change**: Add Rule 5 prohibiting narration on internal-file pass-through re-invokes

**Specific Changes**:
2. **Add Rule 5 — Silent Internal-File Pass-Through Re-Invoke**: Append a new rule section after Rule 4 that explicitly prohibits the agent from emitting any visible tokens (narration, acknowledgment, explanation) when re-invoking a write after the `write-policy-gate` INTERNAL-FILE PASS-THROUGH applies. The rule reinforces the hook's "ZERO tokens" mandate at the agent steering level.

---

**File**: `tests/test_write_policy_gate_integration.py`

**Change**: Remove or update tests that assert the existence and properties of section 0a

**Specific Changes**:
3. **Remove stale test methods**: Remove the test class or methods (lines ~372–456) that assert section "0a" exists, appears before later sections, is near the start, follows the setup preamble, and contains reassuring content. These tests validate content that is being intentionally removed.

---

**File**: `senzing-bootcamp/tests/test_onboarding_question_ownership.py`

**Change**: Remove the 0a heading from `_EXPECTED_HEADINGS`

**Specific Changes**:
4. **Update expected headings list**: Remove the entry `'0a. Why You May See "Rejected"/"Accepted" Messages'` and its associated comment from the `_EXPECTED_HEADINGS` list (around line 290).

---

**File**: `senzing-bootcamp/steering/agent-behavior-rules.md` (Rule 4 reference update)

**Specific Changes**:
5. **Update Rule 4 cross-reference**: In Rule 4's body, the paragraph about `write-policy-gate` intercept/retry cycles references `conversation-protocol.md`. This reference remains valid (it describes leading-question continuity, not the stale 0a note). No change needed to Rule 4 itself.

## Testing Strategy

### Validation Approach

The testing strategy follows a two-phase approach: first, surface counterexamples that demonstrate the bug on unfixed code, then verify the fix works correctly and preserves existing behavior.

### Exploratory Bug Condition Checking

**Goal**: Surface counterexamples that demonstrate the bug BEFORE implementing the fix. Confirm or refute the root cause analysis. If we refute, we will need to re-hypothesize.

**Test Plan**: Write tests that parse the onboarding-flow.md content and check for the presence of the stale section, and that parse agent-behavior-rules.md and verify no explicit prohibition of pass-through narration exists. Run these on the UNFIXED code to observe the defects.

**Test Cases**:
1. **Stale Section Present Test**: Parse `onboarding-flow.md` and assert section "0a" with "Rejected"/"Accepted" content exists (will pass on unfixed code, confirming Defect 1)
2. **No Silent Re-Invoke Rule Test**: Parse `agent-behavior-rules.md` and assert no rule explicitly prohibits narration on internal-file pass-through (will pass on unfixed code, confirming Defect 2)
3. **Tests Assert Stale Content Test**: Run existing test suite and confirm tests in `test_write_policy_gate_integration.py` pass (they assert the stale section exists — will pass on unfixed code)

**Expected Counterexamples**:
- Section "0a" exists in onboarding-flow.md describing behavior that no longer occurs
- No agent behavior rule explicitly reinforces zero-token pass-through behavior
- Possible cause: incremental fixes removed the visible intercept-retry but never cleaned up the explanatory note or added agent-level steering

### Fix Checking

**Goal**: Verify that for all inputs where the bug condition holds, the fixed system produces the expected behavior.

**Pseudocode:**
```
FOR ALL input WHERE isBugCondition(input) DO
  result := F'(input)

  IF input.kind = "onboarding_preamble" THEN
    ASSERT "0a" section NOT IN result.onboarding_content
    ASSERT "Rejected" AND "Accepted" reassurance NOT IN result.onboarding_content
  ELSE IF input.kind = "write_gate_passthrough" THEN
    ASSERT result.emitted_tokens = EMPTY
    ASSERT result.write_operation_proceeds = TRUE
  END IF
END FOR
```

### Preservation Checking

**Goal**: Verify that for all inputs where the bug condition does NOT hold, the fixed system produces the same result as the original system.

**Pseudocode:**
```
FOR ALL input WHERE NOT isBugCondition(input) DO
  ASSERT F(input) = F'(input)
END FOR
```

**Testing Approach**: Property-based testing is recommended for preservation checking because:
- It generates many test cases automatically across the input domain (various onboarding section headings, various write targets)
- It catches edge cases that manual unit tests might miss (e.g., verifying all non-0a onboarding sections remain byte-for-byte)
- It provides strong guarantees that behavior is unchanged for all non-buggy inputs

**Test Plan**: Observe behavior on UNFIXED code first for all non-stale onboarding content and for legitimate write-gate rejections, then write property-based tests capturing that behavior.

**Test Cases**:
1. **Onboarding Content Preservation**: Verify all onboarding sections other than 0a (setup preamble, 0b MCP health check, 0c version display, 1 directory structure, 1b team detection, 2 prerequisite check) remain unchanged after the fix
2. **Write-Gate Rejection Preservation**: Verify that writes containing Senzing SQL, compound questions, feedback overwrites, external paths, or root-blocked placements still produce their documented corrective output
3. **Hook File Integrity Preservation**: Verify `write-policy-gate.json` is byte-for-byte unchanged
4. **Agent Behavior Rules Additive-Only**: Verify Rules 1–4 in `agent-behavior-rules.md` are unchanged; only a new Rule 5 is added

### Unit Tests

- Test that `onboarding-flow.md` does NOT contain the "0a" section heading or "Rejected"/"Accepted" reassurance content
- Test that `agent-behavior-rules.md` contains a rule explicitly prohibiting narration on internal-file pass-through
- Test that `_EXPECTED_HEADINGS` in `test_onboarding_question_ownership.py` does not include the 0a heading
- Test that `write-policy-gate.json` is unchanged (hash or content comparison)

### Property-Based Tests

- Generate random onboarding section indices and verify all non-removed sections are present and unchanged
- Generate random file paths from the internal-file pass-through set and verify the new steering rule covers them
- Generate random combinations of NOT-guard states and verify the steering rule applies only when all guards hold

### Integration Tests

- Run the full test suite after applying the fix and verify no regressions
- Verify the onboarding flow proceeds from "0. Setup Preamble" directly to "0b. MCP Health Check" with no intervening stale content
- Verify the agent behavior rules file parses correctly and all five rules are well-formed
