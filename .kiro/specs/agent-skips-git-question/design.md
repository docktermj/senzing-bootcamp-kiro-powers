# Agent Skips Git Question Bugfix Design

## Overview

During Module 1 Step 1, the agent asks "Would you like me to initialize a git repository for version control?" but does not wait for the bootcamper's response before continuing to Step 2. The root cause is twofold: (1) the steering file says "ask" but never instructs the agent to STOP and wait, and (2) the question lacks the 👉 marker that the `ask-bootcamper` agentStop hook scans for to detect pending questions and suppress further output. The fix is a targeted rewording of Step 1 in `module-01-business-problem.md` to use the 👉 marker, add an explicit stop instruction, and defer the checkpoint until after the bootcamper responds. The `ask-bootcamper.kiro.hook` already correctly handles 👉 detection and needs no changes.

## Glossary

- **Bug_Condition (C)**: The agent reaches Module 1 Step 1, the workspace is not a git repository, and the agent asks the git initialization question but continues to Step 2 without waiting for the bootcamper's response
- **Property (P)**: The agent asks the git question with a 👉 marker and STOPs, the `ask-bootcamper` hook detects the pending question and suppresses output, and the bootcamper's actual response determines whether git is initialized — only then does the agent write the checkpoint and proceed
- **Preservation**: All behavior when the workspace is already a git repo (skip question, proceed directly), all behavior of Steps 2–8 and Phase 2, all existing 👉 detection in the `ask-bootcamper` hook, and all other modules' question-asking patterns
- **`module-01-business-problem.md`**: The steering file at `senzing-bootcamp/steering/module-01-business-problem.md` that defines the Module 1 workflow from version control through problem documentation
- **`ask-bootcamper` hook**: The `agentStop` hook at `senzing-bootcamp/hooks/ask-bootcamper.kiro.hook` that scans for the 👉 character in the most recent assistant message and suppresses output when a question is pending
- **👉 marker**: The established convention across all steering files for prefixing questions that require bootcamper input, enabling the `ask-bootcamper` hook to detect pending questions and enforce one-question-at-a-time flow

## Bug Details

### Bug Condition

The bug manifests when the agent reaches Module 1 Step 1 and the workspace is not already a git repository. The steering file instructs the agent to "ask" the git initialization question, but provides no explicit instruction to stop and wait for the response. The question text also lacks the 👉 marker, so even if the agent does stop (triggering `agentStop`), the hook does not recognize a pending question and may produce additional output or a follow-up question instead of suppressing output.

**Formal Specification:**

```pseudocode
FUNCTION isBugCondition(input)
  INPUT: input of type SteeringStepState
  OUTPUT: boolean

  RETURN input.currentModule = "Module 1"
         AND input.currentStep = "Step 1: Initialize version control"
         AND input.workspaceIsGitRepo = false
         AND input.gitQuestionAsked = true
         AND (input.questionTextLacksPointingMarker = true
              OR input.steeringLacksStopInstruction = true)
END FUNCTION
```

### Examples

- Agent checks git status, finds no repo, outputs "Would you like me to initialize a git repository for version control?", then immediately writes the Step 1 checkpoint and continues to Step 2 (data privacy reminder) → **Bug**: no stop, no wait, checkpoint written prematurely
- Agent asks the git question without 👉, stops (agentStop fires), hook does not detect a pending question and generates a new 👉 closing question about something else → **Bug**: hook doesn't suppress because no 👉 in the git question
- Agent asks the git question without 👉, stops, hook generates a second question, bootcamper answers the hook's question instead of the git question → **Bug**: original question lost, git never initialized even if bootcamper wanted it
- Agent checks git status, finds existing repo, skips the question, writes checkpoint, proceeds to Step 2 → **Correct**: no question needed, existing behavior preserved

## Expected Behavior

### Preservation Requirements

**Unchanged Behaviors:**

- When the workspace is already a git repository, Step 1 skips the question and proceeds directly to Step 2 without prompting
- The `ask-bootcamper` hook continues to detect 👉 markers in all other modules and suppress output when a question is pending
- When the bootcamper answers "no" to the git question, the agent proceeds to Step 2 without initializing git
- Steps 2 through 8 and Phase 2 (Steps 9–16) follow their existing flow, checkpoint logic, and question-asking behavior unchanged
- The `ask-bootcamper.kiro.hook` file is not modified — it already correctly handles 👉 detection

