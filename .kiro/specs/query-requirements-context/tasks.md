# Implementation Plan: Query Requirements Context

## Overview

This implementation updates Module 7 Step 1 in the bootcamp steering file to read the business problem document (`docs/business_problem.md`) before asking query requirements. The agent derives query requirements from previously-stated success criteria and desired outputs, presents them for confirmation, and falls back to the open-ended question only when the document is missing or lacks usable content. A helper parsing script validates document content, and comprehensive property-based and unit tests ensure correctness.

## Tasks

- [x] 1. Create helper parsing script for business problem extraction
  - [x] 1.1 Create `senzing-bootcamp/scripts/parse_business_problem.py` with argparse CLI, dataclasses, and section extraction logic
    - Define `BusinessProblemContent` dataclass with fields: `success_criteria: list[str]`, `desired_output_format: str`, `desired_output_use_case: str`, `desired_output_integration: str`
    - Implement `parse_business_problem(content: str) -> BusinessProblemContent` that extracts Success Criteria bullets and Desired Output fields from markdown content
    - Implement `has_usable_content(bpc: BusinessProblemContent) -> bool` returning True if at least one success criterion exists OR at least one desired output field is non-empty
    - Implement `derive_query_requirements(bpc: BusinessProblemContent, max_count: int = 10) -> list[dict[str, str]]` returning list of `{"requirement": ..., "source": ...}` dicts bounded 1–10
    - Set up argparse with `--file` argument and `main()` entry point
    - _Requirements: 1.1, 1.2, 2.1, 2.2, 2.3_

- [x] 2. Update Module 7 steering file Step 1
  - [x] 2.1 Replace the current Step 1 in `senzing-bootcamp/steering/module-07-query-visualize-discover.md` with the business-problem-first flow
    - Replace the existing `1. **Define query requirements**: Ask: "What questions do you need to answer with your data?"` block with the multi-path instruction block
    - Add read instruction: agent reads `docs/business_problem.md` as the first action
    - Add content check: agent evaluates if success criteria or desired outputs exist
    - Add derivation instruction: agent derives 1–10 query requirements from document content with source attribution
    - Add presentation instruction: agent presents derived requirements with attribution sentence ("Based on your business problem from Module 1...")
    - Add confirmation prompt: agent asks bootcamper if there is anything to add or change
    - Add rejection handler: if bootcamper rejects all, agent asks fresh question without referencing rejected items
    - Add fallback instruction: if file missing or both sections empty, agent asks "What questions do you need to answer with your data?" without mentioning Module 1 or missing documents
    - Retain the existing "Common queries" list as guidance for both paths
    - Preserve the existing Checkpoint at end of Step 1
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 2.1, 2.2, 2.3, 2.4, 3.1, 3.2, 3.3, 3.4, 3.5_

- [x] 3. Checkpoint - Verify steering file is valid
  - Ensure all tests pass, ask the user if questions arise.

- [x] 4. Write property-based tests
  - [x] 4.1 Create `senzing-bootcamp/tests/test_query_requirements_context_properties.py` with Hypothesis strategies and imports
    - Set up test file with `sys.path` manipulation to import `parse_business_problem`
    - Define Hypothesis strategies: `st_success_criteria()` (lists of non-empty strings), `st_desired_output()` (format/use_case/integration strings), `st_business_problem_doc()` (full markdown documents with varying section content)
    - Use `@settings(max_examples=20)` on all property tests per project convention
    - _Requirements: 1.1, 2.1_

  - [x] 4.2 Write property test for Property 1: Read-before-interact ordering
    - **Property 1: Read-before-interact ordering**
    - For any valid Module 7 Step 1 steering content, the instruction to read `docs/business_problem.md` appears before any pointing question, "Ask:" directive, or bootcamper interaction prompt in the step's primary flow
    - **Validates: Requirements 1.1, 3.1, 3.5**

  - [x] 4.3 Write property test for Property 2: Derivation bounds and traceability
    - **Property 2: Derivation bounds and traceability**
    - For any business problem document containing N success criteria and M desired output fields (where N + M >= 1), the derivation logic produces between 1 and 10 query requirements, and each derived requirement references at least one source criterion or desired output
    - **Validates: Requirements 1.2**

  - [x] 4.4 Write property test for Property 3: Fallback on missing or empty content
    - **Property 3: Fallback on missing or empty content**
    - For any state where `docs/business_problem.md` does not exist, OR exists but contains zero success criteria AND zero desired output content, the system signals the fallback path (open-ended question) rather than the derivation path
    - **Validates: Requirements 2.1, 2.2**

  - [x] 4.5 Write property test for Property 4: Derive when content is available
    - **Property 4: Derive when content is available**
    - For any business problem document that contains at least one success criterion OR at least one non-empty desired output field, the system signals the derivation path (not the fallback path)
    - **Validates: Requirements 2.3**

