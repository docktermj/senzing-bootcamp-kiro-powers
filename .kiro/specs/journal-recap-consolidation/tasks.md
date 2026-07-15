# Implementation Plan: Journal-Recap Consolidation

## Overview

Consolidate `docs/bootcamp_recap.md` and `docs/bootcamp_journal.md` into a single Consolidated_Log at `docs/bootcamp_recap.md`, folding the journal's four narrative fields into each recap section as a new `### Journal` subsection. Updates all dependents (scripts, hook, steering slices, tests, CI gates) in lockstep.

## Tasks

- [x] 1. Implement parsing and rendering utilities in `completion_artifacts.py`
  - [x] 1.1 Add `JournalFields` and `ParsedRecapSection` dataclasses and the `MigrationReport` dataclass to `senzing-bootcamp/scripts/completion_artifacts.py`
    - Define `JournalFields` with fields: `what_we_did`, `what_was_produced`, `why_it_matters`, `bootcamper_takeaway`
    - Define `ParsedRecapSection` with fields: `module_number`, `module_name`, `timestamp`, `information_shared`, `questions_responses`, `actions_taken`, `duration`, `journal`
    - Define `MigrationReport` with fields: `modules_merged`, `modules_created`, `already_consolidated`, `journal_path`
    - _Requirements: 1.3, 1.4, 2.1, 2.6_

  - [x] 1.2 Add `parse_recap_sections()` and `render_recap_section()` functions to `senzing-bootcamp/scripts/completion_artifacts.py`
    - `parse_recap_sections(content: str) -> list[ParsedRecapSection]` parses the Consolidated_Log into structured objects
    - `render_recap_section(section: ParsedRecapSection) -> str` renders a structured section back to Markdown
    - `_extract_journal_subsection(section_text: str) -> JournalFields | None` parses the `### Journal` block
    - Handle edge cases: missing subsections, empty fields, N/A values
    - _Requirements: 1.3, 1.4, 1.6, 2.7, 13.1_

  - [x] 1.3 Add `migrate_journal_to_recap()` function to `senzing-bootcamp/scripts/completion_artifacts.py`
    - Parse legacy journal into per-module entries (module number, four narrative fields)
    - For each journal entry, find or create matching `## Module N:` section in recap
    - If section exists and no `### Journal` subsection: insert Journal subsection after last existing subsection
    - If no matching section: create minimal section with Journal subsection and placeholder subsections
    - If `### Journal` already present: skip (idempotent)
    - Add `--migrate` CLI mode to the argparse parser
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 13.1_

  - [x] 1.4 Update `render_backfill_section()` to include a `### Journal` scaffold in every backfilled section
    - Add `### Journal` subsection with N/A placeholders after the existing subsections
    - Ensure the scaffold includes all four narrative fields with N/A values
    - _Requirements: 1.4, 5.4_

- [x] 2. Checkpoint - Ensure parsing/rendering utilities work
  - Ensure all tests pass, ask the user if questions arise.

