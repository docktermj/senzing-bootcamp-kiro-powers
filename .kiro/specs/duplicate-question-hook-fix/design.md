# Duplicate Question Hook Fix — Bugfix Design

## Overview

The "Summarize Progress on Stop" hook (`summarize-on-stop.kiro.hook`) duplicates pending questions during bootcamp interactions. When the agent's output already ends with a pending question (👉 prefix or WAIT pattern), the hook's prompt instructs the agent to "re-state the pending question as the very last element." This causes the bootcamper to see the same question twice — once in the original output and once appended by the hook summary.

The fix is a targeted prompt-text change: remove the re-statement instruction and replace it with an instruction to append only the summary (what was accomplished, which files changed) when a pending question is detected. The question is already visible, so repeating it is unnecessary. The same change must be mirrored in `hook-registry.md` to keep the two sources in sync.

## Glossary

- **Bug_Condition (C)**: The hook prompt contains an instruction to re-state a pending question, causing duplication whenever the agent's output ends with a 👉 line or WAIT pattern.
- **Property (P)**: When a pending question is detected, the hook should append only the summary without re-stating the question.
- **Preservation**: The no-question path (three-element summary), hook metadata (name, version, description, event type, action type), and hook-file/registry synchronization must remain unchanged.
- **Hook prompt**: The `then.prompt` string in `senzing-bootcamp/hooks/summarize-on-stop.kiro.hook` that instructs the agent what to do when it stops.
- **Registry prompt**: The corresponding Prompt field for `summarize-on-stop` in `senzing-bootcamp/steering/hook-registry.md`.
- **Pending question**: A line in the agent's output starting with 👉 or containing a WAIT-for-response pattern, indicating the agent asked the bootcamper something and is awaiting a reply.

## Bug Details

### Bug Condition

The bug manifests whenever the `agentStop` hook fires and the agent's previous output ends with a pending question. The hook prompt explicitly tells the agent to "re-state the pending question as the very last element," which duplicates a question already visible to the bootcamper.

**Formal Specification:**

```
FUNCTION isBugCondition(input)
  INPUT: input of type { hookPrompt: string, agentOutput: string }
  OUTPUT: boolean

  hasPendingQuestion :=
       agentOutput contains a line starting with "👉"
    OR agentOutput contains a WAIT-for-response pattern

  promptRestatesQuestion :=
       hookPrompt contains "re-state the pending question"
    OR hookPrompt contains "restate the pending question"

  RETURN hasPendingQuestion AND promptRestatesQuestion
END FUNCTION
```

### Examples

- **Onboarding welcome**: Agent presents the module overview ending with "👉 Does this outline make sense?" → hook fires → summary is appended → hook re-states "Does this outline make sense?" → bootcamper sees the question twice.
- **Module checkpoint**: Agent finishes a step with "WAIT for the bootcamper's response before continuing" → hook fires → summary is appended → hook re-states the WAIT question → duplicate.
- **Mid-conversation question**: Agent asks "👉 Would you like to proceed with Python or Java?" → hook fires → summary + duplicate question.
- **No pending question (not buggy)**: Agent finishes with a statement, no 👉 or WAIT → hook appends the standard three-element summary → no duplication, works correctly.

## Expected Behavior

### Preservation Requirements

**Unchanged Behaviors:**
- When no pending question is detected, the hook must continue to append the standard three-element summary: (1) what was accomplished, (2) which files were created or modified, (3) what is the next step.
- Hook metadata must remain unchanged: name "Summarize Progress on Stop", version "1.0.0", event type `agentStop`, action type `askAgent`, and description.
- The hook file prompt and the registry prompt must remain in sync (identical text).
- The hook file must remain valid JSON with all required keys (`name`, `version`, `description`, `when`, `then`).

**Scope:**
All agent outputs that do NOT end with a pending question (no 👉 line and no WAIT pattern) should be completely unaffected by this fix. This includes:
- Agent outputs ending with statements or instructions
- Agent outputs ending with file listings or code blocks
- Agent outputs ending with next-step guidance

## Hypothesized Root Cause

Based on the bug description and direct inspection of the prompt text, the root cause is clear and singular:

1. **Explicit re-statement instruction in the prompt**: The prompt text contains the phrase "Then re-state the pending question as the very last element so it is the last thing the bootcamper sees." This directly instructs the agent to duplicate a question that is already present in its output. The agent is faithfully following the prompt — the prompt itself is wrong.

2. **Registry copy has the same defect**: The `hook-registry.md` file contains an identical copy of the prompt, so both sources carry the same re-statement instruction and must both be updated.

There is no code logic bug, no selector issue, no timing problem. The defect is entirely in the prompt wording.

## Correctness Properties

Property 1: Bug Condition — Pending Question Not Re-stated

_For any_ agent output where a pending question is detected (a line starting with 👉 or a WAIT-for-response pattern), the fixed hook prompt SHALL instruct the agent to append only the summary (what was accomplished, which files changed) without re-stating the pending question, so the question appears exactly once.

**Validates: Requirements 2.1, 2.2**

Property 2: Preservation — No-Question Path and Hook Metadata Unchanged

