# Implementation Plan: TruthSet Fallback Source

## Overview

Implement a fallback TruthSet acquisition path for Module 3 (System Verification) that fetches the demo TruthSet from the official Senzing `truth-sets` GitHub repository when the MCP server's `get_sample_data` tool does not expose a named TruthSet. The implementation includes a sanctioned source registry, a Python stdlib-only fetcher script, steering file modifications, and comprehensive test coverage.

## Tasks

- [x] 1. Create Sanctioned Source Registry and core interfaces
  - [x] 1.1 Create `senzing-bootcamp/config/fallback_sources.yaml` registry file
    - Define the YAML schema with version, source identifier, name, purpose, rationale, base_url, files (records list + truth_key), timeout_seconds, approved_by, approved_date
    - Base URL: `https://raw.githubusercontent.com/Senzing/truth-sets/main/truthsets/demo`
    - Record files: `customers.jsonl`, `watchlist.jsonl`, `reference.jsonl`
    - Truth key: `actual_truthset_key.csv`
    - Timeout: 30 seconds
    - _Requirements: 6.1, 6.2_

- [x] 2. Implement Fallback Fetcher Script
  - [x] 2.1 Create `senzing-bootcamp/scripts/fetch_fallback_truthset.py` with registry reader and HTTP fetcher
    - Implement `main()` entry point with argparse CLI accepting `--config` (path to fallback_sources.yaml), `--output-dir` (directory for truthset_data.jsonl), and `--source-id` (registry identifier, default `senzing_truthset_demo`)
    - Read `fallback_sources.yaml` to obtain base_url, file list, and timeout
    - Fetch each record file via `urllib.request.urlopen` with per-request timeout from registry
    - Fetch the truth key file
    - On any non-200 response or timeout, output JSON with `status: "fetch_failed"` and the specific error
    - Python 3.11+ stdlib only (no third-party deps)
    - _Requirements: 3.1, 3.4, 3.5, 6.1, 6.3_

  - [x] 2.2 Implement record normalizer within the fetcher script
    - Concatenate fetched record files into a single JSONL output
    - Parse each line as JSON to validate structure
    - Add `DATA_SOURCE` field if not present (derived from filename: `customers.jsonl` → `CUSTOMERS`)
    - Write all records to the output `truthset_data.jsonl` file, one JSON object per line
    - Ensure normalization is idempotent
    - _Requirements: 4.1, 4.2, 4.3_

  - [x] 2.3 Implement JSONL validator within the fetcher script
    - Validate each line of the output file is valid JSON
    - Verify total line count matches the number of records fetched from source files
    - On validation failure, output JSON with `status: "validation_failed"` identifying which check failed
    - Block progression (do not write success status) on validation failure
    - _Requirements: 4.2, 4.4_

  - [x] 2.4 Implement expected results deriver within the fetcher script
    - Parse `actual_truthset_key.csv` (columns: CLUSTER_ID, RECORD_ID, DATA_SOURCE)
    - Compute expected entity count as count of distinct CLUSTER_ID values
    - Identify known matches: clusters with 2+ records, return at least 3 such clusters
    - If fewer than 3 multi-record clusters found, output JSON with `status: "expected_results_failed"`
    - On success, include `expected_results` object in stdout JSON with entity count, tolerance_percent (5), and known_matches array
    - _Requirements: 5.1, 5.2, 5.4_

  - [x] 2.5 Write property test for normalization round-trip (Property 4)
    - **Property 4: Normalization Round-Trip**
    - For any valid set of TruthSet records, parsing source JSONL, serializing to output file, and re-parsing yields equivalent record set
    - **Validates: Requirements 4.1, 4.2, 4.3**

  - [x] 2.6 Write property test for JSONL validation error detection (Property 5)
    - **Property 5: JSONL Validation Detects Errors**
    - For any file with at least one invalid JSON line or count mismatch, validator reports failure
    - **Validates: Requirements 4.4**

  - [x] 2.7 Write property test for expected results structural completeness (Property 6)
    - **Property 6: Expected Results Structural Completeness**
    - For any valid truth-key CSV, derived results contain positive entity count and at least 3 known-match entries with 2+ records each
    - **Validates: Requirements 5.2**

  - [x] 2.8 Write property test for HTTP error classification (Property 3)
    - **Property 3: HTTP Error Classification**
    - For any HTTP status code outside 200 range, logic classifies source as unreachable and records the specific status code
    - **Validates: Requirements 3.4**

