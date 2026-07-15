# Onboarding Gate-to-Language Handoff Bugfix Design

## Overview

During onboarding Step 3 (entity-resolution-intro), the `ask-bootcamper` hook's Phase 1 closing question previews "picking your programming language" even though the mandatory gate hasn't been cleared and that question hasn't been presented. Additionally, when the bootcamper signals readiness to move on from the gate, the system may re-present the same gate instead of transitioning to Step 4 (programming language selection). The fix adds a gate-awareness constraint to Phase 1 of the hook and clarifies the routing path in the steering file so readiness signals at the gate immediately advance the flow.

## Glossary

- **Bug_Condition (C)**: The condition where the `ask-bootcamper` hook fires at a mandatory gate (⛔) and Phase 1 generates a closing question that references specific content from a subsequent step that has not yet been presented
- **Property (P)**: When a mandatory gate is active, the hook's closing question keeps forward-looking references generic and does not name specific upcoming questions; when the bootcamper signals readiness at the gate, the agent immediately transitions to the next step
- **Preservation**: Existing Phase 1 behavior for non-gate steps, existing follow-up question handling at gates, and existing hook behavior when no mandatory gate is active must remain unchanged
- **ask-bootcamper hook**: The Stop-trigger hook in `senzing-bootcamp/hooks/ask-bootcamper.json` that generates contextual closing questions via Phase 1
- **Mandatory gate**: A step marked with ⛔ where the agent MUST stop and wait for real user input before proceeding (e.g., entity-resolution-intro exploration gate, programming language selection gate)
- **Phase 1 (Closing_Question_Phase)**: The section of the `ask-bootcamper` hook that generates a contextual recap and closing question when conditions are met
- **onboarding-phase1b-intro-language.md**: The steering file governing Steps 3–5b, covering entity resolution introduction and language selection

## Bug Details

### Bug Condition

The bug manifests in two related scenarios:
1. The `ask-bootcamper` hook fires on Stop at the entity-resolution-intro mandatory gate (Step 3) and Phase 1 generates a closing question that references "picking your programming language" — a specific question from Step 4 that hasn't been presented.
2. When the bootcamper signals readiness to move on from the entity-resolution-intro gate, the agent re-presents the same gate content instead of transitioning to Step 4 (programming language selection).

**Formal Specification:**
```
FUNCTION isBugCondition(input)
  INPUT: input of type HookFireEvent
  OUTPUT: boolean
  
  -- Scenario 1: Hook previews upcoming gate-locked content
  scenario1 := input.trigger == "Stop"
               AND currentStepHasMandatoryGate()
               AND mandatoryGateNotCleared()
               AND phase1ClosingQuestionReferencesSpecificUpcomingContent()
  
  -- Scenario 2: Readiness signal doesn't advance past gate
  scenario2 := input.trigger == "UserPromptSubmit"
               AND currentStepHasMandatoryGate()
               AND bootcamperSignaledReadiness(input.userMessage)
               AND agentResponseRePresentsCurrentGate()
  
  RETURN scenario1 OR scenario2
END FUNCTION
```

### Examples

- **Example 1 (Scenario 1)**: Bootcamper is at the entity-resolution-intro gate (Step 3). The agent presents the ER content and stops at the ⛔ gate. The `ask-bootcamper` hook fires and Phase 1 outputs: "👉 Ready to move on to picking your programming language?" — This previews Step 4's specific question content while the gate hasn't been cleared.
- **Example 2 (Scenario 1)**: Same context, but Phase 1 outputs: "👉 Next up we'll be choosing your programming language — any questions about entity resolution first?" — Again previews Step 4 content.
- **Example 3 (Scenario 2)**: Bootcamper responds "ready" or "let's continue" at the entity-resolution-intro gate. Instead of transitioning to Step 4 (programming language selection), the agent re-presents the gate: "Before we move on, this is a good moment to dig deeper..."
- **Example 4 (Expected edge case)**: Bootcamper asks a follow-up question at the gate (e.g., "How does Senzing match records without rules?"). The agent answers the question and re-presents the gate. This is CORRECT behavior that must be preserved.

