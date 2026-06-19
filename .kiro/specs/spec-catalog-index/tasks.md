# Implementation Plan: Spec Catalog Index

## Overview

This plan implements the `Spec_Catalog_Generator` as a single stdlib-only Python
3.11+ CLI script (`senzing-bootcamp/scripts/generate_spec_catalog.py`) with a
property-based test suite (`senzing-bootcamp/tests/test_generate_spec_catalog.py`),
following the conventions of the reference `generate_docs_index.py` and
`test_generate_docs_index.py`.

The work proceeds test-driven through the pure-function pipeline (discover → resolve
metadata → derive status → render/emit), then the thin CLI I/O shell, then the 13
correctness properties as Hypothesis tests (≥100 iterations each, tagged
`Feature: spec-catalog-index, Property N`), example/edge/error unit tests, the
curated `.kiro/spec-catalog.yaml` metadata file, and the CI drift-gate wiring in
`.github/workflows/validate-power.yml`.

All property test sub-tasks are marked optional (`*`) per testing convention; each
references the specific correctness property and requirement clauses it validates.

## Tasks

- [x] 1. Establish script skeleton, constants, and data models
  - Create `senzing-bootcamp/scripts/generate_spec_catalog.py` with shebang
    (`#!/usr/bin/env python3`), module docstring with usage examples,
    `from __future__ import annotations`, and stdlib-only imports
    (`argparse`, `json`, `sys`, `dataclasses`, `pathlib`).
  - Define constants: `DEFAULT_SPECS_ROOT`, `DEFAULT_INDEX_PATH`,
    `DEFAULT_METADATA_PATH`, `CONFIG_FILENAME`, `SPEC_DOCUMENTS`, `STATUS_ORDER`.
  - Define frozen dataclasses `SpecConfig`, `SpecRecord`, `SpecRelationships`,
    `CatalogMetadata` (with `empty()` classmethod), `SpecEntry`, `Catalog`.
  - Define the `CatalogError` exception type for detected processing errors.
  - Add the test module `senzing-bootcamp/tests/test_generate_spec_catalog.py` with
    the `sys.path` import shim importing the script symbols.
  - _Requirements: 8.9, 2.1_

- [x] 2. Implement discovery and config parsing
  - [x] 2.1 Implement `read_config` and `count_task_checkboxes`
    - `read_config(config_path)` parses `.config.kiro` JSON, returns `SpecConfig`
      with `workflow_type`/`spec_type` (None when absent), raises `CatalogError`
      naming the offending spec dir when content is not valid JSON.
    - `count_task_checkboxes(tasks_md)` returns `(total, complete)` by scanning
      lines whose stripped form starts with `- [ ]`, `- [x]`, or `- [X]`; ignores
      all other content including prose with brackets.
    - _Requirements: 1.4, 8.7, 2.4, 2.5, 2.6_

  - [x] 2.2 Implement `discover_specs`
    - Enumerate immediate subdirectories of `specs_root` as `SpecRecord`s, sorted
      by case-insensitive key (`identifier.casefold()`) with raw identifier
      tiebreaker.
    - Record `identifier`, presence flags for each `SPEC_DOCUMENTS` entry, parsed
      config, and task checkbox counts.
    - Include directories with no documents and no config (status resolves to
      `unknown` later).
    - _Requirements: 1.1, 1.2, 1.3, 1.5, 1.6_

  - [x] 2.3 Write property test for discovery completeness and fidelity
    - **Property 1: Discovery completeness and fidelity**
    - **Validates: Requirements 1.1, 1.2, 1.3**
    - Add `st_spec_tree()` helper that materializes random subdir names, random doc
      presence, and stray files into a temp dir; tear down with `shutil.rmtree`.
    - `@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])`.

  - [x] 2.4 Write property test for config faithful read
    - **Property 2: Config values are read faithfully**
    - **Validates: Requirements 1.4**
    - Add `st_config()` generating valid `workflowType`/`specType` JSON objects;
      assert parsed values equal written values, and absence yields None.
    - `@settings(max_examples=100)`.

