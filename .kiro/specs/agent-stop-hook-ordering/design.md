# Agent Stop Hook Ordering Bugfix Design

## Overview

The `summarize-on-stop` agentStop hook appends a progress summary after the agent's complete output. When that output ends with a pending question (e.g., track selection during onboarding), the summary buries the bootcamper's call-to-action. The fix updates the hook's prompt text — in both the hook definition file and the canonical hook registry — to instruct the agent to detect whether its previous output ended with a pending question and, if so, present the summary before re-stating the question as the last element. This is a prompt-only fix: no event type changes, no new hooks, no code changes.

## Glossary

- **Bug_Condition (C)**: The agent's output ends with a pending question for the bootcamper (identified by `👉` prefix or `WAIT` pattern), causing the summary to appear after the question
- **Property (P)**: When a pending question exists, the summary SHALL appear before the question, and the question SHALL be re-stated as the final element
- **Preservation**: When no pending question exists, the summary SHALL continue to be appended at the end exactly as it does today
- **summarize-on-stop hook**: The `agentStop` hook defined in `senzing-bootcamp/hooks/summarize-on-stop.kiro.hook` that fires when the agent finishes working
- **hook-registry.md**: The canonical hook registry at `senzing-bootcamp/steering/hook-registry.md` that documents all hook definitions for agent consumption
- **Pending question**: A question awaiting bootcamper input, identified by `👉` prefix or a `WAIT` instruction in the steering flow

## Bug Details

### Bug Condition

The bug manifests when the agent finishes a turn whose output ends with a question awaiting the bootcamper's response. The `agentStop` event fires after the agent has already produced its complete output, and the hook's prompt simply says "Before finishing" without instructing the agent to detect or reorder around pending questions. The agent appends the summary at the end, burying the question.

**Formal Specification:**

```
FUNCTION isBugCondition(input)
  INPUT: input of type AgentStopEvent
  OUTPUT: boolean

  LET output = input.agentPreviousOutput
  LET lastContentBlock = extractLastContentBlock(output)

  RETURN lastContentBlock contains "👉" prefix
         OR lastContentBlock contains "WAIT" instruction
         OR lastContentBlock is a question requiring bootcamper input
END FUNCTION
```

### Examples

- **Onboarding track selection**: Agent completes setup, asks "👉 Which track sounds right for you?" — summary appears after the question, bootcamper doesn't know what to respond to
- **Language selection**: Agent presents language options, asks "👉 Which language would you like to use?" — summary block appears below, disrupting the flow
- **Module introduction question**: Agent asks "👉 Does this outline make sense? Any questions before we choose a track?" — summary appended after, burying the call-to-action
- **Edge case — no question**: Agent completes a setup step with no user input needed — summary correctly appears at the end (this is NOT the bug condition)

## Expected Behavior

### Preservation Requirements

**Unchanged Behaviors:**
- When the agent's output does NOT end with a pending question, the summary SHALL continue to be appended at the end of the response
- The summary SHALL continue to include all three elements: (1) what was accomplished, (2) which files were created or modified, (3) what the next step is
- The hook SHALL continue to fire on every `agentStop` event across all modules
- When no pending question exists, "what is the next step" SHALL remain the final element of the summary
- The hook event type SHALL remain `agentStop` — no change to when the hook fires
- The hook action type SHALL remain `askAgent` — no change to how the hook executes

**Scope:**
All agent stops where the previous output does NOT end with a pending question (no `👉` prefix, no `WAIT` pattern) should be completely unaffected by this fix. This includes:
- Completing setup steps with no user input needed
- Finishing file creation or modification tasks
- Completing module transitions where the next action is automatic
- Any turn where the agent's output ends with a statement rather than a question

## Hypothesized Root Cause

Based on the bug description, the root cause is straightforward:

1. **Missing detection instructions**: The hook prompt says "Before finishing, provide a brief summary" but does not instruct the agent to check whether its previous output ended with a pending question. The agent has no reason to look for or reorder around questions.

2. **Missing reordering instructions**: Even if the agent noticed a pending question, the prompt provides no instructions for how to handle it — there's no guidance to present the summary first and re-state the question last.

3. **Implicit append-at-end behavior**: The `agentStop` hook fires after the agent's complete output. Without explicit instructions to the contrary, the agent naturally appends the summary at the end of whatever it already said, which is the default and expected behavior for a hook with no reordering logic.

4. **Two files out of sync risk**: The hook definition (`summarize-on-stop.kiro.hook`) and the hook registry (`hook-registry.md`) both contain the prompt text. Both must be updated to avoid drift.

## Correctness Properties

Property 1: Bug Condition — Summary Before Pending Question

_For any_ agent stop event where the agent's previous output ends with a pending question (identified by `👉` prefix or `WAIT` pattern), the updated hook prompt SHALL instruct the agent to present the progress summary first, then re-state the pending question as the final element of the response, ensuring the bootcamper's call-to-action is never buried beneath the summary.

**Validates: Requirements 2.1, 2.2, 2.3**

Property 2: Preservation — No-Question Turns Unchanged

_For any_ agent stop event where the agent's previous output does NOT end with a pending question, the updated hook prompt SHALL instruct the agent to append the summary at the end of the response exactly as before, preserving the original three-element structure (accomplished, files changed, next step) with "next step" as the final element.

