# Hook Silent Fast Path Bugfix Design

## Overview

The `write-policy-gate` preToolUse hook produces visible chat clutter when its fast path passes. Despite the hook prompt explicitly instructing "Do not acknowledge. Do not explain. Do not print anything. Proceed silently.", the agent narrates its internal evaluation reasoning (e.g., "Fast path passes — inside working directory, not .question_pending, no SQL patterns targeting Senzing DB. Proceeding:") before executing the write. The fix must ensure the agent produces zero visible output when the fast-path conditions are met, while preserving all violation-detection behavior on the slow paths.

## Glossary

- **Bug_Condition (C)**: The condition that triggers the bug — when the write-policy-gate hook fires and all fast-path conditions are met (path inside working directory, not `.question_pending`, no Senzing SQL patterns) but the agent still produces visible output
- **Property (P)**: The desired behavior when the fast path passes — exactly zero characters of visible chat output and the write proceeds silently
- **Preservation**: All slow-path violation-detection behaviors (SQL blocking, compound question enforcement, file path policies) that must remain unchanged by the fix
- **write-policy-gate**: The consolidated preToolUse hook in `senzing-bootcamp/hooks/write-policy-gate.kiro.hook` that performs three policy checks on write operations
- **Fast Path**: The code path taken when all three policy checks pass — target is inside working directory, not `.question_pending`, and no Senzing SQL patterns
- **Slow Path**: The code path taken when any policy check fails — produces visible corrective output to the bootcamper

## Bug Details

### Bug Condition

The bug manifests when the `write-policy-gate` hook fires on a write operation and all fast-path conditions are satisfied. The agent evaluates the prompt's fast-path logic correctly (determining the write is safe) but then narrates its reasoning as visible chat output instead of proceeding silently as instructed.

**Formal Specification:**
```
FUNCTION isBugCondition(input)
  INPUT: input of type HookInvocation (hook_name, target_path, content)
  OUTPUT: boolean

  RETURN input.hook_name = "write-policy-gate"
         AND input.target_path IS INSIDE working_directory
         AND NOT endsWith(input.target_path, ".question_pending")
         AND NOT (containsSqlPatterns(input.content) AND containsSenzingDbIndicators(input.content))
         AND visibleOutputProduced(input) != EMPTY
END FUNCTION
```

### Examples

- **Normal file write**: Writing `src/transform.py` with Python code → agent outputs "Fast path passes — inside working directory, not .question_pending, no SQL patterns targeting Senzing DB. Proceeding:" instead of producing zero output
- **Config file write**: Writing `config/data_sources.yaml` with YAML content → agent narrates its evaluation before allowing the write
- **Sequential writes**: Writing 5 files in a row during code generation → agent produces 5 lines of fast-path narration, cluttering the bootcamper's chat
- **Edge case — non-Senzing SQL**: Writing a file containing `SELECT * FROM users` (general SQL, not Senzing) → fast path should pass silently but agent still narrates

## Expected Behavior

### Preservation Requirements

**Unchanged Behaviors:**
- SQL blocking: writes containing SQL patterns targeting Senzing database indicators (G2C.db, RES_ENT, OBS_ENT, etc.) must continue to be blocked with corrective output explaining SDK alternatives
- Compound question enforcement: writes to `.question_pending` paths that violate single-question rules must continue to be blocked with rewrite instructions
- External path blocking: writes to paths outside the working directory must continue to be blocked with project-relative equivalents
- Feedback redirect: feedback content written to non-canonical paths must continue to be redirected to `docs/feedback/SENZING_BOOTCAMP_POWER_FEEDBACK.md`
- Content path checking: file content referencing `/tmp/`, `%TEMP%`, or `~/Downloads` must continue to be flagged
- Valid `.question_pending` writes: question content passing all single-question rules must continue to proceed silently

**Scope:**
All inputs where the fast-path conditions are NOT met should be completely unaffected by this fix. This includes:
- Writes containing Senzing SQL patterns (Check 1 slow path)
- Writes to `.question_pending` paths with compound questions (Check 2 slow path)
- Writes to paths outside the working directory (Check 3 slow path)
- Feedback content written to wrong paths (Check 3 slow path)
- File content referencing external paths (Check 3 content check)

## Hypothesized Root Cause

Based on the bug description, the most likely issues are:

