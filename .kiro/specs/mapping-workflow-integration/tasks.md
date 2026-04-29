# Implementation Plan

- [x] 1. Update data source registry schema to support test_load_status
  - [x] 1.1 Add `test_load_status` and `test_entity_count` fields to `senzing-bootcamp/scripts/data_sources.py`
    - Add `test_load_status` to `VALID_TEST_LOAD_STATUSES = {"complete", "skipped"}` (null also valid)
    - Add `test_load_status: str | None` and `test_entity_count: int | None` to `RegistryEntry` dataclass
    - Update `validate_registry()` to accept and validate the new fields (optional, enum check for test_load_status)
    - Update `_dict_to_registry()` and `_registry_to_dict()` to handle the new fields
    - Update `serialize_registry_yaml()` field_order to include the new fields
    - Update `render_detail()` to display the new fields
    - _Requirements: 8.1_

  - [x] 1.2 Write property-based test for registry schema round-trip with test_load_status
    - **Property 1: Registry schema round-trip with test_load_status**
    - Use Hypothesis to generate random registry entries with `test_load_status` ∈ {`complete`, `skipped`, `None`} and `test_entity_count` ∈ {non-negative int, `None`}
    - Serialize to YAML using `serialize_registry_yaml()`, parse back using `parse_registry_yaml()`
    - Verify round-trip preserves `test_load_status` and `test_entity_count` values
    - Minimum 100 iterations
    - Tag: **Feature: mapping-workflow-integration, Property 1: Registry schema round-trip with test_load_status**
    - _Requirements: 8.1_

  - [x] 1.3 Write unit tests for registry validation with new fields
    - Test that `validate_registry()` accepts entries with valid `test_load_status` values
    - Test that `validate_registry()` accepts entries without `test_load_status` (backward compatible)
    - Test that `validate_registry()` rejects invalid `test_load_status` values
    - Test that `render_detail()` displays the new fields correctly
    - _Requirements: 8.1_

  - [x] 1.4 Run all registry tests and verify they pass
    - Run existing `test_data_sources.py` tests to confirm no regressions
    - Run new property-based and unit tests
    - _Requirements: 8.1_

- [x] 2. Add Phase 3 to Module 5 steering file
  - [x] 2.1 Add Phase 3 section to `senzing-bootcamp/steering/module-05-data-quality-mapping.md`
    - Add Phase 3 header after Phase 2's step 20 (the last Phase 2 step before "Mapping State Checkpointing")
    - Phase 3 title: "Phase 3 — Test Load and Validate (Optional)"
    - Mark Phase 3 as optional — bootcampers can skip directly from Phase 2 to Module 6
    - Add SDK-not-configured handling: inform bootcamper Module 2 is required, offer to skip Phase 3
    - Add steps for mapping_workflow steps 5–8:
      - Step 21: SDK environment detection — call `mapping_workflow(action='advance')` for step 5. Checkpoint: Write step 21.
      - Step 22: Test data loading into fresh SQLite DB — advance through step 6. Checkpoint: Write step 22.
      - Step 23: Validation report generation — advance through step 7. Checkpoint: Write step 23.
      - Step 24: Entity resolution evaluation — advance through step 8. Present match counts, entity counts, quality assessment. Checkpoint: Write step 24.
      - Step 25: Present results and decision gate. Checkpoint: Write step 25.
      - Step 26: Shortcut path decision. Checkpoint: Write step 26.
    - Add agent instruction to update Data_Source_Registry with `test_load_status: complete` and `test_entity_count` after successful test load
    - Add agent instruction to update Data_Source_Registry with `test_load_status: skipped` if Phase 3 is skipped
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 8.1, 8.3_

  - [x] 2.2 Add decision gate and shortcut path to Module 5 steering file
    - After Phase 3 results presentation, add decision gate explaining:
      - For simple use cases (single source, small dataset, no production requirements), Phase 3 results may be sufficient — proceed directly to Module 8
      - For production requirements, multiple sources, or datasets >1000 records, recommend full Module 6–7 path
    - When shortcut path is chosen, instruct agent to update Bootcamp_Progress to mark Modules 6 and 7 as skipped with reason "shortcut_path"
    - _Requirements: 7.1, 7.3, 7.4_

  - [x] 2.3 Add session resume instructions for Phase 3
    - In the "Mapping State Checkpointing" section, add instructions for resuming during Phase 3
    - On session resume: read mapping state checkpoint and Bootcamp_Progress to determine which Phase 3 steps completed
    - Restart `mapping_workflow` and fast-track through completed steps
    - _Requirements: 8.4_

  - [x] 2.4 Verify Phase 3 step numbers are sequential from Phase 2
    - **Property 2: Phase 3 step numbers are sequential continuations of Phase 2**
    - Verify Phase 2 ends at step 20 and Phase 3 starts at step 21
    - Verify all Phase 3 steps (21–26) are present with no gaps
    - Verify no overlap with existing Phase 1/Phase 2 step numbers
    - _Requirements: 8.3_

