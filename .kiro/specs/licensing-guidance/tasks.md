# Implementation Plan: Licensing Guidance

## Overview

Add MCP server license guidance to Module 2 Step 5 of the steering file (`senzing-bootcamp/steering/module-02-sdk-setup.md`). Two content additions are made: one in sub-step 5a (after the SENZ9000 explanation) and one in sub-step 5c's "no license" path (alongside email contacts). A new test file validates the content-specific acceptance criteria.

## Tasks

- [x] 1. Modify steering file to add MCP license guidance
  - [x] 1.1 Add MCP license guidance paragraph to sub-step 5a
    - Insert a new paragraph after the sentence ending with `placed at \`licenses/g2.lic\`.` and before sub-step 5b
    - Content: inform bootcampers they can request a larger evaluation license through the Senzing MCP server
    - Do not introduce new URLs, tool names, pointing questions, or STOP instructions
    - _Requirements: 1.1, 1.2, 1.3, 4.2, 4.3_

  - [x] 1.2 Add MCP license guidance sentence to sub-step 5c "no license" path
    - Insert a sentence after the `support@senzing.com` / `sales@senzing.com` mention and before the `licenses/README.md` reference
    - Content: mention the MCP server as an alternative path for requesting a larger evaluation license interactively
    - Do not introduce new URLs, tool names, pointing questions, or STOP instructions
    - _Requirements: 2.1, 2.2, 2.3, 4.2, 4.3_

- [x] 2. Verify structural test compliance
  - [x] 2.1 Run existing property-based test suite against modified file
    - Execute `pytest senzing-bootcamp/tests/test_steering_structure_properties.py -v`
    - Confirm all six structural properties still pass (YAML frontmatter, pointing question → STOP, single question per step, step-checkpoint, before/after framing, prerequisites)
    - If any test fails, fix the steering file edit before proceeding
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6_

- [x] 3. Checkpoint - Ensure structural tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 4. Create example-based tests for licensing guidance content
  - [x] 4.1 Create test file `senzing-bootcamp/tests/test_licensing_guidance.py`
    - Create a new pytest test file following the project's class-based test organization pattern
    - Import the steering file path and read its content for assertions
    - Use `from __future__ import annotations` and type hints on all signatures
    - _Requirements: 1.1, 2.1_

  - [x] 4.2 Implement tests for sub-step 5a MCP guidance
    - Test that Sub_Step_5a contains text about the MCP server and license requests
    - Test that the MCP guidance line index is greater than the SENZ9000/500-record line index (positioned after existing explanation)
    - Test that Sub_Step_5a still contains "500 records", "SENZ9000", and "licenses/g2.lic" (preserves existing content)
    - _Requirements: 1.1, 1.2, 1.3_

  - [x] 4.3 Implement tests for sub-step 5c "no license" MCP guidance
    - Test that the "no license" branch mentions the MCP server
    - Test that both MCP guidance and email contacts (`support@senzing.com`, `sales@senzing.com`) exist in the same section
    - Test that the "no license" section still contains the confirmation message, email contacts, `licenses/README.md` reference, and `bootcamp_preferences.yaml` recording instruction
    - _Requirements: 2.1, 2.2, 2.3_

  - [x] 4.4 Implement scope and accuracy tests
    - Test that modifications are scoped to Step 5 only (non-Step-5 content unchanged)
    - Test that no new URLs or tool names are introduced beyond what already exists in the file
    - Test that no new pointing questions (👉) or STOP instructions are added in Step 5
    - _Requirements: 4.1, 4.2, 4.3_

- [x] 5. Final checkpoint - Ensure all tests pass
  - Run `pytest senzing-bootcamp/tests/test_licensing_guidance.py senzing-bootcamp/tests/test_steering_structure_properties.py -v`
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- This is a content-only change to a single markdown steering file — no new components or modules
- The existing property-based test suite validates structural invariants; new tests validate content-specific acceptance criteria
- No property-based tests are added because the acceptance criteria are content-specific checks on known static text (no meaningful input variation)
- The Senzing MCP server (`mcp.senzing.com`) is already referenced elsewhere in the power, so no new external endpoints are introduced

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1", "1.2"] },
    { "id": 1, "tasks": ["2.1"] },
    { "id": 2, "tasks": ["4.1"] },
    { "id": 3, "tasks": ["4.2", "4.3", "4.4"] }
  ]
}
```