- [x] 3. Implement metadata loading and reference validation
  - [x] 3.1 Implement `_parse_simple_yaml` and `load_metadata`
    - `_parse_simple_yaml(text)` is a minimal stdlib YAML-subset parser (top-level
      keys, nested mappings, `- ` list items, scalar `key: value`).
    - `load_metadata(metadata_path)` returns `CatalogMetadata.empty()` when the file
      is absent (Req 3.6); parses `status_overrides`, `supersessions`, and `related`
      groups; raises `CatalogError` with parse detail on failure (Req 8.8).
    - _Requirements: 3.1, 3.2, 3.6, 8.8_

  - [x] 3.2 Implement `validate_metadata_refs`
    - Return the sorted list of metadata-referenced identifiers that match no
      discovered `Spec_Directory`; a non-empty result drives exit code 1.
    - _Requirements: 3.5_

  - [x] 3.3 Write property test for error conditions force exit 1
    - **Property 13: Detected errors force exit code 1**
    - **Validates: Requirements 3.5, 8.5, 8.7**
    - Add `st_dangling_metadata()` and `st_invalid_json_config()`; assert stderr
      report and exit code 1 even when other processing could complete.
    - `@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])`.

- [x] 4. Implement status derivation and relationship assembly
  - [x] 4.1 Implement `derive_status`
    - Assign exactly one `Status_Value` using fixed precedence: explicit override →
      recorded supersession → `tasks.md` checkbox state (all complete →
      `implemented`; any incomplete → `in-progress`; present with no checkbox →
      `unknown`) → document presence (`requirements.md` or `design.md` →
      `in-progress`) → otherwise `unknown`.
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 2.8_

  - [x] 4.2 Write property test for single enumerated status value
    - **Property 4: Status is exactly one enumerated value**
    - **Validates: Requirements 2.1**
    - Add `st_record()` × `st_metadata()`; assert result is in `STATUS_ORDER`.
    - `@settings(max_examples=100)`.

  - [x] 4.3 Write property test for status precedence
    - **Property 5: Status precedence**
    - **Validates: Requirements 2.2, 2.3, 2.4, 2.5, 2.7, 2.8**
    - Generate records with conflicting signals × metadata overrides/supersessions;
      assert the highest-precedence applicable signal always wins.
    - `@settings(max_examples=100)`.

  - [x] 4.4 Implement `resolve_relationships`
    - For each directional supersession (A supersedes B), record
      `A.supersedes += [B]` and `B.superseded_by += [A]`; record related links
      symmetrically across each group. All lists sorted for determinism.
    - _Requirements: 3.1, 3.2, 3.3, 3.4_

  - [x] 4.5 Write property test for relationship reciprocity and symmetry
    - **Property 6: Relationship reciprocity and symmetry**
    - **Validates: Requirements 3.1, 3.2, 3.3, 3.4**
    - Add `st_supersessions()` / `st_related_groups()` over known ids; assert
      reciprocal `supersedes`/`superseded_by` and full related-group symmetry.
    - `@settings(max_examples=100)`.