**Scope:**

All inputs that do NOT involve the git initialization question in Module 1 Step 1 should be completely unaffected by this fix. This includes:

- The "already a git repo" path through Step 1
- All other steps in Module 1 (Steps 2–8, Phase 2)
- All other modules' steering files
- The `ask-bootcamper` hook file and its prompt logic
- The hook registry entry for `ask-bootcamper`

## Hypothesized Root Cause

Based on the bug description, the most likely issues are:

1. **Missing Stop Instruction in Step 1**: The steering file says `If not, ask: "Would you like me to initialize a git repository for version control?"` followed immediately by `If yes, initialize. If no or already a repo, proceed.` — this reads as a continuous flow. The agent interprets "ask" as "output the question text" and immediately evaluates the next conditional (`If yes, initialize`) without stopping. There is no explicit instruction to STOP and wait for the bootcamper's response.

2. **Missing 👉 Marker on the Question**: The git question text does not include the 👉 prefix. The `ask-bootcamper` hook's suppression logic depends entirely on finding 👉 in the most recent assistant message. Without it, even if the agent does stop after asking, the hook will not recognize a pending question and will generate additional output — potentially a second question that confuses the bootcamper.

3. **Premature Checkpoint Placement**: The `**Checkpoint:** Write step 1 to config/bootcamp_progress.json` line appears immediately after the question/response logic, with no instruction to defer it until after the bootcamper responds. The agent may write the checkpoint before the bootcamper has answered, marking Step 1 as complete prematurely.

4. **No Conditional Checkpoint Logic**: The checkpoint is unconditional — it doesn't distinguish between the "already a repo" path (where no question is asked and the checkpoint should be written immediately) and the "not a repo" path (where the checkpoint should wait until after the bootcamper responds and the agent acts on the response).

## Correctness Properties

Property 1: Bug Condition - Git Question Uses 👉 Marker and Stop Instruction

_For any_ state where Module 1 Step 1 is reached and the workspace is not a git repository, the fixed steering file SHALL contain the git initialization question prefixed with the 👉 marker AND an explicit stop instruction telling the agent to STOP and wait for the bootcamper's response before proceeding, AND the checkpoint SHALL be deferred until after the bootcamper responds.

**Validates: Requirements 2.1, 2.2, 2.3**

Property 2: Preservation - Non-Git-Question Behavior Unchanged

