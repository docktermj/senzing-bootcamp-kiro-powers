# Implementation Plan: Dead-End "Understood." Response Fix

## Overview

Add an explicit "No Dead-End Responses" rule to the agent's Communication section and strengthen the ask-bootcamper hook to detect and recover from dead-end turns.

## Tasks

- [x] 1. Add "No Dead-End Responses" rule to agent-instructions.md
  - [x] 1.1 Add a new rule to the Communication section in `senzing-bootcamp/steering/agent-instructions.md`
    - Rule text: "Never end a turn with only an acknowledgment (e.g., 'Understood.', 'Got it.', 'I see.'). Every turn must advance the conversation by: (a) asking a 👉 follow-up question, (b) summarizing what was captured and stating what comes next, or (c) proceeding to the next step in the module workflow."
    - Add clarification: "If you acknowledge input, always append a next action in the same response."
    - Place this rule in the Communication section, after the existing question-stop protocol
    - Do NOT modify the question-stop protocol or any other existing rules
    - _Requirements: 1, 4_

- [x] 2. Strengthen ask-bootcamper hook for dead-end recovery
  - [x] 2.1 Update the SECOND branch of the ask-bootcamper prompt in `senzing-bootcamp/steering/hook-registry.md`
    - Add: "If the agent's previous turn was a bare acknowledgment with no follow-up question or next step, treat this as an error state — provide the recap and a contextual closing question to recover the conversation flow."
    - Preserve all existing SECOND branch logic (recap + closing question)
    - Do NOT modify the FIRST branch (suppression when 👉 question is pending)
    - _Requirements: 2_

- [x] 3. Verify the fix
  - Confirm `agent-instructions.md` contains the "No Dead-End Responses" rule
  - Confirm the rule explicitly lists prohibited patterns ("Understood.", "Got it.", "I see.")
  - Confirm the rule requires every turn to advance the conversation
  - Confirm the ask-bootcamper hook references dead-end recovery
  - Confirm no non-interactive steps are affected
  - Run any existing steering validation scripts

## Notes

- This fix complements the self-answering-questions-fix spec — that spec prevents the agent from continuing past questions; this spec prevents the agent from stopping too early after receiving answers
- No Python code changes — only steering markdown edits