- [x] 5. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 6. Implement catalog composition and rendering
  - [x] 6.1 Implement `build_catalog`
    - Compose the fully-resolved, ordered in-memory `Catalog`: ordered `SpecEntry`
      tuple (case-insensitive ascending) plus `status_counts` keyed over
      `STATUS_ORDER`.
    - _Requirements: 1.6, 4.4, 5.4_

  - [x] 6.2 Implement `render_index`
    - Render the CommonMark `Spec_Index`: provenance banner, status-count summary in
      `STATUS_ORDER`, one entry per spec showing identifier, status, `specType`,
      `workflowType`, a CommonMark link to the Spec_Directory, and any
      supersession/related identifiers. Terminate with a single trailing newline.
    - _Requirements: 4.2, 4.3, 4.4, 4.5, 4.6, 9.3_

  - [x] 6.3 Write property test for index rendering completeness
    - **Property 7: Index rendering completeness**
    - **Validates: Requirements 4.2, 4.3, 4.5**
    - Add `st_catalog()` producing fully-resolved random catalogs; assert each
      spec's identifier/status/type/workflow/link/relationships appear.
    - `@settings(max_examples=100)`.

  - [x] 6.4 Write property test for accurate, total status counts
    - **Property 8: Status counts are accurate and total**
    - **Validates: Requirements 4.4**
    - Over `st_catalog()`, assert each rendered count equals the actual number of
      specs with that status and counts sum to the total.
    - `@settings(max_examples=100)`.

  - [x] 6.5 Write property test for case-insensitive ascending ordering
    - **Property 3: Case-insensitive ascending ordering**
    - **Validates: Requirements 1.6, 5.4**
    - Over `st_identifiers()` (mixed-case unique ids), assert index and summary
      entry order is case-insensitive ascending.
    - `@settings(max_examples=100)`.

- [x] 7. Implement machine-readable summary
  - [x] 7.1 Implement `render_summary`
    - Serialize the `Catalog_Summary` as JSON (`indent=2, sort_keys=True`, trailing
      newline), entries ordered case-insensitively by identifier, including for each
      spec the identifier, status, `specType`, `workflowType`, document-presence
      flags, and recorded relationships. Skip writing and signal exit 1 when a
      required field cannot be collected.
    - _Requirements: 5.1, 5.2, 5.4, 5.5_

  - [x] 7.2 Write property test for summary serialization round-trip
    - **Property 9: Summary serialization round-trip**
    - **Validates: Requirements 5.2**
    - Over `st_catalog()`, parse the rendered JSON back and assert every spec's
      fields match the in-memory model.
    - `@settings(max_examples=100)`.

- [x] 8. Implement the CLI I/O shell and drift check
  - [x] 8.1 Implement `main(argv=None)` with argparse and write/check flow
    - Wire `--specs-root`, `--output`, `--metadata`, `--summary`, `--check`
      arguments per the design CLI table.
    - Pre-check specs root existence/type (exit 1 on missing/non-dir); run the
      pipeline; in write mode render the full index string then a single
      `write_text`, plus the optional summary; in `--check` mode compare committed
      vs fresh without writing.
    - Return 0 on success / in-sync, 1 on any detected error or drift; route all
      error messages to `sys.stderr`. Add `if __name__ == "__main__"` entry point.
    - _Requirements: 4.1, 5.1, 5.3, 6.1, 6.2, 6.3, 6.4, 6.5, 8.1, 8.2, 8.3, 8.4, 8.5, 8.6, 9.1, 9.2_

  - [x] 8.2 Write property test for deterministic byte-identical generation
    - **Property 10: Deterministic, byte-identical generation**
    - **Validates: Requirements 7.1**
    - Over `st_spec_tree()` × `st_metadata()`, generate the index twice and assert
      byte-identical output.
    - `@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])`.

  - [x] 8.3 Write property test for strictly read-only operation
    - **Property 11: Strictly read-only over the spec catalog**
    - **Validates: Requirements 7.2, 7.3, 7.4, 6.1**
    - Hash all spec files before/after a write run and a `--check` run; assert spec
      dirs/docs unchanged and only the index/summary paths are created or modified.
    - `@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])`.

  - [x] 8.4 Write property test for drift detection
    - **Property 12: Drift detection**
    - **Validates: Requirements 6.2, 6.3, 6.5**
    - Over `st_catalog()`, write fresh index then `--check` exits 0; mutate index
      content or the spec set and assert `--check` reports drift, exits 1, writes
      nothing.
    - `@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])`.

