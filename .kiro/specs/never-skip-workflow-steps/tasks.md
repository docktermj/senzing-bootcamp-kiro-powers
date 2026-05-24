# Implementation Plan: Never Skip Workflow Steps

## Overview

Enforce strict sequential execution of all numbered workflow steps across the Senzing Bootcamp Power by: (1) creating an `agentStop` hook that detects step-skipping violations, (2) strengthening steering-file language in `agent-instructions.md` and `conversation-protocol.md`, (3) adding a Sequential Execution Reminder block to all 11 module steering files, and (4) registering the new hook in `hook-categories.yaml`.

## Tasks

- [x] 1. Create the enforce-sequential-steps hook
  - [x] 1.1 Create `senzing-bootcamp/hooks/enforce-sequential-steps.kiro.hook`
    - Write the JSON hook file with `name`, `version`, `description`, `when` (agentStop), and `then` (askAgent with detection prompt)
    - The prompt must implement the 7-step detection algorithm from the design: read progress, extract steps, parse parent step numbers, calculate gap, output violation or silence
    - Follow the exact JSON schema pattern used by `enforce-gate-on-stop.kiro.hook`
    - _Requirements: 5.1, 5.2, 5.3, 5.4_

  - [x] 1.2 Register hook in `senzing-bootcamp/hooks/hook-categories.yaml`
    - Add `enforce-sequential-steps` to the `critical` category list (alphabetical order)
    - _Requirements: 5.5_

- [x] 2. Strengthen steering-file language
  - [x] 2.1 Update `senzing-bootcamp/steering/agent-instructions.md`
    - Add the `never-skip-numbered-steps` rule to the existing Mandatory Gate Precedence section
    - Rule text must state: same absolute precedence as ⛔ mandatory gates, execute each numbered step sequentially, advancing by exactly one step at a time
    - Include the consent clause: agent SHALL ask bootcamper for explicit consent before combining or abbreviating steps
    - _Requirements: 7.1, 7.3, 4.1, 2.2_

  - [x] 2.2 Update `senzing-bootcamp/steering/conversation-protocol.md`
    - Add a "Numbered Step Execution Boundary" subsection to the Question Stop Protocol section
    - Must state: every numbered step with a 👉 question is a mandatory execution boundary with same absolute precedence as ⛔ mandatory gates
    - Include all four SHALL clauses from the design (sequential order, no gap > 1, no skip for internal reasons, write `.question_pending`)
    - _Requirements: 7.4, 1.1, 1.2, 1.3, 3.3_

- [x] 3. Add Sequential Execution Reminders to module steering files
  - [x] 3.1 Add reminder block to `module-01-business-problem.md`
    - Insert the blockquote reminder after frontmatter and before the first workflow step
    - Text: `> ⚠️ **Sequential Execution Rule (absolute precedence):** Execute every numbered step in this module one at a time, in order. Never skip, combine, or abbreviate any step containing a 👉 question. This rule has the same precedence as ⛔ mandatory gates — no internal reasoning can override it.`
    - _Requirements: 6.1, 6.2, 6.3_

  - [x] 3.2 Add reminder block to `module-02-sdk-setup.md`
    - Same blockquote reminder text as 3.1, inserted after frontmatter
    - _Requirements: 6.1, 6.2, 6.3_

  - [x] 3.3 Add reminder block to `module-03-system-verification.md`
    - Same blockquote reminder text as 3.1, inserted after frontmatter
    - _Requirements: 6.1, 6.2, 6.3_

  - [x] 3.4 Add reminder block to `module-04-data-collection.md`
    - Same blockquote reminder text as 3.1, inserted after frontmatter
    - _Requirements: 6.1, 6.2, 6.3_

  - [x] 3.5 Add reminder block to `module-05-data-quality-mapping.md`
    - Same blockquote reminder text as 3.1, inserted after frontmatter
    - _Requirements: 6.1, 6.2, 6.3_

  - [x] 3.6 Add reminder block to `module-06-data-processing.md`
    - Same blockquote reminder text as 3.1, inserted after frontmatter
    - _Requirements: 6.1, 6.2, 6.3_

  - [x] 3.7 Add reminder block to `module-07-query-visualize-discover.md`
    - Same blockquote reminder text as 3.1, inserted after frontmatter
    - _Requirements: 6.1, 6.2, 6.3_

  - [x] 3.8 Add reminder block to `module-08-performance.md`
    - Same blockquote reminder text as 3.1, inserted after frontmatter
    - _Requirements: 6.1, 6.2, 6.3_

  - [x] 3.9 Add reminder block to `module-09-security.md`
    - Same blockquote reminder text as 3.1, inserted after frontmatter
    - _Requirements: 6.1, 6.2, 6.3_

  - [x] 3.10 Add reminder block to `module-10-monitoring.md`
    - Same blockquote reminder text as 3.1, inserted after frontmatter
    - _Requirements: 6.1, 6.2, 6.3_

  - [x] 3.11 Add reminder block to `module-11-deployment.md`
    - Same blockquote reminder text as 3.1, inserted after frontmatter
    - _Requirements: 6.1, 6.2, 6.3_

