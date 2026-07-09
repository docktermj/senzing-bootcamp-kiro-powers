# Implementation Plan

- [x] 1. Write bug condition exploration test
  - **Property 1: Bug Condition** - Misplaced Artifacts Route to Wrong Locations
  - **CRITICAL**: This test MUST FAIL on unfixed code - failure confirms the bug exists
  - **DO NOT attempt to fix the test or the code when it fails**
  - **NOTE**: This test encodes the expected behavior - it will validate the fix when it passes after implementation
  - **GOAL**: Surface counterexamples that demonstrate the routing bugs exist in `organize_mapping_files.py`
  - **Scoped PBT Approach**: Scope the property to concrete failing cases for deterministic routing bugs
  - Test file: `senzing-bootcamp/tests/test_file_placement_conventions.py`
  - Import `route` from `organize_mapping_files` via `sys.path` manipulation per project conventions
  - Test cases (all assert expected behavior that will FAIL on unfixed code):
    - `route("sz_json_analyzer.py")` should return `"src/resources"` (currently returns `"src/mapping"`)
    - `route("sz_verbatim_check.py")` should return `"src/resources"` (currently returns `"src/mapping"`)
    - `route("sz_routing_report.py")` should return `"src/resources"` (currently returns `"src/mapping"`)
    - `route("customers_sample.jsonl")` should return `"data/mapping"` (currently returns `"data"`)
    - `route("transactions_sample.jsonl")` should return `"data/mapping"` (currently returns `"data"`)
    - `route("customers_mapping_spec.json")` should return `"data/mapping"` (currently returns `"config"`)
    - `route("customers.jsonl")` should return `"data/transformed"` (currently returns `"data"`)
  - Use Hypothesis `@given()` with strategies generating resource script names (`st.sampled_from(["sz_json_analyzer.py", "sz_verbatim_check.py", "sz_routing_report.py"])`) and sample JSONL names (`st.from_regex(r"[a-z]+_sample\.jsonl")`)
  - Class: `TestBugConditionExploration`
  - Run test on UNFIXED code
  - **EXPECTED OUTCOME**: Test FAILS (this is correct - it proves the bug exists)
  - Document counterexamples found to understand root cause
  - Mark task complete when test is written, run, and failure is documented
  - _Requirements: 1.2, 1.4, 1.5, 2.2, 2.4, 2.5_

- [x] 2. Write preservation property tests (BEFORE implementing fix)
  - **Property 2: Preservation** - Non-Affected Artifacts Route Unchanged
  - **IMPORTANT**: Follow observation-first methodology
  - Test file: `senzing-bootcamp/tests/test_file_placement_conventions.py` (append to same file)
  - Observe on UNFIXED code:
    - `route("senzing_entity_specification.md")` returns `"docs/reference"`
    - `route("customers_mapper.md")` returns `"docs/mapping"`
    - `route("any_report.md")` returns `"docs/mapping"`
    - `route("transform_customers.py")` returns `"src/mapping"`
    - `route("bootcamp_progress.json")` returns `"config"`
  - Write property-based tests with Hypothesis:
    - Strategy `st_non_resource_py`: generates `.py` filenames that do NOT start with `sz_` — assert routes to `"src/mapping"`
    - Strategy `st_non_sample_non_mapping_spec_json`: generates `.json` filenames not ending in `_mapping_spec.json` — assert routes to `"config"`
    - Strategy `st_mapper_md`: generates `*_mapper.md` filenames — assert routes to `"docs/mapping"`
    - Strategy `st_generic_md`: generates `.md` filenames not matching entity spec or mapper — assert routes to `"docs/mapping"`
    - Strategy `st_unknown_ext`: generates filenames with extensions not in routing rules — assert routes to `None`
  - Class: `TestPreservationProperties`
  - Verify tests PASS on UNFIXED code (confirms baseline behavior to preserve)
  - **EXPECTED OUTCOME**: Tests PASS (this confirms baseline behavior to preserve)
  - Mark task complete when tests are written, run, and passing on unfixed code
  - _Requirements: 3.1, 3.2, 3.3, 3.4_