1. **Insufficient Silence Reinforcement in Prompt**: The prompt says "Do not acknowledge. Do not explain. Do not print anything. Proceed silently." but the agent's instruction-following for zero-output directives may require stronger or differently-structured reinforcement. The current phrasing may be interpreted as guidance rather than a hard constraint.

2. **Prompt Structure Encourages Narration**: The fast-path section is embedded within a larger prompt that contains multiple check sections with explicit output instructions (e.g., "Output exactly: ⚠️ COMPOUND QUESTION DETECTED"). The agent may pattern-match on the output-producing sections and generate analogous narration for the fast path.

3. **Missing Explicit Output Suppression Markers**: The prompt lacks a structural signal (such as an empty response template or explicit "OUTPUT: nothing" directive) that unambiguously tells the agent to produce zero tokens. The natural language instruction alone may not be sufficient to override the agent's default behavior of explaining its reasoning.

4. **Fast-Path Logic Spread Across Multiple Sections**: The fast-path "proceed silently" instruction appears in the FAST PATH GATE section at the top, but each individual check (1, 2, 3) also has its own "proceed silently" clause. This repetition may paradoxically encourage the agent to acknowledge which checks passed before proceeding.

## Correctness Properties

Property 1: Bug Condition - Zero Visible Output on Fast Path Pass

_For any_ hook invocation where the bug condition holds (target path is inside working directory, does not end with `.question_pending`, and content does not contain SQL patterns targeting Senzing database indicators), the fixed hook prompt SHALL cause the agent to produce exactly zero characters of visible chat output and silently allow the write to proceed.

**Validates: Requirements 2.1, 2.2, 2.3**

Property 2: Preservation - Violation Detection Behavior Unchanged

_For any_ hook invocation where the bug condition does NOT hold (content contains Senzing SQL patterns, or target path ends with `.question_pending` with compound questions, or target path is outside working directory, or feedback is misrouted), the fixed hook prompt SHALL produce the same corrective output as the original prompt, preserving all violation-detection and blocking behavior.

**Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5, 3.6**

## Fix Implementation

### Changes Required

Assuming our root cause analysis is correct:

**File**: `senzing-bootcamp/hooks/write-policy-gate.kiro.hook`

**Field**: `then.prompt`

**Specific Changes**:

1. **Strengthen Fast-Path Silence Directive**: Replace the current "Do not acknowledge. Do not explain. Do not print anything. Proceed silently." with a more structurally emphatic zero-output instruction. Use explicit formatting such as:
   - `OUTPUT: (none)` or `RESPONSE: empty`
   - A clear structural marker that distinguishes "produce zero tokens" from "produce minimal output"

2. **Add Explicit Empty-Response Template**: After the fast-path condition, add an explicit response template showing the expected output is literally nothing — e.g., `Your response when fast path passes: [empty — produce zero tokens]`

3. **Consolidate Fast-Path Exit**: Restructure the prompt so the fast-path gate at the top is the single authoritative exit point. Remove or reduce the per-check "proceed silently" clauses that may encourage narration by implying the agent should evaluate each check individually before deciding to be silent.

4. **Add Anti-Narration Instruction**: Explicitly prohibit the specific narration pattern observed: "Do NOT output phrases like 'Fast path passes', 'Proceeding', 'All checks pass', or any summary of your evaluation. Zero tokens means zero tokens."

5. **Preserve All Slow-Path Text Verbatim**: The SLOW PATH sections (SQL blocking output, compound question violation format, external path blocking, feedback redirect) must remain character-for-character identical to ensure preservation property holds.

## Testing Strategy

### Validation Approach

The testing strategy follows a two-phase approach: first, surface counterexamples that demonstrate the bug on unfixed code, then verify the fix works correctly and preserves existing behavior. Tests validate the hook prompt text (the artifact we control) rather than agent runtime behavior (which we cannot deterministically test).

### Exploratory Bug Condition Checking

**Goal**: Surface counterexamples that demonstrate the bug BEFORE implementing the fix. Confirm or refute the root cause analysis. If we refute, we will need to re-hypothesize.

**Test Plan**: Write tests that analyze the hook prompt text for patterns that may cause the agent to produce visible output on the fast path. Run these tests on the UNFIXED code to observe failures and understand the root cause.

