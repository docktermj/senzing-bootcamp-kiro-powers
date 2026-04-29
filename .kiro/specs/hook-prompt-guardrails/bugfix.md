# Bugfix Requirements Document

## Introduction

Two related bugs cause hook prompts to produce unwanted output when they should be silent. Bug 1: the `ask-bootcamper` agentStop hook fires after the agent's output already contains a 👉 question and generates a fabricated response that answers the question itself, role-playing as the bootcamper. Bug 2: three preToolUse hooks (`verify-senzing-facts`, `enforce-working-directory`, `enforce-feedback-path`) narrate their internal evaluation reasoning to the bootcamper when checks pass, despite prompts saying "produce no output at all." Both bugs degrade the bootcamp experience — Bug 1 removes the bootcamper's agency by answering their own questions with fabricated content, and Bug 2 clutters the conversation with irrelevant hook-processing chatter on every write operation.

## Bug Analysis

### Current Behavior (Defect)

1.1 WHEN the agent's previous output contains a 👉 question anywhere in the text THEN the `ask-bootcamper` hook fires and generates a fabricated response that answers the question, role-playing as the bootcamper instead of producing no output

1.2 WHEN the agent's previous output ends with a 👉 question and the hook prompt says "do nothing" THEN the agent interprets "do nothing" loosely and still generates text — including full fabricated use-case descriptions, specific record counts, and system names — because the guard language is too weak

1.3 WHEN the `verify-senzing-facts` preToolUse hook fires and the file contains no Senzing-specific content THEN the agent prints its internal reasoning (e.g., "none of these files are feedback content... Proceeding with the writes") instead of producing no output

1.4 WHEN the `enforce-working-directory` preToolUse hook fires and all paths are within the working directory THEN the agent narrates its evaluation process (e.g., "all paths within working directory, no Senzing-specific content. Proceeding.") instead of producing no output

1.5 WHEN the `enforce-feedback-path` preToolUse hook fires and the agent is not in the feedback workflow THEN the agent acknowledges and explains the hook check result instead of producing no output

1.6 WHEN the `hook-registry.md` steering file contains the same weak prompt language as the hook files THEN the registry perpetuates the same defective behavior because it mirrors the insufficient guardrails

### Expected Behavior (Correct)

2.1 WHEN the agent's previous output contains a 👉 character anywhere in the text THEN the `ask-bootcamper` hook SHALL produce absolutely no output — no text, no recap, no question, no fabricated response, no role-playing as the bootcamper

2.2 WHEN the `ask-bootcamper` hook prompt is evaluated THEN it SHALL contain explicit prohibitions against generating any text when a 👉 is detected, against answering questions meant for the bootcamper, and against role-playing as the user — using strong negative instructions and examples

2.3 WHEN the `verify-senzing-facts` preToolUse hook fires and the file contains no Senzing-specific content or all content was already verified THEN the hook SHALL produce no output at all — no acknowledgment, no reasoning narration, no status message, no explanation of the evaluation

2.4 WHEN the `enforce-working-directory` preToolUse hook fires and all paths are within the working directory THEN the hook SHALL produce no output at all — no acknowledgment, no reasoning narration, no status message, no explanation of the evaluation

2.5 WHEN the `enforce-feedback-path` preToolUse hook fires and the agent is not in the feedback workflow THEN the hook SHALL produce no output at all — no acknowledgment, no reasoning narration, no status message, no explanation of the evaluation

2.6 WHEN the hook prompts are updated with stronger guardrail language THEN the `hook-registry.md` steering file SHALL be updated to contain the exact same prompt text for each affected hook, maintaining synchronization

2.7 WHEN the hook prompts are updated with stronger guardrail language THEN the `agent-instructions.md` steering file SHALL reinforce the silent-processing rule in its Hooks section with explicit language that forbids narrating, explaining, or acknowledging hook evaluations when no corrective action is needed

### Unchanged Behavior (Regression Prevention)

3.1 WHEN the `ask-bootcamper` hook fires and the agent's previous output does NOT contain a 👉 character and files were changed THEN the hook SHALL CONTINUE TO recap what was accomplished, list files created or modified with paths, and end with a contextual 👉 question

3.2 WHEN the `ask-bootcamper` hook fires and the agent's previous output does NOT contain a 👉 character and no files changed and no substantive work was done THEN the hook SHALL CONTINUE TO skip the recap and just ask a contextual 👉 question about what the bootcamper wants to do next

3.3 WHEN the `verify-senzing-facts` preToolUse hook fires and the file DOES contain unverified Senzing-specific content THEN the hook SHALL CONTINUE TO instruct the agent to verify content via MCP tools before writing

3.4 WHEN the `enforce-working-directory` preToolUse hook fires and paths reference /tmp/, %TEMP%, ~/Downloads, or locations outside the working directory THEN the hook SHALL CONTINUE TO instruct the agent to replace those paths with project-relative equivalents

3.5 WHEN the `enforce-feedback-path` preToolUse hook fires and the agent IS in the feedback workflow writing to the wrong path THEN the hook SHALL CONTINUE TO stop and redirect the write to docs/feedback/SENZING_BOOTCAMP_POWER_FEEDBACK.md

3.6 WHEN the `capture-feedback` hook fires and the bootcamper's message contains a feedback trigger phrase THEN the hook SHALL CONTINUE TO initiate the feedback workflow with automatic context capture

3.7 WHEN the `capture-feedback` hook fires and the bootcamper's message does NOT contain a feedback trigger phrase THEN the hook SHALL CONTINUE TO produce no output

3.8 WHEN any non-affected hook in hook-registry.md is read THEN its prompt text and metadata SHALL CONTINUE TO be identical to its current content