- [x] 5. Write unit tests for steering file content
  - [x] 5.1 Create `senzing-bootcamp/tests/test_query_requirements_context_unit.py` with unit tests validating steering file structure
    - Test: Step 1 contains read instruction (`docs/business_problem.md`) before any "Ask:" directive or pointing question
    - Test: Step 1 primary path includes derivation instructions (derive query requirements from success criteria/desired outputs)
    - Test: Step 1 includes confirmation phrasing ("add or change")
    - Test: Step 1 includes attribution example sentence ("Based on your business problem from Module 1")
    - Test: Step 1 includes rejection handler without back-references to rejected items
    - Test: Fallback path does not mention Module 1 or missing documents
    - Test: Fallback path is conditional (IF missing/empty)
    - Test: Open-ended question retained only as fallback, not primary path
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 2.4, 3.4, 3.5_

  - [x] 5.2 Write unit tests for parsing logic
    - Test: `parse_business_problem` extracts success criteria from well-formed document
    - Test: `parse_business_problem` extracts desired output fields
    - Test: `has_usable_content` returns False for empty document
    - Test: `has_usable_content` returns True when only success criteria present
    - Test: `has_usable_content` returns True when only desired output present
    - Test: `derive_query_requirements` returns bounded list (1-10)
    - Test: `derive_query_requirements` includes source attribution for each item
    - _Requirements: 1.2, 2.1, 2.2, 2.3_

- [x] 6. Checkpoint - Run all tests
  - Ensure all tests pass, ask the user if questions arise.

- [x] 7. Integration wiring and final validation
  - [x] 7.1 Write integration tests in `senzing-bootcamp/tests/test_query_requirements_context_integration.py`
    - Test: Full steering file passes CommonMark validation (structural integrity after modification)
    - Test: Steering file retains valid YAML frontmatter
    - Test: Module 7 entry in `steering-index.yaml` still resolves correctly
    - Test: Step 1 checkpoint marker is preserved
    - _Requirements: 3.1, 3.5_

  - [x] 7.2 Run `python3 senzing-bootcamp/scripts/validate_commonmark.py` to verify modified steering file remains valid CommonMark
    - _Requirements: 3.1_

  - [x] 7.3 Run `python3 senzing-bootcamp/scripts/measure_steering.py --check` to verify token budgets are not exceeded
    - _Requirements: 3.1_

- [x] 8. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties from the design document
- Unit tests validate specific examples and edge cases
- The parsing script uses Python 3.11+ stdlib only (no third-party deps)
- Tests use pytest + Hypothesis with `@settings(max_examples=20)` per project convention
- Import parsing script in tests via `sys.path` manipulation per project convention
- The steering file modification is the primary deliverable; the parsing script provides testable extraction logic

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1"] },
    { "id": 1, "tasks": ["2.1"] },
    { "id": 2, "tasks": ["4.1", "5.1"] },
    { "id": 3, "tasks": ["4.2", "4.3", "4.4", "4.5", "5.2"] },
    { "id": 4, "tasks": ["7.1"] },
    { "id": 5, "tasks": ["7.2", "7.3"] }
  ]
}
```
