# Implementation Plan: MCP Response Caching

## Overview

Implement a transparent MCP response caching layer for the senzing-bootcamp power via a steering file, supporting configuration entries, and property-based tests. The implementation creates the steering file with caching behavioral rules, registers it in the steering index, updates `.gitignore`, and validates correctness through Hypothesis-based property tests.

## Tasks

- [x] 1. Create steering file with caching behavior
  - [x] 1.1 Create `senzing-bootcamp/steering/mcp-response-caching.md` with YAML frontmatter and caching instructions
    - Add YAML frontmatter with `inclusion: auto` and description
    - Define cache directory path as `config/mcp_cache/`
    - Specify cache key computation: tool_name + "|" + JSON-serialized parameters sorted by key
    - Specify filename derivation: SHA-256 hex digest truncated to 16 characters + `.json`
    - Document cache entry schema (tool_name, parameters_hash, module_id, timestamp, response)
    - Document cache lookup procedure (hit/stale/miss logic)
    - Document module transition invalidation (delete all entries before new module MCP calls)
    - Document error handling (network failure message, corrupted file recovery, directory creation)
    - Document diagnostic logging instructions
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 2.1, 2.2, 2.3, 2.4, 3.1, 3.2, 3.3, 3.4, 4.1, 4.2, 4.3, 5.1, 5.2, 5.3_

- [x] 2. Register steering file in index and update gitignore
  - [x] 2.1 Add keyword entries and file_metadata to `senzing-bootcamp/steering/steering-index.yaml`
    - Add `cache: mcp-response-caching.md` keyword entry
    - Add `mcp cache: mcp-response-caching.md` keyword entry
    - Add `file_metadata` entry for `mcp-response-caching.md` with token_count and size_category
    - _Requirements: 6.1, 6.2, 6.3_

  - [x] 2.2 Add cache directory exclusion to `.gitignore`
    - Add comment: `# MCP response cache runtime state`
    - Add pattern: `senzing-bootcamp/config/mcp_cache/`
    - _Requirements: 7.1, 7.2_

- [x] 3. Checkpoint - Verify steering file and configuration
  - Ensure all steering file sections are present and correctly formatted, ask the user if questions arise.

- [x] 4. Implement test helpers and property-based tests
  - [x] 4.1 Create `senzing-bootcamp/tests/test_mcp_response_caching.py` with test helpers
    - Implement helper functions for cache key computation (matching steering file algorithm)
    - Implement helper function for filename derivation (SHA-256 truncated to 16 hex chars)
    - Implement helper for cache entry serialization/deserialization
    - Implement helper for cache lookup logic simulation
    - _Requirements: 1.4, 2.2, 2.3, 3.1, 3.2, 3.3_

  - [x] 4.2 Write property test for cache key determinism
    - **Property 1: Cache key determinism**
    - **Validates: Requirements 1.4**
    - Use Hypothesis to generate random tool names and parameter dictionaries
    - Assert that computing the cache key with parameters in any insertion order produces the identical key string

  - [x] 4.3 Write property test for cache entry schema round-trip
    - **Property 2: Cache entry schema round-trip**
    - **Validates: Requirements 2.2**
    - Use Hypothesis to generate valid cache entries with all five required fields
    - Assert that serializing to JSON and deserializing back preserves all fields

  - [x] 4.4 Write property test for filename derivation determinism and format
    - **Property 3: Filename derivation determinism and format**
    - **Validates: Requirements 2.3**
    - Use Hypothesis to generate arbitrary cache key strings
    - Assert filename is exactly 16 hex characters + `.json`
    - Assert computing filename multiple times from same key produces same result

  - [x] 4.5 Write property test for cache lookup correctness
    - **Property 4: Cache lookup correctness**
    - **Validates: Requirements 3.1, 3.2, 3.3**
    - Use Hypothesis to generate cache entries and module_id values
    - Assert cached response returned if and only if module_id matches
    - Assert stale entry file is deleted when module_id does not match

  - [x] 4.6 Write property test for no stale fallback on failure
    - **Property 5: No stale fallback on failure**
    - **Validates: Requirements 4.2**
    - Use Hypothesis to generate cache miss scenarios with stale entries present
    - Assert system never returns a previously cached response when MCP call fails

  - [x] 4.7 Write property test for module transition clears all entries
    - **Property 6: Module transition clears all entries**
    - **Validates: Requirements 5.1, 5.2**
    - Use Hypothesis to generate non-empty sets of cache entry files
    - Assert all files are deleted after module transition

- [x] 5. Implement example-based and smoke tests
  - [x] 5.1 Write example-based tests for error handling and edge cases
    - Test network failure produces correct error message with retry suggestion
    - Test corrupted JSON file is deleted and treated as cache miss
    - Test cache directory creation on first write
    - _Requirements: 4.1, 4.3_

  - [x] 5.2 Write smoke tests for static configuration
    - Verify steering file exists at correct path with correct frontmatter
    - Verify steering index contains keyword mappings and file_metadata entry
    - Verify `.gitignore` contains cache directory exclusion with comment
    - _Requirements: 1.1, 1.2, 6.1, 6.2, 6.3, 7.1, 7.2_

- [x] 6. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties from the design document
- The steering file is the primary deliverable — no Python runtime scripts are introduced
- Test helpers replicate the caching algorithms described in the steering file to validate correctness
- All tests use pytest + Hypothesis per project conventions

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1", "2.2"] },
    { "id": 1, "tasks": ["2.1"] },
    { "id": 2, "tasks": ["4.1", "5.2"] },
    { "id": 3, "tasks": ["4.2", "4.3", "4.4", "5.1"] },
    { "id": 4, "tasks": ["4.5", "4.6", "4.7"] }
  ]
}
```