- [x] 3. Update Module 5 documentation
  - [x] 3.1 Add Phase 3 section to `senzing-bootcamp/docs/modules/MODULE_5_DATA_QUALITY_AND_MAPPING.md`
    - Add "Phase 3: Test Load and Validate" section after Phase 2
    - Describe mapping_workflow steps 5–8 (SDK detection, test loading, validation report, evaluation)
    - Explain Phase 3 is optional — can skip if bootcamper prefers custom loading in Module 6
    - List Phase 3 learning objectives: verifying mapping quality through test loading, observing entity resolution results on mapped data, identifying mapping issues before production loading
    - Document output files: validation report, test database, evaluation results
    - _Requirements: 2.1, 2.2, 2.3, 2.4_

  - [x] 3.2 Add "Shortcut Path" section to Module 5 documentation
    - Add section explaining when Phase 3 results are sufficient to skip Modules 6–7
    - Criteria: single source, small dataset, no production requirements
    - Explain that the shortcut path goes directly to Module 8 (Query & Visualize)
    - _Requirements: 7.2_

  - [x] 3.3 Update success criteria in Module 5 documentation
    - Add Phase 3 success criteria section:
      - ✅ SDK environment detected (or Phase 3 skipped)
      - ✅ Test data loaded into fresh SQLite database
      - ✅ Validation report generated
      - ✅ Entity resolution evaluation reviewed
      - ✅ Decision gate completed (full path or shortcut path chosen)
    - _Requirements: 2.5_

- [x] 4. Refocus Module 6 steering file on production-quality loading
  - [x] 4.1 Add conditional workflow to `senzing-bootcamp/steering/module-06-single-source.md`
    - At the start of the workflow, add agent instruction to read `config/data_sources.yaml` and check `test_load_status` for each source
    - If Phase 3 completed: acknowledge test load results, skip basic test loading, proceed directly to production concerns
    - If Phase 3 skipped: include a brief test load step (using mapping_workflow steps 5–8 or a quick manual load) before production concerns
    - _Requirements: 3.3, 3.4, 8.2_

  - [x] 4.2 Refocus Module 6 steps on production-quality concerns
    - Restructure the workflow to emphasize:
      - Error handling per record (robust error logging, retry logic)
      - Progress tracking with throughput reporting
      - Loading statistics documentation
      - Redo queue processing (already present — retain and emphasize)
      - Incremental loading strategies (new section — distinguish from initial bulk loading)
    - Remove or reduce the basic "test with sample data and verify results" steps that overlap with Module 5 Phase 3
    - Retain match accuracy review and single-source validation steps as the production validation phase
    - _Requirements: 3.1, 3.2, 3.5, 3.6_

  - [x] 4.3 Verify Module 6 steering file preserves essential content
    - Verify match accuracy review steps are retained
    - Verify single-source validation steps are retained
    - Verify redo queue processing is retained
    - Verify checkpoint logic is intact
    - _Requirements: 3.5_

- [x] 5. Update Module 6 documentation
  - [x] 5.1 Update `senzing-bootcamp/docs/modules/MODULE_6_SINGLE_SOURCE_LOADING.md`
    - Update overview to describe Module 6 as focused on production-quality loading rather than basic load-and-verify
    - Describe the conditional workflow: abbreviated path for Phase 3 completers, full path for Phase 3 skippers
    - Update learning objectives to production-quality focus: robust error handling, progress tracking, throughput optimization, redo processing, incremental loading strategies
    - Update "What You'll Do" section to reflect production focus
    - _Requirements: 4.1, 4.2, 4.3, 4.4_

