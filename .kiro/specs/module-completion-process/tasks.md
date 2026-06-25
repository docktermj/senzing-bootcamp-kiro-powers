# Implementation Plan: Module Completion Process

## Overview

This implementation adds reliable journal and recap artifact creation to the module completion workflow, introduces graduation-time recap recovery, and provides a validation script for artifact integrity checking. Changes span two steering files, one new Python script, and comprehensive property-based and unit tests.

## Tasks

- [x] 1. Create validation script with core parsing and formatting functions
  - [x] 1.1 Create `senzing-bootcamp/scripts/validate_completion_artifacts.py` with argparse CLI, dataclasses (`JournalEntry`, `JournalDocument`, `RecapHeader`), and the `COMPLETION_STEPS` constant
    - Define `JournalEntry` and `JournalDocument` dataclasses
    - Define `RecapHeader` dataclass
    - Define `COMPLETION_STEPS` list constant with the five ordered steps
    - Set up argparse with `--progress`, `--journal`, `--recap` arguments
    - Add `main()` entry point
    - _Requirements: 2.1, 7.1_

  - [x] 1.2 Implement `format_journal_header()` and `format_journal_entry()` functions
    - `format_journal_header(bootcamper_name, start_date)` returns markdown header string
    - `format_journal_entry(module_number, module_name, date, summary, artifacts, why_it_matters, takeaway)` returns formatted markdown entry
    - Use ISO 8601 date format with timezone offset
    - _Requirements: 1.1, 2.1, 2.3_

  - [x] 1.3 Implement `parse_journal()` and `parse_recap_header()` functions
    - `parse_journal(content)` parses markdown into `JournalDocument`
    - `parse_recap_header(content)` extracts `RecapHeader` from recap file content
    - Handle edge cases: empty content, malformed headers
    - _Requirements: 2.1, 4.1_

  - [x] 1.4 Implement `count_recap_sections()` function
    - Extract module numbers from `## Module N:` headings in recap content
    - Return sorted list of integers
    - _Requirements: 4.5, 5.4_

  - [x] 1.5 Implement validation functions: `validate_journal_structure()`, `validate_recap_consistency()`, `validate_journal_consistency()`
    - `validate_journal_structure(journal)` checks entry completeness and returns list of error strings
    - `validate_recap_consistency(recap_modules, progress_modules)` checks recap sections match progress
    - `validate_journal_consistency(journal_modules, progress_modules)` checks journal entries match progress
    - Wire validation functions into `main()` to read files and report errors
    - _Requirements: 5.4, 3.3_

- [x] 2. Checkpoint - Ensure validation script runs
  - Ensure all tests pass, ask the user if questions arise.

- [x] 3. Update module-completion steering file
  - [x] 3.1 Add explicit completion step ordering section to `senzing-bootcamp/steering/module-completion.md`
    - Add a section at the top of the workflow defining the fixed order: progress_update → recap_append → journal_entry → completion_certificate → next_step_options
    - Document that each step must complete before the next begins
    - _Requirements: 7.1, 7.2, 7.3_

  - [x] 3.2 Add journal file creation instructions to `senzing-bootcamp/steering/module-completion.md`
    - Add instructions to create `docs/` directory if absent on first module completion
    - Add instructions to create `docs/bootcamp_journal.md` with header (level-1 heading, bootcamper name from preferences, start date in ISO 8601)
    - Add instructions to append journal entry after recap append step
    - Document journal entry structure: module number, module name (from `config/module-dependencies.yaml`), completion date, summary, artifacts list, why-it-matters, takeaway
    - _Requirements: 1.1, 1.2, 1.3, 2.1, 2.2, 2.3, 2.4_

  - [x] 3.3 Add non-blocking error handling instructions to `senzing-bootcamp/steering/module-completion.md`
    - Add instructions for each artifact step to catch file-system errors, log a warning, and continue
    - Add 30-second timeout guidance per step
    - Add instruction that predecessor step failure does not block subsequent steps
    - Document that retry happens on next module completion
    - _Requirements: 6.1, 6.2, 6.3, 7.4, 7.5, 1.4_

  - [x] 3.4 Add recap file creation instructions to `senzing-bootcamp/steering/module-completion.md`
    - Add instructions to create `docs/bootcamp_recap.md` with header on first module completion if file does not exist
    - Add default name fallback ("Bootcamper") when preferences file is missing or name field absent
    - Document that recap append executes before journal entry
    - _Requirements: 3.1, 3.2, 3.3, 3.4_

- [x] 4. Update graduation steering file
  - [x] 4.1 Add recap recovery preamble to Step 0 in `senzing-bootcamp/steering/graduation.md`
    - Replace silent skip behavior with error-recovery flow
    - Add check: if `docs/bootcamp_recap.md` does not exist, halt normal flow and attempt regeneration
    - Add check: if progress file exists and has non-empty `modules_completed`, regenerate recap from progress data and module artifacts
    - Add check: validate recap contains `## Module N:` heading matching progress data before proceeding to PDF
    - Add guard: if progress file missing or `modules_completed` empty, skip PDF with message to bootcamper
    - Add bootcamper notification message for reconstruction
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

- [x] 5. Checkpoint - Verify steering file changes
  - Ensure all tests pass, ask the user if questions arise.