- [x] 3. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 4. Implement steering modifications
  - [x] 4.1 Modify `senzing-bootcamp/steering/module-03-phase1-verification.md` Step 2 to add fallback branch
    - After calling `get_sample_data`, add availability classification logic (inspect response for named TruthSet reference)
    - If primary unavailable (CORD-only response), execute the fallback fetcher script
    - Record classification result in `config/bootcamp_progress.json` before selecting path
    - Set provenance to `mcp_primary` when primary used, `github_fallback` when fallback used
    - Reference the Sanctioned_Source_Registry by identifier (not raw URL)
    - Pass appropriate expected results to Step 7 based on provenance
    - State that primary MCP path takes precedence
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 2.1, 2.2, 2.3, 3.1, 3.2, 3.3, 5.3, 9.1, 9.3_

  - [x] 4.2 Modify `senzing-bootcamp/steering/module-03-phase1-verification.md` to add graceful degradation handling
    - When both sources unavailable: display message identifying both failures with remediation steps
    - Offer bootcamper a clearly labeled non-deterministic CORD substitute, wait for decision
    - If accepted: set provenance to `cord_substitute`, mark deterministic verification as `non_deterministic`
    - If declined: mark as `blocked`, record remediation steps
    - When non_deterministic or blocked: record overall Module 3 status as `incomplete`
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

  - [x] 4.3 Modify `senzing-bootcamp/steering/module-03-system-verification.md` Error Handling section
    - Add documentation of the fallback path under Error Handling
    - Reference the Sanctioned_Fallback_Source by registry identifier
    - State the approval rationale for the external-source exception
    - Document that fallback fetches TruthSet DATA only, SDK facts come from MCP
    - _Requirements: 9.1, 9.2, 9.3_

  - [x] 4.4 Add provenance to Verification Report structure in steering
    - Ensure Step 10 (Report Generation) includes TruthSet_Source_Provenance in the report
    - When provenance is `github_fallback`, state that deterministic verification used the sanctioned fallback source
    - Persist provenance to `config/bootcamp_progress.json` alongside TruthSet acquisition check
    - _Requirements: 8.1, 8.2, 8.3_

  - [x] 4.5 Write property test for TruthSet availability classification (Property 1)
    - **Property 1: TruthSet Availability Classification**
    - For any MCP response, classifier outputs `available` iff response contains named TruthSet with retrievable records, `unavailable` iff CORD-only
    - **Validates: Requirements 1.1, 1.2, 1.3**

  - [x] 4.6 Write property test for path selection and provenance consistency (Property 2)
    - **Property 2: Path Selection and Provenance Consistency**
    - For any availability state, acquisition logic assigns exactly the correct provenance label and routes expected-results selection to the matching source
    - **Validates: Requirements 2.1, 2.2, 2.3, 3.1, 3.3, 5.3, 7.3**

  - [x] 4.7 Write property test for degraded status propagation (Property 8)
    - **Property 8: Degraded Status Propagation**
    - For any run where deterministic-verification is `non_deterministic` or `blocked`, overall Module 3 status is `incomplete`
    - **Validates: Requirements 7.5**

- [x] 5. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 6. URL governance and provenance persistence
  - [x] 6.1 Implement URL governance validation (Property 7)
    - Verify no file in the distributed power (excluding `config/fallback_sources.yaml` itself) contains the raw fallback source URL
    - Only the registry identifier is used to reference the fallback source in steering and scripts
    - _Requirements: 6.1_

  - [x] 6.2 Write property test for URL governance — single source of truth (Property 7)
    - **Property 7: URL Governance — Single Source of Truth**
    - For any file in the distributed power (excluding registry), the raw fallback URL does not appear
    - **Validates: Requirements 6.1**

  - [x] 6.3 Write property test for provenance persistence completeness (Property 9)
    - **Property 9: Provenance Persistence Completeness**
    - For any completed acquisition, `bootcamp_progress.json` contains `source_provenance` from valid set, and Verification Report includes the same value
    - **Validates: Requirements 8.1, 8.3**

  - [x] 6.4 Write unit tests for registry YAML parsing and specific edge cases
    - Test registry YAML parsing with expected structure
    - Test specific HTTP error codes (404, 500, 503)
    - Test timeout simulation
    - Test empty response handling
    - Test truth key with exactly 3 matches (minimum)
    - Test truth key with 0 matches (failure case)
    - Test steering file content assertions (fallback documentation present, no raw URLs)
    - Test progress file schema validation after each path
    - _Requirements: 3.4, 3.5, 5.2, 5.4, 6.1, 6.2_

  - [x] 6.5 Write integration tests for end-to-end fallback flow
    - Test: primary available → fallback not attempted
    - Test: primary unavailable → fallback succeeds → deterministic verification runs
    - Test: primary unavailable → fallback fails → CORD offered
    - Test: primary unavailable → fallback partially fails (one file 404) → classified unreachable
    - Mock HTTP responses using `unittest.mock.patch` on `urllib.request.urlopen`
    - _Requirements: 2.1, 3.1, 3.4, 7.1, 7.2_

- [x] 7. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties from the design document
- Unit tests validate specific examples and edge cases
- All scripts use Python 3.11+ stdlib only (no third-party deps)
- Tests use pytest + Hypothesis and live in `senzing-bootcamp/tests/`
- The fetcher script lives in `senzing-bootcamp/scripts/` (not `src/system_verification/` — the agent generates a copy there at runtime)
- Registry file uses the project's YAML config conventions in `senzing-bootcamp/config/`
- Steering files reference the registry identifier, never the raw URL (security rule)

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1"] },
    { "id": 1, "tasks": ["2.1"] },
    { "id": 2, "tasks": ["2.2", "2.3", "2.4"] },
    { "id": 3, "tasks": ["2.5", "2.6", "2.7", "2.8"] },
    { "id": 4, "tasks": ["4.1", "4.2", "4.3", "4.4"] },
    { "id": 5, "tasks": ["4.5", "4.6", "4.7"] },
    { "id": 6, "tasks": ["6.1"] },
    { "id": 7, "tasks": ["6.2", "6.3", "6.4", "6.5"] }
  ]
}
```
