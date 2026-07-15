# Stop-Hook UX Bugfix Design

## Overview

Two UX defects plague the Stop-hook system: (1) the bootcamper sees two Stop-hook labels in the
UI ("to wait for your answer" and "to append module recap on completion") even though only one
ever waits for input, and (2) when the `ask-bootcamper` hook's phases all evaluate to no output,
the agent leaks internal narration instead of emitting the silent "." response.

The fix consolidates the recap-append logic into a new Phase 0 inside `ask-bootcamper.json`,
deletes `module-recap-append.json` as a standalone hook, and strengthens the OUTPUT RULES
preamble so the agent never explains why it produced no output. After consolidation, only one
Stop hook ("to wait for your answer") surfaces in the UI on every agent stop, and the
no-output path reliably produces ".".

## Glossary

- **Bug_Condition (C)**: A Stop event where either (a) the second "to append module recap on
  completion" hook surfaces in the UI, or (b) the `ask-bootcamper` hook's phases all produce
  no output yet the agent emits narration instead of ".".
- **Property (P)**: Under C(X), the bootcamper sees exactly one "waiting for your answer" Stop
  hook label, and a no-output turn produces only ".".
- **Preservation**: All existing recap-capture behavior, precedence ordering, answer processing,
  celebration, gate enforcement, and silent-turn contracts remain unchanged.
- **ask-bootcamper**: The Stop hook in `hooks/ask-bootcamper.json` that owns answer-processing
  and closing questions; absolute precedence (order 1).
- **module-recap-append**: The Stop hook in `hooks/module-recap-append.json` that captures
  structured recap on module completion (order 2).
- **agentstop_order**: The precedence list in `hooks/hook-categories.yaml` that determines
  the firing sequence of Stop-triggered hooks.
- **hooks.lock.yaml**: The auto-generated registry listing all hooks with their category and
  event type.

## Bug Details

### Bug Condition

The bug manifests on every Stop event. Two distinct UI-visible hooks fire, causing visual
clutter. Additionally, on turns where all four phases of `ask-bootcamper` produce no output,
the agent's response includes explanatory narration instead of the contractual ".".

**Formal Specification:**
```
FUNCTION isBugCondition(input)
  INPUT: input of type StopEvent
  OUTPUT: boolean

  LET hooks_surfaced = countVisibleStopHooks(input.hookRegistry)
  LET ask_output = evaluateAskBootcamper(input.sessionContext)

  RETURN hooks_surfaced > 1
         OR (ask_output.allPhasesNoOutput AND ask_output.responseText != ".")
END FUNCTION
```

### Examples

- **Example 1 (dual hooks)**: Agent stops after answering a question. UI shows both "to wait
  for your answer" and "to append module recap on completion". No module was completed this
  turn, so the second hook produces no visible content but still surfaces as a UI label.
  *Expected:* Only "to wait for your answer" appears.

- **Example 2 (narration leak)**: Agent stops. The last message already contains a 👉
  question (Phase 1 skipped), no sequencing violation (Phase 2 skipped), no Senzing content
  (Phase 3 skipped), no compound question (Phase 4 skipped). All phases = no output.
  Agent responds: "My last message ends with a 👉 question, and no module was completed."
  *Expected:* Agent responds with exactly ".".

- **Example 3 (module completion)**: Agent stops after module 2 is completed. Recap logic
  runs, then celebration fires. Two hook labels are surfaced.
  *Expected:* Only "to wait for your answer" surfaces; recap logic executes internally as
  a phase of that single hook.

- **Edge case (question_pending + module completion)**: Agent stops with `config/.question_pending`
  existing and a module just completed. Both recap and answer processing should defer.
  *Expected:* Single hook surfaces, recap defers (no append), answer processing defers.

## Expected Behavior

### Preservation Requirements

**Unchanged Behaviors:**
- When a module is completed, the structured recap section (heading, Q&R, actions, journal)
  is still appended to `docs/bootcamp_recap.md` with the same format and content.
