# Implementation Plan: Entity Resolution Quality Evaluation Loop

## Overview

Add a structured quality evaluation step (Step 3b) to Module 7 steering, document the Module 7→5 feedback loop in `module-transitions.md`, and write tests verifying the new content.

## Tasks

- [x] 1. Add quality evaluation step to module-07-query-validation.md
  - [x] 1.1 In `senzing-bootcamp/steering/module-07-query-validation.md`, insert a new Step 3b "Quality evaluation" after the existing Step 3a (matching concepts) and before the existing Step 3b (entity graph visualization)
  - [x] 1.2 Add an agent instruction block calling `reporting_guide(topic='quality', language='<chosen_language>', version='current')` for the evaluation methodology
  - [x] 1.3 Add an agent instruction block calling `search_docs(query='entity resolution quality evaluation', version='current')` for authoritative context
  - [x] 1.4 Add a quality summary table template with indicators: entity-to-record ratio, possible match count/percentage, cross-source match rate
  - [x] 1.5 Add quality threshold definitions: acceptable (proceed — possible matches < 5%, no split/merge signals), marginal (review — possible matches 5-15% or some signals), poor (iterate — possible matches > 15%, clear patterns, or no matching)
  - [x] 1.6 Add response guidance for each threshold: acceptable → proceed to visualizations, marginal → show specific entities then decide, poor → present recommendations and offer Module 5 feedback loop
  - [x] 1.7 Add the Module 5 feedback loop instructions: 👉 question offering return to Module 5, preservation of Module 6/7 progress, re-entry at Phase 2, tracking via `quality_iteration` key in progress file
  - [x] 1.8 Add checkpoint instruction: "Write step 3b to `config/bootcamp_progress.json`"
    - _Requirements: 1, 2, 3, 4, 5, 6, 7, 8_

- [x] 2. Renumber existing visualization steps
  - [x] 2.1 In `senzing-bootcamp/steering/module-07-query-validation.md`, rename the existing Step 3b (entity graph visualization) to Step 3c, updating the heading, checkpoint reference, and any internal references
  - [x] 2.2 Rename the existing Step 3c (results dashboard visualization) to Step 3d, updating the heading, checkpoint reference, and any internal references
  - [x] 2.3 Update the Success Criteria section to reference the new step numbering (3c and 3d for visualizations)
    - _Requirements: 1_

- [x] 3. Add backward transition to module-transitions.md
  - [x] 3.1 In `senzing-bootcamp/steering/module-transitions.md`, add a "Quality Feedback Loop (Module 7 → Module 5)" section after the existing "Transition Integrity" section
  - [x] 3.2 Document that this is a valid backward transition preserving Module 6/7 progress
  - [x] 3.3 Document that Module 5 is re-entered at Phase 2 (data mapping), not Phase 1
  - [x] 3.4 Document that after remapping, the bootcamper reloads affected sources (Module 6) then re-evaluates (Module 7)
  - [x] 3.5 Document the `quality_iteration` key in progress that tracks which sources triggered the loop
    - _Requirements: 9_

- [x] 4. Write unit tests
  - [x] 4.1 Create `senzing-bootcamp/tests/test_er_quality_evaluation.py` with imports (pathlib, re, pytest) and path constants pointing to `module-07-query-validation.md` and `module-transitions.md`
  - [x] 4.2 Add `TestQualityEvaluationStepExists` class: test that Module 7 steering contains a "Quality evaluation" step (or "quality evaluation" heading/label)
  - [x] 4.3 Add `TestMcpToolReferences` class: test that the quality evaluation step references `reporting_guide` with `topic='quality'`, test that it references `search_docs` with a quality-related query
  - [x] 4.4 Add `TestQualityThresholds` class: test that the step defines three threshold levels (acceptable/marginal/poor), test that each threshold has an associated action
  - [x] 4.5 Add `TestFeedbackLoopInstructions` class: test that Module 5 feedback loop is documented in Module 7 steering, test that progress preservation is mentioned, test that Phase 2 re-entry is specified
  - [x] 4.6 Add `TestModuleTransitionsBackwardLoop` class: test that `module-transitions.md` contains a section about the Module 7→5 quality feedback loop, test that it mentions progress preservation, test that it mentions Phase 2 re-entry
    - _Requirements: 10_

- [x] 5. Run tests and validate
  - [x] 5.1 Run `python3 -m pytest senzing-bootcamp/tests/test_er_quality_evaluation.py -v` and verify all tests pass
  - [x] 5.2 Run `python3 senzing-bootcamp/scripts/validate_commonmark.py` to verify modified markdown files pass CommonMark validation
  - [x] 5.3 Run `python3 senzing-bootcamp/scripts/measure_steering.py --check` to verify token budgets are not exceeded (module-07-query-validation.md should remain under 5000 tokens)

## Notes

- The quality evaluation step adds ~400-500 tokens to `module-07-query-validation.md` (currently 2,193 tokens) — well within the 5,000-token split threshold
- Quality indicators are computed by the agent at runtime using SDK queries — no new Python scripts needed
- The `reporting_guide(topic='quality')` MCP tool provides the evaluation methodology; the agent applies it to the bootcamper's specific data
- Thresholds are advisory — the bootcamper always has the final say
- The feedback loop does NOT use rollback or track switching — it's an iterative refinement within normal flow
- Tests follow the existing pattern in `test_mapping_workflow_integration.py` — reading steering files and asserting content presence
- No Hypothesis/property-based tests needed — these are content-verification tests only
- The `visualization-protocol.md` checkpoint IDs (`m7_exploratory_queries`, `m7_findings_documented`) may need updating if they reference step numbers — check during implementation
