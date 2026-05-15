# Implementation Plan: CORD Data Freshness Indicator

## Overview

Implement a lightweight metadata caching and verification layer between Module 4 (data collection) and Module 6 (data loading). The implementation consists of a single Python script (`cord_metadata.py`) with capture/check subcommands, a minimal YAML serializer, integration into module steering files, and comprehensive tests using pytest + Hypothesis.

## Tasks

- [x] 1. Create data models and YAML serialization
  - [x] 1.1 Create `senzing-bootcamp/scripts/cord_metadata.py` with dataclasses and serialization
    - Define `SourceMetadata`, `CordMetadata`, and `FreshnessResult` dataclasses
    - Implement `serialize_metadata(metadata)` → YAML string (custom minimal serializer, no PyYAML)
    - Implement `parse_metadata(yaml_content)` → `CordMetadata` object
    - Follow project pattern from `data_sources.py` for YAML handling
    - _Requirements: 1, 2_

  - [x] 1.2 Write property test for metadata round-trip (Property 1)
    - **Property 1: Metadata serialization round-trip**
    - Generate random `CordMetadata` objects with arbitrary dataset names, 1+ sources, valid ISO 8601 dates, and SHA-256 hashes
    - Assert `parse_metadata(serialize_metadata(m)) == m` for all generated inputs
    - Use `@settings(max_examples=100)`
    - **Validates: Requirements 1, 2**

  - [x] 1.3 Write unit tests for serialization edge cases
    - Test single source, multiple sources, special characters in dataset name
    - Test empty string fields, large record counts, long file paths
    - _Requirements: 2_

- [x] 2. Implement capture_metadata function
  - [x] 2.1 Implement `capture_metadata(dataset_name, source_files, output_path)`
    - Read each source file to compute record count (count lines for JSONL)
    - Get file size via `os.path.getsize`
    - Implement `compute_content_hash(file_path, max_records=100)` using SHA-256
    - Generate ISO 8601 download timestamp with timezone
    - Write metadata YAML to `output_path` (default: `config/cord_metadata.yaml`)
    - Handle missing files gracefully (skip source, warn to stderr)
    - _Requirements: 1, 2_

  - [x] 2.2 Write unit tests for capture_metadata
    - Test capture creates metadata file with correct content (Requirement 9)
    - Test capture with missing source file (skip and warn)
    - Test capture with no files (exit code 1)
    - Test content hash computation for files with < 100 and > 100 records
    - _Requirements: 1, 2, 9_

- [x] 3. Implement check_freshness function
  - [x] 3.1 Implement `check_freshness(metadata_path)`
    - Read and parse `config/cord_metadata.yaml`
    - Compare stored file sizes against current `os.path.getsize` for each source
    - Compare stored record counts against current line counts
    - Return `FreshnessResult(status="fresh")` when all match
    - Return `FreshnessResult(status="stale", mismatches=[...])` when any differ
    - Return `FreshnessResult(status="skipped")` when metadata file missing or corrupt
    - Handle missing data files as stale (file disappeared)
    - Handle permission errors as stale
    - _Requirements: 3, 4, 5, 8_

  - [x] 3.2 Write property test for mismatch detection (Property 2)
    - **Property 2: Freshness check correctly detects mismatches**
    - Generate metadata + file states with matching and mismatched sizes/counts
    - Assert stale status with non-empty mismatches when any file differs
    - Assert fresh status with empty mismatches when all files match
    - Use `@settings(max_examples=100)`
    - **Validates: Requirements 3, 4**

  - [x] 3.3 Write property test for non-blocking behavior (Property 3)
    - **Property 3: Non-blocking advisory behavior**
    - Generate adversarial inputs: missing files, corrupt YAML, empty metadata, non-CORD data
    - Assert `check_freshness` never raises an exception
    - Assert returned status is always in {"fresh", "stale", "skipped"}
    - Use `@settings(max_examples=100)`
    - **Validates: Requirements 5, 8**

  - [x] 3.4 Write unit tests for check_freshness scenarios
    - Test freshness check pass (Requirement 9)
    - Test freshness check fail with size mismatch (Requirement 9)
    - Test missing metadata file returns skipped (Requirement 9)
    - Test corrupt metadata file returns skipped
    - Test non-CORD data (no metadata) skipped entirely (Requirement 8)
    - _Requirements: 3, 4, 5, 8, 9_

- [x] 4. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 5. Implement CLI entry point and wire components
  - [x] 5.1 Implement `main()` with argparse CLI subcommands
    - Add `capture` subcommand: `--dataset <name> --files <paths...> [--output <path>]`
    - Add `check` subcommand: `[--metadata <path>]`
    - Format user-facing warning message for stale results per Requirement 4
    - Return exit code 0 for fresh/skipped, exit code 0 for stale (advisory only, never block)
    - Add `if __name__ == "__main__"` block
    - _Requirements: 4, 5_

  - [x] 5.2 Write unit tests for CLI subcommands
    - Test `capture` subcommand end-to-end with temp files
    - Test `check` subcommand end-to-end with matching and mismatched files
    - Test warning message format matches Requirement 4 text
    - _Requirements: 4, 5, 9_

- [x] 6. Update module steering files
  - [x] 6.1 Update `senzing-bootcamp/steering/module-06-load-data.md` with pre-load freshness check
    - Add a pre-load verification step that runs `python senzing-bootcamp/scripts/cord_metadata.py check`
    - Present the result to the bootcamper (fresh → proceed, stale → show options, skipped → proceed silently)
    - _Requirements: 6_

  - [x] 6.2 Update `senzing-bootcamp/steering/module-04-data-collection.md` with metadata capture
    - Add instructions to run `python senzing-bootcamp/scripts/cord_metadata.py capture` after CORD data download
    - Only trigger when CORD data is selected (skip for custom data)
    - _Requirements: 7, 8_

- [x] 7. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties from the design document
- Unit tests validate specific examples and edge cases from Requirement 9
- The script uses stdlib only (no PyYAML) per project tech stack rules
- All test files go in `senzing-bootcamp/tests/test_cord_data_freshness.py`

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1"] },
    { "id": 1, "tasks": ["1.2", "1.3", "2.1"] },
    { "id": 2, "tasks": ["2.2", "3.1"] },
    { "id": 3, "tasks": ["3.2", "3.3", "3.4"] },
    { "id": 4, "tasks": ["5.1"] },
    { "id": 5, "tasks": ["5.2", "6.1", "6.2"] }
  ]
}
```
