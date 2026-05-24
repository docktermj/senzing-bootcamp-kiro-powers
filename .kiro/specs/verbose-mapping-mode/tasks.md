# Implementation Plan: Verbose Mapping Mode

## Overview

Fix the Module 5 Phase 2 steering file to prompt the bootcamper for mapping verbosity preference before starting the mapping workflow. Add a `mapping_verbosity` key to the preferences file. Modify per-step presentation instructions to be conditional on the chosen mode. This is a steering-only fix — no new Python scripts or runtime code.

## Tasks

- [x] 1. Add `mapping_verbosity` key to the preferences file
  - [x] 1.1 Add the `mapping_verbosity` key to `senzing-bootcamp/config/bootcamp_preferences.yaml`
    - Add `mapping_verbosity: null` with a comment explaining it's set during Module 5 Phase 2
    - Place it after the existing `verbosity` key for logical grouping
    - Values: `verbose`, `concise`, or `null` (not yet asked)
    - _Requirements: 2.2_

- [x] 2. Add pre-mapping verbosity prompt to the Phase 2 steering file
  - [x] 2.1 Insert a new section before Step 1 in `senzing-bootcamp/steering/module-05-phase2-data-mapping.md`
    - Title: "Mapping Verbosity Check"
    - Instruction: Before starting the mapping workflow, read `config/bootcamp_preferences.yaml` and check the `mapping_verbosity` key
    - If `mapping_verbosity` is `null` or absent: present a single 👉 question: "Before we start mapping, would you like **verbose mode** (I'll show each mapping step in detail — field detection, attribute selection rationale, transformation preview) or **concise mode** (I'll map quickly and show only the final mapped record and any warnings)?"
    - If `mapping_verbosity` is already set to `verbose` or `concise`: say "Using your [verbose/concise] mapping preference from last time — say 'switch to [other]' if you'd prefer [less detail/more detail]" and proceed without waiting
    - Persist the choice to `mapping_verbosity` in the preferences file
    - If the bootcamper skips or doesn't answer directly: default to `verbose` and note "Defaulting to verbose mode — say 'switch to concise' anytime if you want less detail"
    - _Requirements: 2.1, 2.3_

- [x] 3. Add per-step conditional presentation rules
  - [x] 3.1 Modify Step 2 (Profile) presentation instructions
    - Add conditional block: **Verbose:** present full column table with types, sample values, completeness %, and what each means for mapping
    - Add conditional block: **Concise:** present one summary line (N columns, X% overall completeness, key issues only)
    - _Requirements: 2.4, 2.5_

  - [x] 3.2 Modify Step 3 (Plan) presentation instructions
    - Add conditional block: **Verbose:** explain entity type decision, which fields map vs. skip and why for each
    - Add conditional block: **Concise:** state entity type + count of mapped/skipped fields without per-field rationale
    - _Requirements: 2.4, 2.5_

  - [x] 3.3 Modify Step 4 (Map) presentation instructions
    - Add conditional block: **Verbose:** show mapping table with reasoning for each decision and confidence score
    - Add conditional block: **Concise:** show mapping table without rationale column, just source field → Senzing attribute
    - _Requirements: 2.4, 2.5_

  - [x] 3.4 Modify Step 5 (Generate) presentation instructions
    - Add conditional block: **Verbose:** show a sample target JSON record with annotations explaining the structure
    - Add conditional block: **Concise:** state file path and output format only
    - _Requirements: 2.4, 2.5_

  - [x] 3.5 Modify Step 7 (Test) presentation instructions
    - Add conditional block: **Verbose:** show pass/fail, output file path, sample record, and observations
    - Add conditional block: **Concise:** show pass/fail + output file path only
    - _Requirements: 2.4, 2.5_

  - [x] 3.6 Modify Step 8 (Quality) presentation instructions
    - Add conditional block: **Verbose:** show overall score, per-feature coverage with matching implications, and issues found
    - Add conditional block: **Concise:** show overall score + count of mapped vs. unmapped fields + warnings only
    - _Requirements: 2.4, 2.5_

- [x] 4. Add mid-mapping switch instruction
  - [x] 4.1 Add a "Mid-Mapping Verbosity Switch" section to the steering file
    - Place after the Mapping Verbosity Check section and before Step 1
    - Instruction: If the bootcamper says "switch to verbose", "switch to concise", "more detail", "less detail", or natural variants at any point during the mapping workflow, update `mapping_verbosity` in `config/bootcamp_preferences.yaml` and apply the new mode immediately
    - Confirm the switch briefly: "Switched to [verbose/concise] mode" without interrupting the workflow
    - _Requirements: 3.3, 3.4_

- [x] 5. Write tests for the steering file changes
  - [x] 5.1 Create `senzing-bootcamp/tests/test_mapping_verbosity.py`
    - Test that `senzing-bootcamp/steering/module-05-phase2-data-mapping.md` contains a "Mapping Verbosity Check" section
    - Test that the steering file contains verbose-mode and concise-mode conditional blocks for steps 2, 3, 4, 5, 7, and 8
    - Test that `senzing-bootcamp/config/bootcamp_preferences.yaml` contains the `mapping_verbosity` key
    - Test that the steering file contains a "Mid-Mapping Verbosity Switch" section
    - Test that all original steps (1–13) are still present (no regression)
    - Test that the `mapping_workflow` tool call instructions are unchanged (verbosity only affects presentation, not MCP calls)
    - _Requirements: 3.1, 3.2, 3.4_

- [x] 6. Final checkpoint — Run all tests
  - Run `pytest senzing-bootcamp/tests/test_mapping_verbosity.py -v` and ensure all pass
  - Run existing Module 5 related tests (if any) to confirm no regression

## Notes

- This is a steering-only bugfix — no new Python scripts or runtime dependencies
- The `mapping_verbosity` key is additive to the existing `verbosity` system, not a replacement
- Only Module 5 Phase 2 is affected; all other modules continue using the general verbosity system
- The `mapping_workflow` MCP tool calls remain identical regardless of mode — only agent presentation changes
- Default for skipped question is `verbose` (educational benefit for first-time users)
