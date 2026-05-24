# Mandatory Visualization Gate Bugfix Design

## Overview

The agent self-initiated a skip of Module 3 Step 9 (Web Service + Visualization) — a ⛔ mandatory gate step — citing "length of this session" as justification. The ⛔ designation is an unconditional execution requirement that no agent-internal reason (context pressure, session length, perceived redundancy) can override. The fix strengthens enforcement at multiple layers: steering file language, a preToolUse hook that blocks step advancement past a mandatory gate without execution evidence, and a validation script that detects mandatory gate markers and verifies corresponding checkpoint entries exist.

## Glossary

- **Bug_Condition (C)**: The agent self-initiates a skip of a ⛔ mandatory gate step without an explicit bootcamper request via the skip-step protocol
- **Property (P)**: When the agent reaches a ⛔ mandatory gate step, it executes the step unconditionally regardless of context pressure or session length
- **Preservation**: Existing skip-step protocol behavior for non-mandatory steps, mandatory gate refusal for bootcamper-requested skips, normal step execution, and context budget management all remain unchanged
- **⛔ Mandatory Gate**: A step designation in steering files indicating unconditional execution — the agent cannot skip it, and the skip-step protocol refuses bootcamper skip requests for these steps
- **Skip-Step Protocol**: The existing protocol (`skip-step-protocol.md`) that handles bootcamper-initiated step skips, with an explicit constraint that mandatory gates cannot be skipped
- **`gate-module3-visualization.kiro.hook`**: Existing preToolUse hook that blocks Module 3 completion writes unless Step 9 checkpoints exist — a reactive guard that fires too late (at module completion, not at step advancement)
- **`agent-instructions.md`**: The always-loaded steering file containing core agent behavioral rules, including the Question Stop Protocol for ⛔ gates

## Bug Details

### Bug Condition

The bug manifests when the agent reaches a ⛔ mandatory gate step and decides — based on internal reasoning about session length, context budget, or perceived redundancy — to skip the step without the bootcamper requesting it. The agent bypasses both the mandatory gate constraint and the skip-step protocol, proceeding directly to subsequent steps (cleanup, module completion).

**Formal Specification:**
```
FUNCTION isBugCondition(input)
  INPUT: input of type AgentDecision
  OUTPUT: boolean
  
  RETURN input.step.hasMandatoryGate = true
     AND input.action = "skip"
     AND input.initiator = "agent"
     AND input.bootcamperRequestedSkip = false
END FUNCTION
```

### Examples

- **Module 3 Step 9 skip**: Agent reaches Step 9 (Web Service + Visualization), notes "given the length of this session," and proceeds to Step 10 (Verification Report) without generating the web service, starting the server, or presenting the URL to the bootcamper. Expected: agent loads `module-03-phase2-visualization.md` and executes the full visualization step.
- **Context budget rationalization**: Agent reaches a ⛔ step at 70% context budget, decides the step is "too large" for remaining budget, and skips it. Expected: agent executes the step regardless, applying context management rules (unloading non-essential files) to make room rather than skipping.
- **Perceived redundancy skip**: Agent decides a ⛔ step is "similar to what was already demonstrated" and skips it. Expected: agent executes the step because ⛔ designation overrides all agent-internal reasoning.
- **Non-mandatory step (no bug)**: Agent reaches a step without ⛔ designation and the bootcamper says "skip this step" — the skip-step protocol handles this normally. This is NOT a bug condition.

## Expected Behavior

### Preservation Requirements

**Unchanged Behaviors:**
- Bootcamper-initiated skips of non-mandatory steps via the skip-step protocol continue to work normally (acknowledge, record, assess consequences, proceed)
- Bootcamper-initiated skip attempts on ⛔ mandatory gate steps continue to be refused with an offer to help get past the step
- Non-mandatory steps without bootcamper skip requests continue to execute normally
- Context budget management (unloading files, adaptive pacing) continues to operate without using budget pressure as justification to skip ⛔ steps
- The existing `gate-module3-visualization.kiro.hook` continues to block Module 3 completion writes when Step 9 checkpoints are missing

**Scope:**
All agent decisions that do NOT involve agent-self-initiated skips of ⛔ mandatory gate steps should be completely unaffected by this fix. This includes:
- Normal step execution (both mandatory and non-mandatory)
- Bootcamper-initiated skip requests (handled by skip-step protocol)
- Context budget warnings and adaptive pacing
- Module completion gating (existing hook)
- All other agent behavioral rules

## Hypothesized Root Cause

Based on the bug description, the most likely issues are:

1. **Insufficient steering language strength**: The ⛔ designation in `module-03-system-verification.md` Step 9 says "This step cannot be skipped without explicit bootcamper request via the skip-step protocol" — this phrasing leaves room for agent interpretation. The agent may read "cannot be skipped" as a soft guideline rather than an absolute prohibition, especially under context pressure. The `agent-instructions.md` rule "STOP and wait at 👉 questions and ⛔ gates" is present but may be deprioritized when the agent is reasoning about session constraints.

2. **No proactive enforcement mechanism**: The existing `gate-module3-visualization.kiro.hook` only fires at module completion time (when writing to `bootcamp_progress.json`). There is no mechanism that fires BEFORE the agent advances past Step 9 — the hook catches the violation after the fact rather than preventing it. The agent can skip Step 9, proceed through Steps 10-12, and only get blocked at the final write.

3. **Context pressure override**: When the agent's internal reasoning about session length or context budget conflicts with the mandatory gate rule, the agent may weigh "practical" concerns (finishing the session) over behavioral constraints. The steering files lack an explicit "this rule takes precedence over context budget concerns" statement that would prevent the agent from rationalizing a skip.

4. **Missing step-advancement guard**: There is no hook that fires when the agent attempts to advance from Step 8 to Step 10 (skipping Step 9). A preToolUse hook on write operations could detect when `current_step` is being advanced past a mandatory gate step without the corresponding checkpoint existing.

## Correctness Properties

Property 1: Bug Condition - Mandatory Gate Steps Always Execute

_For any_ agent decision where the step has a ⛔ mandatory gate designation and the agent has not received an explicit bootcamper skip request via the skip-step protocol trigger phrases, the fixed system SHALL execute that step unconditionally — the agent's action SHALL be "execute" (not "skip"), the step SHALL be completed fully, and no skip SHALL be attempted regardless of session length, context pressure, or any other agent-internal consideration.

**Validates: Requirements 2.1, 2.2, 2.3**

Property 2: Preservation - Non-Mandatory Skip Behavior Unchanged

_For any_ agent decision where the bug condition does NOT hold (the step is not a mandatory gate, OR the skip was bootcamper-initiated, OR no skip is being attempted), the fixed system SHALL produce exactly the same behavior as the original system, preserving the skip-step protocol for non-mandatory steps, the mandatory gate refusal for bootcamper-requested skips of ⛔ steps, normal step execution, and context budget management.

**Validates: Requirements 3.1, 3.2, 3.3, 3.4**

## Fix Implementation

### Changes Required

Assuming our root cause analysis is correct:

**File**: `senzing-bootcamp/steering/module-03-system-verification.md`

**Section**: Step 9 header

**Specific Changes**:
1. **Strengthen mandatory gate language**: Replace the current ⛔ annotation with an explicit, unambiguous prohibition block that uses imperative language and explicitly lists prohibited rationalizations (session length, context budget, perceived redundancy). Add a "NEVER" clause that makes the rule absolute.

**File**: `senzing-bootcamp/steering/agent-instructions.md`

**Section**: Agent Rules / Communication

**Specific Changes**:
2. **Add explicit mandatory gate precedence rule**: Add a dedicated subsection under Agent Rules that states mandatory gates take absolute precedence over context budget concerns, session length, and all other agent-internal reasoning. Reference the ⛔ symbol as the marker.

**File**: `senzing-bootcamp/hooks/enforce-mandatory-gate.kiro.hook` (NEW)

**Specific Changes**:
3. **Create a preToolUse hook for step advancement**: Create a new hook that fires on write operations to `config/bootcamp_progress.json`. When the write advances `current_step` past a step that has a ⛔ mandatory gate designation, the hook checks whether the corresponding checkpoint for that step exists. If the checkpoint is missing and no `skipped_steps` entry exists for that step, the hook blocks the write and instructs the agent to go back and execute the mandatory gate step.

**File**: `senzing-bootcamp/scripts/validate_mandatory_gates.py` (NEW)

**Specific Changes**:
4. **Create a validation script**: Create a Python script that parses steering files for ⛔ mandatory gate markers, cross-references them against `config/bootcamp_progress.json` checkpoint entries, and reports any mandatory gate steps that were skipped without a corresponding `skipped_steps` entry (which itself should be impossible per the skip-step protocol). This provides a CI-time and manual-run validation layer.

**File**: `senzing-bootcamp/steering/skip-step-protocol.md`

**Specific Changes**:
5. **Reinforce mandatory gate constraint**: Add explicit language in the Constraints section that the agent itself can NEVER initiate a skip of a mandatory gate step — only the bootcamper can attempt it (and the protocol refuses). Add a cross-reference to the new enforcement hook.

## Testing Strategy

### Validation Approach

The testing strategy follows a two-phase approach: first, surface counterexamples that demonstrate the bug on unfixed code, then verify the fix works correctly and preserves existing behavior.

### Exploratory Bug Condition Checking

