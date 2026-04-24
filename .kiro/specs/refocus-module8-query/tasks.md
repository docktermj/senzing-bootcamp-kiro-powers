# Implementation Plan: Refocus Module 8 on Query & Visualize

## Overview

Rename Module 7 from "Query, Visualize & Validate" to "Query & Visualize" and move validation steps (UAT, match accuracy, stakeholder sign-off) into the data loading modules (5 and 6) as their natural conclusion. All changes are documentation and steering file edits — no application code.

> Note: The requirements reference "Module 8" based on the original feedback numbering, but the current codebase numbers this as Module 7. All tasks operate on the actual current file names and module numbers.

## Tasks

- [x] 1. Rename and trim Module 7 documentation
  - [x] 1.1 Update title, banner, and overview in `senzing-bootcamp/docs/modules/MODULE_7_QUERY_VALIDATION.md`
    - Change banner from `MODULE 7: QUERY, VISUALIZE, AND VALIDATE RESULTS` to `MODULE 7: QUERY AND VISUALIZE`
    - Change title from "Module 7: Query, Visualize, and Validate Results" to "Module 7: Query and Visualize"
    - Update overview to focus on query programs, search programs, overlap reports, and visualizations — remove "validating that the solution meets business requirements through User Acceptance Testing (UAT)"
    - Update the Focus line to remove validation
    - _Requirements: 1, 3_
  - [x] 1.2 Remove validation sections from Module 7 documentation
    - Remove Step 5 (Create UAT Test Cases), Step 6 (Execute UAT Tests), Step 7 (Resolve Issues), Step 8 (Get Sign-Off)
    - Remove the "User Acceptance Testing (UAT)" section
    - Remove UAT-related entries from the "File Locations" tree (`uat_executor`, `uat_test_cases.md`, `uat_results.md`, `uat_issues.yaml`, `uat_signoff.md`, `uat_execution.log`)
    - Remove UAT-related items from "Validation Gates" (UAT test cases created, all UAT tests executed, all critical tests pass, issues documented and resolved, stakeholder sign-off obtained)
    - Update "Success Indicators" to remove UAT references — focus on query programs working and visualizations created
    - Remove "Issue: UAT Tests Fail" from Common Issues
    - Remove UAT references from Agent Behavior list (items 7-11 about UAT)
    - Update "Related Documentation" to remove `steering/uat-framework.md` reference
    - _Requirements: 1, 2_
  - [x] 1.3 Update Learning Objectives in Module 7 documentation
    - Remove objectives about UAT: "Create User Acceptance Test (UAT) cases", "Validate results against business requirements", "Get stakeholder sign-off"
    - Add/keep objectives about visualizations and overlap reports
    - _Requirements: 1_

- [x] 2. Rename and trim Module 7 steering file
  - [x] 2.1 Update title, purpose, and before/after in `senzing-bootcamp/steering/module-07-query-validation.md`
    - Change title from "Module 7: Query, Visualize, and Validate Results" to "Module 7: Query and Visualize"
    - Update Purpose line to "Create query programs and visualizations"
    - Update Before/After to remove validation language — focus on "query programs that answer your business questions and visualizations of your resolved entities"
    - _Requirements: 1, 3_
  - [x] 2.2 Remove validation steps from Module 7 steering file
    - Remove step 4 (Create UAT test cases), step 5 (Execute UAT with business users), step 6 (Validate results quality), step 7 (Document findings — keep only the results dashboard visualization offer, move it to after exploratory queries)
    - Remove the "Iterate vs. Proceed Decision Gate" section (UAT pass rate logic)
    - Remove the "Stakeholder Summary" section
    - Update Success Criteria to remove UAT/validation items — keep only query and visualization criteria
    - _Requirements: 1, 2_
  - [x] 2.3 Update the decision gate in Module 7 steering to focus on query completeness
    - Replace the removed UAT-based decision gate with a simpler query completeness gate: "Query programs created and tested? Visualizations offered? Ready to proceed to Module 8 (performance) or stop here if on Path B/C."
    - _Requirements: 1_

- [x] 3. Add validation phase to Module 5 documentation and steering
  - [x] 3.1 Add validation phase section to `senzing-bootcamp/docs/modules/MODULE_5_SINGLE_SOURCE_LOADING.md`
    - Add a new "Validation Phase" section after the existing "Loading Statistics" section
    - Include: basic match accuracy checking (are correct records matched?), false positive/negative review, results validation for single-source scenarios
    - Add UAT-related file locations to the file tree (`docs/uat_test_cases.md`, `docs/uat_results.md`, `docs/results_validation.md`)
    - Update "Validation Gates" to include validation checks (match accuracy reviewed, results validated)
    - Update "Success Indicators" to include validation completion
    - Update "Integration with Other Modules" to note that validation now lives here
    - _Requirements: 2, 4_
  - [x] 3.2 Add validation steps to `senzing-bootcamp/steering/module-05-single-source.md`
    - After step 10 (Repeat for remaining data sources) and before step 11 (Transition to Module 6), add validation steps: validate match accuracy, run basic UAT for single-source, document results
    - Include the results dashboard visualization offer (adapted from Module 7 steering)
    - Update the transition step to reference that validation is now complete
    - Update the SQLite performance note reference from "validate the results in Module 7" to "validate the results here"
    - _Requirements: 2, 4_

