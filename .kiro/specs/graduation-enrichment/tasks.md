# Implementation Plan: Graduation Enrichment

## Overview

This plan implements the graduation enrichment feature: two new Python scripts (`generate_directory_index.py` and `update_readme_index.py`) under `senzing-bootcamp/scripts/`, their test suites under `senzing-bootcamp/tests/`, and the graduation workflow integration in `senzing-bootcamp/steering/graduation.md`. The implementation mirrors the proven architecture of `generate_docs_index.py` — a shared `generate_directory_index.py` parameterized by `--target-root` (serving both `src/` and `data/`) and a separate `update_readme_index.py` for scoped managed-section updates with HTML-comment markers.

Each task builds incrementally: skeleton and data model first, then core pure functions, then pipeline composition, then atomic writes with property tests, then CLI entry points, then unit tests, then steering integration, and finally a closing checkpoint.

## Tasks

- [x] 1. Establish the directory index generator skeleton and data model
  - [x] 1.1 Create `senzing-bootcamp/scripts/generate_directory_index.py` with skeleton and data model
    - Add shebang, module docstring with usage examples, `from __future__ import annotations`
    - Define constants: `INDEX_FILENAME = "README.md"`, `MAX_DESCRIPTION_LEN = 120`, `SUBDIR_INDICATOR = "/"`
    - Define frozen `DirEntry` dataclass with `name: str`, `is_dir: bool`, `description: str`
    - Define `SRC_PURPOSE_MAP` and `DATA_PURPOSE_MAP` dictionaries with curated one-line purposes
    - Define `GENERIC_FILE_DESCRIPTION = "Project file."` and `GENERIC_DIR_DESCRIPTION = "Project directory."`
    - Define `TOC_HEADING = "# Directory Index"`
    - Add `_LIST_ITEM_RE` regex for parsing rendered list items
    - Add stub signatures for `scan_entries`, `describe_entry`, `render_markdown`, `validate_toc`, `generate_index`, `write_index_atomically`, `select_purpose_map`, and `main(argv=None)`
    - _Requirements: 1.1, 1.2, 3.1, 3.3, 10.1, 10.2_

  - [x] 1.2 Create `senzing-bootcamp/scripts/update_readme_index.py` with skeleton and data model
    - Add shebang, module docstring with usage examples, `from __future__ import annotations`
    - Define constants: `BEGIN_MARKER`, `END_MARKER` (HTML-comment markers)
    - Define frozen `IndexRef` dataclass with `path: str`, `description: str`, `exists: bool`
    - Define `INDEX_REFS` list of tuples `(path, description)` for docs/src/data indexes
    - Add stub signatures for `probe_indexes`, `render_managed_section`, `update_readme`, `write_readme_atomically`, and `main(argv=None)`
    - _Requirements: 5.1, 5.2, 10.1, 10.2_

- [x] 2. Implement core pure functions for the directory index generator
  - [x] 2.1 Implement `scan_entries(target_root)` depth-1 enumeration with exclusions and ordering
    - Read only the immediate (depth-1) contents of `target_root`: each regular file and each immediate subdirectory as a single entry, never recursing into subdirectories
    - Exclude the index file (`README.md`) and any entry whose name starts with `.`
    - Return entries sorted case-insensitively by name (key `str.lower`, ties broken by `name`)
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 2.8_

  - [x] 2.2 Implement `describe_entry(name, is_dir, purpose_map)` with purpose map and generic fallback
    - Look up the bare entry name in the provided purpose map
    - Fall back to `GENERIC_FILE_DESCRIPTION` / `GENERIC_DIR_DESCRIPTION` when the name is unknown
    - Guarantee a single-line result of length 1–120; never return an empty string
    - _Requirements: 3.1, 3.3_

  - [x] 2.3 Implement `render_markdown(entries)` deterministic table of contents
    - Emit `TOC_HEADING` followed by one list item per entry: `- **<name><indicator>** — <description>`
    - Append `SUBDIR_INDICATOR` (trailing `/`) to subdirectory entry names; no indicator for files
    - Terminate output with a single trailing newline
    - _Requirements: 1.4, 3.1, 3.2_

  - [x] 2.4 Implement `select_purpose_map(target_root)` for `--target-root` dispatch
    - Inspect the final component of `target_root` path: `src` → `SRC_PURPOSE_MAP`, `data` → `DATA_PURPOSE_MAP`
    - Fall back to an empty dict for unknown directories
    - _Requirements: 10.1_

