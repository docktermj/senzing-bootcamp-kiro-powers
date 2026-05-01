# Implementation Plan: Module 1 Deployment Target & Value Restatement

## Overview

This plan implements two new capabilities in Module 1 (Business Problem): a deployment target discovery step in Phase 1 and a Senzing value restatement step in Phase 2. It also handles Phase 2 renumbering (10–18), downstream module updates (Modules 8 and 11), business problem template updates, and steering index updates. Tests are written first (observation-first for preservation properties) to validate structural correctness before and after changes.

## Tasks

- [x] 1. Write test scaffolding and preservation observation tests
  - [x] 1.1 Create test file with helpers and baseline snapshots
    - Create `senzing-bootcamp/tests/test_module1_deployment_and_value.py`
    - Add imports: `pytest`, `hypothesis`, `re`, `pathlib`
    - Add path constants for Phase 1 file (`module-01-business-problem.md`), Phase 2 file (`module-01-phase2-document-confirm.md`), Module 8, Module 11, and `steering-index.yaml`
    - Add helper `_extract_step(markdown, step_number)` to parse numbered steps (reuse pattern from `test_git_question_preservation.py`)
    - Snapshot baseline content of Phase 1 Steps 1–8 and Phase 2 Steps 9–16 for preservation comparison
    - _Requirements: 8.1, 8.2_

  - [x] 1.2 Write Property 4 test: Phase 1 Steps 1–8 content preservation
    - **Property 4: Phase 1 Steps 1–8 Content Preservation**
    - **Validates: Requirements 8.1**
    - Class `TestProperty4Phase1StepsPreservation` with Hypothesis `@given(st.sampled_from(range(1, 9)))` over step numbers 1–8
    - Assert each step's full text in the modified file is identical to the baseline snapshot
    - `@settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])`

  - [x] 1.3 Write Property 5 test: Phase 2 original step instructional text preservation
    - **Property 5: Phase 2 Original Step Instructional Text Preservation**
    - **Validates: Requirements 8.2**
    - Class `TestProperty5Phase2TextPreservation` with Hypothesis over original step numbers (9–16 mapped to 10–18 excluding new Step 15)
    - Strip step number references and checkpoint numbers before comparison
    - Assert instructional text is preserved after renumbering

- [x] 2. Write property-based tests for structural correctness
  - [x] 2.1 Write Property 1 test: Phase 1 step-checkpoint matching
    - **Property 1: Phase 1 Step-Checkpoint Matching**
    - **Validates: Requirements 1.7, 8.1**
    - Class `TestProperty1Phase1StepCheckpoints` with Hypothesis `@given(st.sampled_from(range(1, 10)))` over step numbers 1–9
    - For each step number, assert a corresponding `Write step N to config/bootcamp_progress.json` checkpoint exists

  - [x] 2.2 Write Property 2 test: Phase 2 step sequentiality
    - **Property 2: Phase 2 Step Sequentiality**
    - **Validates: Requirements 2.1, 2.2**
    - Class `TestProperty2Phase2Sequentiality`
    - Parse all top-level numbered steps from Phase 2 file
    - Assert sequence starts at 10, ends at 18, no gaps, no duplicates
    - Assert consecutive pairs differ by exactly 1

  - [x] 2.3 Write Property 3 test: Phase 2 step-checkpoint matching
    - **Property 3: Phase 2 Step-Checkpoint Matching**
    - **Validates: Requirements 2.2, 4.5**
    - Class `TestProperty3Phase2StepCheckpoints` with Hypothesis `@given(st.sampled_from(range(10, 19)))` over step numbers 10–18
    - For each step number, assert a corresponding `Write step N to config/bootcamp_progress.json` checkpoint exists

- [x] 3. Write example-based tests for new content
  - [x] 3.1 Write example tests for Phase 1 Step 9 content
    - Test Step 9 contains deployment categories: AWS, Azure, GCP, Kubernetes, Docker Swarm, local, "not sure yet"
    - Test Step 9 contains local-development-first reassurance text
    - Test Step 9 contains `deployment_target` persistence instruction to `config/bootcamp_preferences.yaml`
    - Test Step 9 contains `cloud_provider` conditional persistence for hyperscalers
    - Test Step 9 contains `undecided` handling for "not sure yet"
    - Test Step 9 contains checkpoint instruction
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8_

  - [x] 3.2 Write example tests for Phase 2 updates
    - Test Phase 2 header says "Steps 10–18"
    - Test Phase 1 Phase 2 reference says "Steps 10–18"
    - Test business problem template in Step 12 contains Deployment Target section with platform, category, and note fields
    - Test business problem template handles "To be determined" for undecided
    - Test both files retain `inclusion: manual` frontmatter
    - _Requirements: 2.3, 2.4, 3.1, 3.2, 3.3, 8.3, 8.4_

  - [x] 3.3 Write example tests for value restatement step (Step 15)
    - Test Step 15 contains `search_docs` MCP instruction
    - Test Step 15 references bootcamper's specific problem context
    - Test Step 15 mentions entity resolution explanation
    - Test Step 15 contains integration target conditional
    - Test Step 15 contains checkpoint instruction
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6_

  - [x] 3.4 Write example tests for downstream module updates
    - Test Module 11 Step 1 checks `deployment_target` from preferences
    - Test Module 11 Step 1 handles `undecided` case
    - Test Module 11 Step 1 still checks `cloud_provider`
    - Test Module 8 reads `deployment_target` from preferences
    - Test Module 8 contains conditional logic for deployment_target without cloud_provider
    - _Requirements: 5.1, 5.2, 5.3, 6.1, 6.2_

  - [x] 3.5 Write example tests for steering index updates
    - Test steering index Phase 1 step_range is `[1, 9]`
    - Test steering index Phase 2 step_range is `[10, 18]`
    - _Requirements: 7.1, 7.2_

