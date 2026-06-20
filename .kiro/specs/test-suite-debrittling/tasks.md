# Implementation Plan: Test Suite Debrittling

## Overview

This plan builds the stdlib-only brittleness scanner
(`senzing-bootcamp/scripts/scan_brittle_assertions.py`) from the inside out: first
the module skeleton and data models, then the pure `classify_assertion` core (the
primary property-tested unit), then the I/O driver, then the `argparse` CLI and
`--check` exit-code contract. Once the scanner is green it is wired into CI, and
finally the existing brittle assertions are remediated to structural forms and the
end state is verified. Each step builds on the previous one and ends with the
pieces integrated — the CLI wires the core and driver together, CI wires the CLI in,
and remediation is validated by the finished scanner.

Tech stack: Python 3.11+ (stdlib only), pytest + Hypothesis. Scanner tests live in
`senzing-bootcamp/tests/`; CI/hook-prompt tests live in repo-root `tests/`.

## Tasks

- [x] 1. Scaffold the scanner module and taxonomy documentation
  - [x] 1.1 Create `scan_brittle_assertions.py` skeleton and data models
    - Create `senzing-bootcamp/scripts/scan_brittle_assertions.py` with shebang,
      module docstring, `from __future__ import annotations`, stdlib-only imports
      (`argparse`, `ast`, `enum`, `re`, `dataclasses`, `pathlib`)
    - Define `BrittleCategory` enum with exactly the four categories (EXACT_COUNT,
      WHOLE_FILE_SNAPSHOT, SECTION_SNAPSHOT, EXACT_SEQUENCE_SNAPSHOT)
    - Define frozen dataclasses `Finding` and `ScanResult` (with
      `findings_by_category` property) per the design's module surface
    - Add the classification constants (`_COUNT_NAME_PATTERNS`, `_HASH_NAME_PATTERNS`,
      `_SEQUENCE_NAME_PATTERNS`, `_SHA256_HELPERS`, `_FILE_READ_CALLS`,
      `_FILE_READ_HELPERS`, `_SECTION_EXTRACT_HINTS`, `_HEADING_EXTRACT_HELPERS`,
      `_ALLOWLIST_TOKEN`, `_SHA256_HEX_RE`, `_DEFAULT_ROOTS`) and a `main(argv=None)`
      stub returning `0`
    - _Requirements: 1.1, 2.1_

  - [x] 1.2 Write unit tests for enum shape and stdlib-only import
    - Create `senzing-bootcamp/tests/test_scan_brittle_assertions.py` with class-based
      organization and the standard `sys.path` insertion to import the script
    - Assert `BrittleCategory` has exactly the four expected members
    - Assert importing the module brings in no third-party packages
    - _Requirements: 1.1, 2.1_

  - [x] 1.3 Document the brittleness taxonomy and structural replacements
    - Document the four brittle categories and, for each, at least one structural
      replacement form (threshold, marker membership, section invariants,
      ordered-subsequence) in the module docstring and/or a companion doc under
      `senzing-bootcamp/docs/policies/`
    - Note the Legitimate_Hash_Use exclusion (hashing test-generated data)
    - _Requirements: 1.1, 1.2, 1.3_

- [x] 2. Implement the pure classification core
  - [x] 2.1 Implement `classify_assertion`
    - Implement `classify_assertion(node, source_lines) -> BrittleCategory | None`
      matching `ast.Compare` `==` shapes for the four categories using the literal-anchored
      and name-pattern heuristics from the design
    - Implement the Legitimate_Hash_Use guard: return `None` when the hashed input
      derives from test-generated data, or when both sides are computed (no hard-coded
      literal/constant)
    - Resolve ambiguous shapes conservatively to `None`
    - _Requirements: 1.3, 2.3, 2.4, 2.5, 2.6, 2.9_

  - [x] 2.2 Write property test for brittle-assertion classification
    - **Property 1: Brittle assertions classify into their category**
    - Add `st_exact_count_assertion`, `st_whole_file_snapshot_assertion`,
      `st_section_snapshot_assertion`, `st_exact_sequence_snapshot_assertion` generators;
      assert each snippet classifies into its category with correct line/category
    - **Validates: Requirements 2.3, 2.4, 2.5, 2.6, 7.2**

  - [x] 2.3 Write property test for structural / legitimate-hash non-flagging
    - **Property 2: Structural assertions and legitimate hash uses are not flagged**
    - Add `st_structural_assertion` generator (membership, threshold,
      ordered-subsequence, computed-vs-computed, legitimate-hash); assert
      `classify_assertion` returns `None`
    - **Validates: Requirements 1.3, 2.9, 7.3**

  - [x] 2.4 Implement `has_allowlist_marker`
    - Implement `has_allowlist_marker(node, source_lines) -> bool` reading the source
      lines spanning `node.lineno..node.end_lineno` and detecting the `brittle-allow` token
    - _Requirements: 2.7_

  - [x] 2.5 Write property test for allowlist exemption
    - **Property 3: Allowlist marker converts a Finding into an exemption**
    - Generate brittle assertions of each category annotated with `brittle-allow`;
      assert they are reported as exemptions, never as non-allowlisted findings
    - **Validates: Requirements 2.7, 7.4**

