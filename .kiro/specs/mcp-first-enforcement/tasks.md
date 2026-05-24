# Implementation Plan: MCP-First Enforcement

## Overview

Remove hardcoded Entity Specification attribute lists from Steps 3, 4, and 5 of `module-05-phase1-quality-assessment.md` and replace them with an explicit `download_resource` MCP call instruction. Then validate the changes with property-based tests using pytest + Hypothesis.

## Tasks

- [ ] 1. Modify the steering file to enforce MCP-first principle
  - [ ] 1.1 Rewrite Step 3 to replace hardcoded attributes with download_resource instruction
    - Remove the entire bulleted list of identity attributes, contact attributes, required fields, and relationship attributes from Step 3
    - Remove the `search_docs` call instruction
    - Add an explicit instruction to call `download_resource(filename="senzing_entity_specification.md")`
    - Add language directing the agent to use the downloaded content as the authoritative source for all attribute names, types, and structures in this and subsequent steps
    - _Requirements: 1.1, 1.2, 1.3, 4.1, 4.2, 4.3, 4.4_

  - [ ] 1.2 Rewrite Step 4 to remove hardcoded attribute mapping examples
    - Remove hardcoded attribute name examples in parenthetical mappings (e.g., `"full_name" → NAME_FULL`, `"company" → NAME_ORG`)
    - Retain the general workflow structure (identify direct maps, transformations, non-standard names, missing fields, required fields)
    - Add a reference directing the agent to use the Entity Specification retrieved in Step 3 for field comparisons
    - _Requirements: 2.1, 2.2, 2.3_

  - [ ] 1.3 Rewrite Step 5 to remove hardcoded attribute references
    - Remove the phrase "standard Senzing attribute names" where it implies a known static list
    - Retain the three categories (Entity Specification-compliant, Needs mapping, Needs enrichment)
    - Add generic language referencing "the Entity Specification retrieved in Step 3" as the source of truth
    - _Requirements: 3.1, 3.2_

- [ ] 2. Checkpoint - Verify steering file changes
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 3. Implement property-based tests for the modified steering file
  - [ ] 3.1 Create test helper for step extraction and attribute detection
    - Create `senzing-bootcamp/tests/test_mcp_first_enforcement_properties.py`
    - Implement a helper function that extracts individual step content from the steering file by parsing numbered step boundaries (`N. **Title**`)
    - Define the `KNOWN_ENTITY_SPEC_ATTRIBUTES` set and `ALLOWED_STRUCTURAL_REFS` set as specified in the design
    - _Requirements: 1.1, 2.1, 3.1, 5.1_

  - [ ]* 3.2 Write property test: No hardcoded Entity Specification attributes in Steps 3–5
    - **Property 1: No hardcoded Entity Specification attributes in Steps 3–5**
    - For any step content extracted from Steps 3, 4, or 5, verify no Entity Specification attribute names from the known set appear (excluding `DATA_SOURCE` and `RECORD_ID` in Step 4's required-fields check)
    - **Validates: Requirements 1.1, 2.1, 3.1, 5.1**

  - [ ]* 3.3 Write property test: Exactly one download_resource instruction
    - **Property 2: Exactly one download_resource instruction**
    - For content spanning Steps 3 through 5, verify the count of `download_resource` call instructions equals exactly one
    - **Validates: Requirements 4.1**

  - [ ]* 3.4 Write property test: download_resource placement precedes Entity Specification references
    - **Property 3: download_resource placement precedes Entity Specification references**
    - For content in Step 3, verify the `download_resource` call instruction appears before any reference to Entity Specification content usage
    - **Validates: Requirements 4.2**

- [ ] 4. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties from the design document
- The steering file modification (tasks 1.1–1.3) is the core deliverable; tests validate the structural invariants
- `DATA_SOURCE` and `RECORD_ID` are allowed in Step 4 because they are required structural fields, not part of the attribute enumeration being removed

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1"] },
    { "id": 1, "tasks": ["1.2", "1.3"] },
    { "id": 2, "tasks": ["3.1"] },
    { "id": 3, "tasks": ["3.2", "3.3", "3.4"] }
  ]
}
```
