# Implementation Plan: Agent Behavior Rules

## Overview

This plan implements four agent behavior rules as a new steering file with auto-inclusion, a validation script for programmatic rule checking, property-based tests using Hypothesis, and unit tests. The implementation follows the project's established patterns for steering files, Python scripts, and test suites.

## Tasks

- [x] 1. Create validation script with core detection functions
  - [x] 1.1 Create `senzing-bootcamp/scripts/validate_behavior_rules.py` with continuation request detection
    - Implement `CONTINUATION_PHRASES` list and `is_continuation_request(message: str) -> bool`
    - Implement `PAUSE_PATTERNS` list and `contains_pause_language(text: str) -> bool`
    - Follow script pattern: shebang, docstring, `from __future__ import annotations`, stdlib only, `@dataclass`
    - Include `main(argv=None)` with argparse CLI and `if __name__ == "__main__": main()` entry point
    - _Requirements: 1.1, 1.2, 1.4, 1.5_

  - [x] 1.2 Add acknowledgment validation to `validate_behavior_rules.py`
    - Implement `AcknowledgmentResult` dataclass with fields: `valid`, `sentence_count`, `word_count`, `is_substantive`, `position_ok`
    - Implement `CONTENT_FREE_PHRASES` list
    - Implement `validate_acknowledgment(text: str, bootcamper_response: str = "") -> AcknowledgmentResult`
    - Sentence counting via period/exclamation/question mark splitting; word counting via whitespace splitting
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

  - [x] 1.3 Add compound question detection and pointer indicator checking to `validate_behavior_rules.py`
    - Implement `CONJUNCTION_PATTERNS` list and `is_compound_question(question: str) -> bool`
    - Implement `has_pointer_prefix(line: str) -> bool` checking for 👉 prefix
    - Implement `validate_steering_file(path: Path) -> list[Violation]` for full-file validation
    - Define `Violation` dataclass with `rule`, `line_number`, `message` fields
    - _Requirements: 3.1, 3.3, 3.5, 4.1, 4.3_

- [x] 2. Create the steering file
  - [x] 2.1 Create `senzing-bootcamp/steering/agent-behavior-rules.md` with YAML frontmatter and all four rules
    - Frontmatter: `inclusion: auto`, description covering all four rules
    - Rule 1: Honor Explicit Continuation Requests — list continuation phrases, prohibit pause/stop/defer language, context-limit guidance
    - Rule 2: Acknowledge Bootcamper Responses — ≤2 sentences, ≤50 words, substantive content, position within first 2 sentences
    - Rule 3: Eliminate Ambiguous Yes/No Questions — compound question prohibition, numbered list format, rewrite requirement
    - Rule 4: Consistent Pointer Indicator — 👉 prefix on all input-requiring prompts, all contexts, multi-prompt handling
    - Target ~400-600 tokens for `medium` size category
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 2.1, 2.2, 2.3, 2.4, 2.5, 3.1, 3.2, 3.3, 3.4, 3.5, 4.1, 4.2, 4.3, 4.4, 4.5_

  - [x] 2.2 Update `senzing-bootcamp/steering/steering-index.yaml` with new file entry
    - Add `agent-behavior-rules.md` to `file_metadata` section with measured `token_count` and `size_category: medium`
    - _Requirements: 4.4_

- [x] 3. Checkpoint - Verify steering file and script
  - Ensure all tests pass, ask the user if questions arise.