- The recap capture still defers to a pending 👉 question (`config/.question_pending` exists).
- The recap capture still runs before `module-completion-celebration` in logical order.
- All four phases of `ask-bootcamper` (Closing Question, Step Sequencing, MCP-First,
  Question Format) continue to function identically.
- Stop hooks 3–6 (`module-completion-celebration`, `enforce-gate-on-stop`,
  `enforce-visualization-offers`, `enforce-critical-artifacts`) continue to fire unchanged.
- The "." silent-turn contract for all other Stop hooks remains untouched.
- `preToolUse` write-gate hooks are not altered in any way.
- Mouse/keyboard inputs, tool invocations, and all non-Stop triggers are unaffected.

**Scope:**
All inputs where `isBugCondition(input)` is false should be completely unaffected by this fix.
This includes:
- Turns where `ask-bootcamper` produces substantive output (Phase 1 closing question, Phase 2
  violation, Phase 3 MCP correction, or Phase 4 rewrite)
- Turns where no module was completed (recap phase is a no-op)
- Operation of all non-Stop hooks (PostFileSave, PreToolUse, UserPromptSubmit, etc.)

## Hypothesized Root Cause

Based on the bug description, the most likely issues are:

1. **Separate Hook Files Surface Separate UI Labels**: The Kiro hook framework surfaces one
   UI label per Stop-triggered hook file, regardless of whether that hook produces visible
   output. Having `module-recap-append.json` as a standalone file means it always appears as
   a second label in the UI even when it does nothing.

2. **Insufficient Negative Instruction in OUTPUT RULES**: The `ask-bootcamper` prompt says
   "If ALL phases produced no output, your COMPLETE response is a single period character: ."
   but does not explicitly prohibit explaining why each phase was skipped. The LLM interprets
   silence on each phase as an invitation to narrate the no-op reasoning.

3. **Missing Reinforcement at Phase Boundaries**: Each phase says "Phase N output is none"
   but doesn't reiterate that "none" means literally zero tokens — the LLM may still emit a
   sentence justifying the skip before checking the final OUTPUT RULES.

4. **No Negative Examples in Prompt**: The prompt lacks explicit "DO NOT output" examples
   showing the narration pattern to avoid, making it easier for the LLM to drift into
   explanatory mode.

## Correctness Properties

Property 1: Bug Condition - Single Stop Hook Visibility and Silent Turn

_For any_ Stop event where the bug condition holds (isBugCondition returns true), the fixed
hook system SHALL surface exactly one "to wait for your answer" Stop hook label to the
bootcamper, AND when all phases of `ask-bootcamper` evaluate to no output, the hook's
response SHALL be exactly "." with no additional text, narration, or explanation.

**Validates: Requirements 2.1, 2.2, 2.3**

Property 2: Preservation - Recap Capture and Hook Behavior

_For any_ Stop event where the bug condition does NOT hold (isBugCondition returns false),
the fixed system SHALL produce the same result as the original system: recap sections are
appended to `docs/bootcamp_recap.md` on module completion with identical format, precedence
ordering is maintained, answer processing runs unchanged, and all other Stop hooks fire with
their existing behavior preserved.

**Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7**

## Fix Implementation

### Changes Required

Assuming our root cause analysis is correct:

**File**: `senzing-bootcamp/hooks/ask-bootcamper.json`

**Changes**:
1. **Add Phase 0 (Module Recap Append)**: Insert the entire `module-recap-append` prompt
   logic as a new "Phase 0" at the top of the `ask-bootcamper` hook, before the existing
   Phase 1. This phase:
   - Checks boundary detection (`modules_completed` changed)
   - If no new module completed: Phase 0 output is none (no-op)
   - If module completed: Runs the full recap-append workflow (gather content, compute
     duration, append to `docs/bootcamp_recap.md`, verify/backfill)
   - Preserves the `config/.question_pending` deferral check at the top