## Expected Behavior

### Preservation Requirements

**Unchanged Behaviors:**
- Phase 1 closing questions after non-gate steps that have been completed may still reference upcoming content naturally (Requirement 3.1)
- Follow-up questions at the entity-resolution-intro gate are still answered via search_docs and the gate is re-presented (Requirement 3.2)
- When no mandatory gate is active, the hook continues to produce contextual recaps and closing questions with full session context awareness (Requirement 3.3)
- Non-gate step transitions continue to follow the existing steering flow (Requirement 3.4)
- When `config/.question_pending` exists, Phase 1 output continues to be suppressed (Requirement 3.5)

**Scope:**
All inputs that do NOT involve (a) a Phase 1 closing question while a mandatory gate is active or (b) a readiness signal at the entity-resolution-intro gate should be completely unaffected by this fix. This includes:
- Phase 1 behavior at non-gate steps
- Phase 2, 3, and 4 hook behavior (unchanged)
- Mouse/keyboard interactions unrelated to the hook
- All other steering file routing logic

## Hypothesized Root Cause

Based on the bug description, the most likely issues are:

1. **Missing gate-awareness constraint in Phase 1**: The `ask-bootcamper` hook's Phase 1 (Closing_Question_Phase) has no instruction to suppress or genericize forward-looking references when a mandatory gate is active. Phase 1 sees the full session context including loaded steering for upcoming steps and naturally generates a closing question that previews them. The hook prompt needs an additional constraint: "When the current step contains a mandatory gate (⛔) that has not been cleared, any forward-looking references in the closing question MUST remain generic (e.g., 'we'll continue setup') and MUST NOT name or preview specific questions from subsequent steps."

2. **Ambiguous routing in onboarding-phase1b-intro-language.md**: The steering file for Steps 3–5b uses a `#[[file:]]` reference to load entity-resolution-intro.md at Step 3, but there is no explicit routing instruction that says "when the bootcamper signals readiness at the entity-resolution-intro gate, proceed directly to Step 4." The agent may interpret re-loading the same steering as a signal to re-present the gate rather than advance.

3. **Gate clearance signal not explicitly documented**: The entity-resolution-intro.md file's gate section describes handling rules (answer follow-ups, allow flow to continue on readiness signal), but the parent steering file (`onboarding-phase1b-intro-language.md`) lacks a matching explicit transition directive that connects the gate-clearance event to Step 4 execution.

4. **Phase 1 context leakage**: Because the steering files for Steps 3–5b are loaded together (`onboarding-phase1b-intro-language.md` contains both Step 3 and Step 4), Phase 1 of the hook can "see" Step 4's content (programming language selection) and incorporates it into the closing question, even though Step 3's gate hasn't been cleared yet.

## Correctness Properties

Property 1: Bug Condition - Gate-Active Closing Question Genericization

_For any_ Stop trigger where the current step has an active mandatory gate (⛔) that has not been cleared, the `ask-bootcamper` hook's Phase 1 closing question SHALL keep any forward-looking references generic (e.g., "we'll continue setup," "we'll move on to the next step") and SHALL NOT name, preview, or reference specific content from any subsequent step.

**Validates: Requirements 2.1, 2.3**

Property 2: Bug Condition - Gate-to-Step-4 Transition

_For any_ user input at the entity-resolution-intro mandatory gate where the bootcamper signals readiness to proceed (e.g., "ready," "let's go," "continue," "next"), the agent SHALL immediately transition to Step 4 (programming language selection) without re-presenting the entity-resolution-intro gate content.

**Validates: Requirements 2.2**

Property 3: Preservation - Non-Gate Phase 1 Behavior

_For any_ Stop trigger where no mandatory gate is active in the current step, the `ask-bootcamper` hook's Phase 1 SHALL continue to produce contextual closing questions with full awareness of session context, including natural references to upcoming content, preserving all existing non-gate closing question behavior.

