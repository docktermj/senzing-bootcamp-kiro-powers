# Implementation Plan: Module 3 Default-On

## Overview

Convert Module 3 (System Verification) from optional/opt-in to default-on (opt-out) across the three-layer propagation: configuration → steering → manifest. All changes are documentation/configuration updates — no Python runtime changes. Tests validate the new invariants using pytest + Hypothesis.

## Tasks

- [x] 1. Update configuration layer (module-dependencies.yaml)
  - [x] 1.1 Add `soft_requires: [3]` to Module 4 and update gate 3→4 text
    - In `senzing-bootcamp/config/module-dependencies.yaml`:
      - Add `soft_requires: [3]` field to module 4's definition
      - Update module 3's `skip_if` from "Already familiar with Senzing and system verified" to "Bootcamper explicitly requests skip ('skip verification' or 'I've already verified')"
      - Update gate `"3->4"` requires text from "System verification passed or skipped" to "System verification passed or explicitly skipped by bootcamper"
    - _Requirements: 9, 6_

- [x] 2. Update steering layer
  - [x] 2.1 Add opt-out gate section to module-03-system-verification.md
    - In `senzing-bootcamp/steering/module-03-system-verification.md`:
      - Add an "Opt-Out Gate" section immediately after the frontmatter/header block and before "Phase 1: Verification Pipeline"
      - Include trigger phrases: "skip verification", "I've already verified", "skip module 3"
      - Include warning text about potential issues in later modules
      - Include instruction to record skip in `config/bootcamp_progress.json` with status "skipped" and reason "bootcamper_opted_out"
      - Include instruction to proceed to Module 4 after skip
    - _Requirements: 4_

  - [x] 2.2 Update module-prerequisites.md to add Module 3 as soft prerequisite for Module 4
    - In `senzing-bootcamp/steering/module-prerequisites.md`:
      - Update Module 4 row in the Quick Reference table: change "Requires" from "Module 1" to "Module 1 + Module 3 (soft prerequisite)"
      - Update Module 3 row: change "Skip if" from "Already familiar with Senzing and system verified" to "Bootcamper explicitly requests skip ('skip verification' or 'I've already verified')"
      - Add a "Soft Prerequisite Behavior" subsection under "Agent Behavior" explaining: agent recommends Module 3 before Module 4, warns but does not block if skipped, explains unverified environments may cause issues in Modules 5-7
    - _Requirements: 6, 5_

- [x] 3. Checkpoint - Validate configuration and steering changes
  - Ensure all tests pass, ask the user if questions arise.

- [x] 4. Update manifest layer (POWER.md and docs)
  - [x] 4.1 Remove "(Optional)" from POWER.md module table and steering file list
    - In `senzing-bootcamp/POWER.md`:
      - Change Bootcamp Modules table row from `| 3      | System Verification (Optional)                 |` to `| 3      | System Verification                            |`
      - Change steering file list entry from `- \`module-03-system-verification.md\` — Module 3: System Verification (Optional)` to `- \`module-03-system-verification.md\` — Module 3: System Verification`
    - _Requirements: 2, 3_

  - [x] 4.2 Remove "(Optional)" from docs/modules/README.md
    - In `senzing-bootcamp/docs/modules/README.md`:
      - Change heading from `### Module 3: System Verification (Optional)` to `### Module 3: System Verification`
    - _Requirements: 2, 8_

  - [x] 4.3 Remove "(Optional)" from docs/diagrams/module-flow.md
    - In `senzing-bootcamp/docs/diagrams/module-flow.md`:
      - Change the Module 3 box from `│   MODULE 3 (Optional)│` to `│      MODULE 3        │`
    - _Requirements: 2, 8_