- [x] 3. Implement core pure functions for the README updater
  - [x] 3.1 Implement `probe_indexes(project_root)` to detect existing per-directory indexes
    - Check existence of `docs/README.md`, `src/README.md`, `data/README.md` relative to `project_root`
    - Return a list of `IndexRef` objects with `exists` set to True/False based on actual disk state
    - _Requirements: 5.1, 5.8_

  - [x] 3.2 Implement `render_managed_section(refs)` to produce the managed-section Markdown
    - Render only refs where `exists=True` as list items: `- **[<path>](<path>)** — <description>`
    - Wrap with `BEGIN_MARKER` and `END_MARKER`; include `## Project Index` heading
    - _Requirements: 5.1, 5.2, 5.8_

  - [x] 3.3 Implement `update_readme(readme_path, managed_section)` scoped-write logic
    - If both markers present: replace content between them with new managed-section body
    - If markers absent: append managed section to end of existing content
    - If file doesn't exist: return just the managed section as full content
    - Validate result: exactly one begin marker preceding exactly one end marker
    - _Requirements: 5.3, 5.4, 5.5, 5.6_

- [x] 4. Implement pipeline composition and validation for directory index
  - [x] 4.1 Implement `generate_index(target_root, purpose_map)` pipeline
    - Compose `scan_entries` → `describe_entry` (per entry, using `purpose_map`) → `render_markdown`
    - Return the rendered Markdown string
    - _Requirements: 1.4, 2.1_

  - [x] 4.2 Implement `validate_toc(markdown, entries)` for directory index validation
    - Confirm the rendered Markdown opens with `TOC_HEADING`
    - Confirm every entry appears exactly once as a list item with exactly one single-line description of 1–120 chars
    - Confirm no extra entries appear; return boolean
    - _Requirements: 1.4, 1.6_

- [x] 5. Implement atomic writes for both scripts
  - [x] 5.1 Implement `write_index_atomically(target_root, markdown, purpose_map)` in `generate_directory_index.py`
    - Call `validate_toc` before touching any existing file; raise on validation failure
    - Write to a temp file in the target directory then `os.replace` into `README.md`
    - On any failure remove the temp file and leave any existing `README.md` untouched
    - _Requirements: 1.3, 1.6, 10.4_

  - [x] 5.2 Implement `write_readme_atomically(readme_path, content)` in `update_readme_index.py`
    - Validate that content contains exactly one begin marker preceding exactly one end marker
    - Write to a temp file then `os.replace`; on failure leave original untouched
    - _Requirements: 5.9, 10.4_

  - [x] 5.3 Write property test: enumeration matches eligible top-level entries
    - **Property 1: Enumeration matches the eligible top-level entries**
    - **Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5**
    - In `senzing-bootcamp/tests/test_generate_directory_index.py`
    - Use an `st_target_tree()` Hypothesis strategy that materializes a target directory tree under `tmp_path`
    - Assert enumerated entry-name set equals eligible depth-1 set; nested files never appear; each subdir once

  - [x] 5.4 Write property test: index file and dot-prefixed entries always excluded
    - **Property 2: The index file and dot-prefixed entries are always excluded**
    - **Validates: Requirements 2.6, 2.8**
    - Include trees with a pre-existing `README.md` and arbitrary dot-prefixed files/dirs
    - Assert neither ever appears in the index

  - [x] 5.5 Write property test: order is deterministic and case-insensitive
    - **Property 3: Entry order is deterministic and case-insensitive**
    - **Validates: Requirements 2.7, 1.5**
    - Assert order equals `sorted(names, key=str.lower)` and identical contents produce byte-identical output

