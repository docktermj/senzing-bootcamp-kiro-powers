# Implementation Plan: ER Baseline Status Summary

## Overview

Implement `senzing-bootcamp/scripts/baseline_status.py`, a stdlib-only, strictly **read-only**
script that reports which registered `Data_Sources` have an accepted ER baseline and which are
missing one. It derives the source list from the existing registry (via
`data_sources.parse_registry_yaml` and its migration/validation chain), locates each baseline via
the canonical `compare_results.baseline_path()` convention, reads only light metadata
(`captured_at`, `record_count`, `entity_count`) from each present baseline, marks missing sources
with an `accept_baseline` remediation hint, and renders a concise summary. The pass never creates,
modifies, or deletes any file and never raises on missing or malformed inputs.

Work proceeds bottom-up: scaffolding and dataclasses first, then the pure read/transform functions
(`read_registry_sources`, `read_baseline_metadata`, `build_status`, `build_summary`,
`render_summary`), each followed closely by its property test, then the non-blocking read-only
`main`, then the optional steering surfacing in `module-05-phase3-test-load.md` and
`session-resume.md`, and finally the example and guardrail tests. All code targets Python 3.11+
stdlib only, reuses the existing registry parser (no PyYAML), and follows the project script/test
conventions.

## Tasks

- [x] 1. Scaffold the baseline-status script
  - [x] 1.1 Create `baseline_status.py` skeleton and dataclasses
    - Create `senzing-bootcamp/scripts/baseline_status.py` with shebang,
      `from __future__ import annotations`, module docstring with usage examples, stdlib-only
      imports, and the `sys.path` insertion needed to import the sibling `compare_results` and
      `data_sources` scripts (scripts are not a package)
    - Reuse, unmodified: `from compare_results import baseline_path` and
      `from data_sources import parse_registry_yaml, apply_migrations, validate_registry, _dict_to_registry`
    - Define the `BaselineStatus` and `BaselineSummary` dataclasses exactly as specified in the
      design's Components section
    - Add an `argparse`-based `main(argv=None) -> int` stub with a `--registry` option defaulting to
      the canonical path (`config/data_sources.yaml`) and an `if __name__ == "__main__": main()`
      entry point
    - _Requirements: 2.1, 3.3_

- [x] 2. Implement the registry source reader
  - [x] 2.1 Implement `read_registry_sources`
    - Implement `read_registry_sources(registry_path="config/data_sources.yaml", *, read_text=None) -> list[str] | None`:
      read and parse the registry using the existing parser chain
      (`parse_registry_yaml` → `apply_migrations` → `validate_registry` → `_dict_to_registry`) and
      return the registered `data_source` keys in registry order
    - Return `None` when the registry file is absent, unreadable, unparseable, or invalid; the
      injectable `read_text` callable defaults to a UTF-8 file read that raises `FileNotFoundError`
      when absent, so the function is testable without touching disk
    - _Requirements: 3.2, 4.2_

- [x] 3. Implement the baseline metadata reader
  - [x] 3.1 Implement `read_baseline_metadata`
    - Implement `read_baseline_metadata(path: Path, *, read_text=None) -> dict | None`: read a single
      baseline file and extract **only** the light metadata (`captured_at`, `record_count`,
      `entity_count`) from the `ERStatistics` JSON
    - Return `None` if the file is missing, unreadable, not valid JSON, or not a JSON object; missing
      individual fields degrade to `None` values rather than an error; never raise
    - _Requirements: 1.2, 4.1_

  - [x] 3.2 Write property test for the light-metadata contract
    - **Property 2: Present rows carry light metadata and never the full contents** — for any
      baseline written as a valid `ERStatistics` JSON object, the present row carries `captured_at`,
      `record_count`, and `entity_count` equal to the file's values, and surfaces none of the other
      baseline fields (`match_count`, `possible_match_count`, `relationship_count`)
    - Add the `st_er_statistics()` custom strategy (synthetic, PII-free content) in the test module
    - **Validates: Requirements 1.2**

- [x] 4. Implement per-source status classification
  - [x] 4.1 Implement `build_status`
    - Implement `build_status(data_source: str, *, read_text=None) -> BaselineStatus`: compute
      `baseline_path(data_source)`, probe it, and build the row — `present=True` with light metadata
      when the baseline reads cleanly; `present=False` with a non-empty `remediation` string naming
      the `accept_baseline` path when the file is absent; `present=False, unreadable=True` when the
      file exists but cannot be read/parsed
    - _Requirements: 1.1, 1.2, 1.3, 3.1, 4.1_

  - [x] 4.2 Write property test for missing-source remediation
    - **Property 3: Missing sources are marked and carry a remediation hint** — for any registered
      `Data_Source` with no baseline file, its row has `present` false and a non-empty `remediation`
      string that references the existing `accept_baseline` path
    - **Validates: Requirements 1.3**

- [x] 5. Implement summary assembly
  - [x] 5.1 Implement `build_summary`
    - Implement `build_summary(registry_path="config/data_sources.yaml", *, read_text=None) -> BaselineSummary`:
      resolve sources via `read_registry_sources`, then one `build_status` per source in registry
      order; when `read_registry_sources` returns `None`, produce
      `BaselineSummary(registry_present=False, statuses=[])`
    - _Requirements: 1.1, 3.2, 4.2_

  - [x] 5.2 Write property test for completeness and presence flags
    - **Property 1: Every registered source appears exactly once with a correct presence flag** —
      for any registry and any subset of sources whose baselines exist at `baseline_path`,
      `build_summary` produces exactly one row per registered source, in registry order, with
      `present` true iff that source's `baseline_path` file exists and reads as a JSON object
    - Add `st_data_source_key()` and `st_registry(sources)` custom strategies (synthetic, PII-free)
      in the test module; materialize baselines at `baseline_path(datasource)`
    - **Validates: Requirements 1.1, 3.1, 3.2**

  - [x] 5.3 Write property test for degrade-without-raising
    - **Property 5: Missing or malformed baselines degrade without raising** — for any registered
      source whose baseline is missing, empty, non-JSON, JSON-but-not-an-object, or unreadable,
      `build_summary` never raises, marks that source missing or unreadable, and still reports every
      other source correctly
    - Add the `st_malformed_baseline()` adversarial strategy (empty, non-JSON, JSON array/scalar,
      truncated object) in the test module
    - **Validates: Requirements 4.1**