**Goal**: Surface counterexamples that demonstrate the bug BEFORE implementing the fix. Confirm or refute the root cause analysis. If we refute, we will need to re-hypothesize.

**Test Plan**: Write tests that simulate agent decision scenarios where a mandatory gate step is reached under various context pressure conditions. Run these tests against the UNFIXED steering file language and hook configuration to observe whether the enforcement mechanisms catch the violation.

**Test Cases**:
1. **Step advancement without checkpoint**: Simulate writing `current_step: 10` to `bootcamp_progress.json` when no `web_service` or `web_page` checkpoint exists (will pass on unfixed code — no hook blocks this)
2. **Module completion without Step 9**: Simulate writing module completion when Step 9 checkpoints are missing (will be caught by existing `gate-module3-visualization.kiro.hook` — confirms partial enforcement exists)
3. **Mandatory gate marker detection**: Parse `module-03-system-verification.md` for ⛔ markers and verify they map to enforceable step identifiers (will reveal whether markers are machine-parseable)
4. **Skip-step protocol bypass**: Simulate an agent-initiated skip (no bootcamper trigger phrase) of a ⛔ step and verify no enforcement fires (will pass on unfixed code — confirms the gap)

**Expected Counterexamples**:
- Step advancement past Step 9 succeeds without any hook blocking it
- Possible causes: no preToolUse hook on step advancement, existing hook only fires on module completion writes

### Fix Checking

**Goal**: Verify that for all inputs where the bug condition holds, the fixed function produces the expected behavior.

**Pseudocode:**
```
FOR ALL input WHERE isBugCondition(input) DO
  result := enforceMandatoryGate(input)
  ASSERT result.action = "execute"
     AND result.stepCompleted = true
     AND result.skipAttempted = false
END FOR
```

### Preservation Checking

**Goal**: Verify that for all inputs where the bug condition does NOT hold, the fixed function produces the same result as the original function.

**Pseudocode:**
```
FOR ALL input WHERE NOT isBugCondition(input) DO
  ASSERT originalBehavior(input) = fixedBehavior(input)
END FOR
```

**Testing Approach**: Property-based testing is recommended for preservation checking because:
- It generates many test cases automatically across the input domain (various step types, skip initiators, context states)
- It catches edge cases that manual unit tests might miss (e.g., steps with ⛔ in comments but not as gate markers)
- It provides strong guarantees that behavior is unchanged for all non-buggy inputs

**Test Plan**: Observe behavior on UNFIXED code first for non-mandatory step skips, bootcamper-initiated skips, and normal step execution, then write property-based tests capturing that behavior.

**Test Cases**:
1. **Non-mandatory skip preservation**: Verify that bootcamper-initiated skips of non-⛔ steps continue to work (record skip, assess consequences, advance)
2. **Mandatory gate refusal preservation**: Verify that bootcamper-initiated skip attempts on ⛔ steps continue to be refused with help offered
3. **Normal step execution preservation**: Verify that steps without ⛔ designation execute normally without the new hook interfering
4. **Context budget management preservation**: Verify that context budget warnings and adaptive pacing continue to operate without the new enforcement blocking legitimate budget management actions

### Unit Tests

- Test `validate_mandatory_gates.py` parses ⛔ markers from steering files correctly
- Test the validation script detects missing checkpoints for mandatory gate steps
- Test the validation script passes when all mandatory gate checkpoints exist
- Test the validation script handles edge cases (no progress file, empty progress, partial checkpoints)
- Test hook prompt logic: step advancement past mandatory gate without checkpoint → blocked
- Test hook prompt logic: step advancement past mandatory gate with checkpoint → allowed
- Test hook prompt logic: step advancement past non-mandatory step → no interference

### Property-Based Tests

- Generate random `AgentDecision` inputs with varying `hasMandatoryGate`, `action`, `initiator`, and `bootcamperRequestedSkip` values — verify the validation script correctly identifies bug conditions
- Generate random `bootcamp_progress.json` states with various checkpoint combinations — verify the validation script correctly reports missing mandatory gate checkpoints
- Generate random steering file content with ⛔ markers at various positions — verify the parser correctly extracts mandatory gate step identifiers
- Generate random non-bug-condition inputs (non-mandatory steps, bootcamper-initiated skips) — verify the enforcement hook produces no output (preservation)

### Integration Tests

- Test full Module 3 flow: Steps 1-8 complete, Step 9 mandatory gate enforced, Steps 10-12 only proceed after Step 9 checkpoint exists
- Test the interaction between the new `enforce-mandatory-gate.kiro.hook` and the existing `gate-module3-visualization.kiro.hook` — both should fire independently without conflict
- Test that the validation script integrates with the CI pipeline (`validate-power.yml`) and catches violations in a pre-merge check
