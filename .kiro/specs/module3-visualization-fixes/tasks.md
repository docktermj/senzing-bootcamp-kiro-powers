# Implementation Plan: Module 3 Visualization Fixes

## Overview

Three targeted edits to `senzing-bootcamp/steering/module-03-phase2-visualization.md`: (1) add an enforcement block preventing Phase 2 skip, (2) replace the fixed 600px graph container height with viewport-relative sizing, (3) add a post-launch guided tour section. Then write property-based and unit tests validating the changes.

## Tasks

- [ ] 1. Add enforcement block to steering file
  - [ ] 1.1 Insert the "DO NOT SKIP" enforcement block after the CRITICAL LESSONS section and before Step 9
    - Add horizontal rule, `## ⚠️ DO NOT SKIP — Phase 2 Execution Is Mandatory` heading
    - Add blockquote with "🚨 This phase is MANDATORY. It is NOT optional." and "DO NOT SKIP" in uppercase
    - Include explicit prohibition of transitioning to Module 4 before Phase 2 completes
    - Close with horizontal rule to visually isolate the block
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_

- [ ] 2. Fix Entity Graph viewport height
  - [ ] 2.1 Replace fixed pixel height with viewport-relative height in the Entity Graph section
    - In section 9.3 Entity_Graph tab description, specify `height: calc(100vh - 120px)` for the graph container
    - Add comment documenting the 120px offset breakdown (header ~50px, banner ~40px, tab nav ~30px)
    - Remove any existing `600px` fixed height specification for the graph container
    - _Requirements: 2.1, 2.2, 2.3_

- [ ] 3. Add post-launch guided tour
  - [ ] 3.1 Insert guided tour instructions in section 9.4 after URL presentation and before the STOP block
    - Add "Guided Tour" instruction block specifying single structured chat message delivery with no interactive pauses
    - Include "🗺️ What You're Looking At — A Quick Tour" content template
    - Cover cross-source matches (nodes with multiple colors representing entities resolved across data sources)
    - Cover name variations (e.g., Robert Smith / Bob Smith / R. Smith)
    - Cover relationship edges with match key labels (e.g., +NAME+ADDRESS, +PHONE)
    - Cover records-per-entity histogram in the Merge Statistics tab
    - Position after "Your visualization is running" URL presentation and before "🛑 STOP" block
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7_

- [ ] 4. Checkpoint - Verify steering file edits
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 5. Write property-based tests
  - [ ]* 5.1 Write property test for enforcement block completeness
    - **Property 1: Enforcement block completeness**
    - **Validates: Requirements 1.1, 1.2, 1.3, 1.4, 1.5**
    - Extract enforcement block (section between CRITICAL LESSONS and Step 9)
    - Verify presence of "DO NOT SKIP" uppercase, "MANDATORY" uppercase, Module 4 transition prohibition, visual marker (emoji or bold), and "not optional" language

  - [ ]* 5.2 Write property test for graph container viewport-relative height
    - **Property 2: Graph container uses viewport-relative height**
    - **Validates: Requirements 2.1, 2.3**
    - Extract CSS height specification for graph container from steering file
    - Verify value contains `vh` (viewport-relative) and does NOT match `\d+px` fixed pixel pattern

  - [ ]* 5.3 Write property test for guided tour content completeness
    - **Property 3: Guided tour content completeness**
    - **Validates: Requirements 3.2, 3.3, 3.4, 3.5**
    - Extract guided tour section (between URL presentation and STOP block)
    - Verify references to: cross-source matches, name variations, relationship edges with match key labels, records-per-entity histogram

  - [ ]* 5.4 Write property test for guided tour structural ordering
    - **Property 4: Guided tour structural ordering**
    - **Validates: Requirements 3.6, 3.7**
    - Verify guided tour appears after URL presentation text (containing "localhost" or "running") and before STOP block (containing "🛑 STOP")
    - Verify single-message delivery specification with no interactive pauses

- [ ] 6. Write unit tests
  - [ ]* 6.1 Write unit tests for viewport height and guided tour placement
    - Test exact `calc(100vh - 120px)` string presence in steering file
    - Test 120px offset explanation mentions header, banner, tab navigation
    - Test guided tour appears after verification step
    - Test no `600px` string in graph container context
    - _Requirements: 2.1, 2.2, 2.3, 3.1_

- [ ] 7. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- All changes target a single file: `senzing-bootcamp/steering/module-03-phase2-visualization.md`
- Tests go in `senzing-bootcamp/tests/test_module3_visualization_fixes_properties.py` and `senzing-bootcamp/tests/test_module3_visualization_fixes_unit.py`
- Property tests use Hypothesis with `@settings(max_examples=100)` and `st.sampled_from()` strategies over extracted sections
- Unit tests use plain pytest assertions against the parsed steering file content
- Each task references specific requirements for traceability

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1", "2.1", "3.1"] },
    { "id": 1, "tasks": ["5.1", "5.2", "5.3", "5.4", "6.1"] }
  ]
}
```