- [x] 3. Fix steering text: stakeholder summary path

  - [x] 3.1 Update `senzing-bootcamp/steering/module-01-phase2-document-confirm.md` step 17
    - Change output path from `docs/stakeholder_summary_module1.md` to `docs/stakeholder_summary.md`
    - _Bug_Condition: isBugCondition(X) where X.kind = STAKEHOLDER_SUMMARY AND X.directedPath = "docs/stakeholder_summary_module1.md"_
    - _Expected_Behavior: path = "docs/stakeholder_summary.md"_
    - _Preservation: Historical references to old name unchanged per 3.1_
    - _Requirements: 1.1, 2.1_

  - [x] 3.2 Update `senzing-bootcamp/templates/stakeholder_summary.md` MODULE 1 guidance block
    - Change `Output: docs/stakeholder_summary_module1.md` to `Output: docs/stakeholder_summary.md`
    - _Requirements: 1.1, 2.1_

- [x] 4. Fix steering text: module-05 post-run relocation guidance

  - [x] 4.1 Update `senzing-bootcamp/steering/module-05-phase2-data-mapping.md`
    - Add post-run relocation guidance block after the existing "Leave transient run artifacts" block
    - New block instructs: after mapping run completes, relocate `profile_report.md`, `schema_hints.md`, `JOURNAL.md` to `docs/mapping/`; relocate `*_mapping_spec.json`, `{source}_sample.jsonl`, intermediate analyzer JSONL to `data/mapping/`
    - Add clarifying sentence to existing transient block: "Once the mapping_workflow run for a source is complete (after the iterate/finalize step), relocate these artifacts to their durable homes per the file-placement contract."
    - _Bug_Condition: isBugCondition(X) where X.kind IN {MAPPING_MARKDOWN, MAPPING_WORKING_DATA} AND X.directedPath IN data_temp_
    - _Expected_Behavior: Markdown to docs/mapping/, working data to data/mapping/_
    - _Preservation: Files remain readable during the mapping run (3.2)_
    - _Requirements: 1.3, 1.4, 2.3, 2.4, 3.2_

- [x] 5. Fix steering text: file-placement contract and agent-instructions

  - [x] 5.1 Update `senzing-bootcamp/steering/file-placement.md`
    - Add `## Canonical File-Placement Contract` section with the six-row artifact-to-location table
    - Update `.jsonl` row in Root Prohibitions to include `data/mapping/` as valid location
    - Update `.py` row to include `src/resources/` as valid location
    - _Bug_Condition: filePlacementContractNotCodified()_
    - _Expected_Behavior: Contract codified in one authoritative location_
    - _Requirements: 1.6, 2.6_

  - [x] 5.2 Update `senzing-bootcamp/steering/agent-instructions.md` File Placement table
    - Add `Resources` to `src/resources/` row
    - Add `Mapping data` to `data/mapping/` row
    - _Requirements: 2.6_

- [x] 6. Fix steering text: project-structure directories

  - [x] 6.1 Update `senzing-bootcamp/steering/project-structure.md`
    - Add `resources` to `src/` brace expansion in directory tree
    - Add `mapping` to `data/` brace expansion in directory tree
    - Add `"src/resources"` and `"data/mapping"` to the Python `os.makedirs` list
    - Add `resources` to `src/{}` in the Linux/macOS `mkdir -p` command
    - Add `mapping` to `data/{}` in the Linux/macOS `mkdir -p` command
    - Add `'src/resources'` and `'data/mapping'` to the PowerShell array
    - _Bug_Condition: directories not listed in project structure_
    - _Expected_Behavior: src/resources and data/mapping exist in structure_
    - _Requirements: 2.2, 2.4, 2.6_

