# Implementation Plan: Enforce Per-Source Mapping Specification

## Overview

Add hook-based enforcement to guarantee per-source mapping specification files are created during Module 5. Creates a new `enforce-mapping-spec` hook and enhances the existing `analyze-after-mapping` hook.

## Tasks

- [x] 1. Create the enforce-mapping-spec hook
  - [x] 1.1 Create `senzing-bootcamp/hooks/enforce-mapping-spec.kiro.hook` with:
    - name: "Enforce Mapping Specification"
    - version: "1.0.0"
    - when: fileCreated, patterns: ["data/transformed/*.jsonl", "data/transformed/*.json"]
    - then: askAgent with prompt that:
      - Extracts source name from the transformed filename
      - Checks if `docs/{source_name}_mapper.md` exists
      - If exists: produce no output (zero tokens, silent pass)
      - If missing: instruct agent to create it NOW with the full template (source file, data source name, entity type, field mappings table, mapping decisions, quality notes)
      - Explicitly states: "Do not proceed to the next data source or any other work until this file is created"
    - _Requirements: 1, 2, 3, 6_

- [x] 2. Enhance the analyze-after-mapping hook
  - [x] 2.1 Update `senzing-bootcamp/hooks/analyze-after-mapping.kiro.hook` prompt to add mapping spec verification:
    - After the existing quality validation instructions, add: "ADDITIONALLY: Verify that docs/{source_name}_mapper.md exists (extract source name from the transformed filename). If it does not exist, state: 'The per-source mapping specification is missing. Create docs/{source_name}_mapper.md before proceeding to the next source or to loading.'"
    - Preserve all existing quality validation logic unchanged
    - _Requirements: 1, 2_

- [x] 3. Update hook-registry.md
  - [x] 3.1 Add the `enforce-mapping-spec` entry to the Module Hooks section in `senzing-bootcamp/steering/hook-registry.md`
    - Place it under Module 5 hooks, after `analyze-after-mapping`
    - Include: id, name, description, prompt text
    - _Requirements: 1_
  - [x] 3.2 Update the `analyze-after-mapping` entry to reflect the enhanced prompt
    - _Requirements: 2_

- [x] 4. Update hook-categories.yaml
  - [x] 4.1 Add `enforce-mapping-spec` to the Module 5 category in `senzing-bootcamp/hooks/hook-categories.yaml`
    - _Requirements: 1_

- [x] 5. Update hooks README
  - [x] 5.1 Add an entry for the new hook in `senzing-bootcamp/hooks/README.md`
    - Document trigger, action, use case
    - Place it in the Module 5 section
    - _Requirements: 1_

- [x] 6. Strengthen Module 5 completion gate in steering
  - [x] 6.1 In `senzing-bootcamp/steering/module-05-phase2-data-mapping.md` Step 12, strengthen the completion checkpoint text:
    - Add: "BEFORE writing the module completion checkpoint: list ALL files in data/transformed/ and verify that EACH has a corresponding docs/{source_name}_mapper.md. If any are missing, create them now. Do NOT write the module completion checkpoint until all mapping specs exist."
    - Bold and visually emphasize this as a mandatory gate
    - _Requirements: 4, 5_

- [x] 7. Verify enforcement
  - Confirm `enforce-mapping-spec.kiro.hook` exists with correct trigger and prompt
  - Confirm `analyze-after-mapping.kiro.hook` includes the mapping spec reminder
  - Confirm `hook-registry.md` contains both entries and they match the actual hook files
  - Confirm `module-05-phase2-data-mapping.md` Step 12 has the strengthened completion gate
  - Run `sync_hook_registry.py --verify` if available

## Notes

- The enforcement is additive — it doesn't replace the existing steering instructions, it adds hook-based enforcement on top
- The hook fires on the same trigger as `analyze-after-mapping` (fileCreated in data/transformed/) — both hooks will fire, providing defense-in-depth
- The silent-pass rule (produce no output if file exists) follows the same pattern as other preToolUse hooks
- This hook is a Module 5 hook — it should be created when Module 5 starts, not during onboarding