**Validates: Requirements 3.1, 3.2, 3.3, 3.4**

## Fix Implementation

### Changes Required

The fix is prompt-only — updating the natural language instructions in two files so they match.

**File 1**: `senzing-bootcamp/hooks/summarize-on-stop.kiro.hook`

**Field**: `then.prompt`

**Specific Changes**:
1. **Add pending question detection**: Instruct the agent to check if its previous output ended with a pending question, identified by `👉` prefix or `WAIT for response` pattern
2. **Add conditional reordering**: If a pending question is detected, instruct the agent to present the summary first (what was accomplished, files changed), then re-state the pending question as the very last element
3. **Preserve default behavior**: If no pending question is detected, instruct the agent to append the summary at the end as usual (what was accomplished, files changed, next step)
4. **Keep all three summary elements**: The prompt must still require (1) what was accomplished, (2) files created/modified, (3) next step or re-stated question

**File 2**: `senzing-bootcamp/steering/hook-registry.md`

**Section**: `summarize-on-stop` entry under Critical Hooks

**Specific Changes**:
1. **Update the Prompt field**: Replace the existing prompt text with the same updated prompt from File 1, ensuring both files stay in sync
2. **No other fields change**: The `id`, `name`, `description`, event type (`agentStop`), and action type (`askAgent`) all remain unchanged

## Testing Strategy

### Validation Approach

The testing strategy follows a two-phase approach: first, surface counterexamples that demonstrate the bug on unfixed prompt text, then verify the fix works correctly and preserves existing behavior. Since this is a prompt-only fix, testing focuses on verifying the prompt text contains the correct instructions rather than executing agent behavior.

### Exploratory Bug Condition Checking

**Goal**: Surface counterexamples that demonstrate the bug BEFORE implementing the fix. Confirm or refute the root cause analysis. If we refute, we will need to re-hypothesize.

**Test Plan**: Examine the current (unfixed) prompt text in both files and verify it lacks pending-question detection and reordering instructions. Run these checks on the UNFIXED files to confirm the root cause.

**Test Cases**:
1. **Missing detection test**: Verify the current prompt does NOT contain instructions to detect `👉` prefix or `WAIT` pattern (will confirm bug on unfixed prompt)
2. **Missing reordering test**: Verify the current prompt does NOT contain instructions to present summary before a pending question (will confirm bug on unfixed prompt)
3. **Append-only behavior test**: Verify the current prompt only instructs appending a summary, with no conditional logic (will confirm bug on unfixed prompt)
4. **Registry sync test**: Verify the hook file and registry have matching prompt text (baseline check)

**Expected Counterexamples**:
- The prompt text contains no mention of `👉`, `WAIT`, "pending question", or "reorder"
- Possible causes confirmed: missing detection instructions, missing reordering instructions

### Fix Checking

**Goal**: Verify that for all inputs where the bug condition holds, the fixed prompt produces the expected behavior.

**Pseudocode:**

```
FOR ALL input WHERE isBugCondition(input) DO
  result := parsePromptInstructions(fixedPrompt)
  ASSERT result contains pending question detection logic
    AND result contains reordering instructions (summary before question)
    AND result specifies question as final element
END FOR
```

### Preservation Checking

**Goal**: Verify that for all inputs where the bug condition does NOT hold, the fixed prompt produces the same result as the original prompt.

**Pseudocode:**

```
FOR ALL input WHERE NOT isBugCondition(input) DO
  ASSERT parsePromptBehavior(originalPrompt, input) = parsePromptBehavior(fixedPrompt, input)
END FOR
```

**Testing Approach**: Property-based testing is recommended for preservation checking because:
- It can generate many variations of non-question agent output to verify the prompt handles them all the same way
- It catches edge cases where output might be ambiguously interpreted as a question
- It provides strong guarantees that the no-question path is unchanged

**Test Plan**: Observe behavior on UNFIXED prompt first for non-question agent outputs, then write property-based tests capturing that behavior.

**Test Cases**:
1. **No-question summary preservation**: Verify that when agent output has no `👉` or `WAIT`, the prompt still instructs the standard three-element summary appended at end
2. **Three-element completeness**: Verify the fixed prompt still requires all three summary elements (accomplished, files, next step)
3. **Hook metadata preservation**: Verify the hook event type (`agentStop`), action type (`askAgent`), name, and description are unchanged
4. **Registry-hook sync**: Verify the prompt text in `hook-registry.md` matches the prompt in `summarize-on-stop.kiro.hook` after the fix

### Unit Tests

- Verify the fixed prompt text contains `👉` detection instructions
- Verify the fixed prompt text contains `WAIT` pattern detection instructions
- Verify the fixed prompt text contains conditional reordering logic
- Verify the fixed prompt text preserves all three summary elements
- Verify the hook JSON structure is valid after the fix

### Property-Based Tests

- Generate random agent output strings without question markers and verify the prompt's no-question path applies
- Generate random agent output strings with `👉` prefix at various positions and verify the prompt's reordering path applies
- Generate variations of question patterns (with/without `WAIT`, with/without `👉`) to test detection boundary

### Integration Tests

- Verify both files (`summarize-on-stop.kiro.hook` and `hook-registry.md`) contain identical prompt text after the fix
- Verify the hook file is valid JSON after the fix
- Verify the hook registry markdown is well-formed after the fix
