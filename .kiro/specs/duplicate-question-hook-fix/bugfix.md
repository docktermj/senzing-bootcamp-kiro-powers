# Bugfix Requirements Document

## Introduction

The "Summarize Progress on Stop" hook (`senzing-bootcamp/hooks/summarize-on-stop.kiro.hook`) causes duplicate questions during bootcamp interactions. When the agent's output ends with a pending question (identified by a 👉 prefix or a WAIT-for-response pattern), the `agentStop` hook fires and its prompt instructs the agent to re-state that same pending question. The bootcamper sees the question twice — once in the original agent output and once repeated by the hook summary — creating a confusing, broken-feeling experience.

The root cause is in the hook's prompt text: it explicitly instructs the agent to "re-state the pending question as the very last element" when a pending question is detected. This re-statement duplicates a question that already appeared in the agent's output. The fix should change the prompt so that when a pending question is detected, the hook only appends the summary (what was accomplished, which files changed) without re-stating the question, since the question is already visible to the bootcamper. The same prompt must also be updated in the hook registry (`senzing-bootcamp/steering/hook-registry.md`) to stay in sync.

## Bug Analysis

### Current Behavior (Defect)

1.1 WHEN the agent's output ends with a pending question (a line starting with 👉 or a WAIT-for-response pattern) AND the `agentStop` hook fires THEN the system re-states the pending question after the summary, causing the bootcamper to see the same question twice.

1.2 WHEN the agent presents the onboarding welcome banner and module overview ending with a question like "Does this outline make sense?" AND the `agentStop` hook fires THEN the system appends a summary followed by a duplicate of that question, disrupting the conversational flow.

### Expected Behavior (Correct)

2.1 WHEN the agent's output ends with a pending question (a line starting with 👉 or a WAIT-for-response pattern) AND the `agentStop` hook fires THEN the system SHALL append only the summary — (1) what was accomplished, (2) which files were created or modified — without re-stating the pending question, since it is already visible in the agent's output.

2.2 WHEN the agent presents the onboarding welcome banner and module overview ending with a question AND the `agentStop` hook fires THEN the system SHALL present the summary before the existing question ends the conversation, and the question SHALL appear exactly once.

### Unchanged Behavior (Regression Prevention)

3.1 WHEN the agent's output does NOT end with a pending question (no 👉 line and no WAIT pattern) THEN the system SHALL CONTINUE TO append the standard three-element summary at the end: (1) what was accomplished, (2) which files were created or modified, (3) what is the next step.

3.2 WHEN the hook fires THEN the system SHALL CONTINUE TO use the `agentStop` event type and `askAgent` action type with the hook name "Summarize Progress on Stop" and all other hook metadata (version, description) unchanged.

3.3 WHEN the hook prompt is updated in the hook file (`summarize-on-stop.kiro.hook`) THEN the corresponding prompt in the hook registry (`hook-registry.md`) SHALL CONTINUE TO match the hook file prompt exactly.

3.4 WHEN no pending question is detected THEN the system SHALL CONTINUE TO include the "next step" element as the third part of the summary, preserving the existing three-element summary format.