- [x] 6. Refocus Module 7 steering file on production-quality orchestration
  - [x] 6.1 Refocus Module 7 steps on production-quality orchestration
    - Update `senzing-bootcamp/steering/module-07-multi-source.md` to emphasize:
      - Dependency management and load order optimization (already present — retain and emphasize)
      - Parallel loading strategies (already present — retain and emphasize)
      - Cross-source error isolation (new emphasis)
      - Coordinated redo processing (new emphasis)
    - Add production orchestration patterns:
      - Retry with exponential backoff
      - Partial success handling (mark successful sources, retry failed)
      - Orchestrator health monitoring
    - _Requirements: 5.1, 5.4_

  - [x] 6.2 Add Phase 3 results integration to Module 7 steering file
    - When bootcamper completed Phase 3 for multiple sources, instruct agent to reference test load results when planning load order and dependency management
    - Use test entity counts and quality assessments to inform orchestration strategy
    - _Requirements: 5.2_

  - [x] 6.3 Verify Module 7 steering file preserves essential content
    - Verify cross-source match accuracy validation is retained
    - Verify UAT steps are retained
    - Verify stakeholder sign-off steps are retained
    - _Requirements: 5.3_

- [x] 7. Update Module 7 documentation
  - [x] 7.1 Update `senzing-bootcamp/docs/modules/MODULE_7_MULTI_SOURCE_ORCHESTRATION.md`
    - Update overview to describe production-quality multi-source orchestration focus
    - Describe how test load results from Module 5 Phase 3 inform orchestration strategy
    - Update learning objectives: dependency-aware loading, parallel execution, error isolation, coordinated redo processing, cross-source validation
    - Update "When to Use This Module" to clarify single-source skip regardless of Phase 3 completion
    - _Requirements: 6.1, 6.2, 6.3, 6.4_

- [x] 8. Update POWER.md
  - [x] 8.1 Update module table in `senzing-bootcamp/POWER.md`
    - Update Module 5 row: mention optional test load and validate phase
    - Update Module 6 row: emphasize production-quality loading concerns (error handling, throughput, redo, incremental)
    - Update Module 7 row: emphasize production-quality orchestration concerns (dependencies, parallel loading, error isolation)
    - _Requirements: 9.1, 9.2, 9.3_

  - [x] 8.2 Update track descriptions in POWER.md
    - Update Track B (Fast Track) description to note Phase 3 shortcut path benefit for simple use cases
    - Update Track C (Complete Beginner) description to note Phase 3 shortcut path benefit for simple use cases
    - _Requirements: 9.4_

- [x] 9. Write structural validation tests
  - [x] 9.1 Write tests verifying Module 5 steering file Phase 3 content
    - Verify Phase 3 section exists with "Test Load and Validate" title
    - Verify references to mapping_workflow steps 5–8
    - Verify Phase 3 is marked as optional
    - Verify checkpoint step numbers 21–26 are present
    - Verify decision gate content exists
    - Verify shortcut path instructions exist
    - Verify SDK-not-configured handling exists
    - Verify session resume instructions for Phase 3 exist
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 7.1, 7.3, 7.4, 8.3, 8.4_

  - [x] 9.2 Write tests verifying Module 5 documentation Phase 3 content
    - Verify "Test Load and Validate" section exists
    - Verify Phase 3 learning objectives are listed
    - Verify output files are documented
    - Verify success criteria include Phase 3 indicators
    - Verify "Shortcut Path" section exists
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 7.2_

  - [x] 9.3 Write tests verifying Module 6 production focus
    - Verify steering file contains production-quality loading sections (error handling, progress tracking, throughput, redo, incremental)
    - Verify conditional workflow based on Phase 3 completion exists
    - Verify match accuracy review is retained
    - Verify documentation overview describes production-quality loading
    - Verify documentation lists production-quality learning objectives
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 4.1, 4.2, 4.3, 4.4_

  - [x] 9.4 Write tests verifying Module 7 production focus
    - Verify steering file contains production orchestration sections (dependencies, parallel, error isolation, coordinated redo)
    - Verify Phase 3 results are referenced for planning
    - Verify cross-source validation, UAT, and sign-off are retained
    - Verify production orchestration patterns exist (retry, partial success, health monitoring)
    - Verify documentation overview describes production-quality orchestration
    - Verify documentation lists production orchestration learning objectives
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 6.1, 6.2, 6.3, 6.4_

  - [x] 9.5 Write tests verifying POWER.md updates
    - Verify Module 5 description mentions test load and validate
    - Verify Module 6 description emphasizes production-quality loading
    - Verify Module 7 description emphasizes production-quality orchestration
    - Verify track descriptions mention Phase 3 shortcut path
    - _Requirements: 9.1, 9.2, 9.3, 9.4_

- [x] 10. Run full test suite and verify all tests pass
  - Run all existing tests (`test_data_sources.py`, `test_progress_utils.py`, etc.) to confirm no regressions
  - Run all new tests (registry schema, structural validation)
  - Fix any failures before marking complete
  - _Requirements: All_