- [x] 3. Update Completion Planner CLI (`completion_artifacts.py`)
  - [x] 3.1 Make `--journal` argument a no-op with deprecation warning
    - Accept `--journal` but ignore it with a stderr deprecation note: `"Warning: --journal is deprecated; journal content is now part of the consolidated recap."`
    - Remove `journal_modules` from gap detection (always return `missing_journal=[]`)
    - Remove `missing_journal` clause from `is_bug_condition()`
    - Keep `BackfillPlan.journal_modules` as always-empty list for backward compatibility
    - Remove `journal_entries` discovery from the `--plan` and `--check` paths
    - _Requirements: 5.1, 5.2, 5.3, 5.5, 5.7, 5.8_

  - [x] 3.2 Write property tests for consolidated log parsing and migration
    - Create `senzing-bootcamp/tests/test_consolidated_log_properties.py`
    - Implement `st_journal_fields()`, `st_recap_section()`, `st_consolidated_log()`, `st_legacy_journal()` strategies
    - **Property 1: Round-trip parsing preserves structure**
    - **Property 2: Exactly one section per completed module**
    - **Property 3: Journal subsection present in every consolidated section**
    - **Property 4: Migration preserves all journal content**
    - **Property 5: Migration and backfill are idempotent**
    - **Property 6: Existing content is preserved (append-only)**
    - **Validates: Requirements 1.2, 1.3, 1.4, 1.6, 2.1, 2.3, 2.4, 2.6, 2.7, 5.4, 5.5**

  - [x] 3.3 Write migration unit tests
    - Create `senzing-bootcamp/tests/test_journal_recap_migration.py`
    - Test merge of journal entries into existing recap sections
    - Test creation of new sections when recap has no matching module
    - Test idempotency (running migration twice produces no further changes)
    - Test edge cases: empty journal, empty recap, partial overlap, journal with unparseable entries
    - Test `--migrate` CLI mode
    - **Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 11.5**

- [x] 4. Update Record Exporter (`record_export.py`)
  - [x] 4.1 Update `collect_business_problem()` to read from the Consolidated_Log
    - Change path from `docs/bootcamp_journal.md` to `docs/bootcamp_recap.md`
    - Parse Module 1's `### Journal` subsection `**What we did:**` field and `### Information Shared` content
    - Extract problem statement, identified sources, and success criteria from the consolidated content
    - Fall back gracefully (return `None` with warning) when Module 1 or its Journal subsection is absent
    - _Requirements: 7.1, 7.3, 7.5, 7.6_

  - [x] 4.2 Update `collect_performance_tuning()` to read from the Consolidated_Log
    - Change path from `docs/bootcamp_journal.md` to `docs/bootcamp_recap.md`
    - Parse Module 8's `### Journal` subsection for performance tuning evidence
    - Fall back gracefully (return `None`) when Module 8 section or Journal subsection is absent
    - _Requirements: 7.2, 7.4, 7.5, 7.6_

  - [x] 4.3 Update record export tests
    - Update `senzing-bootcamp/tests/test_record_export.py` to assert Module 1 and Module 8 extraction from the Consolidated_Log format
    - Test extraction from `### Journal` subsection instead of separate journal file
    - Test graceful fallback when content is absent
    - **Property 7: Record export extracts correct content from consolidated log**
    - **Validates: Requirements 7.1, 7.2, 7.3, 7.4, 11.3**

- [x] 5. Checkpoint - Ensure planner and exporter updates work
  - Ensure all tests pass, ask the user if questions arise.

- [x] 6. Update Graduation Orchestrator (`ensure_graduation_artifacts.py`)
  - [x] 6.1 Make `--journal` argument a no-op with deprecation warning
    - Accept `--journal` but ignore it with a stderr deprecation note
    - Default `ArtifactPaths.journal` to `docs/bootcamp_recap.md` (same as recap) for signature compatibility
    - Remove the `journal` kwarg from the `backfill_recap_sections()` call inside `ensure_recap_md()`
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7, 6.8_

  - [x] 6.2 Update graduation orchestrator tests
    - Update `senzing-bootcamp/tests/test_ensure_graduation_artifacts_unit.py`
    - Assert `--journal` is accepted but produces a deprecation warning
    - Assert orchestrator operates on the Consolidated_Log as the single source
    - **Validates: Requirements 6.2, 6.3, 11.1**

- [x] 7. Update the Recap-Append Hook (`hooks/module-recap-append.json`)
  - [x] 7.1 Update the hook prompt to produce consolidated format including `### Journal` subsection
    - Add instructions after `### Duration` to produce `### Journal` with the four narrative fields
    - Remove references to `docs/bootcamp_journal.md` from the prompt
    - Remove the `--journal` argument from the planner invocation in the prompt
    - Update the section template to include `### Journal` subsection
    - Ensure hook JSON remains schema-valid with `version` and `hooks` fields
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7, 4.8, 4.9, 13.2_