- [x] 7. Fix script: organize_mapping_files.py routing rules

  - [x] 7.1 Add resource script routing rules to `ROUTING_RULE_LIST`
    - Add `match_name("sz_json_analyzer.py")` to `"src/resources"` BEFORE the generic `.py` rule
    - Add `match_name("sz_verbatim_check.py")` to `"src/resources"` BEFORE the generic `.py` rule
    - Add `match_name("sz_routing_report.py")` to `"src/resources"` BEFORE the generic `.py` rule
    - _Bug_Condition: isBugCondition(X) where X.kind = DOWNLOADED_RESOURCE AND X.directedPath NOT IN "src/resources/"_
    - _Expected_Behavior: route("sz_json_analyzer.py") = "src/resources"_
    - _Preservation: Non-resource .py files still route to "src/mapping"_
    - _Requirements: 1.2, 2.2, 3.3_

  - [x] 7.2 Add mapping data routing rules to `ROUTING_RULE_LIST`
    - Add `match_suffix("_sample.jsonl")` to `"data/mapping"` BEFORE the generic `.jsonl` rule
    - Add `match_suffix("_mapping_spec.json")` to `"data/mapping"` BEFORE the generic `.json` rule
    - _Bug_Condition: isBugCondition(X) where X.kind = MAPPING_WORKING_DATA_
    - _Expected_Behavior: route("customers_sample.jsonl") = "data/mapping", route("customers_mapping_spec.json") = "data/mapping"_
    - _Preservation: Non-mapping JSON still routes to "config"_
    - _Requirements: 1.4, 1.5, 2.4, 2.5, 3.3_

  - [x] 7.3 Update generic `.jsonl` rule destination
    - Change generic `.jsonl` route from `"data"` to `"data/transformed"`
    - Update `ROUTING_RULES` compat dict: `.jsonl` to `"data/transformed"`
    - _Bug_Condition: isBugCondition(X) where X.kind = TRANSFORMED_OUTPUT AND canonicalDestinationNotStated_
    - _Expected_Behavior: route("customers.jsonl") = "data/transformed"_
    - _Preservation: Sample JSONL handled by suffix rule above, so only non-sample JSONL affected_
    - _Requirements: 1.5, 2.5_

- [x] 8. Verify fix

  - [x] 8.1 Verify bug condition exploration test now passes
    - **Property 1: Expected Behavior** - Misplaced Artifacts Now Route Correctly
    - **IMPORTANT**: Re-run the SAME test from task 1 - do NOT write a new test
    - The test from task 1 encodes the expected behavior
    - When this test passes, it confirms the expected behavior is satisfied
    - Run bug condition exploration test from step 1
    - **EXPECTED OUTCOME**: Test PASSES (confirms bug is fixed)
    - _Requirements: 2.2, 2.4, 2.5_

  - [x] 8.2 Verify preservation tests still pass
    - **Property 2: Preservation** - Non-Affected Artifacts Still Route Unchanged
    - **IMPORTANT**: Re-run the SAME tests from task 2 - do NOT write new tests
    - Run preservation property tests from step 2
    - **EXPECTED OUTCOME**: Tests PASS (confirms no regressions)
    - Confirm all tests still pass after fix (no regressions)

  - [x] 8.3 Write integration test for end-to-end file organization
    - Test file: `senzing-bootcamp/tests/test_file_placement_conventions.py` (append to same file)
    - Class: `TestFileOrganizationIntegration`
    - Create a temp directory with mix of files: resource scripts, sample JSONL, transformed JSONL, mapping spec JSON, mapper MD, generic MD
    - Run `main(["--source", source_dir, "--project-root", project_root])` and verify each file lands in correct subdirectory
    - Test `--dry-run` reports planned moves correctly with new routing
    - Verify deduplication behavior unchanged for `senzing_entity_specification.md`
    - _Requirements: 2.2, 2.4, 2.5, 3.3, 3.4_

- [x] 9. Checkpoint - Ensure all tests pass
  - Run full test suite: `python -m pytest senzing-bootcamp/tests/test_file_placement_conventions.py -v`
  - Ensure all tests pass, ask the user if questions arise.
