# Bugfix Design: Module Transition Stall Fix

## Overview

This fix addresses the agent's failure to proceed when the bootcamper confirms readiness for the next module. The root cause is that the module completion/transition steering does not explicitly instruct the agent to immediately begin the next module upon receiving an affirmative response. The fix adds an explicit "act on confirmation" rule to the agent instructions and strengthens the module completion workflow steering.

## Bug Details

### Bug Condition

The bug manifests at module transition points where the agent asks "Ready for Module X?" and the bootcamper responds affirmatively. Instead of immediately starting the next module, the agent produces a dead-end response or no response at all.

### Root Cause

1. **Missing action trigger**: The module completion steering asks the "Ready?" question but doesn't explicitly instruct the agent that an affirmative response is a trigger to immediately execute the next module's startup sequence.
2. **Overlap with dead-end issue**: This is a specific case of the dead-end response problem — the agent acknowledges without acting. But it requires a module-transition-specific fix because the expected action (start a new module) is more complex than a simple follow-up question.
3. **No explicit startup sequence instruction**: When the bootcamper says "yes," the agent needs to know exactly what to do: display the banner, show the journey map, and begin Step 1. This sequence isn't explicitly tied to the affirmative response.

## Expected Behavior

When the bootcamper responds affirmatively to "Ready for Module X?":
1. Immediately display the Module X banner
2. Show the journey map for Module X
3. Begin Step 1 of Module X

No acknowledgment-only response. No waiting for further input. The "yes" IS the instruction to proceed.

## Fix Implementation

### Changes Required

**File**: `senzing-bootcamp/steering/agent-instructions.md`

**Section**: Communication (or Module Transitions subsection)

**Specific Changes**:

1. Add a "Module Transition Protocol" rule:
   - "When you ask 'Ready for Module X?' and the bootcamper responds affirmatively (yes, sure, let's go, ready, etc.), immediately begin that module in the same turn. Display the module banner, journey map, and start Step 1. Never acknowledge without acting at a module transition."

---

**File**: `senzing-bootcamp/steering/module-completion-workflow.md` (or equivalent)

**Specific Changes**:

1. At the point where the "Ready for Module X?" question is asked, add explicit post-confirmation instructions:
   - "Upon receiving an affirmative response, immediately execute the next module's startup sequence: (1) Display module banner, (2) Show journey map, (3) Begin Step 1. Do not produce any intermediate acknowledgment."

## Testing Strategy

- Verify that `agent-instructions.md` contains the "Module Transition Protocol" rule
- Verify the rule explicitly states that affirmative responses trigger immediate module startup
- Verify the rule lists the startup sequence (banner, journey map, Step 1)
- Verify the module completion workflow steering contains post-confirmation instructions
- Verify no other module flow is affected (mid-module steps, negative responses, questions)
