# Implementation Plan: Steering Structural Validation

## Overview

Create a property-based test suite at `senzing-bootcamp/tests/test_steering_structure_properties.py` that validates structural invariants across all module steering files. The suite parses `steering-index.yaml` to discover modules, resolves file paths, and uses Hypothesis to draw module numbers and verify six structural rules plus file existence.

## Tasks

- [x] 1. Create test file with imports, constants, and index parser
  - [x] 1.1 Create `senzing-bootcamp/tests/test_steering_structure_properties.py` with imports and regex patterns
    - Import pytest, hypothesis, re, pathlib, dataclasses, yaml
    - Define all regex constants: `RE_NUMBERED_STEP`, `RE_CHECKPOINT`, `RE_POINTING_QUESTION`, `RE_STOP_INSTRUCTION`, `RE_BEFORE_AFTER`, `RE_PREREQUISITES`, `RE_FRONTMATTER_START`
    - _Requirements: 7.5_
  - [x] 1.2 Implement `ModuleFiles` dataclass and `parse_steering_index` function
    - Define `ModuleFiles` dataclass with `module_number`, `root_file`, `phase_files`, and `all_files` property
    - Implement `parse_steering_index(index_path: Path) -> dict[int, ModuleFiles]` handling both simple string entries and phased object entries
    - Raise `FileNotFoundError` if index path missing, `ValueError` if referenced files don't exist on disk
    - _Requirements: 8.1, 8.2, 8.3, 8.4_
  - [x] 1.3 Implement session-scoped pytest fixture and Hypothesis strategy
    - Create `@pytest.fixture(scope="session")` fixture that parses `senzing-bootcamp/steering/steering-index.yaml`
    - Implement `st_module_number(index)` strategy using `st.sampled_from(sorted(index.keys()))`
    - _Requirements: 7.1, 7.2_

- [x] 2. Implement structural validator functions
  - [x] 2.1 Implement `check_before_after_framing` validator
    - Pure function taking `content: str` and `file_path: Path`, returning `list[str]` of violations
    - Search for `**Before/After**` pattern in file content
    - _Requirements: 1.1, 1.2_
  - [x] 2.2 Implement `check_step_checkpoint_correspondence` validator
    - Extract all numbered steps and checkpoint instructions with step numbers
    - Verify every numbered step has a corresponding checkpoint between it and the next step (or EOF)
    - _Requirements: 2.1, 2.2, 2.3_
  - [x] 2.3 Implement `check_pointing_question_stop` validator
    - Locate each 👉 line, search up to 5 non-blank lines or next numbered step for STOP/WAIT
    - Report file path and line number on failure
    - _Requirements: 3.1, 3.2, 3.3_
  - [x] 2.4 Implement `check_single_question_per_step` validator
    - Group 👉 questions by their enclosing numbered step
    - Report failure if any step has more than one pointing question
    - _Requirements: 4.1, 4.2_
  - [x] 2.5 Implement `check_prerequisites_listed` validator
    - Search for `Prerequisites` followed by colon in root module files
    - _Requirements: 5.1, 5.2_
  - [x] 2.6 Implement `check_yaml_frontmatter` validator
    - Verify file starts with `---` delimiter, extract frontmatter block, check for `inclusion: manual`
    - Report missing frontmatter, missing key, or wrong value
    - _Requirements: 6.1, 6.2, 6.3, 6.4_

- [x] 3. Checkpoint
  - Ensure all validator functions are syntactically correct by running `python -c "import senzing_bootcamp_tests"` or equivalent import check. Ask the user if questions arise.

- [x] 4. Implement Hypothesis property test classes
  - [x] 4.1 Implement `TestProperty1BeforeAfterFraming` class
    - Use `@given(module_num=st_module_number(index))` with `@settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])`
    - For each module, check root file and phase files with steps; phase sub-files may delegate to root
    - Assert `violations == []` with descriptive message including module number
    - _Requirements: 1.3, 7.3, 7.4_
  - [x] 4.2 Implement `TestProperty2StepCheckpointCorrespondence` class
    - Draw module number, resolve files, apply `check_step_checkpoint_correspondence` to all files with numbered steps
    - `@settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])`
    - _Requirements: 2.4, 7.3, 7.4_
  - [x] 4.3 Implement `TestProperty3PointingQuestionStop` class
    - Draw module number, resolve files, apply `check_pointing_question_stop` to all module files
    - `@settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])`
    - _Requirements: 3.4, 7.3, 7.4_
  - [x] 4.4 Implement `TestProperty4SingleQuestionPerStep` class
    - Draw module number, resolve files, apply `check_single_question_per_step` to files with numbered steps
    - `@settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])`
    - _Requirements: 4.3, 7.3, 7.4_
  - [x] 4.5 Implement `TestProperty5PrerequisitesListed` class
    - Draw module number, resolve root file only, apply `check_prerequisites_listed`
    - `@settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])`
    - _Requirements: 5.3, 7.3, 7.4_
  - [x] 4.6 Implement `TestProperty6YamlFrontmatter` class
    - Draw module number, resolve all files (root + phases), apply `check_yaml_frontmatter`
    - `@settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])`
    - _Requirements: 6.5, 7.3, 7.4_
  - [x] 4.7 Implement `TestProperty7IndexFileExistence` class
    - Draw module number, verify all referenced file paths exist on disk
    - `@settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])`
    - _Requirements: 8.1, 8.4, 7.3, 7.4_

- [x] 5. Implement example-based test class
  - [x] 5.1 Implement `TestIndexResolution` class with example-based tests
    - Test simple index entry: verify module 2 resolves to a single root file with no phases
    - Test phased index entry: verify module 5 resolves to root + phase files
    - Test missing file error: create temp index referencing non-existent file, assert `ValueError`
    - _Requirements: 8.2, 8.3, 8.4_

- [x] 6. Final checkpoint
  - Run `pytest senzing-bootcamp/tests/test_steering_structure_properties.py -v` and ensure all tests pass. Ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties from the design document
- All code is Python 3.11+ using pytest + Hypothesis
- The steering index is parsed once per session via a session-scoped fixture
- Hypothesis `@settings(max_examples=100)` ensures thorough coverage across all modules
