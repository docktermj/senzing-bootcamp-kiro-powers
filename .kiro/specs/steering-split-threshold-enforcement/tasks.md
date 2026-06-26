# Implementation Plan: Steering Split Threshold Enforcement

## Overview

This plan adds the **Split_Check** lint rule to
`senzing-bootcamp/scripts/lint_steering.py`, modeled on the existing
router-ceiling machinery. Work proceeds bottom-up: first the standalone helpers
(`get_split_threshold`, `parse_split_allowlist`, `normalize_split_severity`),
then the pure classification rule (`check_split_threshold`), and finally the CLI
flag and `run_all_checks` wiring that integrates everything into the CI gate. Each
implementation sub-task is paired with property-based and unit tests in
`senzing-bootcamp/tests/test_steering_split_threshold_enforcement.py`, using
pytest + Hypothesis with `@settings(max_examples=20)`, `st_`-prefixed strategies,
and the standard `sys.path` import pattern. No changes are made to
`.github/workflows/validate-power.yml`.

All 11 correctness properties from the design are mapped to dedicated test
sub-tasks. Each implementation step builds on the previous and ends fully wired
into `run_all_checks`, leaving no orphaned code.

## Tasks

- [x] 1. Set up test scaffolding and shared Hypothesis strategies
  - [x] 1.1 Create the test file with imports and strategies
    - Create `senzing-bootcamp/tests/test_steering_split_threshold_enforcement.py`
    - Add the standard `sys.path` manipulation
      (`_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")`)
      and import `get_split_threshold`, `parse_split_allowlist`,
      `check_split_threshold`, `normalize_split_severity`, and
      `SplitAllowlistEntry` from `lint_steering`
    - Define the shared `st_`-prefixed strategies used across property tests:
      `st_token_count()` (0–1,000,000), `st_threshold()` (1–1,000,000),
      `st_filename()` (kebab-case `.md` names), `st_justification_valid()`
      (1–280 chars), `st_justification_invalid()` (empty or 281–400 chars),
      `st_file_metadata()` (filename → `{"token_count": int}`),
      `st_invalid_severity()` (text excluding `WARNING`/`ERROR`)
    - Imports may reference symbols not yet implemented; that is expected —
      they are filled in by later tasks
    - _Requirements: 6.1, 6.8_

- [x] 2. Implement the Split_Threshold reader
  - [x] 2.1 Implement `DEFAULT_SPLIT_THRESHOLD` and `get_split_threshold`
    - Add module-level constant `DEFAULT_SPLIT_THRESHOLD = 5000` (the only
      permitted hardcoded threshold value)
    - Implement `get_split_threshold(index_path: Path) -> int` using a localized
      `re.finditer(r"split_threshold_tokens:\s*(\d+)", content)`, mirroring
      `get_router_ceiling`
    - Return the first captured value that parses to a positive integer (≥ 1);
      fall back to `DEFAULT_SPLIT_THRESHOLD` when the file is missing, the key is
      absent, or no match is a positive integer (zero/negative excluded by the
      `≥ 1` check, non-numeric/negative excluded by `\d+`)
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7_

  - [x] 2.2 Write property test that a configured positive-integer threshold is honored (first wins)
    - **Property 3: A configured positive-integer threshold is honored (first occurrence wins)**
    - **Validates: Requirements 1.2, 1.6**
    - Generate a positive integer `N` (plus trailing positive-integer values),
      render them as `budget.split_threshold_tokens` lines in a temp index, assert
      `get_split_threshold` returns the first value `N`

  - [x] 2.3 Write property test for invalid/absent threshold fallback
    - **Property 4: An invalid or absent threshold falls back to the Default_Threshold**
    - **Validates: Requirements 1.5**
    - Generate non-positive-integer values (non-numeric, zero, negative) and the
      key-absent case, assert `get_split_threshold` returns 5000

  - [x] 2.4 Write unit tests for missing-file and absent-key default fallback
    - Assert `get_split_threshold` returns 5000 when the index file does not exist
    - Assert `get_split_threshold` returns 5000 when the index exists but the key
      is absent
    - _Requirements: 1.3, 1.4, 6.6_

- [x] 3. Implement the allowlist parser
  - [x] 3.1 Implement `SplitAllowlistEntry` dataclass and `parse_split_allowlist`
    - Add `@dataclass SplitAllowlistEntry` with `filename: str` and
      `justification: str`
    - Implement `parse_split_allowlist(index_path: Path) -> list[SplitAllowlistEntry]`
      using the same minimal indentation-based line parsing as
      `parse_steering_index` (no PyYAML)
    - Return `[]` when the file is missing or the `split_allowlist:` section is
      absent/empty; preserve the raw justification (including empty string) so
      validation happens downstream in `check_split_threshold`
    - _Requirements: 4.1_

  - [x] 3.2 Write property test for allowlist round-tripping
    - **Property 11: Allowlist parsing round-trips filename/justification pairs**
    - **Validates: Requirements 4.1**
    - Generate sets of (exact case-sensitive filename, 1–280-char justification)
      pairs, render them into a `split_allowlist:` section, assert
      `parse_split_allowlist` returns entries preserving each filename and
      justification