- [x] 9. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 10. Write example, edge-case, and error-path unit tests
  - [x] 10.1 Write edge-case unit tests
    - Empty directory → `unknown` and still listed (1.5); `tasks.md` with prose but
      no checkbox → `unknown` (2.6); metadata absent → derived-only, empty
      relationships (3.6); `--check` with no index → exit 1 reporting missing (6.4).
    - _Requirements: 1.5, 2.6, 3.6, 6.4_

  - [x] 10.2 Write CLI and I/O example unit tests
    - Write mode creates index at configured path, exits 0 (4.1); provenance banner
      at top (4.6); `--summary` writes valid JSON (5.1); omitting `--summary` writes
      no summary (5.3); incomplete record → no summary + exit 1 (5.5); `--specs-root`
      (8.1), `--output` (9.2), `--check` (8.2) wiring; missing/file specs root →
      exit 1 (8.6); malformed metadata → exit 1 (8.8); default index path under
      `.kiro/` and not under `senzing-bootcamp/` (9.1).
    - _Requirements: 4.1, 4.6, 5.1, 5.3, 5.5, 8.1, 8.2, 8.6, 8.8, 9.1, 9.2_

  - [x] 10.3 Write CommonMark compliance smoke test
    - Generate an index from a small fixture catalog and run it through
      `validate_commonmark.py`; assert compliance (1-2 examples, not iterated).
    - _Requirements: 9.3_

- [x] 11. Create the curated metadata file
  - Create `.kiro/spec-catalog.yaml` with the documented schema: `status_overrides`,
    `supersessions` (list of `{supersedes, superseded}`), and `related` groups.
    Seed it with the known chains (e.g. `self-answering-questions-fix` →
    `self-answering-prevention-v2` → `self-answering-reinforcement`, and the
    `module-recap-document` / `module-recap-document-fix` related pair), ensuring
    every referenced identifier resolves to a discovered Spec_Directory.
  - _Requirements: 3.1, 3.2, 3.5_

- [x] 12. Generate the committed index and wire the CI drift gate
  - [x] 12.1 Generate the committed Spec_Index
    - Run `generate_spec_catalog.py` to produce `.kiro/SPEC_CATALOG.md` so the
      committed index matches the actual catalog.
    - _Requirements: 4.1, 9.1_

  - [x] 12.2 Add the drift-gate step to the CI workflow
    - Add a `generate_spec_catalog.py --check` step to
      `.github/workflows/validate-power.yml`, consistent with the existing `--check`
      / `--verify` gates (emit an `::error::` hint to regenerate on failure).
    - _Requirements: 6.1, 9.4_

- [x] 13. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional test sub-tasks and can be skipped for a faster
  MVP; core implementation tasks are never optional.
- Each task references specific requirement clauses for traceability.
- Each property test sub-task names the correctness property and the requirements it
  validates, runs ≥100 iterations (`@settings(max_examples=100)`), and is tagged
  `# Feature: spec-catalog-index, Property N: ...`.
- Tests follow `test_generate_docs_index.py` conventions: `sys.path` import,
  class-based organization, `st_`-prefixed strategies, and
  `suppress_health_check=[HealthCheck.function_scoped_fixture]` when materializing
  temp trees.
- The generator is stdlib-only (Python 3.11+) and strictly read-only over the spec
  catalog; it writes only the configured index and optional summary paths.

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1"] },
    { "id": 1, "tasks": ["2.1"] },
    { "id": 2, "tasks": ["2.2", "2.3", "2.4"] },
    { "id": 3, "tasks": ["3.1", "3.2"] },
    { "id": 4, "tasks": ["3.3", "4.1", "4.4"] },
    { "id": 5, "tasks": ["4.2", "4.3", "4.5"] },
    { "id": 6, "tasks": ["6.1", "6.2"] },
    { "id": 7, "tasks": ["6.3", "6.4", "6.5", "7.1"] },
    { "id": 8, "tasks": ["7.2", "8.1"] },
    { "id": 9, "tasks": ["8.2", "8.3", "8.4", "10.1", "10.2", "10.3"] },
    { "id": 10, "tasks": ["11"] },
    { "id": 11, "tasks": ["12.1"] },
    { "id": 12, "tasks": ["12.2"] }
  ]
}
```
