# Implementation Plan: Agent Answer Processing Failures

## Overview

Fix three manifestations of the agent failing to process bootcamper answers to 👉 questions by: (1) adding answer-processing priority directives to steering files, (2) broadening the enforce-step-and-transition hook's Phase 2 from module-transition-only to all-question-type detection with type-specific retry instructions, and (3) adding a new Phase 3 not-waiting violation detection. The implementation uses the structured `config/.question_pending` file schema (type on first line, question text on subsequent lines) to enable targeted recovery.

## Tasks

- [ ] 1. Update steering files with answer-processing priority directives
  - [ ] 1.1 Add Answer Processing Priority section to `agent-instructions.md`
    - Add a new section after the session-start rule containing: absolute precedence directive (processing pending 👉 answer takes priority over all other actions), delete-and-process instruction (when `config/.question_pending` exists and bootcamper responded, delete file and process answer first), protocol violation statement (minimal output after pending answer = ⛔ mandatory gate violation)
    - _Requirements: 1.1, 1.2, 1.3_

  - [ ] 1.2 Add Answer Processing Priority section to `conversation-protocol.md`
    - Add a new "Answer Processing Priority" section before the existing "End-of-Turn Protocol" containing: highest-priority action declaration, substantive output requirement when processing an answer, treat-as-answer rule (if `.question_pending` exists, treat any bootcamper message as an answer), no-substantive-output-while-pending rule (while `.question_pending` exists, produce only answer-processing output)
    - _Requirements: 2.1, 2.2, 2.3, 6.3_

- [ ] 2. Restructure hook Phase 2 and add Phase 3
  - [ ] 2.1 Broaden Phase 2 from MODULE TRANSITION RETRY to ANSWER PROCESSING RETRY
    - In `senzing-bootcamp/hooks/enforce-step-and-transition.kiro.hook`: rename Phase 2 heading from "MODULE TRANSITION RETRY" to "ANSWER PROCESSING RETRY", remove the Transition_Confirmation detection logic (pattern matching for "Ready for Module", affirmative phrases), replace with two-condition activation (`config/.question_pending` exists AND agent output is Minimal_Output), add question type extraction from the file's first line, add type-specific retry instruction dispatch for all five types plus fallback
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 4.1, 4.2, 4.3, 4.4, 4.5, 4.6_

  - [ ] 2.2 Add Phase 3: Not-Waiting Detection to the hook
    - Add a new Phase 3 section to the hook prompt that detects when the agent advances the workflow while a question is still pending: activation conditions (`.question_pending` exists AND output is NOT minimal AND output contains workflow-advancing content AND `.question_pending` was NOT deleted), recovery instructions (discard premature output, acknowledge pending question, wait for bootcamper's response)
    - _Requirements: 6.1, 6.2_

  - [ ] 2.3 Update hook `description` field to reflect broadened scope
    - Update the JSON `description` field to mention three phases: sequential step enforcement, answer processing retry (all question types), and not-waiting detection
    - _Requirements: 3.3_

- [ ] 3. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 4. Update Question_Pending file schema documentation in steering
  - [ ] 4.1 Update End-of-Turn Protocol in `conversation-protocol.md` with structured schema
    - Modify the existing "Write the file `config/.question_pending`" instruction to specify the structured format: type on first line (one of: `track_selection`, `module_transition`, `step_question`, `confirmation`, `choice`), full question text on subsequent lines, default to `step_question` when type is undetermined
    - _Requirements: 5.1, 5.2, 5.3_

  - [ ] 4.2 Update `agent-instructions.md` Question Stop Protocol with structured schema
    - Add a note in the Communication section specifying that when writing `config/.question_pending`, the agent must use the structured format (type on first line, question text on subsequent lines)
    - _Requirements: 5.1, 5.2, 5.3_

- [ ] 5. Implement question_pending schema utilities and tests
  - [ ] 5.1 Create `senzing-bootcamp/tests/test_answer_processing_failures_properties.py`
    - Implement Property 3 (Question_Pending File Round-Trip): use Hypothesis to generate random valid question types and multi-line question texts, serialize to the file format, parse back, and verify identity
    - Implement Property 2 (Type-Specific Retry Instruction Completeness): parse the hook JSON and verify all five question types have distinct retry instruction blocks plus a generic fallback
    - Implement Property 1 (Phase 2 Activation Broadening): parse the hook JSON and verify Phase 2 activation uses question_pending existence + minimal output, and does NOT contain old Transition_Confirmation patterns
    - _Requirements: 3.1, 3.4, 4.1-4.6, 5.1-5.3_

  - [ ]* 5.2 Write property test for Question_Pending round-trip
    - **Property 3: Question_Pending File Round-Trip**
    - **Validates: Requirements 5.1, 5.2, 5.3**

  - [ ]* 5.3 Write property test for Phase 2 activation broadening
    - **Property 1: Phase 2 Activation Broadening**
    - **Validates: Requirements 3.1, 3.3, 3.4**

  - [ ]* 5.4 Write property test for type-specific retry instruction completeness
    - **Property 2: Type-Specific Retry Instruction Completeness**
    - **Validates: Requirements 4.1, 4.2, 4.3, 4.4, 4.5, 4.6**

- [ ] 6. Create repo-level hook prompt validation tests
  - [ ] 6.1 Create `tests/test_answer_processing_hook_prompt.py`
    - Verify hook Phase 2 is named "ANSWER PROCESSING RETRY" (not "MODULE TRANSITION RETRY")
    - Verify hook prompt contains all five type-specific retry instruction blocks plus fallback
    - Verify hook prompt contains not-waiting violation detection logic (Phase 3)
    - Verify hook prompt does NOT contain old Transition_Confirmation prerequisite patterns ("Ready for Module", "move on to Module", "proceed to Module" + affirmative response matching)
    - _Requirements: 3.3, 3.4, 4.1-4.6, 6.1, 6.2_

  - [ ]* 6.2 Write property test for Minimal_Output classification
    - **Property 4 (supplementary): Minimal_Output classification correctness**
    - Use Hypothesis to generate strings and verify the minimal output detection logic correctly classifies them (empty, ".", whitespace-only, <50 chars, single-word acks)
    - **Validates: Requirements 3.1**

- [ ] 7. Create steering file content validation tests
  - [ ] 7.1 Create `tests/test_answer_processing_steering.py`
    - Verify `agent-instructions.md` contains the answer-processing priority directive (absolute precedence, delete-and-process, protocol violation statement)
    - Verify `conversation-protocol.md` contains the "Answer Processing Priority" section
    - Verify `conversation-protocol.md` contains the structured `.question_pending` schema documentation
    - _Requirements: 1.1, 1.2, 1.3, 2.1, 2.2, 2.3, 5.1, 5.2_

- [ ] 8. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties from the design document
- Hook prompt validation tests go in repo-root `tests/` per project conventions
- Power-level schema tests go in `senzing-bootcamp/tests/` per project conventions
- The implementation language is Python 3.11+ with pytest + Hypothesis for all test files
- Hook files are JSON (`.kiro.hook`), steering files are Markdown with YAML frontmatter

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1", "1.2"] },
    { "id": 1, "tasks": ["2.1", "4.1", "4.2"] },
    { "id": 2, "tasks": ["2.2", "2.3"] },
    { "id": 3, "tasks": ["5.1", "6.1", "7.1"] },
    { "id": 4, "tasks": ["5.2", "5.3", "5.4", "6.2"] }
  ]
}
```
