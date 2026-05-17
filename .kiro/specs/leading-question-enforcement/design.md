# Leading Question Enforcement Bugfix Design

## Overview

After a bootcamper answers the last gap-filling sub-step question in a multi-part sequence (e.g., Step 7d in Module 1), the agent acknowledges the input and writes the checkpoint but stops without asking the next numbered step's leading question (Step 8). The fix adds an explicit "step-chaining" instruction to the module steering file so the agent knows that completing the final sub-step in a gap-filling sequence requires immediate advancement to the next numbered step's 👉 question in the same turn.

## Glossary

- **Bug_Condition (C)**: The condition that triggers the bug — the agent completes the last sub-step in a multi-part gap-filling sequence (all undetermined items resolved) and writes the checkpoint without advancing to the next numbered step's question.
- **Property (P)**: The desired behavior — after processing the last sub-step answer, the agent writes the checkpoint AND asks the next numbered step's 👉 question in the same turn.
- **Preservation**: The one-question-per-turn rule, 🛑 STOP behavior at mid-sequence sub-steps, ⛔ gate behavior, and all existing non-gap-filling step transitions must remain unchanged.
- **Gap-filling sub-steps**: Lettered sub-steps (e.g., 7a–7d) within a numbered step that each ask about one undetermined item, following the "ask about only one undetermined item per turn" instruction.
- **Step-chaining**: The act of advancing from the last sub-step of one numbered step to the 👉 question of the next numbered step within the same agent turn.
- **Leading question**: The 👉-prefixed question that opens a new workflow step, requiring bootcamper input before the agent can proceed.

## Bug Details

### Bug Condition

The bug manifests when the bootcamper answers the last gap-filling sub-step question in a multi-part sequence (e.g., Step 7d) and no further undetermined items remain. The agent acknowledges the input, writes the checkpoint for the sub-step, but treats the checkpoint write as the end of its work — it does not recognize that the workflow requires immediate progression to the next numbered step's question.

**Formal Specification:**
```
FUNCTION isBugCondition(input)
  INPUT: input of type AgentTurnContext
  OUTPUT: boolean
  
  RETURN input.currentStep IS a lettered sub-step (e.g., "7d")
         AND input.isLastSubStepInSequence = TRUE
         AND input.undeterminedItemsRemaining = 0
         AND input.nextNumberedStepExists = TRUE
         AND NOT agentAsksNextStepQuestion(input.agentResponse)
END FUNCTION
```

### Examples

- **Step 7d → Step 8 (Module 1)**: Bootcamper answers "What does the end result look like?" with "A clean master list exported to CSV." Agent responds: "Got it — you're looking for a clean master list in CSV format." Writes checkpoint for 7d. **Stops.** Expected: Agent should continue with Step 8's question: "👉 Will the entity resolution results need to interface with other software...?"
- **Step 7c → Step 7d (not a bug)**: Bootcamper answers "How many data sources?" with "Three." Agent responds with the next undetermined item question (7d). This is correct behavior — sub-steps remain within the sequence.
- **Step 7b → Step 7c (not a bug)**: Bootcamper answers record types question. Agent asks about source count (7c). Correct — more undetermined items remain.
- **Step 7d → Step 8 with all items pre-filled (edge case)**: If the bootcamper's initial open-ended response (Step 5) already covered all items, Step 7 may have zero undetermined items. In this case, Step 7a (confirmation) is the only sub-step asked, and after confirmation the agent should advance to Step 8.

## Expected Behavior

### Preservation Requirements

**Unchanged Behaviors:**
- The one-question-per-turn rule must continue to apply: each turn contains exactly one 👉 question.
- Mid-sequence sub-step behavior must remain unchanged: when undetermined items remain (e.g., answering 7b when 7c and 7d are still needed), the agent asks only the next undetermined sub-step question and stops.
- 🛑 STOP behavior at each sub-step's question must remain unchanged: after asking a 👉 question, the agent stops and waits.
- ⛔ mandatory gates must continue to block advancement until explicit confirmation.
- Clarifying questions for unclear/off-topic input must continue to take priority over step advancement.
- Session pause/end requests must continue to be honored.

**Scope:**
All inputs that do NOT involve completing the final sub-step in a multi-part gap-filling sequence should be completely unaffected by this fix. This includes:
- Mid-sequence sub-step answers (undetermined items still remain)
- Non-gap-filling steps (steps without lettered sub-steps)
- Steps that already have explicit "proceed to Step N" instructions
- ⛔ gate interactions
- Off-topic or unclear bootcamper input

## Hypothesized Root Cause

Based on the bug description and analysis of the steering files, the most likely issues are:

