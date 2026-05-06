# Implementation Plan: Conversation UX Rules

## Overview

Strengthen conversation UX enforcement across the senzing-bootcamp power's steering files by adding explicit rules, violation examples, STOP markers, and 👉 prefixes. Changes follow the design's implementation order: authoritative source first (conversation-protocol.md), then reinforcement files, then token count updates, then tests.

## Tasks

- [x] 1. Add four new sections to conversation-protocol.md
  - [x] 1.1 Add "One Question Rule" section after "Question Stop Protocol"
    - State that each turn contains at most one 👉 question
    - Define multi-question patterns with conjunctions (and, or, also, but first) as violations
    - State sequential information gathering requires separate turns
    - _Requirements: 1.1, 1.2, 1.4, 2.4_
  - [x] 1.2 Add "Violation Examples" section with before/after examples
    - Include one concrete before/after example for each of the five rule categories: multi-question, not-waiting, dead-end, missing-prefix, and self-answering
    - Use WRONG/CORRECT format as shown in design
    - _Requirements: 8.1_
  - [x] 1.3 Add "Rule Priority" section
    - State conversation UX rules take precedence over content generation
    - Agent must never sacrifice turn-taking correctness to deliver more information
    - _Requirements: 8.2_
  - [x] 1.4 Add "Self-Check" section with four verification questions
    - (a) Does this turn contain more than one 👉 question?
    - (b) Does any 👉 question lack the prefix?
    - (c) Is there content after a 👉 question?
    - (d) Am I answering my own question?
    - _Requirements: 8.3_
  - [x] 1.5 Add mandatory question_pending statement
    - State that writing `config/.question_pending` is mandatory for every 👉 question, not optional
    - _Requirements: 8.4, 5.5_

- [x] 2. Add Behavioral Rules Reload section to session-resume.md
  - [x] 2.1 Insert new section between Step 2 (Load Language Steering) and Step 3 (Summarize and Confirm)
    - Title: "Step 2b: Behavioral Rules Reload"
    - Re-state all five core rules in one sentence each: one-question-per-turn, wait-for-response, no-dead-ends, 👉-prefix-required, no-self-answering
    - Reference conversation-protocol.md as authoritative source
    - Include self-answering prohibition with example forbidden phrases ("just me", "I'll go with X")
    - Instruct agent to write `config/.question_pending` after the "Ready to continue?" question
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 5.2, 5.3_

- [x] 3. Add Communication section reinforcement to agent-instructions.md
  - [x] 3.1 Expand the Communication section's "One question at a time" bullet
    - Add explicit prohibition against combining questions with conjunctions (and, or, also, but first)
    - Add cross-reference: "These rules apply in ALL contexts — onboarding, feedback workflow, module steps, and session resume. See conversation-protocol.md for the full rule set."
    - Add statement that a question without 👉 prefix is a formatting violation
    - _Requirements: 1.5, 4.5, 7.5_

- [x] 4. Modify feedback-workflow.md with preamble and STOP markers
  - [x] 4.1 Add "Conversation Rules" preamble section before Step 0
    - State: one question per turn, use 👉 prefix, 🛑 STOP after each question, do not combine confirmation and priority questions
    - _Requirements: 7.1_
  - [x] 4.2 Add 👉 prefix and 🛑 STOP markers to Step 2 questions
    - Prefix each of the six questions in Step 2 with 👉
    - Add `🛑 STOP — End your response here.` block after each question
    - _Requirements: 1.3, 4.3, 7.3_

- [x] 5. Checkpoint — Validate CommonMark and token budgets
  - Run `python3 senzing-bootcamp/scripts/validate_commonmark.py` on modified files
  - Run `python3 senzing-bootcamp/scripts/measure_steering.py --check` to verify no budget overruns
  - Ensure all tests pass, ask the user if questions arise.

- [x] 6. Add 👉 prefix to module-09-phaseA-assessment.md questions
  - [x] 6.1 Add 👉 prefix to Step 1a question
    - Change `"Do you have any compliance requirements?..."` to `👉 "Do you have any compliance requirements?..."`
    - _Requirements: 4.2, 7.2_
  - [x] 6.2 Add 👉 prefix to Step 1b question
    - Change `"Who are the security stakeholders..."` to `👉 "Who are the security stakeholders..."`
    - _Requirements: 4.2, 7.2_

