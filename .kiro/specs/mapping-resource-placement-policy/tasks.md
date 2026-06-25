# Implementation Plan: Mapping Resource Placement Policy

## Overview

This is a documentation-and-steering-only change scoped to exactly two files:

- `senzing-bootcamp/steering/module-05-phase2-data-mapping.md` (agent steering)
- `senzing-bootcamp/docs/modules/MODULE_5_DATA_QUALITY_AND_MAPPING.md` (companion doc)

The core change is **timing**: insert a post-download Organize_Step instruction
immediately after the `mapping_workflow(action='start')` download, retain the
existing post-transformation organize step, document the transient run
artifacts that intentionally stay in the workspace, and document the entity
specification's canonical home (`docs/reference/`). No code is modified — not
the `mapping_workflow` MCP tool, the organizer's routing rules, nor the
`write-policy-gate` policy. Property-based testing is intentionally not
applicable (the design omits a Correctness Properties section); verification is
documentation review plus the repository's existing lint/steering checks and a
read-only organizer `--dry-run` spot-check.

## Tasks

- [x] 1. Update Module 5 Phase 2 steering with post-download organize timing
  - [x] 1.1 Insert post-download Organize_Step instruction after `action='start'`
    - Edit `senzing-bootcamp/steering/module-05-phase2-data-mapping.md`
    - In Step 1 (the `mapping_workflow(action='start')` download point), add an
      agent instruction to run the organizer immediately after the download
      completes and before any further mapping work proceeds
    - Invoke the organizer as
      `python3 senzing-bootcamp/scripts/organize_mapping_files.py --source <workspace_dir> --project-root <bootcamper_project_root>`
    - Add an instruction to review the organizer summary output to confirm
      files landed at expected locations (`.py` → `src/`, entity spec →
      `docs/reference/`, reference `.md`/`.json` → policy-correct homes)
    - _Requirements: 1.1, 1.2, 1.4_

  - [x] 1.2 Retain the post-transformation Organize_Step
    - Keep the existing "organize mapping output files" instruction (currently
      in Step 5, after `action='paths'`) so transformation output produced
      later in the workflow is also relocated
    - Ensure it uses the same `--source`/`--project-root` invocation contract
    - _Requirements: 1.3_

  - [x] 1.3 Document transient run artifacts that remain in the workspace
    - Add steering content identifying `profile_report.md`, `schema_hints.md`,
      `JOURNAL.md`, and generated JSONL output as transient run artifacts that
      stay in `workspace_dir` for the workflow's continued use during the run
    - Instruct the agent NOT to relocate, delete, or redirect these out of
      `workspace_dir` while the run is in progress
    - _Requirements: 3.1, 3.2, 5.2_

  - [x] 1.4 State reliance on existing routing and document graceful handling
    - State that the guidance relies on the organizer's existing routing rules
      and introduces no alternative placement destinations
    - Document that unrouted files are left in `workspace_dir` and reported as
      warnings in the summary, and that blocked writes leave the file in place
      and report the blocked destination as an error — directing the agent to
      review the summary rather than force a destination
    - _Requirements: 2.4, 5.3, 5.4, 5.5_

- [x] 2. Update Module 5 companion doc with organize timing and entity spec home
  - [x] 2.1 Document the Organize_Step timing in the Phase 2 narrative
    - Edit `senzing-bootcamp/docs/modules/MODULE_5_DATA_QUALITY_AND_MAPPING.md`
    - Describe that the Organize_Step runs after the `mapping_workflow`
      download completes and before further mapping work proceeds, to place
      reusable resources in policy-correct locations
    - _Requirements: 4.2_

  - [x] 2.2 Document the entity specification's canonical home
    - Reference the entity specification by file name
      (`senzing_entity_specification.md`) and state that its canonical home
      after the Organize_Step completes is `docs/reference/`
    - Ensure a bootcamper can locate the file at that path without inspecting
      `workspace_dir`
    - _Requirements: 4.1, 4.3_

- [x] 3. Checkpoint - Review edits against acceptance criteria
  - Perform a documentation review confirming each edited file satisfies its
    mapped requirements (steering: 1.1, 1.2, 1.3, 1.4, 2.4, 3.1, 3.2, 5.2, 5.3,
    5.4, 5.5; companion doc: 4.1, 4.2, 4.3)
  - Confirm no code was modified (MCP tool, organizer routing, write-policy-gate
    remain untouched) per 5.3
  - Ensure all checks pass, ask the user if questions arise.

- [x] 4. Verify documentation and steering compliance
  - [x] 4.1 Run CommonMark and steering budget validation
    - Run `python3 senzing-bootcamp/scripts/validate_commonmark.py` and confirm
      both edited files pass markdown validation
    - Run `python3 senzing-bootcamp/scripts/measure_steering.py --check` and
      confirm the edited steering file stays within its token budget
    - _Requirements: 5.3_

  - [x] 4.2 Behavioral spot-check of the existing organizer via --dry-run
    - Create a temporary sample directory containing representative downloaded
      resources (`sz_schema_generator.py`, `sz_json_analyzer.py`,
      `senzing_entity_specification.md`, `senzing_mapping_examples.md`,
      `identifier_crosswalk.json`)
    - Run `organize_mapping_files.py --source <sample> --project-root <tmp> --dry-run`
      (no code change) to confirm documented destinations match actual routing
      (`.py` → `src/mapping`, entity spec → `docs/reference`, reference `.md` →
      `docs/mapping`, `.json` → `config`)
    - Clean up the temporary directory afterward
    - _Requirements: 2.1, 2.2, 2.3, 5.1_

  - [x] 4.3 Update steering-index.yaml if token counts changed
    - If the steering edits changed token counts, update
      `senzing-bootcamp/steering/steering-index.yaml` so
      `measure_steering.py --check` passes
    - _Requirements: 5.3_

- [x] 5. Final checkpoint - Ensure all validations pass
  - Ensure `validate_commonmark.py` and `measure_steering.py --check` pass and
    the documentation review is complete, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP.
- This is a documentation/steering-only change; no executable code is added or
  modified (no MCP tool, organizer, or write-policy-gate changes).
- Property-based testing is intentionally not applicable — the design omits a
  Correctness Properties section. The organizer's routing correctness is already
  covered by its existing, unchanged PBT suite
  (`senzing-bootcamp/tests/test_organize_mapping_files.py`).
- Each task references specific requirements by their EARS clause numbers for
  traceability.
- The organizer `--dry-run` spot-check is read-only and validates the claims the
  docs make using the organizer as-is.

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1", "2.1"] },
    { "id": 1, "tasks": ["1.2", "2.2"] },
    { "id": 2, "tasks": ["1.3"] },
    { "id": 3, "tasks": ["1.4"] },
    { "id": 4, "tasks": ["4.1", "4.2"] },
    { "id": 5, "tasks": ["4.3"] }
  ]
}
```
