# Implementation Plan: Proceed on Confirmation

## Overview

Implement a two-layer defense against minimal-output violations after module transition confirmations. Layer 1 strengthens steering language across three existing files. Layer 2 adds a detect-and-retry agentStop hook that catches violations and forces the agent to retry with proper module start content. Property-based tests validate the core detection logic.

## Tasks

- [x] 1. Modify steering files with strengthened transition rules
  - [x] 1.1 Add Minimum Content Requirement to conversation-protocol.md
    - Insert the "📏 MINIMUM CONTENT REQUIREMENT" rule into the Module Transition Protocol section
    - Place it after the existing "When you ask 'Ready for Module X'" paragraph and before the "⛔ PROHIBITED" rule
    - Content must specify the four required elements (banner, journey map, before/after framing, Step 1 content)
    - Content must state that output under 50 characters is a protocol violation
    - All existing rules (⛔ PROHIBITED, 🔒 COMMITMENT RULE, ⚠️ CONTEXT-LIMIT GUIDANCE) must remain unchanged
    - _Requirements: 2.2, 3.1, 3.4_

  - [x] 1.2 Add Module Transition Execution section to agent-instructions.md
    - Add a new `## Module Transition Execution` section after the `## Communication` section
    - Include the four-step execution sequence (banner, journey map, before/after framing, Step 1)
    - Include the ⛔ ZERO TOLERANCE rule prohibiting output under 50 characters
    - State this rule takes precedence over agent-internal reasoning when a Transition_Confirmation is received
    - _Requirements: 2.3, 3.3_

  - [x] 1.3 Add Confirmation Response Requirements section to module-transitions.md
    - Add a new `## Confirmation Response Requirements` section after the `## Transition Integrity` section
    - Include the required elements table (Module Start Banner, Journey Map, Before/After Framing, Step 1 Introduction)
    - Include the 50-character hard minimum rule
    - List the violation patterns that trigger the detect-and-retry hook
    - _Requirements: 3.2_

- [x] 2. Checkpoint - Verify steering modifications
  - Ensure all three steering files contain the new sections while retaining existing content, ask the user if questions arise.

- [x] 3. Create the detect-and-retry hook
  - [x] 3.1 Create detect-transition-retry.kiro.hook in senzing-bootcamp/hooks/
    - Create valid JSON hook file with `name`, `version`, `description`, `when`, and `then` fields
    - `name` field: `"to detect minimal output after module transition confirmation and force retry"`
    - `version` field: `"1.0.0"`
    - `when.type`: `"agentStop"`
    - `then.type`: `"askAgent"`
    - `then.prompt`: Implement the three-step detection logic (detect Transition_Confirmation, evaluate output, produce retry instructions or ".")
    - Prompt must include the transition question patterns, affirmative phrase list, and 50-character threshold
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 5.1, 5.2, 5.3, 5.4, 5.5_

  - [x] 3.2 Register detect-transition-retry in hook-categories.yaml
    - Add `detect-transition-retry` to the `critical` category list in alphabetical order
    - _Requirements: 5.6_

- [x] 4. Checkpoint - Verify hook file and registration
  - Ensure the hook file is valid JSON with all required fields, and the hook is registered in hook-categories.yaml under critical, ask the user if questions arise.

- [x] 5. Write property-based tests for detection logic
  - [x] 5.1 Create tests/test_detect_transition_retry.py with test helpers
    - Implement `is_minimal_output(output: str) -> bool` helper function matching the design specification
    - Implement `is_transition_confirmation(message: str, prior_assistant_message: str) -> bool` helper function
    - Implement `hook_decision(is_confirmation: bool, is_minimal: bool) -> str` helper function
    - Define `TRANSITION_QUESTION_PATTERNS`, `AFFIRMATIVE_PHRASES`, and `MINIMAL_OUTPUT_THRESHOLD` constants
    - _Requirements: 1.2, 1.3, 4.2, 4.6_

  - [x] 5.2 Write property test for minimal output classification
    - **Property 1: Minimal Output Classification Correctness**
    - Test that strings empty, whitespace-only, exactly ".", single-word acknowledgments, or < 50 chars return True
    - Test that strings ≥ 50 chars that are not single-word acknowledgments return False
    - Use Hypothesis strategies generating random strings of varying lengths and content types
    - **Validates: Requirements 1.2, 1.3, 2.1**

  - [x] 5.3 Write property test for transition confirmation recognition
    - **Property 2: Transition Confirmation Recognition**
    - Test that detection returns True iff prior message contains a transition question pattern AND bootcamper message contains an affirmative phrase
    - Use Hypothesis strategies generating random (prior_message, response) pairs
    - **Validates: Requirements 4.2, 4.6**

  - [x] 5.4 Write property test for hook decision logic
    - **Property 3: Hook Decision Logic Completeness**
    - Test that retry instructions are produced iff is_transition_confirmation=True AND is_minimal_output=True
    - Test that "." is produced in all other cases
    - Use Hypothesis strategies generating all boolean combinations
    - **Validates: Requirements 4.3, 4.4, 4.5**

  - [x] 5.5 Write property test for hook file schema validation
    - **Property 4: Hook File Schema Validity**
    - Parse `senzing-bootcamp/hooks/detect-transition-retry.kiro.hook` as JSON
    - Verify required fields (`name`, `version`, `description`, `when`, `then`) exist
    - Verify `when.type` is `"agentStop"` and `then.type` is `"askAgent"`
    - Verify `name` field starts with "to "
    - **Validates: Requirements 5.2, 5.4, 5.5**

- [x] 6. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties from the design document
- The implementation language is Python (pytest + Hypothesis) per the project's tech stack
- Hook tests validating real hook files go in repo-root `tests/`, not `senzing-bootcamp/tests/`
- All steering file modifications are additive — existing content must be preserved

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1", "1.2", "1.3"] },
    { "id": 1, "tasks": ["3.1", "3.2"] },
    { "id": 2, "tasks": ["5.1"] },
    { "id": 3, "tasks": ["5.2", "5.3", "5.4", "5.5"] }
  ]
}
```
