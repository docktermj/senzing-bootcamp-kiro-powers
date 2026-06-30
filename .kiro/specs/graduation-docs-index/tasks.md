# Implementation Plan: Graduation Docs Index

## Overview

This plan reworks the existing `senzing-bootcamp/scripts/generate_docs_index.py` to match the new requirements (depth-1 enumeration of all entries, dot/index exclusion, predefined purpose map with generic fallback, subdirectory visual indicator, deterministic case-insensitive ordering, validated atomic writes) and wires a new non-blocking Docs Index Generation step into `senzing-bootcamp/steering/graduation.md`. Existing `docs-file-placement` tests in `senzing-bootcamp/tests/test_generate_docs_index.py` are updated to assert the new behavior, and Hypothesis property tests are added for each correctness property.

Each task builds incrementally: the data model and pure functions come first, then the pipeline, then the atomic write and CLI contract, then the property/unit tests, and finally the graduation workflow integration.

## Tasks

- [x] 1. Establish the reworked generator skeleton and data model
  - In `senzing-bootcamp/scripts/generate_docs_index.py`, replace the old module docstring and constants with the new contract: `DEFAULT_DOCS_ROOT = Path("docs")`, `INDEX_FILENAME = "README.md"`, `MAX_DESCRIPTION_LEN = 120`, `SUBDIR_INDICATOR = "/"`
  - Keep the project script pattern: shebang, `from __future__ import annotations`, dataclasses, `argparse`
  - Define the frozen `DocsEntry` dataclass with `name: str`, `is_dir: bool`, `description: str`
  - Add the module-level predefined purpose map (known file and subdirectory names → curated one-line purposes) keyed by bare entry name
  - Add stub signatures for `scan_entries`, `describe_entry`, `render_markdown`, `validate_toc`, `generate_index`, `write_index_atomically`, and `main(argv=None)` so later tasks fill them in
  - _Requirements: 3.3_

- [x] 2. Implement enumeration, description, ordering, and rendering
  - [x] 2.1 Implement `scan_entries(docs_root)` depth-1 enumeration with exclusions and ordering
    - Read only the immediate (depth-1) contents of `docs_root`: each regular file and each immediate subdirectory as a single entry, never recursing into subdirectories
    - Exclude the index file (`README.md`) and any entry whose name starts with `.`
    - Return entries sorted case-insensitively by name (key `str.lower`, ties broken by `name`)
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 2.8_

  - [x] 2.2 Implement `describe_entry(name, is_dir)` with purpose map and generic fallback
    - Look up the bare entry name in the predefined purpose map
    - Fall back to a non-empty generic description ("Bootcamp documentation file." / "Bootcamp documentation directory.") when the name is unknown
    - Guarantee a single-line result of length 1–120; never return an empty string
    - _Requirements: 3.1, 3.3_

  - [x] 2.3 Implement `render_markdown(entries)` deterministic table of contents
    - Emit a top-level heading followed by one list item per entry, each showing the name and exactly one single-line description
    - Append the `SUBDIR_INDICATOR` (trailing `/`) to subdirectory entry names and to no file entry
    - Terminate output with a single trailing newline
    - _Requirements: 1.3, 3.1, 3.2_

  - [x] 2.4 Implement `generate_index(docs_root)` pipeline
    - Compose `scan_entries` → `describe_entry` (per entry) → `render_markdown` into a single function returning the rendered Markdown string
    - _Requirements: 1.3, 2.1_

  - [x] 2.5 Write property test: enumeration matches eligible top-level entries
    - **Property 1: Enumeration matches the eligible top-level entries**
    - **Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5**
    - Use an `st_docs_tree()` Hypothesis strategy that materializes a `docs/` tree under `tmp_path` (top-level files, subdirectories with optional nested files, varied casing)
    - Assert the enumerated entry-name set equals the eligible depth-1 set; nested files never appear; each subdirectory appears exactly once

  - [x] 2.6 Write property test: index file and dot-prefixed entries always excluded
    - **Property 2: The index file and dot-prefixed entries are always excluded**
    - **Validates: Requirements 2.6, 2.8**
    - Include trees with a pre-existing `README.md` and arbitrary dot-prefixed files/dirs; assert neither ever appears in the index

  - [x] 2.7 Write property test: order is deterministic and case-insensitive
    - **Property 3: Entry order is deterministic and case-insensitive**
    - **Validates: Requirements 2.7**
    - Assert order equals `sorted(names, key=str.lower)` and identical contents produce byte-identical output

  - [x] 2.8 Write property test: every entry has exactly one well-formed description
    - **Property 6: Every entry has exactly one well-formed description**
    - **Validates: Requirements 3.1, 3.3**
    - Include known purpose-map names and unknown random names; assert each entry shows exactly one single-line description of length 1–120

  - [x] 2.9 Write property test: subdirectories carry a visual indicator files never carry
    - **Property 7: Subdirectories carry a visual indicator that files never carry**
    - **Validates: Requirements 3.2**
    - Assert every subdirectory entry renders with the trailing `/` and no file entry does

