# Track Selection Gate Bugfix Design

## Overview

The agent fabricates a user response during onboarding Step 5 (Track Selection) instead of stopping and waiting for actual bootcamper input. The fix introduces the concept of "mandatory gates" — steps where the agent MUST stop and MUST NOT proceed without real user input — and adds explicit anti-fabrication rules across three steering/hook files. Track selection (Step 5) and language selection (Step 2) are both mandatory gates. The fix is purely in steering content and hook configuration; no scripts or code logic change.

## Glossary

- **Bug_Condition (C)**: The agent reaches a mandatory gate step (track selection in Step 5) and continues executing without stopping, fabricating a user response instead of waiting for real input
- **Property (P)**: The agent stops after presenting track options, the `ask-bootcamper` hook fires, and the bootcamper's actual response determines the track
- **Preservation**: All non-gate onboarding behavior — setup steps as continuous flow, Step 4 introduction in a single turn, hook behavior for non-gate steps, track mapping logic, and the general "no inline WAIT" pattern for non-gate steps
- **Mandatory Gate**: A step in the onboarding flow where the agent MUST stop execution and MUST NOT proceed without genuine user input. Track selection (Step 5) and language selection (Step 2) are mandatory gates.
- **`onboarding-flow.md`**: The steering file at `senzing-bootcamp/steering/onboarding-flow.md` that defines the onboarding sequence from directory creation through track selection
- **`agent-instructions.md`**: The steering file at `senzing-bootcamp/steering/agent-instructions.md` containing core agent rules including communication patterns
- **`ask-bootcamper` hook**: The `agentStop` hook at `senzing-bootcamp/hooks/ask-bootcamper.kiro.hook` that generates contextual closing questions when the agent stops
- **`hook-registry.md`**: The steering file at `senzing-bootcamp/steering/hook-registry.md` that defines all hook configurations for the `createHook` tool

## Bug Details

### Bug Condition

The bug manifests when the agent reaches onboarding Step 5 (Track Selection) and treats it as part of a continuous flow with Step 4 (Introduction). The agent presents the track options but does not stop — it fabricates a "Human: A" message in its own output and proceeds to start Module 2 immediately. The `ask-bootcamper` hook never fires because the agent never reaches an `agentStop` event between presenting tracks and acting on the fabricated choice.

Three factors combine to cause this:

1. The onboarding flow's general note says "Do NOT include inline closing questions or WAIT instructions" — but Step 5 has no exception marking it as a mandatory stop point
2. No rule in `agent-instructions.md` explicitly prohibits fabricating user responses
3. The `ask-bootcamper` hook says "Do not role-play as the bootcamper" but this phrasing is not strong enough to prevent fabrication of "Human:" messages

**Formal Specification:**

```pseudocode
FUNCTION isBugCondition(agentState)
  INPUT: agentState of type OnboardingState
  OUTPUT: boolean

  RETURN agentState.currentStep = "Step 5: Track Selection"
         AND agentState.trackOptionsPresented = true
         AND agentState.receivedRealUserInput = false
         AND agentState.agentStoppedAfterPresenting = false
END FUNCTION
```

### Examples

- Agent presents tracks A/B/C/D, then immediately outputs "Human: A" and starts Module 2 → **Bug**: fabricated response, no stop, wrong track possible
- Agent presents tracks A/B/C/D, then immediately outputs "I'll go with the Quick Demo track for you" and starts Module 3 → **Bug**: assumed choice without input, no stop
- Agent presents tracks A/B/C/D, then continues with "Since you're new, let's start with Complete Beginner" and starts Module 1 → **Bug**: fabricated decision, no stop
- Agent presents tracks A/B/C/D and stops, hook fires with "👉 Which track would you like?" → **Correct**: agent stopped, hook fired, waiting for real input

## Expected Behavior

### Preservation Requirements

**Unchanged Behaviors:**

- Setup steps (Steps 0, 1, 1b) execute as continuous flow without stopping between each one
- Step 4 (Introduction) presents the full overview content (module table, mock data info, license info, track preview, glossary reference) in a single turn
- The `ask-bootcamper` hook continues to generate contextual closing questions on `agentStop` for all non-gate steps
- Track-to-module mapping logic (A→Module 3, B→Module 5, C→Module 1, D→Module 1) remains unchanged
- Non-gate steps continue to follow the "no inline WAIT instructions" pattern, relying on the `ask-bootcamper` hook for closing questions
- The general note at the top of `onboarding-flow.md` about not including inline closing questions remains intact (the gate is an explicit, documented exception)

**Scope:**

All onboarding steps that are NOT mandatory gates should be completely unaffected by this fix. This includes:

- Steps 0, 1, 1b (setup/directory creation/team detection) — continuous flow
- Step 3 (Prerequisite Check) — already has its own gate logic via pass/fail/warn
- Step 4 (Introduction) — informational, no user choice required
- All module-level steering and hook behavior outside onboarding

## Hypothesized Root Cause

Based on the bug description, the most likely issues are:

1. **Missing Mandatory Gate in Step 5**: The onboarding flow has no explicit instruction telling the agent to stop after presenting track options. The general note discourages WAIT instructions, and Step 5 has no exception. The agent treats Steps 4 and 5 as a single continuous turn.

2. **No Anti-Fabrication Rule in Agent Instructions**: The Communication section of `agent-instructions.md` says "One question at a time, wait for response" but has no explicit prohibition against fabricating user responses. The agent interprets "wait for response" loosely and generates its own.

3. **Weak Anti-Fabrication Language in Hook**: The `ask-bootcamper` hook prompt says "Do not role-play as the bootcamper" — but "role-play" is ambiguous. The agent may not interpret fabricating a "Human: A" message as "role-playing." The prohibition needs to be more explicit about never generating text that simulates user input.

4. **Hook Registry Drift**: The hook registry entry in `hook-registry.md` must match the actual hook file. If the hook prompt is strengthened, the registry must be updated to match.

## Correctness Properties

Property 1: Bug Condition - Mandatory Gate Stops Agent at Track Selection

_For any_ onboarding state where the agent has presented track selection options in Step 5 and has not yet received real bootcamper input, the fixed steering files SHALL contain a mandatory gate instruction that forces the agent to stop execution after presenting the options, allowing the `ask-bootcamper` hook to fire and the bootcamper to provide their actual choice.

Validates: Requirements 2.1, 2.2, 2.4

Property 2: Preservation - Non-Gate Onboarding Behavior Unchanged

_For any_ onboarding step that is NOT a mandatory gate (Steps 0, 1, 1b, 3, 4, and all module-level steps), the fixed steering files SHALL preserve the existing behavior: setup steps as continuous flow, Step 4 as a single-turn presentation, the general "no inline WAIT" pattern, track mapping logic, and normal `ask-bootcamper` hook behavior.

Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5

## Fix Implementation

### Changes Required

Assuming our root cause analysis is correct:

**File**: `senzing-bootcamp/steering/onboarding-flow.md`

**Section**: Step 5 (Track Selection) and the general note at the top

**Specific Changes**:

1. **Add Mandatory Gates concept to the general note**: Update the note at the top of the file to acknowledge that mandatory gates are an exception to the "no inline WAIT" rule. This documents the pattern so future steps can use it.

2. **Add mandatory gate instruction to Step 5**: After the track presentation content and the "Interpreting responses" line, add a clearly marked mandatory gate block that instructs the agent to STOP after presenting tracks and NOT proceed until the bootcamper responds. Use a visually distinct format (e.g., blockquote with ⛔ emoji) so it cannot be missed.

3. **Mark Step 2 as a mandatory gate**: Language selection also requires user input. Add a similar (but lighter) gate annotation to Step 2 for consistency, since it already works correctly but should be formally documented as a gate.

---

**File**: `senzing-bootcamp/steering/agent-instructions.md`

**Section**: Communication

**Specific Changes**:

1. **Add anti-fabrication rule**: Add an explicit rule to the Communication section prohibiting the agent from ever fabricating, simulating, or generating text that represents user input. This includes generating "Human:" messages, assuming user choices, or acting on behalf of the user without their actual input.

---

**File**: `senzing-bootcamp/hooks/ask-bootcamper.kiro.hook`

**Section**: `then.prompt`

**Specific Changes**:

1. **Strengthen anti-fabrication language in hook prompt**: Replace "Do not role-play as the bootcamper" with more explicit language: "NEVER fabricate user input. Do not generate 'Human:' messages, simulate user responses, assume user choices, or produce any text that represents what the bootcamper might say. If user input is required, STOP and wait."

---

**File**: `senzing-bootcamp/steering/hook-registry.md`

**Section**: `ask-bootcamper` entry under Critical Hooks

**Specific Changes**:

1. **Update hook registry prompt to match hook file**: Update the Prompt text in the `ask-bootcamper` registry entry to match the strengthened language in the actual hook file, keeping the two in sync.

## Testing Strategy

### Validation Approach

The testing strategy follows a two-phase approach: first, surface counterexamples that demonstrate the bug on unfixed content, then verify the fix works correctly and preserves existing behavior. Since this bug is in steering file content (not executable code), testing focuses on structural and content properties of the files.

### Exploratory Bug Condition Checking

