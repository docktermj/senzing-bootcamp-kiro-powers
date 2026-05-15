# Suppress Policy Pass Output Bugfix Design

## Overview

The `enforce-file-path-policies` preToolUse hook outputs the literal text "policy: pass" as visible chat text whenever a write operation passes its path validation checks. This internal hook machinery clutters the bootcamper's conversation with noise. The fix modifies the hook's prompt so that on the fast path, the agent proceeds silently without producing any visible output, while preserving all violation-detection (slow path) behavior unchanged.

## Glossary

- **Bug_Condition (C)**: The condition that triggers the bug — when the hook fires on a compliant write and the prompt instructs the agent to "output exactly: policy: pass", producing visible chat text
- **Property (P)**: The desired behavior when a compliant write passes — the hook should instruct the agent to proceed silently with no visible output
- **Preservation**: The existing violation-detection behavior (external path blocking, feedback path enforcement, content path checking) that must remain unchanged by the fix
- **enforce-file-path-policies**: The preToolUse hook in `senzing-bootcamp/hooks/enforce-file-path-policies.kiro.hook` that validates write target paths
- **Fast Path**: The code path taken when a write passes all policy checks (Q1=YES, Q2=NO) — currently outputs "policy: pass"
- **Slow Path**: The code path taken when a write violates a policy (external path or misrouted feedback) — outputs corrective instructions

## Bug Details

### Bug Condition

The bug manifests when the `enforce-file-path-policies` hook fires on a write operation that passes all policy checks. The hook prompt explicitly instructs the agent to "output exactly: policy: pass" on the fast path, which the agent renders as visible chat text to the bootcamper.

**Formal Specification:**
```
FUNCTION isBugCondition(input)
  INPUT: input of type HookInvocation (hook_name, target_path, is_feedback_content, content_refs_external)
  OUTPUT: boolean

  RETURN input.hook_name = "enforce-file-path-policies"
         AND input.target_path IS INSIDE working_directory
         AND NOT (input.is_feedback_content AND input.target_path != "docs/feedback/SENZING_BOOTCAMP_POWER_FEEDBACK.md")
         AND NOT input.content_refs_external
END FUNCTION
```

### Examples

- **Single compliant write**: Agent writes `src/transform.py` → hook fires → agent outputs "policy: pass" as visible text → bootcamper sees noise
- **Multi-file edit**: Agent writes 5 files in sequence → hook fires 5 times → "policy: pass" appears 5 times in chat → significant clutter
- **Feedback to correct path**: Agent writes `docs/feedback/SENZING_BOOTCAMP_POWER_FEEDBACK.md` → hook fires → agent outputs "policy: pass" → noise even for correct feedback writes
- **Edge case — violation**: Agent writes `/tmp/test.py` → hook fires → agent outputs corrective instructions (this is correct behavior, not the bug)

## Expected Behavior

### Preservation Requirements

**Unchanged Behaviors:**
- External path blocking: writes to `/tmp/`, `%TEMP%`, `~/Downloads`, or any path outside the working directory must continue to be blocked with corrective instructions
- Feedback path enforcement: feedback content written to a path other than `docs/feedback/SENZING_BOOTCAMP_POWER_FEEDBACK.md` must continue to be redirected
- Content path checking: file content referencing external paths must continue to be flagged with corrective instructions
- Hook event configuration: `when.type` must remain `preToolUse` and `when.toolTypes` must remain `["write"]`
- Hook JSON structure: all required fields (`name`, `version`, `description`, `when`, `then`) must remain present and valid

**Scope:**
All inputs where the bug condition does NOT hold (policy violations) should be completely unaffected by this fix. This includes:
- Writes targeting paths outside the working directory
- Feedback content being written to the wrong file
- File content containing references to external paths like `/tmp/`, `%TEMP%`, `~/Downloads`

## Hypothesized Root Cause

Based on the bug description, the root cause is straightforward:

1. **Explicit "output exactly: policy: pass" instruction in hook prompt**: The hook's `then.prompt` field contains the literal instruction "output exactly: policy: pass" on the fast path. The agent follows this instruction faithfully, rendering "policy: pass" as visible chat text. The prompt was designed this way intentionally (as a signal), but the visible output is undesirable UX.

2. **No silent-proceed alternative**: The prompt does not offer a "proceed silently" option for the fast path. It only knows two modes: output "policy: pass" (fast path) or output corrective instructions (slow path). There is no third mode of "produce no visible output."

3. **CONTENT CHECK section reinforces the output**: The prompt's CONTENT CHECK section says "output was already 'policy: pass' — do not add anything" which further cements the expectation that "policy: pass" is the correct fast-path output.

## Correctness Properties

Property 1: Bug Condition - Silent Fast Path for Compliant Writes

_For any_ hook invocation where the target path is inside the working directory, is not misrouted feedback, and content does not reference external paths (isBugCondition returns true), the fixed hook prompt SHALL instruct the agent to proceed silently with no visible output rather than outputting "policy: pass".

**Validates: Requirements 2.1, 2.2**

Property 2: Preservation - Violation Detection Unchanged

_For any_ hook invocation where the target path is outside the working directory, or feedback is misrouted, or content references external paths (isBugCondition returns false), the fixed hook prompt SHALL produce the same corrective output as the original hook prompt, preserving all violation-detection behavior.

**Validates: Requirements 3.1, 3.2, 3.3**

## Fix Implementation

### Changes Required

Assuming our root cause analysis is correct:

**File**: `senzing-bootcamp/hooks/enforce-file-path-policies.kiro.hook`

**Field**: `then.prompt`

**Specific Changes**:
1. **Replace fast-path output instruction**: Change "output exactly:\npolicy: pass" to an instruction that tells the agent to proceed silently without any visible output (e.g., "Do not acknowledge. Do not explain. Do not print anything. Proceed silently.")

2. **Update CONTENT CHECK section**: The trailing "output was already 'policy: pass' — do not add anything" should be updated to reflect the new silent-proceed behavior (e.g., "do nothing — proceed silently")

3. **Remove "Just output: policy: pass" reinforcement**: The line "Just output: policy: pass" at the end of the fast-path block must be removed or replaced with a silent-proceed instruction

4. **Preserve slow-path instructions verbatim**: The SLOW PATH section with its corrective instructions for external paths and misrouted feedback must remain exactly as-is

5. **Update `test_hook_prompt_standards.py` if needed**: The `test_real_pass_through_hooks_have_silent_processing` test checks for `SILENT_PROCESSING_PATTERNS` which includes `r"policy:\s*pass"`. After the fix removes "policy: pass" from the prompt, the test must still pass — verify that one of the other patterns (e.g., "do not acknowledge.*do not explain.*do not print" or "produce no output at all") matches the new prompt text

## Testing Strategy

### Validation Approach

The testing strategy follows a two-phase approach: first, surface counterexamples that demonstrate the bug on unfixed code, then verify the fix works correctly and preserves existing behavior.

### Exploratory Bug Condition Checking

**Goal**: Surface counterexamples that demonstrate the bug BEFORE implementing the fix. Confirm that the hook prompt currently instructs visible "policy: pass" output on the fast path.

**Test Plan**: Parse the hook prompt and assert it does NOT contain "output exactly: policy: pass" or similar visible-output instructions on the fast path. Run these tests on the UNFIXED code to observe failures confirming the bug.

**Test Cases**:
1. **Visible output instruction present**: Assert the prompt does NOT contain "output exactly.*policy.*pass" — will fail on unfixed code, confirming the bug
2. **Silent-proceed instruction missing**: Assert the prompt DOES contain a silent-proceed instruction (e.g., "do not acknowledge", "produce no output") on the fast path — will fail on unfixed code
3. **Multiple writes scenario**: For any sequence of N compliant writes, assert the prompt would produce zero visible output per invocation — will fail on unfixed code
4. **"Just output" reinforcement present**: Assert the prompt does NOT contain "Just output: policy: pass" — will fail on unfixed code