**Validates: Requirements 3.1, 3.3**

Property 4: Preservation - Gate Follow-Up Question Handling

_For any_ user input at the entity-resolution-intro mandatory gate where the bootcamper asks a follow-up question (not a readiness signal), the agent SHALL answer the question using search_docs and re-present the gate, preserving existing follow-up handling behavior.

**Validates: Requirements 3.2**

## Fix Implementation

### Changes Required

Assuming our root cause analysis is correct:

**File**: `senzing-bootcamp/hooks/ask-bootcamper.json`

**Section**: Phase 1 (Closing_Question_Phase) prompt text

**Specific Changes**:
1. **Add gate-awareness constraint to Phase 1**: Insert a new condition check at the beginning of Phase 1's "SECOND — Recap and closing question" block. Before generating the closing question, the hook must detect whether the current step contains an active mandatory gate (⛔) that has not been cleared. Detection criteria: the most recent assistant message contains "⛔ **MANDATORY GATE**" AND the assistant message contains "🛑 **STOP" — indicating the gate was just presented and is awaiting bootcamper input.

2. **Define generic phrasing rule**: When a mandatory gate is detected as active, add the constraint: "Your closing question MUST NOT name, preview, or reference specific content from any step beyond the current gate. Use generic forward-looking language only, such as 'we'll continue when you're ready' or 'we'll move on to the next setup step.' Do NOT mention programming language selection, track selection, or any other specific upcoming topic."

3. **Preserve existing Phase 1 logic for non-gate contexts**: The gate-awareness check is an additional filter that only constrains the closing question content when a gate is active. All other Phase 1 conditions and behavior remain untouched.

---

**File**: `senzing-bootcamp/steering/onboarding-phase1b-intro-language.md`

**Section**: Between Step 3 (Entity Resolution Introduction) and Step 4 (Programming Language Selection)

**Specific Changes**:
4. **Add explicit transition directive after Step 3**: Insert a clear routing instruction between the `#[[file:]]` reference and Step 4 that tells the agent: "When the bootcamper signals readiness to proceed at the entity-resolution-intro mandatory gate (words like 'ready,' 'let's go,' 'continue,' 'next,' or similar acknowledgments), immediately proceed to Step 4 below. Do NOT re-present the entity-resolution-intro content or the gate question."

5. **Add readiness-signal recognition guidance**: Include a brief list of readiness-signal patterns the agent should recognize as gate-clearance: acknowledgments ("ready," "got it," "let's go," "continue," "next," "move on"), affirmative responses ("yes," "sure," "yep"), and forward-looking statements ("what's next," "let's keep going"). Contrast with follow-up questions, which should still trigger the answer-then-re-present-gate flow.

## Testing Strategy

### Validation Approach

The testing strategy follows a two-phase approach: first, surface counterexamples that demonstrate the bug on unfixed code, then verify the fix works correctly and preserves existing behavior.

### Exploratory Bug Condition Checking

**Goal**: Surface counterexamples that demonstrate the bug BEFORE implementing the fix. Confirm or refute the root cause analysis. If we refute, we will need to re-hypothesize.

**Test Plan**: Simulate the hook firing at the entity-resolution-intro gate and inspect Phase 1 output for specific upcoming-step references. Also simulate readiness signals at the gate and verify whether the agent transitions or re-presents.

**Test Cases**:
1. **Phase 1 Preview Leak Test**: Simulate Phase 1 firing after the entity-resolution-intro gate is presented. Check if the closing question contains "programming language," "language selection," or other Step 4-specific content (will fail on unfixed code — hook will preview Step 4)
2. **Gate Re-Presentation Test**: Simulate the bootcamper sending "ready" at the entity-resolution-intro gate. Check if the agent response contains the gate content again instead of Step 4's language question (will fail on unfixed code — agent may re-present gate)
3. **Multiple Readiness Signals Test**: Test with variations ("let's go," "continue," "next," "I'm ready to move on"). Verify each triggers transition to Step 4 (may fail on unfixed code)
4. **Ambiguous Response Test**: Simulate the bootcamper sending "interesting" (ambiguous — could be acknowledgment or follow-up). Verify behavior is consistent (may reveal edge case in unfixed code)

