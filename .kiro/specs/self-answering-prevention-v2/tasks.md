# Implementation Plan: Self-Answering Prevention v2

## Overview

Structural fix for the self-answering questions issue. Replaces prompt-only mitigations with a defense-in-depth approach: steering-embedded recap behavior, a question-pending sentinel file, and a silence-first hook prompt.

## Tasks

- [x] 1. Add End-of-Turn Protocol to agent-instructions.md
  - [x] 1.1 Replace the "Closing-question ownership" rule in the Communication section
    - Remove: "Closing-question ownership: never end your turn with a closing question — the ask-bootcamper hook owns those."
    - Replace with an "### End-of-Turn Protocol" subsection containing:
      - When completing work that does NOT end with a 👉 question: briefly recap what was accomplished, list files changed, end with a contextual 👉 closing question
      - When ending with a 👉 question: write `config/.question_pending` containing the question text
      - When processing the bootcamper's next message: delete `config/.question_pending` before doing anything else
      - Explicit statement: "The ask-bootcamper hook is a safety net only — do not rely on it for closing questions"
    - Preserve the Question Stop Protocol subsection unchanged
    - _Requirements: 2.3, 3.1_

- [x] 2. Restructure the ask-bootcamper hook prompt
  - [x] 2.1 Replace the prompt in `senzing-bootcamp/hooks/ask-bootcamper.kiro.hook` with the silence-first structure:
    - Line 1: "PRODUCE NOTHING. YOUR OUTPUT IS EMPTY. ZERO TOKENS. DO NOT GENERATE ANY TEXT."
    - Separator: "---"
    - Exception clause: "EXCEPTION (read ONLY if you are certain no question is pending):"
    - Verification checklist: (1) config/.question_pending does NOT exist, (2) most recent assistant message does NOT contain 👉, (3) most recent assistant message does NOT end with a question directed at the bootcamper
    - Failure rule: "If ANY condition fails: PRODUCE NOTHING. STOP. ZERO TOKENS."
    - Success rule: "If ALL conditions pass: You may provide a brief recap of work done and a contextual 👉 closing question. Keep it to 2-3 sentences maximum."
    - Safety default: "CRITICAL: If you are uncertain about ANY condition, default to SILENCE. Silence is always safe."
    - _Requirements: 2.1, 2.2, 3.1_

- [x] 3. Update hook-registry.md to match
  - [x] 3.1 Update the ask-bootcamper entry in `senzing-bootcamp/steering/hook-registry.md` with the new prompt text
  - [x] 3.2 Update the description to reflect the silence-first approach
    - _Requirements: 2.1_

- [x] 4. Add sentinel file management to Question Stop Protocol
  - [x] 4.1 In the Question Stop Protocol subsection of `agent-instructions.md`, add:
    - "After asking a 👉 question, write the file `config/.question_pending` with the question text before ending your turn."
    - "At the start of every turn where you process bootcamper input, check for and delete `config/.question_pending` if it exists."
    - _Requirements: 2.1, 2.2_

- [x] 5. Add .question_pending to .gitignore
  - [x] 5.1 Add `config/.question_pending` to the project's `.gitignore` (this is a transient state file, not a project artifact)
    - _Requirements: N/A (housekeeping)_

- [x] 6. Verify the structural change
  - Confirm `agent-instructions.md` contains the End-of-Turn Protocol with sentinel file instructions
  - Confirm the ask-bootcamper hook prompt starts with "PRODUCE NOTHING" as the unconditional default
  - Confirm the hook prompt's exception clause requires checking the sentinel file AND conversation history
  - Confirm the "Closing-question ownership" rule has been replaced with the new protocol
  - Confirm hook-registry.md matches the actual hook file
  - Run `sync_hook_registry.py --verify` if available

- [x] 7. Remove the feedback-submission-reminder hook (consolidation)
  - [x] 7.1 Since we're restructuring the ask-bootcamper hook anyway, fold the feedback reminder logic into the exception clause:
    - After the recap, if track completion was detected, append the 📋 feedback reminder
    - This eliminates the second agentStop hook entirely (addresses the `consolidate-agentstop-hooks` spec)
  - [x] 7.2 Delete `senzing-bootcamp/hooks/feedback-submission-reminder.kiro.hook`
  - [x] 7.3 Remove the feedback-submission-reminder entry from hook-registry.md
    - _Requirements: 2.1 (reduces hook-triggered turns)_

## Notes

- This is a structural fix, not a prompt-strength fix. The previous spec (`self-answering-questions-fix`) tried stronger language and failed. This spec changes the architecture.
- The key insight: make silence the DEFAULT and output the EXCEPTION. The model's failure mode (failing to process the exception clause) results in silence — which is safe.
- The sentinel file provides a concrete, file-system-level signal that doesn't depend on the model correctly parsing conversation history.
- Defense in depth: even if one layer fails, the others provide protection.
- This spec supersedes the prompt-strengthening aspects of `self-answering-questions-fix` but preserves its hard-stop blocks in module steering files (those are still valuable as first-line defense).