- [x] 6. Write property-based tests
  - [x] 6.1 Create `senzing-bootcamp/tests/test_module_completion_process_properties.py` with Hypothesis strategies and imports
    - Set up test file with `sys.path` manipulation to import validation script
    - Define Hypothesis strategies for journal entries, module numbers (1-11), bootcamper names, ISO 8601 dates, artifact lists
    - Use `@settings(max_examples=100)` on all property tests
    - _Requirements: 2.1_

  - [x] 6.2 Write property test for Property 1: Journal entry round-trip
    - **Property 1: Journal entry round-trip**
    - For any valid journal entry, formatting as markdown then parsing back produces equivalent JournalEntry
    - **Validates: Requirements 2.1, 2.3**

  - [x] 6.3 Write property test for Property 2: Journal append preserves existing content
    - **Property 2: Journal append preserves existing content**
    - For any existing journal content and new entry, appending preserves all prior bytes
    - **Validates: Requirements 1.2**

  - [x] 6.4 Write property test for Property 3: Recap section count matches progress
    - **Property 3: Recap section count matches progress**
    - For any set of completed modules, recap section count equals number of completed modules
    - **Validates: Requirements 3.3, 4.5**

  - [x] 6.5 Write property test for Property 4: Journal header creation uses preferences
    - **Property 4: Journal header creation uses preferences**
    - For any bootcamper name and date, header contains both in expected format
    - **Validates: Requirements 1.1**

  - [x] 6.6 Write property test for Property 5: Recap validation detects missing sections
    - **Property 5: Recap validation detects missing sections**
    - For progress with N modules and recap with fewer than N sections, validation reports errors
    - **Validates: Requirements 5.4**

  - [x] 6.7 Write property test for Property 6: Completion step ordering is invariant
    - **Property 6: Completion step ordering is invariant**
    - For any sequence of module completions, steps always execute in fixed order
    - **Validates: Requirements 7.1, 7.2, 7.3**

  - [x] 6.8 Write property test for Property 7: Default name fallback
    - **Property 7: Default name fallback**
    - When preferences missing or name field absent, header uses "Bootcamper" as default
    - **Validates: Requirements 3.2**

- [x] 7. Write unit tests
  - [x] 7.1 Create `senzing-bootcamp/tests/test_module_completion_process_unit.py` with unit tests for journal and recap creation
    - Test journal file creation when `docs/` directory doesn't exist
    - Test recap header creation with specific known values
    - Test journal entry formatting with known inputs and expected output
    - _Requirements: 1.1, 2.1, 3.1_

  - [x] 7.2 Write unit tests for graduation recovery scenarios
    - Test graduation recovery when progress file is empty
    - Test graduation recovery when progress file has modules but recap is missing
    - Test recap validation passes when sections match progress
    - _Requirements: 5.1, 5.2, 5.5_

  - [x] 7.3 Write unit tests for error handling and edge cases
    - Test error message formatting for skipped steps
    - Test default name fallback when preferences file missing
    - Test module name derivation from `module-dependencies.yaml`
    - Test validation detects missing recap sections
    - _Requirements: 6.1, 6.2, 3.2, 5.4_

- [x] 8. Checkpoint - Run all tests
  - Ensure all tests pass, ask the user if questions arise.

- [x] 9. Integration wiring and final validation
  - [x] 9.1 Update `senzing-bootcamp/steering/steering-index.yaml` token counts for modified steering files
    - Update token count for `module-completion.md`
    - Update token count for `graduation.md`
    - _Requirements: 7.1_

  - [x] 9.2 Write integration tests in `senzing-bootcamp/tests/test_module_completion_process_integration.py`
    - Test complete Module 1 flow: verify both journal and recap created from scratch
    - Test sequential module completions (1, 2, 3): verify cumulative artifacts
    - Test graduation with missing recap: verify regeneration flow
    - Test validation script CLI end-to-end with sample files
    - _Requirements: 1.1, 1.2, 3.1, 3.3, 5.1, 5.2_

  - [x] 9.3 Run `python3 senzing-bootcamp/scripts/validate_commonmark.py` to verify all modified steering files remain valid CommonMark
    - _Requirements: 7.1_

  - [x] 9.4 Run `python3 senzing-bootcamp/scripts/measure_steering.py --check` to verify token budgets are not exceeded
    - _Requirements: 7.1_

- [x] 10. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties from the design document
- Unit tests validate specific examples and edge cases
- The validation script uses Python 3.11+ stdlib only (no third-party deps)
- Tests use pytest + Hypothesis with `@settings(max_examples=100)`
- Import validation script in tests via `sys.path` manipulation per project convention

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1"] },
    { "id": 1, "tasks": ["1.2", "1.3"] },
    { "id": 2, "tasks": ["1.4", "1.5"] },
    { "id": 3, "tasks": ["3.1", "3.4", "4.1"] },
    { "id": 4, "tasks": ["3.2", "3.3"] },
    { "id": 5, "tasks": ["6.1", "7.1"] },
    { "id": 6, "tasks": ["6.2", "6.3", "6.4", "6.5", "6.6", "6.7", "6.8", "7.2", "7.3"] },
    { "id": 7, "tasks": ["9.1", "9.2"] },
    { "id": 8, "tasks": ["9.3", "9.4"] }
  ]
}
```
