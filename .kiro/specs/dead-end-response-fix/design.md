# Bugfix Design: Dead-End "Understood." Responses

## Overview

This fix addresses the agent's tendency to produce dead-end acknowledgments ("Understood.", "Got it.", "I see.") without following up with a next action or question. The root cause is that the agent's Communication rules and the ask-bootcamper hook prompt do not explicitly prohibit bare acknowledgments. The fix adds an explicit "no dead-end responses" rule to `agent-instructions.md` and strengthens the ask-bootcamper hook to detect and prevent dead-end turns.

## Bug Details

### Bug Condition

The bug manifests when the agent receives substantive bootcamper input (an answer to a question, a description of their problem, a design decision) and responds with only a brief acknowledgment without advancing the conversation. The agent treats the acknowledgment as a complete turn rather than recognizing it must always provide a next step.

### Root Cause

1. **No explicit prohibition**: The Communication rules in `agent-instructions.md` do not explicitly prohibit bare acknowledgments. The agent has no rule saying "never end a turn with just an acknowledgment."
2. **Hook gap**: The ask-bootcamper hook fires on agentStop and provides a closing question, but if the agent already produced "Understood." as its full response, the hook's closing question may not fire or may feel disconnected.
3. **Missing advancement rule**: There's no rule stating that every agent turn must either (a) end with a 👉 question, (b) advance to the next step, or (c) present actionable content.

## Expected Behavior

After receiving substantive bootcamper input, the agent must always:
1. Acknowledge briefly (optional), AND
2. Follow up with one of: a leading question, a summary of what was captured + what comes next, or the next step in the workflow

The agent must NEVER end a turn with only an acknowledgment and no follow-up.

## Fix Implementation

### Changes Required

**File**: `senzing-bootcamp/steering/agent-instructions.md`

**Section**: Communication

**Specific Changes**:

1. Add a "No Dead-End Responses" rule to the Communication section:
   - "Never end a turn with only an acknowledgment (e.g., 'Understood.', 'Got it.', 'I see.'). Every turn must advance the conversation by: (a) asking a 👉 follow-up question, (b) summarizing what was captured and stating what comes next, or (c) proceeding to the next step in the module workflow."
   - "If you acknowledge input, always append a next action in the same response."

---

**File**: `senzing-bootcamp/steering/hook-registry.md`

**Section**: ask-bootcamper hook prompt (SECOND branch — recap + closing question)

**Specific Changes**:

1. Add reinforcement language: "If the agent's previous turn was a bare acknowledgment with no follow-up, treat this as an error state — provide the recap and closing question to recover the conversation flow."

## Testing Strategy

- Verify that `agent-instructions.md` Communication section contains the "No Dead-End Responses" rule
- Verify the rule explicitly prohibits bare acknowledgments
- Verify the rule requires every turn to advance the conversation
- Verify the ask-bootcamper hook prompt references dead-end recovery
- Verify no non-interactive steps are affected (file creation, code generation should still complete without interruption)