- [x] 7. Add 👉 prefix to onboarding-flow.md gate and preference questions
  - [x] 7.1 Add 👉 prefix to Language Selection prompt (Step 2)
    - Prefix the language choice question with 👉
    - _Requirements: 4.1, 7.4_
  - [x] 7.2 Add 👉 prefix to Verbosity Preference question (Step 4b)
    - Prefix the verbosity question with 👉
    - _Requirements: 4.1, 7.4_
  - [x] 7.3 Add 👉 prefix to Comprehension Check question (Step 4c)
    - Prefix the check-in question with 👉
    - _Requirements: 4.1, 7.4_
  - [x] 7.4 Add 👉 prefix to Track Selection prompt (Step 5)
    - Prefix the track choice question with 👉
    - _Requirements: 4.1, 7.4_

- [x] 8. Update steering-index.yaml token counts
  - [x] 8.1 Update token counts for all modified steering files
    - Run `python3 senzing-bootcamp/scripts/measure_steering.py` to get new counts
    - Update `file_metadata` entries for: conversation-protocol.md, session-resume.md, agent-instructions.md, feedback-workflow.md, module-09-phaseA-assessment.md, onboarding-flow.md
    - Verify no file exceeds `split_threshold_tokens: 5000`
    - _Requirements: (infrastructure — supports all requirements by keeping CI green)_

- [x] 9. Checkpoint — Full CI validation
  - Run `python3 senzing-bootcamp/scripts/validate_commonmark.py` on all steering files
  - Run `python3 senzing-bootcamp/scripts/measure_steering.py --check`
  - Ensure all tests pass, ask the user if questions arise.

- [x] 10. Write property-based tests for conversation UX rules
  - [x] 10.1 Write property test: Universal 👉 prefix on bootcamper-directed questions
    - **Property 1: Universal 👉 prefix on bootcamper-directed questions**
    - Parse steering files, find questions with adjacent 🛑 STOP markers or ⛔ gates, verify all have 👉 prefix
    - **Validates: Requirements 4.1, 4.2, 4.3, 4.4, 7.2, 7.4**
  - [x] 10.2 Write property test: STOP marker follows every 👉 question before next question
    - **Property 2: STOP marker follows every 👉 question before next question**
    - Parse steering files with multiple 👉 questions, verify 🛑 STOP marker (or EOF) between each pair
    - **Validates: Requirements 1.3, 2.3, 7.3**
  - [x] 10.3 Write property test: Behavioral Rules Reload completeness and ordering
    - **Property 3: Behavioral Rules Reload completeness and ordering**
    - Parse session-resume.md, verify "Behavioral Rules Reload" section exists before Step 3 and references all five core rules
    - **Validates: Requirements 6.1, 6.2**
  - [x] 10.4 Write property test: Violation Examples section covers all five rule categories
    - **Property 4: Violation Examples section covers all five rule categories**
    - Parse conversation-protocol.md, verify "Violation Examples" section contains examples for: multi-question, not-waiting, dead-end, missing-prefix, self-answering
    - **Validates: Requirements 8.1**
  - [x] 10.5 Write property test: Self-Check section contains all verification questions
    - **Property 5: Self-Check section contains all verification questions**
    - Parse conversation-protocol.md, verify "Self-Check" section contains all four verification questions
    - **Validates: Requirements 8.3**

- [x] 11. Write unit tests for conversation UX rules
  - [x] 11.1 Write unit tests for structural requirements
    - Verify conversation-protocol.md contains "Rule Priority" section
    - Verify conversation-protocol.md states question_pending is mandatory
    - Verify session-resume.md references conversation-protocol.md as authoritative source
    - Verify agent-instructions.md Communication section contains conjunction prohibition
    - Verify feedback-workflow.md has "Conversation Rules" preamble section
    - Verify session-resume.md contains self-answering prohibition text before Step 3
    - _Requirements: 8.2, 8.4, 6.3, 1.5, 7.1, 5.2_

- [x] 12. Final checkpoint — Ensure all tests pass
  - Run full pytest suite: `python3 -m pytest senzing-bootcamp/tests/ -v`
  - Run `python3 senzing-bootcamp/scripts/validate_commonmark.py`
  - Run `python3 senzing-bootcamp/scripts/measure_steering.py --check`
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- All changes are to Markdown steering files — no code, scripts, or new hook files
- Tests use pytest + Hypothesis (already in the project) in `senzing-bootcamp/tests/`
- CI pipeline (`validate-power.yml`) already runs validate_commonmark, measure_steering --check, and pytest
- Token budget is the primary constraint — conversation-protocol.md additions (~400 tokens) keep it under the 5000-token split threshold
- Each task references specific requirements for traceability
- Property tests validate universal correctness properties from the design document