2. **Strengthen OUTPUT RULES preamble**: Add explicit negative examples and reinforce:
   ```
   DEFAULT OUTPUT: .
   If ALL phases below produce no output, your COMPLETE response is a single period character: .
   Do NOT explain your reasoning. Do NOT describe condition checks. Do NOT narrate which
   phases were evaluated. Do NOT output phrases like "My last message ends with..." or
   "No module was completed" or "Phase N silenced" or any variation. NEVER explain WHY
   you are outputting a period. Just output: .

   NEGATIVE EXAMPLES (NEVER produce output like these):
   ✗ "My last message ends with a 👉 question, and no module was completed."
   ✗ "Phase 1 was silenced because a question is already pending."
   ✗ "No phases produced output, so responding with a period."
   ✗ "All conditions checked — no action needed."
   The ONLY acceptable no-output response is the literal single character: .
   ```

3. **Renumber existing phases**: Phase 1 → Phase 1 (unchanged), Phase 2 → Phase 2, etc.
   (The new Phase 0 is prepended, existing phases keep their numbers.)

4. **Preserve Phase 0 constraints**: The recap phase inherits the same constraints as the
   original `module-recap-append` hook — all timestamps ISO 8601, no secrets, byte-for-byte
   preservation of existing content, duration from planner only.

**File**: `senzing-bootcamp/hooks/module-recap-append.json`

**Change**: Delete this file. Its logic now lives inside `ask-bootcamper.json` as Phase 0.

**File**: `senzing-bootcamp/hooks/hook-categories.yaml`

**Changes**:
1. Remove `module-recap-append` from the `any` list under `modules:`
2. Remove the `module-recap-append` entry from `agentstop_order`
3. Renumber remaining `agentstop_order` entries:
   - `ask-bootcamper` → order 1 (unchanged; now internally handles recap at Phase 0)
   - `module-completion-celebration` → order 2 (was 3)
   - `enforce-gate-on-stop` → order 3 (was 4)
   - `enforce-visualization-offers` → order 4 (was 5)
   - `enforce-critical-artifacts` → order 5 (was 6)

**File**: `senzing-bootcamp/hooks/hooks.lock.yaml`

**Change**: Regenerate by running `python3 senzing-bootcamp/scripts/sync_hook_registry.py --write`
after the above changes. This removes the `module-recap-append` entry from the lock file.

**File**: `senzing-bootcamp/hooks/module-completion-celebration.json`

**Change**: No functional change. The prompt already says "produce no output at all — defer to
`ask-bootcamper`" when `.question_pending` exists. It continues to detect boundary changes in
`modules_completed`. Its relative ordering (now order 2) still fires after recap logic completes
inside `ask-bootcamper`.

## Testing Strategy

### Validation Approach

The testing strategy follows a two-phase approach: first, surface counterexamples that
demonstrate the bug on unfixed code, then verify the fix works correctly and preserves
existing behavior.

### Exploratory Bug Condition Checking

**Goal**: Surface counterexamples that demonstrate the bug BEFORE implementing the fix.
Confirm or refute the root cause analysis. If we refute, we will need to re-hypothesize.

**Test Plan**: Write tests that inspect the hook registry to count visible Stop hooks, and
simulate the `ask-bootcamper` prompt's output path when all phases produce no output. Run
these tests on the UNFIXED code to observe failures.

**Test Cases**:
1. **Dual Hook Visibility Test**: Assert that `hook-categories.yaml` `agentstop_order`
   contains only one hook whose `name` in its JSON file starts with "to wait" or "to
   append" — count of UI-surfaced Stop hooks with user-facing labels (will fail on
   unfixed code because two exist).
2. **No-Output Narration Test**: Simulate a session context where Phase 1–4 all produce
   no output. Assert the prompt's OUTPUT RULES produce exactly "." and no other text
   (will fail on unfixed code due to weak preamble).
3. **Module Completion Recap Test**: Simulate a module completion boundary. Assert that
   the recap logic runs and appends to `docs/bootcamp_recap.md` (will pass on unfixed
   code — baseline for preservation).
4. **Question Pending Deferral Test**: Set `config/.question_pending` to exist. Assert
   that recap logic defers (produces no output) (will pass on unfixed code — baseline).