**Test Cases**:
1. **No "policy: pass" Output Instruction**: Verify the prompt does not contain instructions like "output exactly...policy...pass" that tell the agent to produce visible text on the fast path (will fail on unfixed code if such patterns exist)
2. **No "Just output" Reinforcement**: Verify the prompt does not contain "Just output: policy: pass" or similar reinforcement of visible output (will fail on unfixed code if present)
3. **Silent-Proceed Instruction Present**: Verify the prompt contains a genuine silent-processing instruction like "do not acknowledge.*do not explain.*do not print" (will fail on unfixed code if missing or insufficient)
4. **No Narration-Encouraging Patterns**: Verify the prompt does not contain patterns that encourage the agent to summarize its evaluation before proceeding

**Expected Counterexamples**:
- The prompt may contain explicit instructions to output "policy: pass" as visible text
- The prompt structure may lack sufficient zero-output reinforcement
- Possible causes: explicit output instruction, insufficient silence directive, structural ambiguity

### Fix Checking

**Goal**: Verify that for all inputs where the bug condition holds, the fixed prompt instructs zero visible output.

**Pseudocode:**
```
FOR ALL input WHERE isBugCondition(input) DO
  prompt := loadFixedHookPrompt()
  ASSERT prompt does NOT contain "output exactly" followed by "policy...pass"
  ASSERT prompt does NOT contain "Just output: policy: pass"
  ASSERT prompt CONTAINS genuine silent-processing instruction
  ASSERT prompt CONTAINS explicit anti-narration directive
END FOR
```

### Preservation Checking

**Goal**: Verify that for all inputs where the bug condition does NOT hold, the fixed prompt produces the same corrective instructions as the original.

**Pseudocode:**
```
FOR ALL input WHERE NOT isBugCondition(input) DO
  ASSERT fixedPrompt.slowPathSection = originalPrompt.slowPathSection
  ASSERT fixedPrompt.sqlBlockingInstructions = originalPrompt.sqlBlockingInstructions
  ASSERT fixedPrompt.compoundQuestionFormat = originalPrompt.compoundQuestionFormat
  ASSERT fixedPrompt.externalPathBlocking = originalPrompt.externalPathBlocking
  ASSERT fixedPrompt.feedbackRedirect = originalPrompt.feedbackRedirect
END FOR
```

**Testing Approach**: Property-based testing is recommended for preservation checking because:
- It generates many test cases automatically across the input domain (various path patterns, content types)
- It catches edge cases that manual unit tests might miss (unusual path characters, boundary conditions)
- It provides strong guarantees that slow-path behavior is unchanged for all violation scenarios

**Test Plan**: Observe behavior on UNFIXED code first for slow-path sections, capture baseline text, then write property-based tests verifying the slow-path text remains identical after the fix.

**Test Cases**:
1. **SQL Blocking Preservation**: Observe that the prompt contains SQL blocking instructions with all Senzing indicators on unfixed code, then verify this section is character-identical after fix
2. **Compound Question Format Preservation**: Observe that the `⚠️ COMPOUND QUESTION DETECTED` output format is present on unfixed code, then verify it remains unchanged
3. **External Path Blocking Preservation**: Observe that the SLOW PATH section contains "STOP" and project-relative equivalents on unfixed code, then verify identical after fix
4. **Hook JSON Structure Preservation**: Observe that all required fields (name, version, when.type, when.toolTypes, then.type) are valid on unfixed code, then verify unchanged after fix

### Unit Tests

- Test that the fast-path section does not instruct visible output
- Test that the fast-path section contains a genuine silent-processing directive
- Test that the slow-path sections contain all expected blocking instructions
- Test that the hook JSON structure has all required fields with correct values

### Property-Based Tests

- Generate random project-relative file paths and verify the prompt instructs silence for all of them (fix checking)
- Generate random external path prefixes (`/tmp/`, `%TEMP%`, `~/Downloads`) and verify the prompt contains blocking instructions for all of them (preservation)
- Generate random non-canonical feedback paths and verify the prompt contains redirect instructions (preservation)
- Generate random required hook field names and verify all are present with valid values (structural preservation)

### Integration Tests

- Test full hook file loading and JSON parsing round-trip
- Test that the prompt text is non-empty and contains both fast-path and slow-path sections
- Test that the hook's `when.type` is `preToolUse` and `when.toolTypes` is `["write"]`