- [x] 4. Implement severity normalization
  - [x] 4.1 Implement `normalize_split_severity`
    - Implement `normalize_split_severity(value: str | None) -> str`
    - Return `"WARNING"` when `value` is `None`; return the canonical
      `"WARNING"`/`"ERROR"` for valid overrides; raise `ValueError` for any other
      value rather than silently defaulting
    - _Requirements: 3.7_

  - [x] 4.2 Write property test that invalid severity overrides are rejected
    - **Property 7: Invalid severity overrides are rejected**
    - **Validates: Requirements 3.7**
    - Generate strings that are neither `WARNING` nor `ERROR`, assert
      `normalize_split_severity` raises rather than returning a default

- [x] 5. Implement the classification rule `check_split_threshold`
  - [x] 5.1 Implement `check_split_threshold`
    - Implement `check_split_threshold(file_metadata, split_threshold, allowlist, severity="WARNING") -> list[LintViolation]`
      mirroring `check_router_convention`'s structure and MISSING handling
    - Validate allowlist entries (justification present, 1–280 chars); invalid
      entries emit an ERROR violation and are excluded from the exempt set
    - Emit an ERROR violation for each stale allowlist filename absent from
      `file_metadata`, retaining remaining entries
    - Iterate `file_metadata` in sorted filename order, evaluating each entry
      exactly once: skip exempt files; emit one MISSING violation for
      absent/non-int counts; emit one over-threshold violation at `severity` when
      `token_count > split_threshold` (naming filename, integer token_count, and
      threshold); no violation at or below threshold (including equality)
    - Emit every finding via `LintViolation(level, file=str(INDEX_PATH), line=0, message=...)`
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 3.1, 3.3, 3.6, 4.2, 4.3, 4.4, 4.5, 4.6_

  - [x] 5.2 Write property test for the over-threshold IFF rule
    - **Property 1: Over-threshold classification is an IFF on strictly-greater-than**
    - **Validates: Requirements 2.1, 2.2, 2.3, 2.5, 6.2, 6.3, 6.7**
    - Generate a `token_count` (0–1,000,000) and `threshold` (1–1,000,000), run
      with an empty allowlist, assert exactly one over-threshold violation iff
      `token_count > threshold` (explicitly exercising the `==` boundary), and
      that the message contains filename, integer token_count, and threshold

  - [x] 5.3 Write property test for missing/non-integer counts
    - **Property 2: Missing or non-integer counts yield exactly one unclassifiable violation**
    - **Validates: Requirements 2.4**
    - Generate entries whose `token_count` is absent or non-integer (file not
      exempt), assert exactly one "cannot classify" violation naming the file and
      no over-threshold violation

  - [x] 5.4 Write property test that violations carry the configured severity
    - **Property 5: Over-threshold violations carry the configured severity**
    - **Validates: Requirements 3.1, 3.3**
    - Generate a `file_metadata` map and a severity in `{WARNING, ERROR}`, assert
      every over-threshold violation's `level` equals that severity, and defaults
      to `WARNING` with no override

  - [x] 5.5 Write property test that every emitted violation is well-formed
    - **Property 6: Every emitted violation is a well-formed LintViolation**
    - **Validates: Requirements 3.6**
    - For arbitrary inputs, assert every returned object is a `LintViolation` with
      `level` in `{WARNING, ERROR}`, non-empty string `file`, integer `line`, and
      non-empty string `message`

  - [x] 5.6 Write property test for exemption matching
    - **Property 8: Exemption holds iff a file exactly (case-sensitively) matches a valid allowlist entry**
    - **Validates: Requirements 4.2, 4.3, 4.4, 6.4**
    - Generate over-threshold entries and allowlists, assert no over-threshold
      violation iff the filename exactly (case-sensitively) matches a valid
      allowlist entry; otherwise evaluated per Property 1 (including empty
      allowlist)

  - [x] 5.7 Write property test for stale allowlist entries
    - **Property 9: Stale allowlist entries are reported while others still apply**
    - **Validates: Requirements 4.5**
    - Generate allowlists with filenames absent from `file_metadata`, assert
      exactly one stale-entry violation per absent filename while present entries
      still exempt their files

  - [x] 5.8 Write property test for invalid justifications
    - **Property 10: Invalid justifications produce a violation and do not exempt**
    - **Validates: Requirements 4.6**
    - Generate allowlist entries with empty or >280-char justifications on
      over-threshold files, assert a violation is produced and the file is NOT
      exempted (still flagged)

  - [x] 5.9 Write unit test for empty file_metadata
    - Assert `check_split_threshold` produces zero violations for an empty
      `file_metadata` map
    - _Requirements: 2.6_

