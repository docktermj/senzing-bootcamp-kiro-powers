# Technical Design: no-skip-offer-mandatory-gate

## Overview

The agent offers to skip Module 3 Step 9 (Web Service + Visualization) by asking a question like "Would you like to continue with the visualization, or skip ahead?" This violates the ⛔ mandatory gate rule — the agent should never present a mandatory step as optional. Existing hooks catch actual skips but not the **offer** to skip. The fix adds steering language prohibiting skip offers for ⛔ steps and adds a self-check rule to the conversation protocol.

## Glossary

- **Bug_Condition (C)**: The agent generates a 👉 question that offers to skip or bypass a ⛔ mandatory gate step
- **Property (P)**: When the agent reaches or is near a ⛔ mandatory gate step, it never presents that step as optional or skippable in any question
- **Preservation**: Questions about non-mandatory steps, closing questions that don't reference ⛔ steps, and all existing hook behaviors remain unchanged
- **⛔ Mandatory Gate**: A step designation in steering files indicating unconditional execution — the agent cannot skip it and cannot offer to skip it
- **Skip Offer**: A question that presents a ⛔ step as a choice — phrases like "or skip ahead", "would you like to continue with [mandatory step]", "or move on to the next module"

## Bug Details

### Bug Condition

The bug manifests when the agent completes steps preceding a ⛔ mandatory gate step and generates a closing question that frames the upcoming mandatory step as optional. The agent doesn't actually skip the step — it asks the bootcamper whether to skip, which still violates the mandatory gate principle because the step should never be presented as a choice.

**Formal Specification:**
```pascal
FUNCTION isBugCondition(input)
  INPUT: input of type AgentQuestion
  OUTPUT: boolean
  
  RETURN input.type = "question"
     AND input.referencesStep.hasMandatoryGate = true
     AND input.offersSkipOrBypass = true
     AND input.initiator = "agent"
END FUNCTION
```

### Examples

- **Skip offer after Step 8**: Agent completes Module 3 Steps 1–8, then asks "Would you like to continue with the visualization, or skip ahead to Module 4?" Expected: agent announces "Proceeding to Step 9 — the visualization" and executes it.
- **Choice list including skip**: Agent presents a numbered choice list where one option is "Skip the visualization and move on." Expected: no skip option for ⛔ steps.
- **Conditional framing**: Agent says "If you'd like, we can skip the web service step and go straight to cleanup." Expected: no conditional framing for ⛔ steps.
- **Non-mandatory step (no bug)**: Agent asks "Would you like to see the performance report, or skip to the next module?" for a non-⛔ step — this is permitted.

## Expected Behavior

### Preservation Requirements

**Unchanged Behaviors:**
- Questions about non-mandatory steps can offer skip options
- The `ask-bootcamper` hook continues to generate contextual closing questions
- The `enforce-single-question` hook continues to validate question format
- All existing mandatory gate enforcement hooks (`gate-module3-visualization`, `enforce-mandatory-gate`, `enforce-gate-on-stop`) continue to operate
- Bootcamper-initiated skip requests via the skip-step protocol continue to be handled normally (refused for ⛔ steps, allowed for non-⛔ steps)

**Scope:**
All agent questions that do NOT offer to skip a ⛔ mandatory gate step should be completely unaffected by this fix.

## Hypothesized Root Cause

1. **No question-content rule for mandatory gates**: The `agent-instructions.md` Mandatory Gate Precedence section prohibits skipping ⛔ steps but does not prohibit **offering** to skip them. The agent interprets "don't skip" as "don't skip without asking" rather than "don't even ask."

2. **Self-check gap**: The `conversation-protocol.md` Self-Check section has 4 items (multiple questions, missing prefix, content after question, self-answering) but no item checking whether a question offers to bypass a mandatory gate.

3. **No module-specific instruction**: `module-03-system-verification.md` marks Step 9 as ⛔ mandatory but doesn't explicitly instruct the agent to proceed directly without asking.

## Correctness Properties

Property 1: Bug Condition — No Skip Offers for Mandatory Gates

_For any_ agent question where the question references a ⛔ mandatory gate step and offers to skip or bypass it, the fixed system SHALL NOT generate that question. The agent SHALL instead proceed directly to the mandatory step without asking permission.

**Validates: Requirements 2.1, 2.2, 2.3**

Property 2: Preservation — Non-Mandatory Questions Unaffected

_For any_ agent question where the bug condition does NOT hold (the question doesn't reference a ⛔ step, or doesn't offer to skip), the fixed system SHALL produce exactly the same behavior as the original system.

**Validates: Requirements 3.1, 3.2, 3.4**

## Fix Implementation

### Changes Required

**File**: `senzing-bootcamp/steering/agent-instructions.md`

**Section**: Mandatory Gate Precedence

**Specific Changes**:
1. Add a new bullet prohibiting skip offers for ⛔ steps. Language: "NEVER offer to skip a ⛔ mandatory gate step. Do not ask 'would you like to continue with [step]?', 'or skip ahead?', 'or move on to the next module?' when the next step is a ⛔ mandatory gate. Instead, announce that you are proceeding to the step and execute it. The ⛔ designation means the step is unconditional — presenting it as a choice undermines the gate."

---

**File**: `senzing-bootcamp/steering/conversation-protocol.md`

**Section**: Self-Check

**Specific Changes**:
2. Add item 5: "Does any 👉 question offer to skip or bypass an upcoming ⛔ mandatory gate step?" Update the "If any answer is yes" instruction to reference 5 checks.

---

**File**: `senzing-bootcamp/steering/module-03-system-verification.md`

**Section**: Before Step 9

**Specific Changes**:
3. Add: "**Agent behavior:** After Step 8 completes, proceed DIRECTLY to Step 9. Do not ask whether the bootcamper wants to continue — Step 9 is mandatory and unconditional."

## Testing Strategy

### Exploratory Bug Condition Checking

**Goal**: Confirm the steering gap exists before fixing it.

**Test Plan**: Parse the three steering files and verify the prohibition language is absent.

**Test Cases**:
1. `agent-instructions.md` Mandatory Gate Precedence section does not contain "offer to skip" or "presenting it as a choice"
2. `conversation-protocol.md` Self-Check section has exactly 4 items (no mandatory gate check)
3. `module-03-system-verification.md` does not contain "proceed DIRECTLY to Step 9"

**Expected**: Tests FAIL on unfixed code (confirming the gap).

### Fix Checking

**Goal**: Verify the prohibition language is present after the fix.

**Test Cases**:
1. `agent-instructions.md` contains "NEVER offer to skip a ⛔ mandatory gate step"
2. `conversation-protocol.md` Self-Check has 5 items including the mandatory gate check
3. `module-03-system-verification.md` contains "proceed DIRECTLY to Step 9"

### Preservation Checking

**Goal**: Verify non-mandatory step behavior is unchanged.

**Test Cases**:
1. Questions about non-⛔ steps are not flagged by the new self-check
2. The existing 4 self-check items still function correctly
3. All existing hooks produce the same behavior as before