- [x] 3. Implement the scanner driver (I/O + orchestration)
  - [x] 3.1 Implement `discover_test_files`
    - Implement `discover_test_files(roots) -> list[Path]` returning every `test_*.py`
      under the roots, sorted
    - _Requirements: 2.2_

  - [x] 3.2 Write property test for test-file discovery
    - **Property 4: Discovery finds exactly the test files**
    - Add `st_test_tree` generator producing trees of `test_*.py` and non-matching
      files; assert discovery returns exactly the `test_*.py` set
    - **Validates: Requirements 2.2**

  - [x] 3.3 Implement `scan_file` and `scan` with parse-error handling
    - Implement `scan_file(path) -> (list[Finding], str | None)` parsing with `ast`,
      classifying asserts, applying the allowlist, and returning a parse-error message
      on `SyntaxError`/unreadable file
    - Implement `scan(roots) -> ScanResult` orchestrating discovery + per-file scan,
      separating findings from exemptions and aggregating `parse_errors`; treat a
      missing root as an error
    - _Requirements: 2.8, 3.7_

  - [x] 3.4 Implement `format_summary`
    - Implement `format_summary(result) -> str` rendering files-scanned,
      per-category finding counts, and exemption count
    - _Requirements: 3.4_

  - [x] 3.5 Write property test for summary counts
    - **Property 6: Summary counts match the scan result**
    - Assert the rendered summary's files-scanned, per-category, and exemption counts
      equal the corresponding `ScanResult` values
    - **Validates: Requirements 3.4**

- [x] 4. Implement the CLI and exit-code contract
  - [x] 4.1 Implement `main` with argparse
    - Implement `main(argv=None) -> int` with `--check` and repeatable `--root`
      (defaulting to `senzing-bootcamp/tests` and `tests`), printing the summary/findings,
      and returning exit codes: non-zero on parse errors regardless of `--check`,
      non-zero under `--check` when ≥1 non-allowlisted finding, else 0
    - Wire `classify_assertion`/`scan`/`format_summary` together behind the CLI
    - _Requirements: 3.1, 3.2, 3.3, 3.7_

  - [x] 4.2 Write property test for `--check` exit code
    - **Property 5: `--check` exit code reflects non-allowlisted findings**
    - Across generated fixtures, assert `--check` exits non-zero iff ≥1 non-allowlisted
      finding (clean or fully-allowlisted fixtures exit 0)
    - **Validates: Requirements 3.2, 3.3**

  - [x] 4.3 Write unit tests for CLI entry point and parse errors
    - Assert `main([])` and `main(["--check"])` return integer exit codes
    - Add an invalid-Python fixture; assert a parse error is reported and exit is
      non-zero regardless of `--check`
    - _Requirements: 3.1, 2.8, 3.7_

- [x] 5. Checkpoint
  - Ensure all tests pass, ask the user if questions arise.

- [x] 6. Wire the scanner into CI
  - [x] 6.1 Add the scanner step to the CI workflow
    - Add a "Scan for brittle test assertions" step running
      `python senzing-bootcamp/scripts/scan_brittle_assertions.py --check` immediately
      before the `Run tests` step in `.github/workflows/validate-power.yml`, with no
      `continue-on-error`
    - _Requirements: 3.5, 3.6_

  - [x] 6.2 Write CI-wiring test
    - In repo-root `tests/`, parse `validate-power.yml`; assert the scanner step uses
      `--check`, has no `continue-on-error`, and precedes the `Run tests` step
    - _Requirements: 3.5, 3.6_

- [x] 7. Remediate exact total-test-count assertions
  - [x] 7.1 Replace Exact_Count_Assertions with non-regression thresholds
    - Replace whole-suite/total count `==` checks (e.g. `_PASSING_BASELINE == 4648`)
      with `observed >= FLOOR` threshold checks, preserving the original intent as a
      comment/docstring naming the guarded behavior
    - _Requirements: 4.1, 4.2, 4.3, 4.4_

  - [x] 7.2 Write property test for the remediated count threshold
    - **Property 7: Remediated count assertion is a non-regression threshold**
    - In `senzing-bootcamp/tests/test_remediation_invariants.py`, assert the threshold
      passes iff observed ≥ floor (adding/splitting tests never fails; below-floor fails)
    - **Validates: Requirements 4.1, 4.3, 4.4**