_For any_ input where the bug condition does NOT hold (workspace is already a git repo, or the agent is on any step other than Step 1's git question), the fixed steering file SHALL produce the same behavior as the original file, preserving the "already a repo" skip path, Steps 2–8 content, Phase 2 reference, and all checkpoint logic for non-Step-1 steps.

**Validates: Requirements 3.1, 3.2, 3.3, 3.4**

## Fix Implementation

### Changes Required

Assuming our root cause analysis is correct:

**File**: `senzing-bootcamp/steering/module-01-business-problem.md`

**Section**: Step 1 (Initialize version control)

**Specific Changes**:

1. **Add 👉 marker to the git question**: Change the question text from `ask: "Would you like me to initialize a git repository for version control?"` to use the 👉 prefix: `👉 "Would you like me to initialize a git repository for version control?"`. This enables the `ask-bootcamper` hook to detect the pending question and suppress additional output.

2. **Add explicit STOP instruction**: After the 👉-prefixed question, add a clear instruction telling the agent to STOP and wait for the bootcamper's response. This should follow the pattern established by other mandatory gates in the project (e.g., the ⛔ gates in `onboarding-flow.md`), but adapted for a conditional question rather than a full mandatory gate.

3. **Defer the checkpoint**: Move the checkpoint instruction so it only fires AFTER the bootcamper responds and the agent acts on the response (initialize git if yes, skip if no). The "already a repo" path should still write the checkpoint immediately since no question is asked.

4. **Restructure the conditional flow**: Rewrite the step to clearly separate the two paths: (a) already a repo → write checkpoint, proceed; (b) not a repo → ask 👉 question, STOP, wait for response, act on response, THEN write checkpoint and proceed.

5. **Do NOT change the `ask-bootcamper.kiro.hook`**: The hook already correctly detects 👉 markers and suppresses output. No changes needed.

## Testing Strategy

### Validation Approach

The testing strategy follows a two-phase approach: first, surface counterexamples that demonstrate the bug on unfixed content, then verify the fix works correctly and preserves existing behavior. Since this bug is in steering file content (not executable code), testing focuses on structural and content properties of the markdown file.

### Exploratory Bug Condition Checking

**Goal**: Surface counterexamples that demonstrate the bug BEFORE implementing the fix. Confirm or refute the root cause analysis. If we refute, we will need to re-hypothesize.

**Test Plan**: Write tests that parse the unfixed `module-01-business-problem.md` Step 1 section and verify the absence of the 👉 marker and stop instruction. Run these tests on the UNFIXED content to observe failures and confirm the root cause.

**Test Cases**:

1. **Missing 👉 Marker Test**: Parse Step 1 and check whether the git question text contains the 👉 marker (will fail on unfixed code — no marker exists)
2. **Missing Stop Instruction Test**: Parse Step 1 and check for an explicit stop/wait instruction after the question (will fail on unfixed code — no stop instruction exists)
3. **Premature Checkpoint Test**: Parse Step 1 and check whether the checkpoint is deferred until after the response (will fail on unfixed code — checkpoint is unconditional)

**Expected Counterexamples**:

- Step 1 git question text lacks the 👉 prefix — hook cannot detect pending question
- Step 1 has no stop/wait instruction after the question — agent has no reason to stop
- Step 1 checkpoint is placed unconditionally — written before bootcamper responds

### Fix Checking

**Goal**: Verify that for all inputs where the bug condition holds, the fixed file contains the necessary instructions to prevent the bug.

**Pseudocode:**

```pseudocode
FOR ALL section WHERE isGitQuestionStep(section) DO
  content := parseSteeringSection(section)
  ASSERT containsPointingMarker(content, "👉")
  ASSERT containsStopInstruction(content)
  ASSERT checkpointIsDeferred(content)
END FOR
```

### Preservation Checking

**Goal**: Verify that for all inputs where the bug condition does NOT hold, the fixed file preserves existing behavior.

**Pseudocode:**

```pseudocode
FOR ALL step WHERE step != "Step 1 git question path" DO
  ASSERT stepContent(fixed, step) = stepContent(original, step)
         OR stepContent(fixed, step) preserves behavioral intent
END FOR
```

**Testing Approach**: Property-based testing is recommended for preservation checking because:

- It can generate many step identifiers and verify structural properties hold across all non-Step-1 sections
- It catches edge cases where changes might inadvertently affect other steps
- It provides strong guarantees that Steps 2–8 content and checkpoint logic are unchanged

**Test Plan**: Observe the structure of the UNFIXED file first (step boundaries, content patterns, checkpoint placements), then write property-based tests verifying these structural properties are preserved after the fix.

**Test Cases**:

1. **Steps 2–8 Content Preservation**: Verify Steps 2 through 8 content is unchanged between unfixed and fixed versions
2. **Phase 2 Reference Preservation**: Verify the Phase 2 reference line at the end of the file is unchanged
3. **Already-a-Repo Path Preservation**: Verify the "already a git repo" skip logic is preserved in Step 1
4. **Step Count Preservation**: Verify the file still contains exactly 8 numbered steps plus the Phase 2 reference
5. **Hook File Unchanged**: Verify `ask-bootcamper.kiro.hook` is not modified

### Unit Tests

- Test that Step 1 contains the 👉 marker in the git question text
- Test that Step 1 contains a stop/wait instruction after the question
- Test that Step 1's checkpoint is deferred (appears after the response handling, not before)
- Test that the "already a repo" path still skips the question and writes the checkpoint immediately
- Test that the `ask-bootcamper.kiro.hook` file is unchanged (byte-identical to original)

### Property-Based Tests

- Generate random step numbers (1–8) and verify only Step 1 contains the 👉 git question marker
- Generate random step numbers (2–8) and verify their content is identical between fixed and unfixed versions
- Parse both fixed and unfixed files and verify the total number of checkpoint lines is identical
- Verify the Phase 2 reference line is present and unchanged across random samples

### Integration Tests

- Parse the complete `module-01-business-problem.md` and verify the document structure is valid markdown with correct heading hierarchy
- Verify the 👉 marker in Step 1 would be detected by the `ask-bootcamper` hook's scanning logic (regex match against the hook's prompt pattern)
- Trace the Step 1 flow: git check → not a repo → 👉 question → stop instruction → (response) → act → checkpoint → proceed to Step 2