- [x] 3. Implement validation and atomic write
  - [x] 3.1 Implement `validate_toc(markdown, entries)`
    - Confirm the rendered Markdown parses as a valid table of contents: every entry appears exactly once as a list item with exactly one single-line description of 1–120 chars, and no extra entries appear
    - Return a boolean
    - _Requirements: 1.3, 1.4_

  - [x] 3.2 Implement `write_index_atomically(docs_root, markdown)`
    - Call `validate_toc` before touching any existing file; raise on validation failure
    - Write to a temp file in the docs directory then `os.replace` into `docs/README.md`; on any failure remove the temp file and leave any existing `README.md` untouched (never partial/malformed)
    - Return the written path
    - _Requirements: 1.1, 1.2, 1.4_

  - [x] 3.3 Write property test: regeneration fully replaces prior content and is idempotent
    - **Property 4: Regeneration fully replaces prior content and is idempotent**
    - **Validates: Requirements 1.2**
    - Seed arbitrary stale `docs/README.md` content; assert post-generation content equals a fresh `generate_index(docs_root)` and a second run is byte-identical

  - [x] 3.4 Write property test: rendered index round-trips as a valid Markdown TOC
    - **Property 5: Rendered index round-trips as a valid Markdown table of contents**
    - **Validates: Requirements 1.3, 1.4**
    - Parse the rendered output back into a set of entry names and assert it equals the rendered set; assert `validate_toc` accepts the output

- [x] 4. Checkpoint - Ensure all generator tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 5. Implement the CLI entry point and output contract
  - [x] 5.1 Implement `main(argv=None)` with skip, success, and failure behavior
    - Add `--docs-root <dir>` (default `docs`) and `--check` (report drift, exit non-zero on difference, write nothing)
    - When `docs/` is missing or not a directory: print a one-line "not generated" summary and exit `0` (skip is success, no confirmation prompt)
    - On successful write: print `Wrote docs index: docs/README.md` (success message naming the location) before the one-line summary, exit `0`
    - On validation/write/OS failure: print the failure reason to stderr and exit `1`, leaving no partial/malformed `docs/README.md`
    - _Requirements: 1.1, 1.4, 4.2, 4.3, 4.4, 4.5_

  - [x] 5.2 Write unit tests for the CLI output contract
    - Output location: generating over a populated `docs/` writes `docs/README.md` at the docs root (Req 1.1)
    - Skip: non-existent `--docs-root` exits `0` and prints a "not generated" summary (Req 4.2)
    - Success ordering: stdout contains the success message naming `docs/README.md` before the one-line summary (Req 4.4, 4.5)
    - No partial file on failure: with `validate_toc` forced to reject or a simulated write failure, any pre-existing `docs/README.md` is unchanged and no temp/malformed file remains (Req 1.4)
    - `--check` drift: in-sync index exits `0`; stale or missing index exits `1`
    - _Requirements: 1.1, 1.4, 4.2, 4.4, 4.5_

- [x] 6. Update existing docs-file-placement tests to the new behavior
  - [x] 6.1 Rework `senzing-bootcamp/tests/test_generate_docs_index.py` assertions
    - Replace assertions of the old recursive / Markdown-only / heading-derived / grouped behavior with the new depth-1, all-entries, purpose-map, subdirectory-indicator, deterministic-order behavior
    - Keep imports via the documented `sys.path` insertion; prefix Hypothesis strategies with `st_` and tag each property test with `Feature: graduation-docs-index, Property {number}: {property_text}`
    - _Requirements: 2.1, 2.2, 2.3, 3.1, 3.2_

- [x] 7. Checkpoint - Ensure the full test module passes
  - Ensure all tests pass, ask the user if questions arise.

- [x] 8. Integrate the Docs Index Generation step into the graduation workflow
  - [x] 8.1 Add the non-blocking Docs Index Generation step to `senzing-bootcamp/steering/graduation.md`
    - Place the new step after the Q&A transcript generation (Step 0b.4) and before Step 1, alongside the other documentation-generation steps
    - If `docs/` does not exist: report the index was not generated and proceed (success, no confirmation prompt when it does exist)
    - Otherwise run `python scripts/generate_docs_index.py`; on exit 0 with a `Wrote docs index:` line, report `📑 Docs index generated at docs/README.md` then the one-line summary
    - On any failure (exit 1, or success message present but one-line summary cannot be reported), record the failure reason in `production/GRADUATION_REPORT.md` under "⚠️ Issues Encountered" and proceed without halting
    - Match the wording and non-blocking contract of the existing recap-PDF and transcript steps
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6_

- [x] 9. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional test sub-tasks and can be skipped for a faster MVP.
- Each task references specific requirements for traceability.
- Property tests (one per correctness property) validate universal invariants; unit tests cover the concrete output/location/skip contract and `--check` drift detection.
- Checkpoints ensure incremental validation after the generator logic, the test-module update, and the workflow integration.
- Example counts come from the active Hypothesis profile (`fast`=10 locally, `thorough`=100 in CI); do not hand-set `@settings(max_examples=...)`.

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1"] },
    { "id": 1, "tasks": ["2.1", "2.2", "2.3"] },
    { "id": 2, "tasks": ["2.4", "3.1"] },
    { "id": 3, "tasks": ["3.2", "2.5", "2.6", "2.7", "2.8", "2.9"] },
    { "id": 4, "tasks": ["5.1", "3.3", "3.4"] },
    { "id": 5, "tasks": ["5.2", "6.1"] },
    { "id": 6, "tasks": ["8.1"] }
  ]
}
```
