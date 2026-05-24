# Implementation Plan: Enforce File Placement

## Overview

Add CHECK 4 (Root File Placement Enforcement) to the existing `write-policy-gate.kiro.hook`, extend the FAST PATH GATE with a root placement condition, and update both steering files (`agent-instructions.md`, `project-structure.md`) with explicit prohibition language. Property-based tests validate the hook prompt structure and steering file content using pytest + Hypothesis.

## Tasks

- [x] 1. Update write-policy-gate hook with CHECK 4 and FAST PATH GATE extension
  - [x] 1.1 Extend the FAST PATH GATE condition in write-policy-gate.kiro.hook
    - Add a fourth bullet to the existing FAST PATH GATE conditions list
    - New condition: "The target path is NOT a blocked file type in the project root (or if it is in the root, it is on the ROOT WHITELIST)"
    - Existing three conditions must remain character-for-character identical
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6_

  - [x] 1.2 Append CHECK 4: ROOT FILE PLACEMENT ENFORCEMENT after CHECK 3
    - Add the `---` separator and full CHECK 4 prompt text after CHECK 3's CONTENT CHECK section
    - Include Q1 (root detection), Q2 (whitelist check), and blocked extension routing
    - Root Whitelist: `.gitignore`, `.env`, `.env.example`, `README.md`, `requirements.txt`, `pom.xml`, `*.csproj`, `Cargo.toml`, `package.json`
    - Blocked extensions: `.py`, `.md`, `.jsonl`, `.csv`, `.json` (non-whitelist)
    - Include corrective routing output for each blocked extension with ⚠️ prefix
    - Content-aware `.py` routing: transform → `src/transform/`, load → `src/load/`, query → `src/query/`, default → `scripts/`
    - `.md` routing → `docs/`; `.jsonl`/`.csv` routing → `data/` subdirectories; `.json` routing → `data/` or `config/`
    - Unknown extensions pass silently
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8, 3.9_

  - [x] 1.3 Update the hook description field to mention the fourth check
    - Change description from "three policy checks" to "four policy checks"
    - Add root file placement enforcement to the description list
    - _Requirements: 1.1_

- [x] 2. Checkpoint - Verify hook modifications
  - Ensure the hook file is valid JSON with all required fields, CHECK 4 is present, FAST PATH GATE has four conditions, and CHECKs 1-3 remain unchanged. Ask the user if questions arise.

- [x] 3. Update steering files with prohibition language
  - [x] 3.1 Add Root Prohibitions section to agent-instructions.md
    - Add a `### Root Prohibitions` subsection under the existing `## File Placement` section
    - Include the 🚫 table listing blocked types (`.py`, `.md` except README.md, `.jsonl`, `.csv`, non-config `.json`) with reasons and correct locations
    - Include the ✅ permitted files list (`.gitignore`, `.env`, `.env.example`, `README.md`, `requirements.txt`, `pom.xml`, `*.csproj`, `Cargo.toml`, `package.json`)
    - Place after the existing "If about to write a `.md` file to `scripts/`" rule
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

  - [x] 3.2 Add Root File Placement Enforcement section to project-structure.md
    - Add a `### Root File Placement Enforcement` subsection under the existing `## Rules` section
    - Include the 🚫 list of blocked types with routing destinations
    - Include the ✅ exhaustive root-permitted file list
    - Include the note that `write-policy-gate` hook enforces at write time
    - Place after the existing Markdown documentation rule
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6_

- [x] 4. Checkpoint - Verify steering file updates
  - Ensure both steering files contain the new prohibition sections while retaining all existing content. Ask the user if questions arise.