**Expected Counterexamples**:
- Two Stop hooks surface distinct UI labels even when only one produces output
- The no-output path produces explanatory narration instead of "."
- Possible causes: separate hook file = separate UI label; weak negative instruction

### Fix Checking

**Goal**: Verify that for all inputs where the bug condition holds, the fixed function produces the expected behavior.

**Pseudocode:**
```
FOR ALL input WHERE isBugCondition(input) DO
  hookFiles := listStopTriggerHookFiles(input.hooksDir)
  ASSERT countUserFacingHookLabels(hookFiles) == 1
  
  IF allPhasesNoOutput(input.sessionContext) THEN
    result := evaluateAskBootcamperPrompt(input.sessionContext)
    ASSERT result == "."
  END IF
END FOR
```

### Preservation Checking

**Goal**: Verify that for all inputs where the bug condition does NOT hold, the fixed function produces the same result as the original function.

**Pseudocode:**
```
FOR ALL input WHERE NOT isBugCondition(input) DO
  ASSERT recapContent_fixed(input) == recapContent_original(input)
  ASSERT hookFiringOrder_fixed(input) == hookFiringOrder_original(input)
  ASSERT askBootcamperOutput_fixed(input) == askBootcamperOutput_original(input)
END FOR
```

**Testing Approach**: Property-based testing is recommended for preservation checking because:
- It generates many session-context configurations automatically
- It catches edge cases in the recap append logic that manual tests might miss
- It provides strong guarantees that the consolidated Phase 0 produces byte-identical
  output to the original standalone hook across all non-buggy inputs

**Test Plan**: Observe behavior on UNFIXED code first for module completions, question-pending
states, and normal turn endings, then write property-based tests capturing that behavior.

**Test Cases**:
1. **Recap Format Preservation**: Verify that for any module completion event, the appended
   section in `docs/bootcamp_recap.md` has identical format (headings, Q&R pairs, actions,
   journal) after consolidation.
2. **Deferral Preservation**: Verify that when `config/.question_pending` exists, the recap
   phase produces no output (same as before).
3. **Precedence Preservation**: Verify that recap logic completes before celebration fires,
   and all hooks still defer to `ask-bootcamper` when a question is pending.
4. **Other Hook Preservation**: Verify that `enforce-gate-on-stop`,
   `enforce-visualization-offers`, and `enforce-critical-artifacts` continue to fire with
   unchanged behavior and ordering.
5. **Silent-Turn Preservation**: Verify that Stop hooks other than `ask-bootcamper` still
   honor "." when they have nothing to output.

### Unit Tests

- Test that `hook-categories.yaml` after fix contains exactly 5 entries in `agentstop_order`
  (down from 6) and `module-recap-append` is absent.
- Test that `hooks.lock.yaml` after regeneration does not contain `module-recap-append`.
- Test that `ask-bootcamper.json` prompt contains "Phase 0" or "PHASE 0" section header.
- Test that the OUTPUT RULES section contains negative examples.
- Test that the recap-append constraints (ISO 8601, no secrets, planner-only durations) are
  present in the consolidated prompt.

### Property-Based Tests

- Generate random `bootcamp_progress.json` states (varying `modules_completed` arrays) and
  verify the Phase 0 boundary detection produces recap output if and only if a new module
  number was added.
- Generate random session contexts with various Phase 1–4 evaluations and verify the output
  is either substantive content or exactly "." — never narration.
- Generate random `agentstop_order` configurations and verify the ordering invariant
  (recap before celebration, celebration before gate) is maintained after renumbering.

### Integration Tests

- Full end-to-end: simulate an agent stop with a module just completed. Verify single hook
  surfaces, recap is appended, and celebration fires afterward.
- Full end-to-end: simulate an agent stop with no module completed and no pending question.
  Verify single hook surfaces, no recap is appended, output is ".".
- Full end-to-end: simulate an agent stop with `.question_pending` existing. Verify single
  hook surfaces, all phases defer, output is ".".