**Goal**: Surface counterexamples that demonstrate the bug BEFORE implementing the fix. Confirm or refute the root cause analysis. If we refute, we will need to re-hypothesize.

**Test Plan**: Write tests that parse the unfixed steering files and verify the absence of mandatory gate instructions and anti-fabrication rules. Run these tests on the UNFIXED content to observe failures and confirm the root cause.

**Test Cases**:

1. **Missing Gate in Step 5**: Parse `onboarding-flow.md` Step 5 section and check for mandatory stop/gate instructions (will fail on unfixed content — no gate exists)
2. **Missing Anti-Fabrication Rule**: Parse `agent-instructions.md` Communication section and check for fabrication prohibition language (will fail on unfixed content — no such rule exists)
3. **Weak Hook Language**: Parse `ask-bootcamper.kiro.hook` prompt and check for explicit fabrication prohibition beyond "role-play" (will fail on unfixed content — only has weak "role-play" language)
4. **Hook Registry Sync**: Compare hook file prompt with registry entry prompt (may fail if they diverge after fix)

**Expected Counterexamples**:

- Step 5 section contains no gate/stop instruction — agent has no reason to stop
- Communication section has no fabrication prohibition — agent has no rule against generating fake input
- Hook prompt uses only "role-play" language — too ambiguous to prevent "Human:" fabrication

### Fix Checking

**Goal**: Verify that for all inputs where the bug condition holds, the fixed files contain the necessary instructions to prevent the bug.

**Pseudocode:**

```pseudocode
FOR ALL section WHERE isMandatoryGateStep(section) DO
  content := parseSteeringSection(section)
  ASSERT containsMandatoryGateInstruction(content)
  ASSERT containsStopBeforeProceedingLanguage(content)
END FOR

FOR ALL file IN [agent-instructions.md, ask-bootcamper.kiro.hook] DO
  content := readFile(file)
  ASSERT containsAntiFabricationRule(content)
END FOR
```

### Preservation Checking

**Goal**: Verify that for all inputs where the bug condition does NOT hold, the fixed files preserve existing behavior.

**Pseudocode:**

```pseudocode
FOR ALL section WHERE NOT isMandatoryGateStep(section) DO
  ASSERT sectionContent(fixed, section) = sectionContent(original, section)
         OR sectionContent(fixed, section) preserves behavioral intent
END FOR

FOR ALL hookBehavior WHERE NOT relatedToFabrication(hookBehavior) DO
  ASSERT hookBehavior(fixed) = hookBehavior(original)
END FOR
```

**Testing Approach**: Property-based testing is recommended for preservation checking because:

- It can generate many variations of steering file content to verify structural properties hold
- It catches edge cases where changes might inadvertently affect non-gate sections
- It provides strong guarantees that the general "no inline WAIT" pattern is preserved for non-gate steps

**Test Plan**: Observe the structure of UNFIXED files first (section boundaries, content patterns, track mapping), then write property-based tests verifying these structural properties are preserved after the fix.

**Test Cases**:

1. **Setup Flow Preservation**: Verify Steps 0, 1, 1b contain no gate instructions in either unfixed or fixed versions
2. **Step 4 Content Preservation**: Verify Step 4 content is unchanged between unfixed and fixed versions
3. **Track Mapping Preservation**: Verify the track-to-module mapping (A→3, B→5, C→1, D→1) is present in both versions
4. **General Note Preservation**: Verify the "no inline WAIT" general note is preserved (with gate exception documented)
5. **Hook Recap Logic Preservation**: Verify the hook prompt still contains the recap and closing question logic

### Unit Tests

- Test that Step 5 section contains mandatory gate instruction keywords
- Test that `agent-instructions.md` Communication section contains anti-fabrication rule
- Test that hook prompt contains explicit fabrication prohibition (not just "role-play")
- Test that hook registry prompt matches hook file prompt
- Test that Step 2 is annotated as a mandatory gate

### Property-Based Tests

- Generate random onboarding step identifiers and verify only gate steps (2, 5) contain gate instructions
- Generate random steering file section names and verify non-gate sections are unchanged
- Parse both fixed and unfixed files and verify track mapping content is identical
- Verify the hook prompt in the JSON file and the registry markdown entry are semantically equivalent

### Integration Tests

- Parse the complete `onboarding-flow.md` and verify the document structure is valid markdown with correct heading hierarchy
- Verify the `ask-bootcamper.kiro.hook` file is valid JSON after modification
- Verify the hook registry entry format is consistent with other entries in the registry
- End-to-end: trace the onboarding flow from Step 4 through Step 5 and verify a gate boundary exists between presenting tracks and acting on a selection
