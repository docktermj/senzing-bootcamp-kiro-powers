# Implementation Plan: Probe Entities Visualization

## Overview

Enrich the Module 3 Phase 2 steering file to specify resolution reasoning (match keys, feature scores, resolution rules) in the Probe tab. The primary deliverable is updating `module-03-phase2-visualization.md` so the agent generates enriched search behavior during the bootcamp. Property-based tests validate the extraction function contracts, and unit tests validate steering file content.

## Tasks

- [x] 1. Update steering file with enriched Probe tab specification
  - [x] 1.1 Add enriched `/api/search` response schema to steering file
    - Add a new `GET /api/search` response schema section to `senzing-bootcamp/steering/module-03-phase2-visualization.md` specifying `match_keys`, `feature_scores`, `resolution_rules`, and `enrichment_error` fields
    - Include the full JSON schema example showing entity-level and per-record match keys, feature score entries (feature, score, label), and resolution rule entries (data_source, record_id, rule)
    - Include the error case response (null enrichment fields + `enrichment_error` string)
    - Include the single-record entity response (empty `per_record` list, empty `resolution_rules` list)
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 6.3_

  - [x] 1.2 Update `search_builder.py` specification in steering file
    - Update the `search_builder.py` description in the Required Files table to specify it calls `get_entity_by_entity_id` after `search_by_attributes` for enrichment
    - Add specification that enrichment is capped at 10 entities maximum
    - Specify extraction of match keys (entity-level + per-record), feature scores (feature, score, label), and resolution rules (data_source, record_id, rule)
    - Specify graceful degradation: if `get_entity_by_entity_id` raises any exception, return basic result with null enrichment fields and `enrichment_error` string
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 6.2_

  - [x] 1.3 Update Probe_Panel specification with resolution reasoning display
    - Update the Probe_Panel section (tab 4) to specify display of match keys, feature scores, and resolution rules for each search result
    - Specify match key chips: each feature indicator (`+NAME`, `+DOB`) as a separate inline `<span>` element with visible border/background
    - Specify feature scores: structured list showing feature name, percentage, and classification label
    - Specify resolution rules: per-record rule strings in monospace/code-style format
    - Specify per-record match key omission for single-record entities
    - Specify placeholder label when no match key data is available
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 3.1, 3.2, 3.3, 4.1, 4.2, 4.3, 6.1_

- [x] 2. Checkpoint - Verify steering file updates
  - Ensure all tests pass, ask the user if questions arise.

- [x] 3. Write property-based tests for extraction functions
  - [x] 3.1 Write property test for enrichment cap (Property 1)
    - Create `senzing-bootcamp/tests/test_probe_entities_visualization_properties.py`
    - Implement Hypothesis strategy generating search result lists of varying length (0–30 entities)
    - **Property 1: Enrichment cap limits SDK calls**
    - Verify exactly min(N, 10) entities are enriched; remaining have null enrichment fields
    - Use `@settings(max_examples=20)` per project convention
    - **Validates: Requirements 1.1, 1.6**

  - [x] 3.2 Write property test for match key extraction (Property 2)
    - **Property 2: Match key extraction preserves structure**
    - Generate random entity detail JSON with entity-level match key string and variable per-record match keys
    - Verify `_extract_match_keys` returns dict with correct `entity_level` string and `per_record` list length matching input record count
    - **Validates: Requirements 1.2, 5.1**

  - [x] 3.3 Write property test for feature score extraction (Property 3)
    - **Property 3: Feature score extraction completeness**
    - Generate random search match info with variable feature comparisons
    - Verify `_extract_feature_scores` returns list with correct length, each entry having `feature` (non-empty string), `score` (int 0–100), `label` (non-empty string)
    - **Validates: Requirements 1.3, 5.2**

  - [x] 3.4 Write property test for resolution rule extraction (Property 4)
    - **Property 4: Resolution rule extraction preserves per-record association**
    - Generate random entity detail JSON with records containing resolution rules
    - Verify `_extract_resolution_rules` returns list with correct length, each entry having `data_source`, `record_id`, `rule` (all non-empty strings)
    - **Validates: Requirements 1.4, 5.3**

  - [x] 3.5 Write property test for enrichment error handling (Property 5)
    - **Property 5: Enrichment error produces graceful degradation**
    - Generate random exception type names and message strings
    - Verify enrichment result has null `match_keys`, null `feature_scores`, null `resolution_rules`, and `enrichment_error` as non-empty string containing both exception type and message
    - **Validates: Requirements 1.5, 5.4**

  - [x] 3.6 Write property test for single-record entities (Property 6)
    - **Property 6: Single-record entities have empty per-record fields**
    - Generate random single-record entity detail (record_count = 1)
    - Verify `match_keys.per_record` is empty list, `resolution_rules` is empty list, while `match_keys.entity_level` and `feature_scores` remain populated
    - **Validates: Requirements 5.5**

- [x] 4. Write unit tests for steering file content validation
  - [x] 4.1 Write unit tests verifying steering file contains enrichment specifications
    - Create `senzing-bootcamp/tests/test_probe_entities_visualization_unit.py`
    - Verify `module-03-phase2-visualization.md` contains `match_keys` field specification
    - Verify steering file contains `feature_scores` field specification
    - Verify steering file contains `resolution_rules` field specification
    - Verify steering file specifies `get_entity_by_entity_id` call
    - Verify steering file specifies enriched `/api/search` response schema
    - _Requirements: 6.1, 6.2, 6.3_

  - [x] 4.2 Write unit tests verifying frontend rendering specifications
    - Verify steering file specifies inline chip elements for match keys (separate `<span>` with visible boundary)
    - Verify steering file specifies structured format for feature scores (feature name, percentage, label)
    - Verify steering file specifies monospace/code-style format for resolution rules
    - Verify steering file specifies per-record match key omission for single-record entities
    - Verify steering file specifies placeholder for missing match key data
    - _Requirements: 2.3, 2.4, 2.5, 3.2, 4.3_

- [x] 5. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties from the design document
- Unit tests validate steering file content to ensure the specification is complete
- Tests use `@settings(max_examples=20)` per project convention for `senzing-bootcamp/tests/`
- The steering file is the primary deliverable — it specifies what the agent generates during the bootcamp
- Python 3.11+ stdlib only for scripts; pytest + Hypothesis for tests

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1"] },
    { "id": 1, "tasks": ["1.2", "1.3"] },
    { "id": 2, "tasks": ["3.1", "4.1"] },
    { "id": 3, "tasks": ["3.2", "3.3", "3.4", "3.5", "3.6", "4.2"] }
  ]
}
```