**Expected Counterexamples**:
- The prompt contains "output exactly:\npolicy: pass" as a literal instruction
- The prompt contains "Just output: policy: pass" as reinforcement
- No silent-proceed instruction exists in the fast-path section

### Fix Checking

**Goal**: Verify that for all inputs where the bug condition holds, the fixed hook prompt instructs silent processing with no visible output.

**Pseudocode:**
```
FOR ALL input WHERE isBugCondition(input) DO
  prompt := readFixedHookPrompt()
  ASSERT "output exactly" NOT IN prompt.fast_path_section
         OR "policy: pass" NOT IN prompt.fast_path_output_instruction
  ASSERT prompt.fast_path_section CONTAINS silent_proceed_instruction
END FOR
```

### Preservation Checking

**Goal**: Verify that for all inputs where the bug condition does NOT hold, the fixed hook prompt produces the same corrective output as the original.

**Pseudocode:**
```
FOR ALL input WHERE NOT isBugCondition(input) DO
  ASSERT fixedPrompt.slow_path_section = originalPrompt.slow_path_section
  ASSERT fixedPrompt.contains("/tmp/")
  ASSERT fixedPrompt.contains("%TEMP%")
  ASSERT fixedPrompt.contains("~/Downloads")
  ASSERT fixedPrompt.contains("docs/feedback/SENZING_BOOTCAMP_POWER_FEEDBACK.md")
END FOR
```

**Testing Approach**: Property-based testing is recommended for preservation checking because:
- It generates many test cases automatically across the input domain
- It catches edge cases that manual unit tests might miss
- It provides strong guarantees that violation-detection behavior is unchanged for all non-compliant inputs

**Test Plan**: Observe behavior on UNFIXED code first for violation scenarios (external paths, misrouted feedback, content with external refs), then write property-based tests capturing that behavior.

**Test Cases**:
1. **External path blocking preserved**: Verify the prompt still references `/tmp/`, `%TEMP%`, `~/Downloads` and instructs STOP for external paths
2. **Feedback redirect preserved**: Verify the prompt still references `docs/feedback/SENZING_BOOTCAMP_POWER_FEEDBACK.md` and instructs redirect for misrouted feedback
3. **Content path check preserved**: Verify the prompt still checks file content for external path references
4. **Hook JSON structure preserved**: Verify all required fields remain present and valid
5. **Hook event config preserved**: Verify `when.type` is still `preToolUse` and `when.toolTypes` still contains `write`

### Unit Tests

- Test that the fixed prompt does NOT contain "output exactly: policy: pass"
- Test that the fixed prompt DOES contain a silent-proceed instruction matching `SILENT_PROCESSING_PATTERNS`
- Test that the fixed prompt still contains all slow-path corrective instructions
- Test that the hook JSON remains valid with all required fields
- Test that `hook-categories.yaml` still lists `enforce-file-path-policies` under `critical`

### Property-Based Tests

- Generate random project-relative paths and verify the prompt instructs silent processing (no "output exactly: policy: pass")
- Generate random external paths and verify the prompt still contains blocking instructions for each
- Generate random hook field combinations and verify required fields are always present
- Test across all `SILENT_PROCESSING_PATTERNS` to ensure at least one matches the fixed prompt

### Integration Tests

- Test that `test_real_pass_through_hooks_have_silent_processing` still passes after the fix (the `has_silent_processing` function must still return True for the fixed prompt)
- Test that `sync_hook_registry.py --verify` still passes (hook-categories.yaml consistency)
- Test that the full CI validation suite (`validate-power.yml`) passes with the fixed hook
