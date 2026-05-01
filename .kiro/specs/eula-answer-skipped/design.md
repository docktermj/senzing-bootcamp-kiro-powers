# EULA Answer Skipped Bugfix Design

## Overview

During Module 2 Step 3 (Install Senzing SDK), the agent presents the EULA acceptance question but does not wait for the bootcamper's explicit response before continuing with the remaining installation sub-steps. The EULA question also lacks the 👉 marker, so the `ask-bootcamper` agentStop hook cannot detect it as a pending question. This is the same class of bug as `agent-skips-git-question` — the steering file instructs the agent to ask a question that requires user input but provides no explicit STOP instruction and no 👉 marker.

The fix rewrites Step 3 in `module-02-sdk-setup.md` to split the installation flow into three phases: pre-EULA steps (add repo, install package), the EULA question with 👉 marker and STOP instruction, and post-EULA steps (install language bindings) that only execute after explicit acceptance. The `ask-bootcamper.kiro.hook` is unchanged — it already correctly detects 👉 markers.

## Glossary

- **Bug_Condition (C)**: The condition that triggers the bug — the agent reaches the EULA acceptance question in Step 3 and continues without waiting for the bootcamper's response because the steering file has no STOP instruction and no 👉 marker
- **Property (P)**: The desired behavior — the agent presents the EULA question with a 👉 marker, STOPs, and only proceeds after the bootcamper explicitly accepts or declines
- **Preservation**: Existing behavior that must remain unchanged — pre-EULA sub-steps execute without stopping, Steps 1-2 and 4-9 are unmodified, the hook file is untouched, and previously-accepted EULA skip logic is preserved
- **`module-02-sdk-setup.md`**: The steering file in `senzing-bootcamp/steering/` that defines the Module 2 installation flow, including Step 3 where the bug occurs
- **`ask-bootcamper.kiro.hook`**: The agentStop hook that scans the last assistant message for the 👉 character and suppresses output when a question is pending
- **👉 marker**: The emoji prefix convention used to signal a pending question that the hook should detect
- **STOP instruction**: An explicit directive in the steering file telling the agent to stop execution and wait for the bootcamper's response before proceeding

## Bug Details

### Bug Condition

The bug manifests when the agent reaches Module 2 Step 3 and encounters the EULA acceptance question. The steering file lists EULA acceptance as item 3 in a continuous numbered list of installation sub-steps (`1. Add repo, 2. Install package, 3. Accept EULA, 4. Install bindings`) with no explicit instruction to STOP and wait. The agent treats the entire list as a sequential flow and continues past the EULA question. Additionally, because the question lacks the 👉 marker, the `ask-bootcamper` hook does not detect it as pending and may fire a second question.

**Formal Specification:**

```text
FUNCTION isBugCondition(input)
  INPUT: input of type SteeringFileStep3Content
  OUTPUT: boolean

  step3 := extractStep(input.steeringFile, 3)
  eulaSection := findEULAQuestion(step3)

  RETURN eulaSection EXISTS
         AND NOT containsPointingMarker(eulaSection, "👉")
         AND NOT containsStopInstruction(eulaSection)
END FUNCTION
```

### Examples

- **Example 1**: Agent reaches Step 3, presents "Do you accept the Senzing EULA?" without 👉, immediately runs `pip install senzing` — expected: agent STOPs after 👉-prefixed EULA question, actual: agent continues to install bindings
- **Example 2**: Hook fires after EULA question, scans for 👉, finds none, produces a second question about "what to do next" — expected: hook detects 👉 and suppresses output, actual: bootcamper sees two questions and can only answer one
- **Example 3**: Bootcamper wants to decline the EULA — expected: agent stops installation and explains SDK cannot be used, actual: agent has already installed bindings and written the checkpoint
- **Edge case**: EULA was previously accepted on the system — expected: agent skips the EULA question entirely and proceeds, actual: this path is unaffected by the bug (no question is asked)

## Expected Behavior

### Preservation Requirements

Unchanged Behaviors:

- Pre-EULA sub-steps in Step 3 (adding the package repository, installing the SDK package) must continue to execute in sequence without stopping
- The `ask-bootcamper.kiro.hook` file must remain byte-identical — it already correctly handles 👉 markers
- Other 👉-prefixed questions in any module must continue to be detected by the hook
- Module 2 Steps 1, 2, and 4 through 9 must remain unchanged in content, checkpoint logic, and flow
- The previously-accepted EULA skip logic (Step 1 checks for existing installation) must be preserved
- YAML frontmatter (`inclusion: manual`) must be preserved
- The total checkpoint count in the file must remain unchanged