- [x] 4. Checkpoint — Run preservation tests (should pass on unmodified files)
  - Run `pytest senzing-bootcamp/tests/test_module1_deployment_and_value.py -k "Property4 or Property5"` to confirm preservation tests pass on baseline
  - Ensure all tests pass, ask the user if questions arise.

- [x] 5. Implement Phase 1 changes: Add Step 9 and update Phase 2 reference
  - [x] 5.1 Add Step 9 (deployment target) to `senzing-bootcamp/steering/module-01-business-problem.md`
    - Insert new Step 9 after Step 8 and before the Phase 2 reference line
    - Include categorized deployment options: cloud hyperscalers (AWS, Azure, GCP), container platforms (Kubernetes, Docker Swarm), local/on-premises (current machine, other internal infrastructure), "not sure yet"
    - Include local-development-first reassurance statement
    - Include `deployment_target` persistence to `config/bootcamp_preferences.yaml`
    - Include conditional `cloud_provider` dual-write for hyperscalers
    - Include `undecided` handling for "not sure yet"
    - Include checkpoint: `Write step 9 to config/bootcamp_progress.json`
    - Follow one-question-at-a-time pattern (separate from Step 8)
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8_

  - [x] 5.2 Update Phase 2 reference text in Phase 1 file
    - Change `**Phase 2 (Steps 9–16):**` to `**Phase 2 (Steps 10–18):**`
    - _Requirements: 2.4_

- [x] 6. Implement Phase 2 changes: Renumber, add template section, add value step
  - [x] 6.1 Renumber Phase 2 steps from 9–16 to 10–18
    - Update header text from "Steps 9–16" to "Steps 10–18"
    - Renumber step 9→10, 10→11, 11→12, 12→13, 13→14, 14→16, 15→17, 16→18
    - Update all checkpoint instructions to reference new step numbers
    - Preserve all existing instructional text unchanged
    - _Requirements: 2.1, 2.2, 2.3, 8.2_

  - [x] 6.2 Add Deployment Target section to business problem template in Step 12
    - Add `## Deployment Target` section with Platform, Category, and Note fields
    - Include "To be determined" variant for undecided deployment target
    - Place after Integration Requirements section in the template
    - _Requirements: 3.1, 3.2, 3.3_

  - [x] 6.3 Insert new Step 15 (value restatement) after Step 14
    - Add `search_docs(query='value proposition <use_case_category>', version='current')` instruction
    - Tie value explanation to bootcamper's specific problem, data sources, and desired outcomes
    - Explain entity resolution (matching, relating, deduplicating records) in terms of bootcamper's data
    - Include conditional: if integration targets identified in Step 8, explain how Senzing fits alongside those systems
    - Include checkpoint: `Write step 15 to config/bootcamp_progress.json`
    - Push original steps 14→16, 15→17, 16→18
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6_

- [x] 7. Checkpoint — Run all Phase 1 and Phase 2 tests
  - Run `pytest senzing-bootcamp/tests/test_module1_deployment_and_value.py -k "Property1 or Property2 or Property3 or Property4 or Property5 or Step9 or Phase2"` to verify structural correctness
  - Ensure all tests pass, ask the user if questions arise.

- [x] 8. Update downstream modules
  - [x] 8.1 Update Module 11 Step 1 in `senzing-bootcamp/steering/module-11-deployment.md`
    - Add check for `deployment_target` in `config/bootcamp_preferences.yaml` before the existing `cloud_provider` check
    - If `deployment_target` is set and not `undecided`: confirm with bootcamper ("You indicated [target]. Still your target?")
    - If `deployment_target` is `undecided` or not set: ask the full deployment target question as today
    - Preserve existing `cloud_provider` check logic
    - _Requirements: 5.1, 5.2, 5.3_

  - [x] 8.2 Update Module 8 in `senzing-bootcamp/steering/module-08-performance.md`
    - Add `deployment_target` read from `config/bootcamp_preferences.yaml` alongside existing `cloud_provider` read
    - Add conditional: when `deployment_target` is set but `cloud_provider` is not, use deployment target to inform performance guidance
    - _Requirements: 6.1, 6.2_

- [x] 9. Update steering index
  - [x] 9.1 Update `senzing-bootcamp/steering/steering-index.yaml`
    - Change Phase 1 `step_range` from `[1, 8]` to `[1, 9]`
    - Change Phase 2 `step_range` from `[9, 16]` to `[10, 18]`
    - Update `token_count` for both Phase 1 and Phase 2 files (measure after edits)
    - Update `token_count` in `file_metadata` for both files
    - Update `size_category` if token count crosses thresholds
    - _Requirements: 7.1, 7.2_

- [x] 10. Final checkpoint — Run full test suite
  - Run `pytest senzing-bootcamp/tests/test_module1_deployment_and_value.py -v` to verify all property and example tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties from the design document
- Preservation tests (Properties 4 and 5) are written first and run against unmodified files to establish baselines
- The Phase 2 step range is 10–18 (not 10–17) per the design document, which accounts for both the Phase 1 shift and the new value restatement step
- Token counts in the steering index must be measured after all edits are complete (use `measure_steering.py` or manual count)