**Expected Counterexamples**:
- Phase 1 closing question references "programming language" or "language selection" while gate is active
- Possible causes: no gate-awareness constraint in Phase 1, steering context leakage from loaded Step 4 content

### Fix Checking

**Goal**: Verify that for all inputs where the bug condition holds, the fixed function produces the expected behavior.

**Pseudocode:**
```
FOR ALL input WHERE isBugCondition(input) DO
  IF input.scenario == "phase1_preview_leak" THEN
    result := askBootcamperHook_fixed(input)
    ASSERT NOT containsSpecificUpcomingContent(result.phase1Output)
    ASSERT isGenericForwardReference(result.phase1Output) OR result.phase1Output == none
  END IF
  
  IF input.scenario == "gate_transition_failure" THEN
    result := processReadinessSignal_fixed(input)
    ASSERT result.nextStep == "Step 4: Programming Language Selection"
    ASSERT NOT containsGateRePresentation(result.agentResponse)
  END IF
END FOR
```

### Preservation Checking

**Goal**: Verify that for all inputs where the bug condition does NOT hold, the fixed function produces the same result as the original function.

**Pseudocode:**
```
FOR ALL input WHERE NOT isBugCondition(input) DO
  ASSERT askBootcamperHook_original(input) = askBootcamperHook_fixed(input)
END FOR
```

**Testing Approach**: Property-based testing is recommended for preservation checking because:
- It generates many test cases automatically across the input domain (various non-gate steps, various Phase 1 conditions)
- It catches edge cases that manual unit tests might miss (e.g., steps that mention "gate" but aren't mandatory gates)
- It provides strong guarantees that behavior is unchanged for all non-buggy inputs

**Test Plan**: Observe behavior on UNFIXED code first for non-gate hook firings and follow-up question handling at gates, then write property-based tests capturing that behavior.

**Test Cases**:
1. **Non-Gate Phase 1 Preservation**: Verify that Phase 1 closing questions after completed non-gate steps continue to reference upcoming content naturally (e.g., after Step 2 prerequisite check completes, Phase 1 can still mention "entity resolution")
2. **Follow-Up Question Preservation**: Verify that follow-up questions at the entity-resolution-intro gate are still answered via search_docs and the gate is re-presented
3. **Question Pending Suppression Preservation**: Verify that when `config/.question_pending` exists, Phase 1 output is still suppressed regardless of gate status
4. **Non-Gate Transition Preservation**: Verify that transitions between non-gate steps continue to follow the existing steering flow without interference from the new gate-awareness logic

### Unit Tests

- Test Phase 1 gate detection logic: verify the hook correctly identifies when a mandatory gate is active from the assistant message content
- Test generic phrasing enforcement: verify that when gate is detected, closing questions do not contain Step 4-specific terms
- Test readiness signal recognition: verify "ready," "let's go," "continue," "next" are correctly identified as gate-clearance signals
- Test follow-up question detection: verify that actual questions ("How does Senzing match?") are NOT treated as readiness signals

### Property-Based Tests

- Generate random session contexts (with and without active gates) and verify Phase 1 closing questions only contain specific upcoming references when no gate is active
- Generate random bootcamper messages at the entity-resolution-intro gate and verify correct classification as readiness signal vs. follow-up question
- Generate random non-gate step contexts and verify Phase 1 behavior is unchanged from the original hook

### Integration Tests

- Test full onboarding flow from Step 3 gate presentation through readiness signal to Step 4 language question appearance
- Test that the hook fires correctly at the gate and produces a generic closing question
- Test that follow-up questions at the gate cycle correctly (answer → re-present gate) without triggering premature transition