1. **Missing step-chaining instruction in module steering**: The `module-01-business-problem.md` Step 7 says "Ask about only one undetermined item per turn" and each sub-step (7a–7d) ends with "🛑 STOP." But there is no explicit instruction telling the agent what to do after the LAST sub-step is complete and the checkpoint is written. The agent interprets the 🛑 STOP on 7d as a terminal stop rather than recognizing that 7d's stop applies only to the question-asking phase, not to the post-answer processing phase.

2. **Ambiguity in checkpoint-as-completion signal**: The pattern "write checkpoint → proceed" is implicit in the module steering. Steps 1–6 each write a checkpoint and then the agent naturally flows to the next step. But for sub-steps, the agent writes the checkpoint for "7d" and sees no further sub-step to ask about, so it treats the checkpoint write as the end of its work for the entire numbered step — without recognizing that "completing Step 7" means "now do Step 8."

3. **No explicit "after all sub-steps complete" instruction**: The `module-transitions.md` Sub-Step Convention defines naming and checkpointing for sub-steps but does not specify what happens after the last sub-step in a sequence is completed. The convention is silent on step-chaining.

4. **Conversation protocol gap**: The `conversation-protocol.md` "No Dead-End Responses" rule says every turn must advance the conversation, but the agent may interpret writing a checkpoint as "advancing" even though no question was asked. The rule doesn't explicitly address the sub-step-to-next-step transition.

## Correctness Properties

Property 1: Bug Condition - Step-Chaining After Final Sub-Step

_For any_ agent turn where the bootcamper answers the last gap-filling sub-step question (all undetermined items resolved) and a next numbered step exists in the workflow, the fixed steering SHALL cause the agent to write the sub-step checkpoint AND ask the next numbered step's 👉 question in the same turn.

**Validates: Requirements 2.1, 2.2, 2.3**

Property 2: Preservation - Mid-Sequence Sub-Step Behavior

_For any_ agent turn where the bootcamper answers a gap-filling sub-step question but additional undetermined items remain, the fixed steering SHALL produce the same behavior as the original steering: ask only the next undetermined sub-step's question and stop, following the one-question-per-turn rule.

**Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5**

## Fix Implementation

### Changes Required

Assuming our root cause analysis is correct:

**File**: `senzing-bootcamp/steering/module-01-business-problem.md`

**Section**: Step 7 (gap-filling sequence)

**Specific Changes**:
1. **Add step-chaining instruction after Step 7d**: Insert an explicit instruction after the Step 7d checkpoint that tells the agent: "Once all gap-filling sub-steps are complete (no undetermined items remain), immediately proceed to Step 8 in the same turn — present Step 8's 👉 question as your closing question."

2. **Add a completion marker after the last sub-step**: Add a clear textual signal after Step 7d's checkpoint instruction:
   ```
   **All sub-steps complete?** → Proceed immediately to Step 8 below. 
   Do NOT end your turn here — the bootcamper expects the next question.
   ```

**File**: `senzing-bootcamp/steering/module-transitions.md`

**Section**: Sub-Step Convention

**Specific Changes**:
3. **Add step-chaining rule to the Sub-Step Convention**: Append a bullet to the convention:
   ```
   - **After the last sub-step**: When the bootcamper's answer completes the 
     final sub-step (no undetermined items remain), write the checkpoint and 
     immediately proceed to the next numbered step's 👉 question in the same 
     turn. Do not end the turn after writing the last sub-step's checkpoint.
   ```

**File**: `senzing-bootcamp/steering/conversation-protocol.md`

**Section**: End-of-Turn Protocol

**Specific Changes**:
4. **Add sub-step completion clause to End-of-Turn Protocol**: Add a clarifying paragraph:
   ```
   When you complete the LAST sub-step in a gap-filling sequence (all 
   undetermined items resolved): writing the checkpoint is NOT the end of 
   your turn. You must also present the next numbered step's 👉 question. 
   The checkpoint marks sub-step completion; the 👉 question marks turn 
   completion.
   ```

5. **Reinforce in No Dead-End Responses section**: Add an example:
   ```
   ### Sub-Step Completion Dead-End (WRONG)
   
   > Got it — you're looking for a clean master list. ✅ Checkpoint written.
   
   ### Sub-Step Completion (CORRECT)
   
   > Got it — you're looking for a clean master list. ✅ Checkpoint written.
   > 
   > 👉 Will the entity resolution results need to interface with other 
   > software — for example, a CRM, search engine, data warehouse, or 
   > downstream application?
   ```

## Testing Strategy

### Validation Approach

The testing strategy follows a two-phase approach: first, surface counterexamples that demonstrate the bug on unfixed steering, then verify the fix works correctly and preserves existing behavior.

### Exploratory Bug Condition Checking

**Goal**: Surface counterexamples that demonstrate the bug BEFORE implementing the fix. Confirm or refute the root cause analysis. If we refute, we will need to re-hypothesize.