_For any_ agent output where no pending question is detected, the fixed hook prompt SHALL produce the same three-element summary as the original prompt (what was accomplished, which files changed, what is the next step), and all hook metadata (name, version, description, event type, action type) and hook-file/registry synchronization SHALL remain unchanged.

**Validates: Requirements 3.1, 3.2, 3.3, 3.4**

## Fix Implementation

### Changes Required

Assuming our root cause analysis is correct (the prompt text explicitly instructs re-statement):

**File**: `senzing-bootcamp/hooks/summarize-on-stop.kiro.hook`

**Field**: `then.prompt`

**Specific Changes**:
1. **Remove re-statement instruction**: Delete the clause "Then re-state the pending question as the very last element so it is the last thing the bootcamper sees."
2. **Replace with append-only instruction**: When a pending question is detected, instruct the agent to append only the summary — (1) what was accomplished, (2) which files were created or modified — without re-stating the question, since it is already visible in the agent's output.
3. **Preserve no-question path**: The "If no pending question is detected" branch must remain unchanged, continuing to produce the three-element summary.
4. **Preserve detection logic**: The 👉 and WAIT detection instructions at the start of the prompt must remain unchanged.

**File**: `senzing-bootcamp/steering/hook-registry.md`

**Field**: Prompt for `summarize-on-stop`

**Specific Changes**:
5. **Mirror the hook file change**: Update the registry prompt to match the new hook file prompt exactly, maintaining synchronization.

## Testing Strategy

### Validation Approach

The testing strategy follows a two-phase approach: first, surface counterexamples that demonstrate the bug on unfixed code, then verify the fix works correctly and preserves existing behavior.

### Exploratory Bug Condition Checking

**Goal**: Surface counterexamples that demonstrate the bug BEFORE implementing the fix. Confirm or refute the root cause analysis. If we refute, we will need to re-hypothesize.

**Test Plan**: Write property-based tests that parse the hook prompt text and assert it does NOT contain re-statement instructions. Run these tests on the UNFIXED code to observe failures, confirming the bug exists in the prompt wording.

**Test Cases**:
1. **Hook prompt lacks re-statement instruction**: Assert the hook prompt does not contain "re-state" or "restate" in the context of pending questions (will fail on unfixed code).
2. **Hook prompt contains pending-question detection**: Assert the prompt mentions 👉 or WAIT detection (will pass on unfixed code — detection is fine, re-statement is the problem).
3. **Registry prompt lacks re-statement instruction**: Assert the registry prompt does not contain "re-state" or "restate" (will fail on unfixed code).

**Expected Counterexamples**:
- The prompt text contains the literal string "re-state the pending question as the very last element"
- Both hook file and registry carry this defective instruction

### Fix Checking

**Goal**: Verify that for all inputs where the bug condition holds, the fixed prompt produces the expected behavior.

**Pseudocode:**

```
FOR ALL input WHERE isBugCondition(input) DO
  fixedPrompt := readFixedHookPrompt()
  ASSERT fixedPrompt does NOT contain "re-state" or "restate" for pending questions
  ASSERT fixedPrompt instructs append-only summary when pending question detected
END FOR
```

### Preservation Checking

**Goal**: Verify that for all inputs where the bug condition does NOT hold, the fixed prompt produces the same result as the original prompt.

**Pseudocode:**

```
FOR ALL input WHERE NOT isBugCondition(input) DO
  ASSERT fixedPrompt contains three-element summary instructions
  ASSERT hookMetadata is unchanged (name, version, description, event type, action type)
  ASSERT fixedHookPrompt == fixedRegistryPrompt
END FOR
```

**Testing Approach**: Property-based testing is recommended for preservation checking because:
- It generates many random agent-output strings (without 👉 or WAIT) and verifies the prompt still instructs the three-element summary for all of them
- It catches edge cases where prompt changes might accidentally affect the no-question path
- It provides strong guarantees that hook metadata and registry sync are unchanged

**Test Plan**: Observe behavior on UNFIXED code first for the no-question path and hook metadata, then write property-based tests capturing that behavior. These preservation tests should PASS on both unfixed and fixed code.

**Test Cases**:
1. **Three-element summary preserved**: For any agent output without 👉 or WAIT, verify the prompt still instructs accomplished + files + next step.
2. **Hook metadata unchanged**: Verify name, version, description, event type, action type are identical before and after fix.
3. **Registry sync preserved**: Verify the hook file prompt and registry prompt remain identical after fix.
4. **Hook JSON structure preserved**: Verify the hook file remains valid JSON with all required keys.

### Unit Tests

- Test that the fixed prompt does not contain "re-state the pending question" or equivalent
- Test that the fixed prompt still contains 👉 and WAIT detection instructions
- Test that the fixed prompt still contains all three summary elements for the no-question path
- Test that hook JSON structure and metadata are unchanged

### Property-Based Tests

- Generate random question markers (👉-prefixed strings, WAIT patterns) and verify the fixed prompt does not instruct re-statement for any of them
- Generate random agent outputs without question markers and verify the prompt still instructs the three-element summary
- Generate random agent outputs and verify hook metadata is unchanged regardless of output content

### Integration Tests

- Test full hook file parse → prompt extraction → assertion that pending-question path appends only summary
- Test hook file and registry prompt synchronization after fix
- Test that the hook file remains a valid, loadable hook configuration