- [x] 6. Checkpoint - Ensure core logic tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 7. Implement CLI entry points and remaining property tests
  - [x] 7.1 Implement `main(argv=None)` in `generate_directory_index.py`
    - Add `--target-root <dir>` (required) and `--check` (report drift) arguments via `argparse`
    - Target directory missing or not a directory → print "not generated" summary, exit `0`
    - On successful write → print `Wrote directory index: <path>` then one-line summary, exit `0`
    - On validation/write failure → print reason to stderr, exit `1`, no partial file
    - `--check` mode: compare fresh generation vs on-disk, exit `0` in sync / `1` out of sync
    - _Requirements: 1.1, 1.2, 1.6, 4.2, 4.3, 4.4, 4.5, 10.3_

  - [x] 7.2 Implement `main(argv=None)` in `update_readme_index.py`
    - Add `--readme <path>` (default `README.md`), `--project-root <dir>` (default `.`), `--check` arguments
    - On successful write → print `Updated README index: <path>`, exit `0`
    - On create (no existing file) → print `Created README index: <path>`, exit `0`
    - On validation/write failure → print reason to stderr, exit `1`, leave original untouched
    - `--check` mode: compare fresh generation vs on-disk, exit `0`/`1`
    - _Requirements: 5.1, 5.4, 5.5, 5.6, 5.9, 10.3_

  - [x] 7.3 Write property test: regeneration fully replaces prior content and is idempotent
    - **Property 4: Regeneration fully replaces prior content and is idempotent**
    - **Validates: Requirements 1.3, 1.5**
    - Seed arbitrary stale `README.md` content; assert post-generation equals fresh `generate_index(target_root)`; second run byte-identical

  - [x] 7.4 Write property test: rendered index round-trips as a valid Markdown TOC
    - **Property 5: Rendered index round-trips as a valid Markdown table of contents**
    - **Validates: Requirements 1.4, 1.6**
    - Parse rendered output back into entry names; assert equals rendered set; assert `validate_toc` accepts

  - [x] 7.5 Write property test: every entry has exactly one well-formed description
    - **Property 6: Every entry has exactly one well-formed description**
    - **Validates: Requirements 3.1, 3.3**
    - Include known purpose-map names and unknown random names; assert each entry shows exactly one single-line description of length 1–120

  - [x] 7.6 Write property test: subdirectories carry a visual indicator files never carry
    - **Property 7: Subdirectories carry a visual indicator that files never carry**
    - **Validates: Requirements 3.2**
    - Assert every subdirectory entry renders with trailing `/`; no file entry does

  - [x] 7.7 Write property test: managed section lists exactly existing per-directory indexes
    - **Property 8: Managed section lists exactly the existing per-directory indexes**
    - **Validates: Requirements 5.1, 5.2, 5.8**
    - In `senzing-bootcamp/tests/test_update_readme_index.py`
    - Use `st_index_existence()` strategy (boolean triple for docs/src/data existence)
    - Assert managed section contains entries for exactly the indexes that exist; each with 1–120 char synopsis

  - [x] 7.8 Write property test: content outside markers is preserved (scoped-write)
    - **Property 9: Content outside markers is preserved (scoped-write)**
    - **Validates: Requirements 5.3, 5.4, 5.5**
    - Use `st_readme_content()` strategy generating README content with/without pre-existing markers
    - Assert all content outside markers is byte-identical after update; when no markers existed, original is prefix

  - [x] 7.9 Write property test: README update is idempotent
    - **Property 10: README update is idempotent**
    - **Validates: Requirements 5.7**
    - Run twice with unchanged state; assert byte-identical output

- [x] 8. Write CLI unit tests for both scripts
  - [x] 8.1 Write unit tests for `generate_directory_index.py` CLI output contract
    - In `senzing-bootcamp/tests/test_generate_directory_index.py`
    - Output location: generating over populated `src/` and `data/` writes `README.md` at target root (Req 1.1, 1.2)
    - Skip: non-existent `--target-root` exits `0` with "not generated" (Req 4.2)
    - Success ordering: stdout has success message before one-line summary (Req 4.4, 4.5)
    - No partial file on validation failure: monkeypatch `validate_toc` to reject; original untouched (Req 1.6)
    - No partial file on write failure: monkeypatch `os.replace` to raise; original untouched (Req 10.4)
    - `--check` drift detection: in-sync exits `0`; stale/missing exits `1` (Req 10.3)
    - Purpose map selection: `--target-root src` uses `SRC_PURPOSE_MAP`; `--target-root data` uses `DATA_PURPOSE_MAP` (Req 10.1)
    - _Requirements: 1.1, 1.2, 1.6, 4.2, 4.4, 4.5, 10.3, 10.4_

  - [x] 8.2 Write unit tests for `update_readme_index.py` CLI output contract
    - In `senzing-bootcamp/tests/test_update_readme_index.py`
    - Create when missing: no existing README → file created with managed section (Req 5.6)
    - Append when no markers: existing content without markers → original preserved as prefix (Req 5.5)
    - Replace between markers: existing managed section → only inner content replaced (Req 5.4)
    - No partial file on failure: monkeypatch validation to reject; original untouched (Req 5.9)
    - `--check` drift detection: in-sync exits `0`; out-of-sync exits `1` (Req 10.3)
    - Omit missing indexes: only existing index files appear in managed section (Req 5.8)
    - _Requirements: 5.4, 5.5, 5.6, 5.8, 5.9, 10.3_