- [x] 4. Add validation phase to Module 6 documentation and steering
  - [x] 4.1 Add validation phase section to `senzing-bootcamp/docs/modules/MODULE_6_MULTI_SOURCE_ORCHESTRATION.md`
    - Add a "Validation Phase" section as the final section before "Agent Behavior"
    - Include: cross-source match accuracy, full UAT with business users, stakeholder sign-off, results validation — this is the comprehensive validation since multi-source is where cross-source matching happens
    - Add UAT-related file locations to the output files list
    - Update "Validation Gates" to include validation checks
    - Update "Success Indicators" to include validation and sign-off
    - _Requirements: 2, 4_
  - [x] 4.2 Add validation steps to `senzing-bootcamp/steering/module-06-multi-source.md`
    - After step 12 (Document results), add validation steps as a new final phase: validate cross-source results quality (match accuracy, false positives/negatives), execute UAT with business users, get stakeholder sign-off
    - Include the results dashboard visualization offer
    - Include the "Iterate vs. Proceed Decision Gate" (moved from Module 7) with UAT pass rate logic
    - Include the stakeholder summary offer (moved from Module 7)
    - Update Success Criteria to include validation items
    - Update the SQLite performance note reference from "confirm results in Module 7" to "validate results here"
    - _Requirements: 2, 4_

- [x] 5. Update POWER.md
  - [x] 5.1 Update module tables in `senzing-bootcamp/POWER.md`
    - In the main module table, change Module 7 description from "Query, Visualize & Validate" to "Query & Visualize" and update the "Why It Matters" column to "Proves the system answers your business questions" (remove validation language)
    - In the Bootcamp Modules table at the bottom, change Module 7 topic from "Query, Visualize, and Validate Results" to "Query and Visualize"
    - Update Module 5 "Why It Matters" to mention validation as part of loading
    - Update Module 6 "Why It Matters" to mention cross-source validation
    - _Requirements: 3_
  - [x] 5.2 Update steering file list in POWER.md
    - Change `module-07-query-validation.md` description from "Module 7: Query and Validation" to "Module 7: Query and Visualize"
    - _Requirements: 3_

- [x] 6. Update cross-references across documentation
  - [x] 6.1 Update `senzing-bootcamp/docs/diagrams/module-flow.md`
    - Change Module 7 box label from "Query, Viz & Validate" to "Query & Visualize"
    - Update Module 7 outputs line from "src/query/* programs, UAT results" to "src/query/* programs, visualizations"
    - _Requirements: 3_
  - [x] 6.2 Update `senzing-bootcamp/docs/modules/README.md`
    - Change Module 7 heading from "Module 7: Query, Visualize, and Validate Results" to "Module 7: Query and Visualize"
    - Update Module 7 Purpose and Key Topics to remove UAT/validation references
    - Update Module 5 and 6 Key Topics to mention validation
    - _Requirements: 3_
  - [x] 6.3 Update `senzing-bootcamp/steering/module-08-performance.md`
    - Update prerequisite description to reference Module 7 (query) completion rather than validation completion
    - Update Step 6 reference from "Benchmark all query patterns from Module 7" — keep the reference but ensure it doesn't imply validation
    - _Requirements: 3_
  - [x] 6.4 Update remaining steering file cross-references
    - `senzing-bootcamp/steering/module-05-single-source.md`: Update step 11 transition text from "Module 7 (Query, Visualize, and Validate Results)" to "Module 7 (Query and Visualize)"
    - `senzing-bootcamp/steering/module-06-multi-source.md`: Update any references to "confirm results in Module 7" to reflect validation now happening in Module 6
    - `senzing-bootcamp/steering/module-prerequisites.md`: Change Module 7 entry from "Query & Validate" to "Query & Visualize"
    - `senzing-bootcamp/steering/common-pitfalls.md`: Change Module 7 heading from "Query and Validation" to "Query and Visualize"
    - `senzing-bootcamp/steering/visualization-guide.md`: Update triggers and prerequisites to remove validation references, update "after validation in Module 7 step 6" trigger
    - `senzing-bootcamp/steering/cloud-provider-setup.md`: Update "Module 7→8 validation gate" reference if needed
    - `senzing-bootcamp/steering/onboarding-flow.md`: Update hook descriptions that reference Module 7 validation
    - `senzing-bootcamp/steering/data-lineage.md`: Update Module 7 usage description if it references validation
    - _Requirements: 3_
  - [x] 6.5 Update `senzing-bootcamp/docs/modules/MODULE_8_PERFORMANCE_TESTING.md`
    - Update "After validating results in Module 7" reference in the Purpose section
    - _Requirements: 3_

- [x] 7. Validate changes
  - [x] 7.1 Run `python3 senzing-bootcamp/scripts/validate_power.py` to check cross-reference integrity
    - _Requirements: 3_
  - [x] 7.2 Run `python3 senzing-bootcamp/scripts/validate_commonmark.py` to verify markdown formatting
    - _Requirements: 3_

## Notes

- All tasks are documentation and steering file edits — no application code is created or modified
- No property-based tests apply since there are no functions or data transformations to test
- The `module8-visualization-enforcement` spec references `module-08-query-validation.md` which doesn't exist (it references the old numbering). Those spec files are in `.kiro/specs/` and are not part of the distributed power — they don't need updating as part of this task
- Hook files (`offer-visualization`, `enforce-visualization-offers`) trigger on file patterns and module number checks, not module names — they remain functionally correct but their description text in `hooks/README.md` may reference the old name. Updating hook descriptions is optional and can be done separately
- Each task references specific requirements from the requirements document for traceability