- [x] 8. Remediate whole-file and section content-hash snapshots
  - [x] 8.1 Replace whole-file snapshot assertions with structural assertions
    - Replace `_sha256(content) == _HASH_*` whole-file checks with marker /
      cross-reference membership and invariant checks that preserve the guarded
      behavior; keep the original intent as a comment and retain any historical
      bug-condition coverage via an equivalent structural assertion
    - _Requirements: 5.1, 6.2, 6.6_

  - [x] 8.2 Replace section snapshot assertions with structural assertions
    - Replace section digest-equality checks (`_SNAP_*`,
      `_snapshot_section_content`) with section-content invariant assertions
      (required markers/sentinels in the required relation), preserving intent as a
      comment and retaining equivalent bug-condition coverage
    - _Requirements: 5.2, 6.2, 6.6_

  - [x] 8.3 Write property test for remediated snapshot marker checks
    - **Property 8: Remediated snapshot assertion checks marker presence and tolerates additions**
    - Add `st_required_markers` + `st_extra_content`; assert content with all markers
      (plus arbitrary additions) passes and content with a marker removed fails
    - **Validates: Requirements 5.1, 5.2, 5.4, 5.5**

- [x] 9. Remediate exact heading/line-sequence snapshots
  - [x] 9.1 Replace Exact_Sequence_Snapshot_Assertions with ordered-subsequence checks
    - Replace full-list-equality checks (e.g. `_extract_headings(content) == _HEADINGS_*`)
      with ordered-subsequence assertions that require the headings in relative order
      while tolerating unrelated additions, preserving intent as a comment and
      retaining equivalent bug-condition coverage
    - _Requirements: 5.3, 6.2, 6.6_

  - [x] 9.2 Write property test for remediated sequence checks
    - **Property 9: Remediated sequence assertion checks ordered subsequence and tolerates additions**
    - Assert the check passes when required headings appear in order with arbitrary
      interleaved headings, and fails when a required heading is removed or two are reordered
    - **Validates: Requirements 5.3, 5.4, 5.5**

- [x] 10. Checkpoint
  - Ensure all tests pass, ask the user if questions arise.

- [x] 11. Verify the debrittled end state
  - [x] 11.1 Add end-state self-check and regression-coverage tests
    - Add an automated test that invokes `scan()` over `senzing-bootcamp/tests/` and
      `tests/` and asserts zero non-allowlisted findings in every category
    - Add a test asserting the inventory of Exploration_Tests / historical bug
      conditions did not decrease after remediation
    - _Requirements: 4.5, 5.6, 6.1, 6.3, 6.4, 6.5_

  - [x] 11.2 Add documentation-review test for preserved intent
    - Assert each remediated count/snapshot/sequence assertion carries a comment or
      docstring preserving the original guarded intent
    - _Requirements: 4.2, 6.2_

- [x] 12. Final checkpoint
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional test sub-tasks and can be skipped for a faster MVP.
- Each task references specific requirement clauses for traceability.
- Property tests (Properties 1–9) validate the universal correctness properties from
  the design; unit/example tests cover enum shape, stdlib-only import, the CLI entry
  point, parse-error handling, and CI wiring.
- Checkpoints ensure the suite stays green between scanner build-out, CI wiring, and
  remediation.
- Remediation tasks (7–9) must keep the full pytest suite passing and must not reduce
  historical bug-condition coverage (Requirement 6).

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1", "1.3"] },
    { "id": 1, "tasks": ["2.1", "1.2"] },
    { "id": 2, "tasks": ["2.4", "2.2"] },
    { "id": 3, "tasks": ["3.1", "2.3"] },
    { "id": 4, "tasks": ["3.3", "2.5"] },
    { "id": 5, "tasks": ["3.4", "3.2"] },
    { "id": 6, "tasks": ["4.1", "3.5"] },
    { "id": 7, "tasks": ["4.2", "6.1", "7.1", "8.1", "9.1"] },
    { "id": 8, "tasks": ["4.3", "6.2", "8.2"] },
    { "id": 9, "tasks": ["7.2"] },
    { "id": 10, "tasks": ["8.3"] },
    { "id": 11, "tasks": ["9.2"] },
    { "id": 12, "tasks": ["11.1", "11.2"] }
  ]
}
```