- [x] 9. Checkpoint - Ensure all script tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 10. Integrate graduation steps and artifact announcement into steering
  - [x] 10.1 Add Steps 0b.6, 0b.7, 0b.8 to `senzing-bootcamp/steering/graduation.md`
    - Step 0b.6 (Src Index Generation): if `src/` does not exist → report not generated and proceed; otherwise run `python senzing-bootcamp/scripts/run_bundled_script.py generate_directory_index.py --target-root src`; on success → "📑 Source index generated at `src/README.md`." + one-line summary; on failure → record in GRADUATION_REPORT.md, proceed
    - Step 0b.7 (Data Index Generation): same pattern with `--target-root data`
    - Step 0b.8 (README Index Update): run `python senzing-bootcamp/scripts/run_bundled_script.py update_readme_index.py`; on success → "📑 Top-level README updated with project index."; on failure → record, proceed
    - Match wording and non-blocking contract of existing Steps 0b.4/0b.5
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 9.1, 9.2, 9.3, 9.4_

  - [x] 10.2 Extend the Mandatory Closing Step with Artifact_Announcement
    - Add artifact announcement to the existing mandatory closing announcement block
    - Name `docs/bootcamp_recap.md` as the single per-module recap + journal
    - Name `docs/bootcamp_recap.pdf` (or `.html` fallback) as the rendered recap
    - Name `docs/README.md`, `src/README.md`, `data/README.md`, and top-level `README.md`
    - Report only artifacts confirmed to exist at their stated paths at announcement time
    - Emit exactly once as part of the existing closing announcement
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 8.1, 8.2, 8.3, 8.4, 8.5_

  - [x] 10.3 Update `senzing-bootcamp/steering/steering-index.yaml` token count for `graduation.md`
    - Run `measure_steering.py` to get the new token count
    - Update the entry for `graduation.md` in `steering-index.yaml`
    - Verify `measure_steering.py --check` passes
    - _Requirements: 10.6_

- [x] 11. Final checkpoint - Ensure all tests and CI gates pass
  - Ensure all tests pass, ask the user if questions arise.
  - Verify `validate_commonmark.py` passes on generated outputs.
  - Verify `measure_steering.py --check` passes.

## Notes

- Tasks marked with `*` are optional test sub-tasks and can be skipped for a faster MVP.
- Each task references specific requirements for traceability.
- `generate_directory_index.py` is a single shared script parameterized by `--target-root` (serving both `src/` and `data/`); only the purpose map differs between the two directories.
- `update_readme_index.py` is a separate script because its scoped-write behavior (preserve content outside markers) is fundamentally different from full-file replacement.
- Property tests 1–7 target `generate_directory_index.py`; properties 8–10 target `update_readme_index.py`.
- Both test files go in `senzing-bootcamp/tests/` following the `sys.path` import pattern.
- Example counts come from the active Hypothesis profile (`fast`=5 locally, `thorough`=100 in CI); do not hand-set `@settings(max_examples=...)`.
- Checkpoints ensure incremental validation after core logic, after CLI + tests, and after steering integration.
- The graduation steering changes are non-blocking: any step failure records in GRADUATION_REPORT.md and proceeds.

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1", "1.2"] },
    { "id": 1, "tasks": ["2.1", "2.2", "2.3", "2.4", "3.1", "3.2", "3.3"] },
    { "id": 2, "tasks": ["4.1", "4.2", "5.2"] },
    { "id": 3, "tasks": ["5.1", "5.3", "5.4", "5.5"] },
    { "id": 4, "tasks": ["7.1", "7.2", "7.3", "7.4", "7.5", "7.6", "7.7", "7.8", "7.9"] },
    { "id": 5, "tasks": ["8.1", "8.2"] },
    { "id": 6, "tasks": ["10.1", "10.2", "10.3"] }
  ]
}
```
