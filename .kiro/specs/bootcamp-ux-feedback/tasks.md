# Implementation Plan: Bootcamp UX Feedback

## Overview

This plan implements two UX improvements to the Senzing Bootcamp Power: reordering the onboarding overview bullet points in Step 4 of `onboarding-flow.md`, and adding a delivery-mode selection flow to `visualization-protocol.md` with corresponding tracker schema updates. All changes are to Markdown steering files and Python test files.

## Tasks

- [x] 1. Reorder onboarding overview bullet points in Step 4
  - [x] 1.1 Reorder the three bullet points in `senzing-bootcamp/steering/onboarding-flow.md` Step 4
    - In the overview section (after the modules table, before section 4a), change the bullet order from: Test data → License → Tracks to: Tracks → License → Test data
    - Preserve all existing bullet text exactly as-is (no wording changes)
    - Ensure the guided-discovery preamble bullet remains first and the glossary reference bullet remains last
    - _Requirements: 1.1, 1.2, 1.3_

  - [x] 1.2 Write unit tests for onboarding bullet order
    - Create `senzing-bootcamp/tests/test_bootcamp_ux_feedback_unit.py`
    - Test that the three reordered bullets appear in correct sequence (Tracks → License → Test data)
    - Test that all original bullet points are present with unaltered text
    - Test that guided-discovery preamble is first and glossary reference is last
    - _Requirements: 1.1, 1.2, 1.3_

- [x] 2. Add delivery-mode selection to visualization protocol
  - [x] 2.1 Add the "Delivery-Mode Selection" section to `senzing-bootcamp/steering/visualization-protocol.md`
    - Insert new section between the existing "Offer Template" section and the "Dispatch Rules" section
    - Include the skip condition for static-only checkpoints (Module 5)
    - Include the two delivery-mode options (Static HTML, Web service + HTML) with descriptions
    - End with a STOP directive waiting for bootcamper input
    - _Requirements: 2.1, 2.2, 2.6, 2.7_

  - [x] 2.2 Update dispatch rules in `senzing-bootcamp/steering/visualization-protocol.md`
    - Web service delivery mode: dispatch to `visualization-web-service.md` for scaffolding and lifecycle
    - Static HTML delivery mode: generate inline, do NOT load `visualization-web-service.md`
    - Interactive_D3_Graph or Web_Service_Dashboard type + static delivery: load `visualization-guide.md` for generation logic only
    - _Requirements: 2.3, 2.4_

  - [x] 2.3 Write unit tests for delivery-mode section
    - Test that `visualization-protocol.md` contains the delivery-mode question with both options
    - Test that delivery-mode section appears after type selection and before dispatch rules
    - Test that dispatch rules reference `visualization-web-service.md` for web service mode
    - Test that static path does NOT load `visualization-web-service.md`
    - Test that delivery-mode section ends with a STOP directive
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.7_

- [x] 3. Update visualization tracker schema for delivery mode
  - [x] 3.1 Update tracker schema in `senzing-bootcamp/steering/visualization-protocol.md`
    - Add `delivery_mode` field to the JSON schema example (valid values: `"static"`, `"web_service"`, or `null`)
    - Update version from `"1.0.0"` to `"1.1.0"`
    - Add `delivery_mode` to the field documentation table
    - Update Read/Write Instructions to document delivery_mode behavior on state transitions
    - _Requirements: 3.1, 3.2, 3.3, 3.4_

  - [x] 3.2 Write unit test for schema version
    - Test that tracker schema version in `visualization-protocol.md` is `"1.1.0"`
    - Test that `delivery_mode` field is documented in the schema
    - _Requirements: 3.4, 3.1_

- [x] 4. Checkpoint — Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 5. Write property-based tests for correctness properties
  - [x] 5.1 Write property test for tracker delivery_mode field validity
    - Create `senzing-bootcamp/tests/test_bootcamp_ux_feedback_properties.py`
    - **Property 1: Tracker delivery_mode field validity**
    - Generate random tracker entries with arbitrary field values; validate that only `"static"`, `"web_service"`, or `null` are accepted
    - **Validates: Requirements 3.1**

  - [x] 5.2 Write property test for new offer entries having null delivery_mode
    - **Property 2: New offer entries have null delivery_mode**
    - Generate random offer creation events (random module, checkpoint_id, timestamp); verify all created entries have `delivery_mode = null`
    - **Validates: Requirements 3.2**

  - [x] 5.3 Write property test for acceptance setting delivery_mode
    - **Property 3: Acceptance sets delivery_mode**
    - Generate random acceptance events (random chosen_type, random delivery_mode from valid set); verify resulting entry has non-null `delivery_mode` matching input
    - **Validates: Requirements 2.5, 3.3**

  - [x] 5.4 Write property test for static-only checkpoint defaulting
    - **Property 4: Static-only checkpoints default to static**
    - Generate random checkpoint configurations; for any config where `types == ["Static_HTML_Report"]`, verify resolved delivery_mode is `"static"`
    - **Validates: Requirements 2.6**

- [x] 6. Final checkpoint — Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties from the design document
- Unit tests validate specific examples and structural expectations of the steering files
- All tests use pytest + Hypothesis and live in `senzing-bootcamp/tests/`