- [x] 4. Write property-based tests
  - [x] 4.1 Write property test for continuation request classification
    - **Property 1: Continuation Request Classification Round-Trip**
    - **Validates: Requirements 1.1, 1.4, 1.5**
    - Create `senzing-bootcamp/tests/test_agent_behavior_rules_properties.py`
    - Use `@given()` with `@settings(max_examples=100)` for pure-function tests
    - Custom `st_continuation_message()` strategy generating strings with/without continuation phrases

  - [x] 4.2 Write property test for pause language detection
    - **Property 2: Pause Language Detection**
    - **Validates: Requirements 1.1, 1.2, 1.4**
    - Custom `st_pause_text()` strategy generating strings with/without pause patterns

  - [x] 4.3 Write property test for acknowledgment length constraint
    - **Property 3: Acknowledgment Length Constraint**
    - **Validates: Requirements 2.1, 2.2**
    - Custom `st_acknowledgment_text()` strategy generating texts of varying sentence/word counts

  - [x] 4.4 Write property test for substantive acknowledgment rejection
    - **Property 4: Substantive Acknowledgment Rejection of Content-Free Phrases**
    - **Validates: Requirements 2.3**
    - Strategy generating combinations of content-free phrases with optional punctuation/whitespace

  - [x] 4.5 Write property test for compound question detection
    - **Property 5: Compound Question Detection**
    - **Validates: Requirements 3.1, 3.3, 3.5**
    - Custom `st_compound_question()` strategy generating questions with/without prose conjunctions

  - [x] 4.6 Write property test for numbered list format requirement
    - **Property 6: Numbered List Format Requirement**
    - **Validates: Requirements 3.2**
    - Strategy generating multi-alternative questions in numbered vs. prose format

  - [x] 4.7 Write property test for universal pointer indicator presence
    - **Property 7: Universal Pointer Indicator Presence**
    - **Validates: Requirements 4.1, 4.3, 4.4, 4.5**
    - Strategy generating prompt lines with/without 👉 prefix

- [x] 5. Write unit tests
  - [x] 5.1 Write unit tests for continuation and pause detection
    - Create `senzing-bootcamp/tests/test_agent_behavior_rules_unit.py`
    - Test specific examples: "continue", "let's keep going", "next module", mixed case, negatives
    - Test pause patterns: "take a break", "pick this up later", "call it a day", negatives
    - Edge cases: empty string, whitespace only, unicode, very long input
    - _Requirements: 1.1, 1.2, 1.4, 1.5_

  - [x] 5.2 Write unit tests for acknowledgment validation
    - Test boundary conditions: exactly 50 words, exactly 2 sentences, 51 words, 3 sentences
    - Test substantiveness: "Got it" alone fails, "Got it, your Senzing instance uses PostgreSQL" passes
    - Test position checking and empty/whitespace responses
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

  - [x] 5.3 Write unit tests for compound question and pointer indicator
    - Test compound questions: "Would you like A or B?", "Should we do X, or alternatively Y?"
    - Test simple questions: "Ready to continue?", "Does that look correct?"
    - Test pointer prefix: "👉 Ready?", "Ready?" (missing), "- 👉 Choose:" (with list marker)
    - Test steering file validation end-to-end
    - _Requirements: 3.1, 3.2, 3.3, 3.5, 4.1, 4.3, 4.5_

  - [x] 5.4 Write unit tests for steering file structure validation
    - Verify `agent-behavior-rules.md` has valid YAML frontmatter with `inclusion: auto`
    - Verify `steering-index.yaml` contains the new file entry
    - Verify file is well-formed CommonMark
    - _Requirements: 4.4_

- [x] 6. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties from the design document
- Unit tests validate specific examples and edge cases
- The validation script uses Python 3.11+ stdlib only (no third-party deps)
- Tests use pytest + Hypothesis with `@settings(max_examples=100)` for pure-function property tests
- Import the validation script via `sys.path` manipulation per project convention

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1"] },
    { "id": 1, "tasks": ["1.2", "2.1"] },
    { "id": 2, "tasks": ["1.3", "2.2"] },
    { "id": 3, "tasks": ["4.1", "4.2", "5.1"] },
    { "id": 4, "tasks": ["4.3", "4.4", "5.2"] },
    { "id": 5, "tasks": ["4.5", "4.6", "4.7", "5.3"] },
    { "id": 6, "tasks": ["5.4"] }
  ]
}
```