- [x] 6. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 7. Implement rendering
  - [x] 7.1 Implement `render_summary`
    - Implement `render_summary(summary: BaselineSummary) -> str`: format a header, then one line per
      source (present with its timestamp/counts, `MISSING` with the remediation hint, or
      `UNREADABLE`), or the single line "No data sources have been registered yet." when
      `registry_present` is false; presentation only, no I/O, and never emit row-level data
    - _Requirements: 1.1, 1.2, 1.3, 4.2_

- [x] 8. Implement `main` orchestration, non-blocking and read-only
  - [x] 8.1 Wire read → build → render in `main`
    - In `main`, parse `--registry`, call `build_summary`, and print `render_summary`'s output
    - Wrap the body in a top-level guard that, on any unexpected exception, logs a warning to stderr
      and returns without raising; return 0 on any clean run (including empty-registry and
      all-missing cases) and 1 only on an internally handled error path
    - Open no file for writing, never call `accept_baseline`, and never create directories
    - _Requirements: 2.1, 2.3, 4.1, 4.2_

  - [x] 8.2 Write property test for the read-only guarantee
    - **Property 4: The summary is read-only** — for any registry and any mix of present, missing,
      and malformed baseline files, running the summary leaves the workspace byte-for-byte unchanged
    - Snapshot the temp workspace (file set + contents) before and after; assert identical and that
      no write occurred (monkeypatch `accept_baseline` to fail if called)
    - **Validates: Requirements 2.3**

  - [x] 8.3 Write property test for the missing/invalid registry path
    - **Property 6: A missing or invalid registry yields no sources and a clean result** — for any
      absent, empty, or invalid registry content, `build_summary` returns `registry_present` false
      with an empty `statuses` list, and `main` returns cleanly without raising
    - **Validates: Requirements 4.2**

- [x] 9. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 10. Surface the summary at natural checkpoints (optional steering wiring)
  - [x] 10.1 Add optional surfacing to Module 5 completion and session resume
    - Edit `senzing-bootcamp/steering/module-05-phase3-test-load.md` so Phase 3 completion MAY run
      `python3 senzing-bootcamp/scripts/baseline_status.py` and render its summary, and edit
      `senzing-bootcamp/steering/session-resume.md` (an `inclusion: auto` steering file) to MAY run
      the same on resume so missing baselines are visible at natural checkpoints
    - Document that this surfacing is advisory and non-blocking (never blocks the workflow), adds no
      hook and no per-write cost, and that the script is strictly read-only
    - _Requirements: 2.2, 2.3_

  - [x] 10.2 Write architecture-guardrail tests
    - Assert the feature adds no `postToolUse` write-tool hook, that the script's imports are limited
      to the standard library plus the sibling `compare_results` / `data_sources` scripts
      (stdlib-only guardrail), and that the steering surfacing is prose-only
    - _Requirements: 2.3, 3.3_

- [x] 11. Example and rendering tests
  - [x] 11.1 Write example tests for the Requirement 5.1 scenarios
    - Cover: all sources have baselines (every row `present` with expected metadata); a mix of
      present and missing (correct per-row classification and remediation text); an unreadable
      baseline (a corrupt file yields an `unreadable` row while siblings stay correct); a missing
      registry ("No data sources have been registered yet." and a clean return); and an on-demand
      CLI run — `main([...])` against a temp workspace returns 0 and prints the rendered summary.
      Use synthetic, PII-free fixtures only
    - _Requirements: 5.1, 5.2, 2.1, 4.2_

  - [x] 11.2 Write rendering unit tests
    - Assert `render_summary` output includes a line per source with the correct
      present/missing/unreadable markers and emits no row-level data
    - _Requirements: 1.1, 1.2, 1.3_

- [x] 12. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional test sub-tasks and can be skipped for a faster MVP.
- Property tests use Hypothesis with the project's registered profiles (`fast`=5 local,
  `thorough`=100 CI); do not hand-set `@settings(max_examples=...)` to restate the baseline.
- Tests live in `senzing-bootcamp/tests/test_baseline_status.py`, are class-based
  (`TestBaselineStatus`), and import scripts via the `sys.path` convention.
- Each property task references its property number and the requirement clause it validates for
  traceability.
- The script is strictly read-only: it never calls `accept_baseline`, never opens a file for
  writing, and never creates directories (Requirement 2.3).
- All fixtures are synthetic and PII-free (Requirement 5.2); the summary reports counts and a
  timestamp only, never row-level data.

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1"] },
    { "id": 1, "tasks": ["2.1", "3.1"] },
    { "id": 2, "tasks": ["3.2", "4.1"] },
    { "id": 3, "tasks": ["4.2", "5.1"] },
    { "id": 4, "tasks": ["5.2", "5.3", "7.1"] },
    { "id": 5, "tasks": ["8.1"] },
    { "id": 6, "tasks": ["8.2", "8.3", "10.1"] },
    { "id": 7, "tasks": ["10.2", "11.1", "11.2"] }
  ]
}
```