- [x] 5. Write example-based tests for root placement logic
  - [x] 5.1 Create tests/test_enforce_file_placement.py with test helpers and example tests
    - Implement `is_root_path(path: str) -> bool` helper (True if path has no subdirectory)
    - Implement `is_whitelisted(filename: str) -> bool` helper (exact match + `*.csproj` pattern)
    - Implement `has_blocked_extension(filename: str) -> bool` helper (`.py`, `.md`, `.jsonl`, `.csv`, `.json`)
    - Implement `get_expected_routing(filename: str) -> str` helper (returns target directory)
    - Define constants: `ROOT_WHITELIST_EXACT`, `ROOT_WHITELIST_PATTERNS`, `BLOCKED_EXTENSIONS`
    - Write example tests verifying each blocked extension is rejected in root
    - Write example tests verifying each whitelisted file is permitted
    - Write example tests verifying corrective routing destinations
    - Write example tests verifying CHECK 4 text is present in the hook prompt
    - Write example tests verifying steering files contain prohibition language
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 2.1, 2.5, 2.6, 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8, 3.9, 4.1, 4.2, 4.3, 4.4, 4.5, 5.1, 5.2, 5.3, 5.4, 5.5, 5.6_

- [x] 6. Write property-based tests for root placement enforcement
  - [x] 6.1 Write property test: blocked extensions are rejected in root
    - **Property 1: Blocked extensions are rejected in root**
    - Use Hypothesis to generate filenames with blocked extensions (`.py`, `.md`, `.jsonl`, `.csv`, `.json`) that are not on the whitelist
    - Verify the hook prompt contains STOP directives and corrective routing for each blocked extension
    - **Validates: Requirements 1.1, 1.2, 1.3, 1.4, 1.5**

  - [x] 6.2 Write property test: whitelisted files are permitted
    - **Property 2: Whitelisted files are permitted**
    - Use Hypothesis to generate filenames from the Root Whitelist (including pattern-matched `.csproj` variants)
    - Verify the hook prompt contains whitelist logic that permits these files silently
    - **Validates: Requirements 1.6, 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8, 3.9**

  - [x] 6.3 Write property test: corrective routing maps to valid destinations
    - **Property 3: Corrective routing maps blocked extensions to valid destinations**
    - Use Hypothesis to generate blocked filenames and verify routing output references valid project subdirectories (`src/transform/`, `src/load/`, `src/query/`, `scripts/`, `docs/`, `data/raw/`, `data/transformed/`, `data/samples/`, `data/temp/`, `config/`)
    - **Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7**

  - [x] 6.4 Write property test: steering files enumerate all whitelist entries
    - **Property 4: Steering files enumerate all whitelist entries**
    - For each file on the Root Whitelist, verify both `agent-instructions.md` and `project-structure.md` contain that filename or pattern
    - **Validates: Requirements 4.5, 5.6**

  - [x] 6.5 Write property test: steering files enumerate all routing destinations
    - **Property 5: Steering files enumerate all routing destinations**
    - For each blocked extension, verify `project-structure.md` contains the corrective routing destination(s)
    - **Validates: Requirements 5.5**

  - [x] 6.6 Write property test: existing hook checks are preserved
    - **Property 6: Existing hook checks are preserved**
    - Load the hook prompt and verify CHECK 1, CHECK 2, and CHECK 3 section headers and key content remain present and unmodified
    - Compare against known reference strings for each check's critical content
    - **Validates: Requirements 1.1, 1.2, 1.3, 1.4, 1.5, 1.6**

- [x] 7. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties from the design document
- The implementation language is Python (pytest + Hypothesis) per the project's tech stack
- Hook tests validating real hook files go in repo-root `tests/`, not `senzing-bootcamp/tests/`
- All steering file modifications are additive — existing content must be preserved
- The hook file is JSON — ensure valid JSON after modifications (escape special characters in prompt string)
- CHECK 4 is appended after CHECK 3; existing checks remain character-for-character identical

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1", "1.2", "1.3"] },
    { "id": 1, "tasks": ["3.1", "3.2"] },
    { "id": 2, "tasks": ["5.1"] },
    { "id": 3, "tasks": ["6.1", "6.2", "6.3", "6.4", "6.5", "6.6"] }
  ]
}
```