Scope:

All content outside of Step 3 in `module-02-sdk-setup.md` should be completely unaffected by this fix. Within Step 3, only the EULA question flow changes — the pre-EULA sub-steps (add repo, install package) and the TypeScript/Windows warnings remain unchanged.

## Hypothesized Root Cause

Based on the bug description and analysis of the steering file, the root cause has two parts:

1. **No STOP instruction after EULA question**: Step 3 lists four sub-steps as a continuous numbered list. The agent treats this as a sequential flow and executes all four items without pausing. There is no explicit instruction telling the agent to STOP and wait for the bootcamper's response after presenting the EULA question.

2. **Missing 👉 marker on EULA question**: The EULA acceptance question does not use the 👉 prefix that the `ask-bootcamper` hook scans for. Without this marker, the hook cannot detect the question as pending and may produce additional output or a second question, violating the one-question-at-a-time flow.

3. **No decline handling**: The current Step 3 has no conditional branching based on the bootcamper's EULA response. There is no path for declining the EULA — the agent unconditionally proceeds to install language bindings and write the checkpoint.

4. **Unconditional checkpoint**: The `**Checkpoint:**` line at the end of Step 3 is written regardless of whether the bootcamper accepted or declined the EULA, or even whether the question was answered at all.

## Correctness Properties

Property 1: Bug Condition - EULA Question Has 👉 Marker and STOP Instruction

_For any_ steering file content where Step 3 contains the EULA acceptance question, the fixed Step 3 SHALL include the 👉 marker prefix on the EULA question text AND an explicit STOP instruction telling the agent to wait for the bootcamper's response before proceeding with subsequent installation sub-steps.

**Validates: Requirements 2.1, 2.2**

Property 2: Preservation - Non-Step-3 Content Unchanged

_For any_ step in Module 2 that is NOT Step 3 (Steps 1, 2, 4 through 9), the fixed steering file SHALL contain identical content to the original file, preserving all existing flow, checkpoint logic, and question-asking behavior.

**Validates: Requirements 3.1, 3.3**

## Fix Implementation

### Changes Required

Assuming our root cause analysis is correct:

**File**: `senzing-bootcamp/steering/module-02-sdk-setup.md`

**Section**: Step 3 (Install Senzing SDK)

**Specific Changes**:

1. **Split Step 3 into pre-EULA and post-EULA phases**: Restructure the numbered list so that sub-steps 1-2 (add repo, install package) execute first, then the EULA question is presented as a separate block with the 👉 marker and STOP instruction.

2. **Add 👉 marker to EULA question**: Prefix the EULA acceptance question with the 👉 emoji so the `ask-bootcamper` hook detects it as a pending question and suppresses further output.

3. **Add explicit STOP instruction**: After the 👉-prefixed EULA question, add a clear instruction telling the agent to STOP and wait for the bootcamper's explicit response. Do not proceed with any subsequent sub-steps.

4. **Add EULA acceptance path**: After the STOP, add instructions for the acceptance path — proceed with installing language-specific SDK bindings (the original sub-step 4).

5. **Add EULA decline path**: Add instructions for the decline path — stop the installation process and explain that the Senzing SDK cannot be used without EULA acceptance. Do not install language bindings or write the checkpoint.

6. **Defer checkpoint**: Move the `**Checkpoint:**` line so it only applies after the full Step 3 completes (EULA accepted + bindings installed). The checkpoint should not be written if the EULA is declined.

7. **Preserve existing content**: Keep the TypeScript/Node.js warning, Windows-specific instructions, anti-patterns check, shell configuration warning, and all other non-EULA content in Step 3 unchanged.

## Testing Strategy

### Validation Approach

The testing strategy follows a two-phase approach: first, surface counterexamples that demonstrate the bug on unfixed code, then verify the fix works correctly and preserves existing behavior. Tests parse the steering file markdown directly — no runtime agent execution is needed.

### Exploratory Bug Condition Checking

**Goal**: Surface counterexamples that demonstrate the bug BEFORE implementing the fix. Confirm or refute the root cause analysis. If we refute, we will need to re-hypothesize.