**Test Plan**: Write property-based tests that simulate agent turn contexts where the last sub-step is completed. Generate random module states with varying numbers of undetermined items (0 remaining = bug condition). Assert that the steering text, when parsed for step-chaining instructions, provides explicit guidance to advance. Run these tests against the UNFIXED steering files to observe failures.

**Test Cases**:
1. **Module 1 Step 7d Complete**: Simulate completing Step 7d with 0 undetermined items remaining. Assert steering provides instruction to ask Step 8's question. (will fail on unfixed steering)
2. **Module 1 Step 7a Confirmation with All Pre-Filled**: Simulate Step 7a confirmation when all items were inferred from Step 5. Assert steering provides instruction to advance to Step 8. (will fail on unfixed steering)
3. **Sub-Step Convention Completeness**: Assert that `module-transitions.md` Sub-Step Convention includes a rule for what happens after the last sub-step. (will fail on unfixed steering)
4. **Conversation Protocol Coverage**: Assert that `conversation-protocol.md` addresses the sub-step-to-next-step transition explicitly. (will fail on unfixed steering)

**Expected Counterexamples**:
- The steering text for Step 7d contains no instruction to proceed to Step 8 after the checkpoint
- The Sub-Step Convention is silent on post-final-sub-step behavior
- Possible causes: missing instruction, ambiguous checkpoint-as-completion signal

### Fix Checking

**Goal**: Verify that for all inputs where the bug condition holds, the fixed steering provides explicit step-chaining instructions.

**Pseudocode:**
```
FOR ALL input WHERE isBugCondition(input) DO
  steeringText := getRelevantSteering(input.module, input.currentStep)
  ASSERT containsStepChainingInstruction(steeringText, input.nextStep)
  ASSERT instructionIsUnambiguous(steeringText)
END FOR
```

### Preservation Checking

**Goal**: Verify that for all inputs where the bug condition does NOT hold, the fixed steering produces the same behavior as the original steering.

**Pseudocode:**
```
FOR ALL input WHERE NOT isBugCondition(input) DO
  ASSERT getSteeringBehavior_original(input) = getSteeringBehavior_fixed(input)
END FOR
```

**Testing Approach**: Property-based testing is recommended for preservation checking because:
- It generates many test cases automatically across the input domain (various sub-step positions, undetermined item counts, module states)
- It catches edge cases that manual unit tests might miss (e.g., Step 7a with partial pre-fill)
- It provides strong guarantees that mid-sequence behavior is unchanged for all non-final sub-steps

**Test Plan**: Observe behavior on UNFIXED steering first for mid-sequence sub-steps (where the agent correctly asks the next undetermined item), then write property-based tests capturing that behavior.

**Test Cases**:
1. **Mid-Sequence Preservation**: Verify that for any sub-step where undetermined items remain, the steering still instructs "ask about only one undetermined item per turn" and includes 🛑 STOP. Assert this is unchanged after the fix.
2. **🛑 STOP Preservation**: Verify that all existing 🛑 STOP markers in sub-steps 7a–7d remain intact and are not removed or weakened by the fix.
3. **One-Question-Per-Turn Preservation**: Verify that the conversation-protocol.md "One Question Rule" is not weakened — the fix adds a step-chaining instruction but does not allow multiple questions in a single turn.
4. **⛔ Gate Preservation**: Verify that ⛔ gates continue to block advancement regardless of the step-chaining rule.

### Unit Tests

- Test that `module-01-business-problem.md` contains an explicit step-chaining instruction after Step 7d
- Test that `module-transitions.md` Sub-Step Convention includes a "last sub-step" rule
- Test that `conversation-protocol.md` addresses sub-step completion in the End-of-Turn Protocol
- Test that all existing 🛑 STOP markers in Steps 7a–7d are preserved
- Test that the step-chaining instruction references the correct next step (Step 8)

### Property-Based Tests

- Generate random sub-step positions (7a, 7b, 7c, 7d) with random undetermined item counts (0–4) and verify: if count = 0 AND position = last sub-step, steering contains step-chaining instruction; otherwise, steering contains "ask next undetermined item" instruction
- Generate random module states and verify the Sub-Step Convention rule applies consistently across all modules with gap-filling sequences
- Test that the fix does not introduce any new 👉 questions into sub-step definitions (preserving one-question-per-turn)

### Integration Tests

- Test full Module 1 flow: Steps 5 → 6 → 7a → 7b → 7c → 7d → 8, verifying the agent chains from 7d to 8
- Test Module 1 flow with pre-filled items: Steps 5 (comprehensive answer) → 6 → 7a (confirmation) → 8, verifying the agent chains from 7a to 8 when all items are already determined
- Test that mid-sequence stops still work: Steps 7a → wait → 7b → wait → 7c → wait → 7d → chain to 8