- [x] 8. Update Steering Slices
  - [x] 8.1 Update `senzing-bootcamp/steering/module-completion.md`
    - Change 6-step ordering to 5 steps: remove `journal_entry` step
    - Rename `recap_append` to describe the consolidated append step
    - Update Shared Boundary-Detection Trigger to reference single consolidated step
    - Remove references to `docs/bootcamp_journal.md`
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 9.1_

  - [x] 8.2 Update `senzing-bootcamp/steering/module-completion-artifacts.md`
    - Remove the entire "Bootcamp Journal" section
    - Update "Recap Append" section to describe consolidated format including Journal subsection
    - Update the synchronous verification and backfill section (remove `--journal` arg from example commands)
    - Update "Backfill for Already-Completed Modules" section (remove `--journal` arg, remove `journal_modules` references)
    - _Requirements: 3.1, 9.2_

  - [x] 8.3 Update `senzing-bootcamp/steering/module-completion-error-handling.md`
    - Remove `journal_entry` from the list of steps that handle errors
    - Update to reference the single consolidated step instead of separate recap and journal steps
    - _Requirements: 3.7, 3.8, 3.9, 9.3_

  - [x] 8.4 Update `senzing-bootcamp/steering/module-completion-next-steps.md`
    - Change "After the journal entry" to "After the consolidated recap append"
    - _Requirements: 9.4_

  - [x] 8.5 Update `senzing-bootcamp/steering/module-completion-track.md`
    - Replace references to `docs/bootcamp_journal.md` with the Consolidated_Log
    - Remove `--journal` arg from example commands
    - Update "Reference to `docs/bootcamp_journal.md`" in the celebration to reference the Consolidated_Log
    - _Requirements: 9.5, 9.6, 9.7_

- [x] 9. Checkpoint - Ensure steering consistency and hook validity
  - Ensure all tests pass, ask the user if questions arise.

- [x] 10. Update integration tests and CI gates
  - [x] 10.1 Update module-completion integration tests
    - Update `senzing-bootcamp/tests/test_module_completion_artifacts_integration.py` to assert the single consolidated step and consolidated Recap_Section format (with `### Journal`)
    - Update `senzing-bootcamp/tests/test_module_completion_process_integration.py` to assert 5-step ordering (no `journal_entry` step)
    - _Requirements: 11.2_

  - [x] 10.2 Add Property 8 test for duration computation
    - Add to `senzing-bootcamp/tests/test_consolidated_log_properties.py` or `test_module_completion_artifacts_properties.py`
    - **Property 8: Duration computation from timestamps is correct**
    - **Validates: Requirements 5.6**

  - [x] 10.3 Update `senzing-bootcamp/steering/steering-index.yaml` token counts
    - Run `measure_steering.py` against all changed steering files
    - Update the recorded token counts for each changed file
    - _Requirements: 10.1, 10.2_

- [x] 11. Final checkpoint - Ensure all tests pass and CI gates are green
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties from the design document
- Unit tests validate specific examples and edge cases
- The `--journal` argument becomes a no-op (accepted with deprecation warning) rather than being removed, so existing invocations don't break during transition
- All scripts remain Python 3.11+ stdlib-only
- The hook JSON must remain valid with required `version` and `hooks` fields
- Steering slices must be updated atomically to maintain internal consistency

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1"] },
    { "id": 1, "tasks": ["1.2"] },
    { "id": 2, "tasks": ["1.3", "1.4"] },
    { "id": 3, "tasks": ["3.1", "4.1", "4.2", "6.1"] },
    { "id": 4, "tasks": ["3.2", "3.3", "4.3", "6.2", "7.1"] },
    { "id": 5, "tasks": ["8.1", "8.2", "8.3", "8.4", "8.5"] },
    { "id": 6, "tasks": ["10.1", "10.2"] },
    { "id": 7, "tasks": ["10.3"] }
  ]
}
```