**Test Plan**: Write tests that parse `module-02-sdk-setup.md`, extract Step 3, and assert the EULA question has the 👉 marker and a STOP instruction. Run these tests on the UNFIXED code to observe failures and confirm the bug.

**Test Cases**:

1. **Missing 👉 Marker Test**: Parse Step 3, find the EULA question text, assert it contains the 👉 marker (will fail on unfixed code)
2. **Missing STOP Instruction Test**: Parse Step 3, find the EULA question text, assert a STOP/wait instruction follows (will fail on unfixed code)
3. **Unconditional Checkpoint Test**: Parse Step 3, assert the checkpoint is deferred until after EULA acceptance — not placed unconditionally after the question (will fail on unfixed code)
4. **Missing Decline Handling Test**: Parse Step 3, assert it contains decline handling logic (will fail on unfixed code)

**Expected Counterexamples**:

- The 👉 marker is absent from the EULA question text in Step 3
- No STOP instruction exists between the EULA question and the language bindings installation sub-step
- Possible causes: EULA acceptance listed as item 3 in a continuous numbered list with no flow control

### Fix Checking

**Goal**: Verify that for all inputs where the bug condition holds, the fixed function produces the expected behavior.

**Pseudocode:**

```text
FOR ALL input WHERE isBugCondition(input) DO
  step3 := extractStep(input.fixedSteeringFile, 3)
  eulaSection := findEULAQuestion(step3)
  ASSERT containsPointingMarker(eulaSection, "👉")
  ASSERT containsStopInstruction(eulaSection)
  ASSERT hasDeclineHandling(step3)
  ASSERT checkpointIsDeferred(step3)
END FOR
```

### Preservation Checking

**Goal**: Verify that for all inputs where the bug condition does NOT hold, the fixed function produces the same result as the original function.

**Pseudocode:**

```text
FOR ALL step WHERE step.number != 3 DO
  ASSERT extractStep(fixedFile, step.number) = extractStep(originalFile, step.number)
END FOR
ASSERT hookFile IS BYTE-IDENTICAL TO originalHookFile
ASSERT frontmatter IS UNCHANGED
ASSERT checkpointCount IS UNCHANGED
```

**Testing Approach**: Property-based testing is recommended for preservation checking because:

- It generates step numbers from {1, 2, 4, 5, 6, 7, 8, 9} and verifies each step's content is identical to the baseline
- It catches accidental modifications to steps outside the fix scope
- It provides strong guarantees that non-Step-3 behavior is unchanged

**Test Plan**: Observe behavior on UNFIXED code first for all non-Step-3 content, then write property-based tests capturing that behavior as the baseline.

**Test Cases**:

1. **Steps 1-2, 4-9 Content Preservation**: Snapshot each step from the unfixed file and assert the fixed file matches
2. **Hook File Preservation**: Assert `ask-bootcamper.kiro.hook` is byte-identical to the original
3. **YAML Frontmatter Preservation**: Assert the file starts with `---` and contains `inclusion: manual`
4. **Checkpoint Count Preservation**: Assert the total number of `**Checkpoint:**` lines is unchanged
5. **Pre-EULA Sub-Steps Preservation**: Assert the add-repo and install-package sub-steps in Step 3 are preserved and do not contain STOP instructions

### Unit Tests

- Test that Step 3 EULA question contains the 👉 marker
- Test that Step 3 contains a STOP instruction after the EULA question
- Test that Step 3 contains EULA decline handling
- Test that the checkpoint is deferred until after EULA acceptance
- Test that pre-EULA sub-steps (add repo, install package) do not contain STOP instructions

### Property-Based Tests

- Generate random step numbers from {1, 2, 4, 5, 6, 7, 8, 9} and verify content is identical to the unfixed baseline (preservation)
- Generate step numbers from {1..9} and verify only Step 3 contains the EULA question with 👉 marker (bug condition identification)
- Verify the hook file is unchanged across all test runs

### Integration Tests

- Test the full Step 3 flow structure: pre-EULA steps → 👉 EULA question → STOP → acceptance path → bindings → checkpoint
- Test that the decline path exists and does not include bindings installation or checkpoint
- Test that the TypeScript/Node.js warning and Windows-specific instructions are preserved within Step 3