- [x] 5. Update existing tests
  - [x] 5.1 Update test_system_verification_unit.py gate condition test
    - In `senzing-bootcamp/tests/test_system_verification_unit.py`:
      - Update `test_gate_condition_updated` to assert the new gate text "explicitly skipped" is present in the gate 3→4 requires text
    - _Requirements: 8, 9_

  - [x] 5.2 Update test_module_flow_integration.py if needed
    - In `senzing-bootcamp/tests/test_module_flow_integration.py`:
      - Review `test_no_system_verification_bullet` — this test asserts "System Verification" is NOT in Step 5 track selection content. Verify this still holds after changes (Module 3 is default-on but may not appear as a separate track bullet). Update assertion text/docstring if needed.
    - _Requirements: 8_

- [x] 6. Checkpoint - Validate manifest and test updates
  - Ensure all tests pass, ask the user if questions arise.

- [x] 7. Write property-based tests for module3-default-on
  - [x] 7.1 Write property test for Property 1: Module 3 is in every track containing Modules 2 and 4
    - Create or extend `senzing-bootcamp/tests/test_module3_default_on_properties.py`
    - **Property 1: Module 3 is in every track that contains both Module 2 and Module 4**
    - Use Hypothesis with `@settings(max_examples=20)` to generate permutations of track definitions from `module-dependencies.yaml`
    - Assert: for any track containing both Module 2 and Module 4, Module 3 is present and positioned after Module 2 and before Module 4
    - **Validates: Requirements 1, 9**

  - [x] 7.2 Write property test for Property 2: No "(Optional)" qualifier on Module 3
    - In `senzing-bootcamp/tests/test_module3_default_on_properties.py`
    - **Property 2: No "(Optional)" qualifier on Module 3 in user-facing documentation**
    - Use Hypothesis to generate file path strategies from the `senzing-bootcamp/` distribution directory
    - Assert: for any file referencing Module 3 or "System Verification", no "(Optional)" text is adjacent
    - **Validates: Requirements 2, 3, 8**

  - [x] 7.3 Write property test for Property 3: Dependency graph reachability
    - In `senzing-bootcamp/tests/test_module3_default_on_properties.py`
    - **Property 3: Dependency graph reachability — Module 3 is on the path from Module 2 to Module 4**
    - Use Hypothesis to generate valid dependency graph variations from `module-dependencies.yaml`
    - Assert: following `requires` and `soft_requires` edges from Module 4 backward reaches Module 3, and from Module 3 backward reaches Module 2
    - **Validates: Requirements 5, 6, 9**

- [x] 8. Write unit tests for module3-default-on
  - [x] 8.1 Write unit tests for the concrete file content changes
    - Create `senzing-bootcamp/tests/test_module3_default_on_unit.py`
    - Test cases:
      - Assert POWER.md module table row for Module 3 does not contain "(Optional)"
      - Assert POWER.md steering file list entry for Module 3 does not contain "(Optional)"
      - Assert `module-dependencies.yaml` Module 4 has `soft_requires: [3]`
      - Assert gate 3→4 text references "explicitly skipped"
      - Assert `module-prerequisites.md` Module 4 row mentions Module 3
      - Assert `docs/modules/README.md` Module 3 heading does not contain "(Optional)"
      - Assert `docs/diagrams/module-flow.md` Module 3 box does not contain "(Optional)"
      - Assert Module 3 steering file contains opt-out gate section with trigger phrases
    - _Requirements: 1, 2, 3, 4, 5, 6, 8, 9_

- [x] 9. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties from the design document
- Unit tests validate specific examples and edge cases
- The design confirms `steering/onboarding-flow.md`, `steering/onboarding-phase2-track-setup.md`, and `steering/steering-index.yaml` need NO changes (Module 3 is already listed correctly in those files)
- All test files use pytest + Hypothesis, class-based organization, and follow the project's Python conventions

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1"] },
    { "id": 1, "tasks": ["2.1", "2.2", "4.1", "4.2", "4.3"] },
    { "id": 2, "tasks": ["5.1", "5.2"] },
    { "id": 3, "tasks": ["7.1", "7.2", "7.3", "8.1"] }
  ]
}
```