- [x] 6. Checkpoint - Ensure all helper and classification tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 7. Wire the Split_Check into the CLI and `run_all_checks`
  - [x] 7.1 Add `--split-severity` flag and integrate into `run_all_checks`
    - Add `--split-severity` argument to `main()` with
      `choices=["WARNING", "ERROR"]`, `default="WARNING"`
    - Add a `split_severity: str = "WARNING"` parameter to `run_all_checks`,
      threaded from `args.split_severity`
    - After the existing router block, call `get_split_threshold`,
      `parse_split_allowlist`, and extend `violations` with
      `check_split_threshold(index_data.get("file_metadata", {}), split_threshold, split_allowlist, severity=normalize_split_severity(split_severity))`
    - Rely on the existing exit-code logic (ERROR always fails; WARNING fails
      under `--warnings-as-errors`) and existing `LintViolation.format()` output —
      no new exit-code or output code
    - _Requirements: 3.2, 3.4, 3.5, 5.1, 5.3, 5.4_

  - [x] 7.2 Write integration test for aggregation wiring
    - Run `run_all_checks` against a temp index containing a known over-threshold
      file, assert a Split_Check violation appears in the aggregate results
    - _Requirements: 5.1_

  - [x] 7.3 Write integration tests for exit-code behavior
    - Assert WARNING-level Split_Check violations do not by themselves fail the
      linter, but do fail under `--warnings-as-errors`; assert ERROR-severity
      violations always fail
    - _Requirements: 3.2, 3.4, 3.5, 5.3, 5.4_

  - [x] 7.4 Write integration test for output format
    - Assert printed violation lines use `LintViolation.format()` and contain the
      file path, token_count, and Split_Threshold
    - _Requirements: 5.5_

  - [x] 7.5 Write unit test that argparse rejects an invalid `--split-severity`
    - Assert invoking the CLI with an out-of-choices `--split-severity` value
      exits non-zero with an error message rather than silently defaulting
    - _Requirements: 3.7_

- [x] 8. Real-corpus and CI configuration smoke tests
  - [x] 8.1 Write real-corpus smoke test
    - Run the Split_Check against the actual `steering-index.yaml` with an empty
      allowlist, assert `hook-registry-critical.md`, `graduation.md`,
      `module-05-phase2-data-mapping.md`, and `module-01-phase1-discovery.md` are
      reported as over-threshold
    - _Requirements: 5.6_

  - [x] 8.2 Write CI configuration smoke test
    - Assert the "Lint steering files" step in `validate-power.yml` is unchanged
      (no new/required step) and the test matrix lists Python 3.11, 3.12, 3.13
    - _Requirements: 5.2_

- [x] 9. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional test sub-tasks and can be skipped for a
  faster MVP, though they protect the enforcement behavior against regression.
- Each task references specific requirements for traceability; property test
  tasks additionally reference their design property number.
- All implementation changes are confined to
  `senzing-bootcamp/scripts/lint_steering.py`; all tests live in
  `senzing-bootcamp/tests/test_steering_split_threshold_enforcement.py`.
- No changes are made to `.github/workflows/validate-power.yml`; the Split_Check
  runs automatically inside the existing "Lint steering files" gate.
- Property tests use Hypothesis `@given` with `@settings(max_examples=20)` and
  `st_`-prefixed strategies, per Requirement 6.7.
- Checkpoints ensure incremental validation at natural breaks.

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1", "2.1"] },
    { "id": 1, "tasks": ["2.2", "3.1"] },
    { "id": 2, "tasks": ["2.3", "4.1"] },
    { "id": 3, "tasks": ["2.4", "5.1"] },
    { "id": 4, "tasks": ["3.2", "7.1"] },
    { "id": 5, "tasks": ["4.2"] },
    { "id": 6, "tasks": ["5.2"] },
    { "id": 7, "tasks": ["5.3"] },
    { "id": 8, "tasks": ["5.4"] },
    { "id": 9, "tasks": ["5.5"] },
    { "id": 10, "tasks": ["5.6"] },
    { "id": 11, "tasks": ["5.7"] },
    { "id": 12, "tasks": ["5.8"] },
    { "id": 13, "tasks": ["5.9"] },
    { "id": 14, "tasks": ["7.2"] },
    { "id": 15, "tasks": ["7.3"] },
    { "id": 16, "tasks": ["7.4"] },
    { "id": 17, "tasks": ["7.5"] },
    { "id": 18, "tasks": ["8.1"] },
    { "id": 19, "tasks": ["8.2"] }
  ]
}
```
