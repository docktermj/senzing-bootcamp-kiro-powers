# Implementation Plan: Suppress Hook Reasoning

## Overview

Restructure both hook prompts (`write-policy-gate.kiro.hook` and `question-format-gate.kiro.hook`) with dual suppression reinforcement (front-loaded preamble + closing OUTPUT FORMAT section) and strengthen the hook silence rule in `agent-instructions.md`. Extend existing test files with property-based tests validating the new suppression structure.

## Tasks

- [x] 1. Restructure Write Policy Gate prompt with dual suppression reinforcement
  - [x] 1.1 Add suppression preamble and anti-narration directives to write-policy-gate.kiro.hook
    - Add `⚠️ SILENCE RULE` preamble as the first line of the prompt (before "WRITE POLICY GATE")
    - Add explicit anti-narration directive with enumerated forbidden phrases in the FAST PATH GATE section
    - Add edge-case instruction for non-SQL content referencing Senzing indicators (JSON configs with connection strings)
    - Preserve all existing CHECK 1, CHECK 2, CHECK 3 logic verbatim
    - _Requirements: 1.1, 1.2, 1.4, 1.5, 2.1, 2.2, 2.3, 6.1, 7.1, 7.2, 7.3_

  - [x] 1.2 Add closing OUTPUT FORMAT section to write-policy-gate.kiro.hook
    - Append OUTPUT FORMAT (STRICT) section after CHECK 3
    - Include zero-output directive for passing checks
    - Include FORBIDDEN output list with specific narration phrases
    - Ensure SLOW PATH text remains character-for-character identical to baseline
    - _Requirements: 1.3, 6.2_

  - [x] 1.3 Write property tests for Write Policy Gate suppression structure (Properties 1-4)
    - **Property 1: Write Policy Gate front-loaded suppression preamble**
    - **Property 2: Write Policy Gate closing OUTPUT FORMAT section**
    - **Property 3: Write Policy Gate anti-narration directives**
    - **Property 4: Write Policy Gate edge-case Senzing indicator suppression**
    - Add `TestDualReinforcementStructure` class to `tests/test_suppress_policy_pass_output.py`
    - Use `@settings(max_examples=20)` and class-based organization
    - **Validates: Requirements 1.2, 1.3, 1.4, 1.5, 2.1, 2.2, 2.3, 6.1, 6.2, 8.1, 8.2**

- [x] 2. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 3. Restructure Question Format Gate prompt with dual suppression reinforcement
  - [x] 3.1 Add suppression preamble and anti-narration directives to question-format-gate.kiro.hook
    - Add `⚠️ SILENCE RULE` preamble as the first line of the prompt (before "QUESTION FORMAT GATE")
    - Add explicit anti-narration directive forbidding phrases like "The question is not compound", "No rewrite needed", "Scanning for compound questions"
    - Add anti-narration directive for rewrite case forbidding "This is a compound question", "Let me rewrite"
    - Preserve all existing DETECTION, NOT COMPOUND, ACTION, and RULES logic verbatim
    - _Requirements: 3.1, 3.2, 3.4, 4.1, 4.2, 4.3, 6.3, 7.4, 7.5_

  - [x] 3.2 Add closing OUTPUT FORMAT section to question-format-gate.kiro.hook
    - Append OUTPUT FORMAT (STRICT) section after the RULES section
    - Include period-only directive for no-rewrite and corrected-question-only directive for rewrite
    - Include FORBIDDEN output list with specific narration phrases
    - Include instruction to preserve non-question content
    - _Requirements: 3.3, 6.4_

  - [x] 3.3 Write property tests for Question Format Gate suppression structure (Properties 5-7)
    - **Property 5: Question Format Gate front-loaded suppression preamble**
    - **Property 6: Question Format Gate closing OUTPUT FORMAT section**
    - **Property 7: Question Format Gate rewrite-only output directive**
    - Add `TestQuestionFormatGateSuppression` class to `tests/test_hook_silent_fast_path_properties.py`
    - Use `@settings(max_examples=20)` and class-based organization
    - **Validates: Requirements 3.2, 3.3, 3.4, 4.1, 4.2, 4.3, 6.3, 6.4, 6.5, 8.3**

- [x] 4. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 5. Strengthen Agent Instructions hook silence rule
  - [x] 5.1 Replace hook silence rule in agent-instructions.md with strengthened version
    - Replace the existing single-paragraph `🔇 Hook silence rule` with multi-line strengthened rule
    - Add enumerated FORBIDDEN hook reasoning output list
    - Add zero-visible-tokens language for passing checks
    - Add corrective-output-only rule for slow-path cases
    - Add explicit coverage of all hook types (preToolUse, agentStop, future hooks)
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

  - [x] 5.2 Write property tests for Agent Instructions hook silence rule (Property 8)
    - **Property 8: Agent Instructions strengthened hook silence rule**
    - Add `TestAgentInstructionsHookSilence` class to `tests/test_suppress_policy_pass_output.py`
    - Validate enumerated forbidden patterns, zero-visible-tokens language, corrective-only output, all hook types coverage
    - Use `@settings(max_examples=20)` and class-based organization
    - **Validates: Requirements 5.1, 5.2, 5.3, 5.4, 5.5, 8.4**

- [x] 6. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 7. Validate preservation of existing behavior
  - [x] 7.1 Run existing preservation tests to confirm no regressions
    - Run `TestPreservationProperties` in both test files to confirm SLOW PATH baseline unchanged
    - Run existing SQL blocking, compound question, and file path policy tests
    - Confirm hook JSON schema conformance (name, version, when, then fields)
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

  - [x] 7.2 Write property tests for preservation of violation detection (Properties 9-12)
    - **Property 9: Write Policy Gate SQL blocking preservation**
    - **Property 10: Write Policy Gate single-question enforcement preservation**
    - **Property 11: Write Policy Gate file path policy preservation**
    - **Property 12: Question Format Gate detection logic preservation**
    - Extend existing `TestPreservationProperties` classes or add new assertions
    - **Validates: Requirements 7.1, 7.2, 7.3, 7.4, 7.5, 8.5**

- [x] 8. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties from the design document
- The implementation language is Python (pytest + Hypothesis) matching the existing test infrastructure
- All hook prompt modifications must preserve existing slow-path logic character-for-character
- Hook JSON schema (name, version, when, then) must remain valid after modifications
- Test files extend existing classes in `tests/test_suppress_policy_pass_output.py` and `tests/test_hook_silent_fast_path_properties.py`

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1", "3.1", "5.1"] },
    { "id": 1, "tasks": ["1.2", "3.2"] },
    { "id": 2, "tasks": ["1.3", "3.3", "5.2"] },
    { "id": 3, "tasks": ["7.1"] },
    { "id": 4, "tasks": ["7.2"] }
  ]
}
```