- [x] 4. Checkpoint - Verify hook and steering changes
  - Ensure all tests pass, ask the user if questions arise.

- [x] 5. Write tests for the enforce-sequential-steps feature
  - [x] 5.1 Create `senzing-bootcamp/tests/test_enforce_sequential_steps.py`
    - Write unit tests verifying: hook JSON has valid schema (name, version, when, then), hook `when.type` is `"agentStop"`, hook is registered in `hook-categories.yaml` under `critical`, hook prompt contains key detection phrases
    - Write property tests using Hypothesis for: step-gap violation detection across random progress states, valid single-step progression produces no false positives, question-pending violation detection
    - Implement the detection logic as a pure Python function to enable property testing
    - _Requirements: 5.1, 5.2, 5.3, 5.4_

  - [x] 5.2 Write property test for step-gap violation detection
    - **Property 1: Step-gap violations are always detected**
    - **Validates: Requirements 1.1, 1.2, 5.3**

  - [x] 5.3 Write property test for valid progression (no false positives)
    - **Property 2: Valid single-step progression produces no violation**
    - **Validates: Requirements 5.4**

  - [x] 5.4 Write property test for question-pending advancement detection
    - **Property 3: Question-pending advancement is always detected**
    - **Validates: Requirements 1.3, 3.3**

  - [x] 5.5 Create `senzing-bootcamp/tests/test_sequential_reminder_presence.py`
    - Write property tests verifying: all 11 module steering files contain the Sequential Execution Reminder block, reminder text contains required key phrases (absolute precedence, sequential, never skip)
    - _Requirements: 6.1, 6.2, 6.3_

  - [x] 5.6 Write property test for reminder presence in all modules
    - **Property 4: Sequential Execution Reminder is present in all module steering files**
    - **Validates: Requirements 6.1, 6.2, 6.3**

- [x] 6. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties from the design document
- Unit tests validate specific examples and edge cases
- The implementation language is Python (pytest + Hypothesis), matching the existing test infrastructure
- Hook tests validating real hook files go in `senzing-bootcamp/tests/` per project structure rules
- The 11 module steering files use varying naming (some have phase suffixes); the primary module file for each module is the target for the reminder block

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1", "2.1", "2.2"] },
    { "id": 1, "tasks": ["1.2", "3.1", "3.2", "3.3", "3.4", "3.5", "3.6", "3.7", "3.8", "3.9", "3.10", "3.11"] },
    { "id": 2, "tasks": ["5.1", "5.5"] },
    { "id": 3, "tasks": ["5.2", "5.3", "5.4", "5.6"] }
  ]
}
```
