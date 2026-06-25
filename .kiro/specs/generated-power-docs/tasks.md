# Implementation Plan: Generated POWER.md Docs

## Overview

Build a single deterministic generator, `senzing-bootcamp/scripts/generate_power_docs.py`, that
regenerates the four volatile sections of `POWER.md` (MCP tools, hooks, steering files, modules) in
place between marker comments, preserves hand-written prose byte-for-byte, and exposes
`--write` (default) / `--verify` modes mirroring `sync_hook_registry.py`. The implementation is
stdlib-only (PyYAML permitted where YAML is parsed), produces CommonMark-compliant Unix-newline
output, keeps `check_mcp_tool_inventory()` green, and is wired into CI before the pytest step.

Tasks are incremental and test-driven: data models and pure helpers first, then per-region
renderers, then the orchestration/CLI, then bring-up (adding markers to the real `POWER.md` and
regenerating), then CI and documentation. Each region renderer ships with its error-path checks and
property tests close to its implementation so drift and invariant violations are caught early.

## Tasks

- [x] 1. Establish module skeleton, data models, and shared helpers
  - [x] 1.1 Create `generate_power_docs.py` skeleton with conventions and data models
    - Create `senzing-bootcamp/scripts/generate_power_docs.py` with `from __future__ import annotations`, a module docstring documenting the `--write` / `--verify` usage, and the `if __name__ == "__main__": main()` guard, matching `sync_hook_registry.py`
    - Import only stdlib at module top level; import `yaml` only where YAML is parsed
    - Define the frozen dataclasses `SourcePaths`, `HookInfo`, `SteeringFileInfo`, `ModuleInfo`, `Sources`, `RegionSpan`, `VerifyResult` (with `ok`/`drift_count` properties), and the `GeneratorError` and `MarkerError` exception types
    - Define default `SourcePaths` resolved relative to the repository root (real paths), overridable for tests
    - _Requirements: 6.1, 6.2_

  - [x] 1.2 Implement `normalize_newlines` and `write_atomic`
    - `normalize_newlines(text)`: convert `\r\n` and bare `\r` to `\n` and ensure exactly one trailing `\n`
    - `write_atomic(path, content)`: write to a temp file in the same directory then `os.replace` over the target so no partial write is ever observable
    - _Requirements: 5.5, 5.6_

  - [x] 1.3 Write unit tests for newline normalization and atomic write
    - Assert CRLF/CR inputs produce LF-only output with a single trailing newline
    - Assert `write_atomic` replaces content fully and leaves no temp file behind
    - _Requirements: 5.5, 5.6_

- [x] 2. Implement marker scheme and region location
  - [x] 2.1 Implement the marker regex and `locate_regions`
    - Define anchored, whitespace-tolerant begin/end marker regexes (`^<!--\s*BEGIN GENERATED:\s*(?P<id>[a-z0-9-]+)\s*-->\s*$` and the END analogue)
    - Implement `locate_regions(doc, expected_ids) -> dict[str, RegionSpan]` that scans all markers in order and returns a `RegionSpan` per region (offsets after begin / before end, plus current body text)
    - Raise `MarkerError(region_id, reason)` for: missing begin/end for an expected id, begin without matching end, end before its begin, duplicate begin id
    - _Requirements: 2.1, 2.4, 2.5, 2.6, 2.7_

  - [x] 2.2 Write unit tests for marker matching and `locate_regions` violations
    - Assert markers match the HTML-comment regex and region ids are parsed and unique
    - Assert each marker-integrity violation raises `MarkerError` naming the affected region id
    - _Requirements: 2.1, 2.4, 2.5, 2.6, 2.7_

- [x] 3. Implement source loading and the region renderer interface
  - [x] 3.1 Implement `load_sources` and the `Region` interface
    - Implement `load_sources(paths) -> Sources`: import `mcp_tool_inventory` (`ALL_TOOLS`, `TOTAL_COUNT`) via the established `sys.path` convention; discover `hooks/*.kiro.hook` via `sorted(glob(...))` and parse `hook-categories.yaml`; parse `steering-index.yaml` (`file_metadata`, `budget.total_tokens`); parse `config/module-dependencies.yaml` (`modules`)
    - On any read failure (`OSError`) or parse failure (`yaml.YAMLError` / import error), raise an error naming the file path and cause; never write
    - Define the `Region` protocol (`region_id`, pure `render(sources) -> str`) and `kiro_include(repo_root, path)` emitting `#[[file:<repo-relative-path>]]`
    - _Requirements: 1.5, 1.6, 5.3, 6.2_

  - [x] 3.2 Write unit tests for source-load error paths and `kiro_include`
    - Assert unreadable/unparseable sources raise an error naming the file path and cause and write nothing
    - Assert `kiro_include` emits `#[[file:<repo-relative-path>]]`
    - _Requirements: 1.5, 5.3_

- [x] 4. Implement the MCP tools region
  - [x] 4.1 Implement `McpToolsRegion`
    - Embed the static `TOOL_DESCRIPTIONS` presentation map; assert `set(ALL_TOOLS)` is a subset of its keys with no extra keys (tool without a description is a hard error)
    - Render one bullet per tool in `ALL_TOOLS` tuple order with the exact shape `` - `tool_name` — description `` so `validate_power.py`'s `_power_md_tool_bullets` regex extracts exactly the tool names
    - If `TOTAL_COUNT != len(ALL_TOOLS)`, raise `GeneratorError` reporting both numbers; never write
    - _Requirements: 1.1, 9.1, 9.2, 9.3, 9.4_

  - [x] 4.2 Write unit tests for MCP tools region error paths
    - Assert `TOTAL_COUNT` mismatch reports both values and aborts non-zero
    - Assert a tool missing a description-map entry names the tool and aborts non-zero
    - _Requirements: 9.1, 9.4_

- [x] 5. Implement the hooks region
  - [x] 5.1 Implement `HooksRegion`
    - Render a count line equal to the number of discovered `*.kiro.hook` files plus one entry per hook
    - Mark hooks listed under `critical:` in `hook-categories.yaml` with `⭐`; order critical hooks first (alphabetical by hook id), then the remainder (alphabetical) — hook id as deterministic tie-breaker
    - Cross-check: every hook id named in `hook-categories.yaml` must have a matching file (Req 10.4); every discovered file must appear in at least one category list (Req 10.5); either inconsistency names the offending hook and aborts non-zero
    - _Requirements: 1.2, 10.1, 10.2, 10.3, 10.4, 10.5_

  - [x] 5.2 Write unit tests for hooks region cross-check error paths
    - Assert a category-listed hook with no file names the hook and aborts non-zero
    - Assert a discovered file in no category list names the hook and aborts non-zero
    - _Requirements: 10.4, 10.5_

- [x] 6. Implement the steering files region
  - [x] 6.1 Implement `SteeringRegion`
    - Render a table with one row per `file_metadata` entry, sorted alphabetically by filename, emitting filename, `token_count`, and `size_category` exactly as recorded
    - Emit a footer line with `budget.total_tokens` verbatim
    - Verify each listed steering filename exists under `senzing-bootcamp/steering/`; a missing referenced file names the path and aborts non-zero
    - A `file_metadata` entry missing `token_count` or `size_category` names the file and the missing field and aborts non-zero
    - _Requirements: 1.3, 5.4, 11.1, 11.2, 11.3, 11.4, 11.5_

  - [x] 6.2 Write unit tests for steering region error paths
    - Assert an entry missing `token_count`/`size_category` names the file and missing field and aborts non-zero
    - Assert a missing referenced steering file names the path and aborts non-zero
    - _Requirements: 5.4, 11.5_

- [x] 7. Implement the modules region
  - [x] 7.1 Implement `ModulesRegion`
    - Render a table with one row per `modules` entry ordered by module number ascending (numeric sort), emitting number and `name` exactly as recorded
    - Emit a count line equal to the number of rows / recorded modules
    - A module missing its number or `name` names the offender and the missing field and aborts non-zero
    - _Requirements: 1.4, 12.1, 12.2, 12.3, 12.4, 12.5_

  - [x] 7.2 Write unit tests for modules region error paths
    - Assert a module missing its number/name names the offender and missing field and aborts non-zero
    - Assert rows are emitted in ascending module-number order
    - _Requirements: 12.3, 12.5_

- [x] 8. Checkpoint - region renderers complete
  - Ensure all tests pass, ask the user if questions arise.

- [x] 9. Implement orchestration: render, assemble, verify
  - [x] 9.1 Implement `render_all` and `assemble`
    - `render_all(sources, regions)`: iterate the fixed, ordered region list and return `region_id -> body`
    - `assemble(doc, spans, bodies)`: replace each region body in place using `RegionSpan` offsets, leaving markers and all out-of-region bytes byte-for-byte unchanged
    - _Requirements: 2.2, 2.3, 8.1_

  - [x] 9.2 Implement `verify`
    - `verify(doc, spans, bodies) -> VerifyResult`: per-region byte comparison of committed body vs rendered body; record drifted and missing region ids; never open any file for writing
    - A region the generator produces but absent from `POWER.md` is treated as drifted/missing
    - _Requirements: 3.1, 3.4, 3.7, 4.3, 8.2_

  - [x] 9.3 Write unit tests for assemble prose preservation and verify results
    - Assert `assemble` mutates only region bodies and leaves markers/prose unchanged
    - Assert `verify` reports exactly the drifted/missing region ids and a matching drift count
    - _Requirements: 2.2, 2.3, 3.1, 3.7_

- [x] 10. Implement CommonMark validation hook and the `main` CLI
  - [x] 10.1 Wire CommonMark validation into Write_Mode
    - Before atomic write, validate the fully assembled, newline-normalized document via `validate_commonmark.py`; on failure report the validation failure, perform no partial write, leave `POWER.md` unchanged, and exit non-zero
    - _Requirements: 5.1, 5.7_

  - [x] 10.2 Implement `main(argv=None)` with argparse and mode wiring
    - Add a mutually exclusive `--write` (default) / `--verify` group plus optional `--power-md` and source-path overrides for testing
    - Write_Mode: load sources -> render all -> locate regions -> assemble -> normalize -> validate -> `write_atomic`; return 0 on success
    - Verify_Mode: load sources -> render -> locate -> compare; on drift print every drifted/missing region id, the drift count, and the exact runnable `--write` regeneration command, exit 1; on clean print success and exit 0; if `POWER.md` is missing/unreadable report it and exit non-zero without modifying any file
    - Catch `GeneratorError`/`MarkerError`/OS/parse errors in `main`, print cause to stderr, return non-zero; never leak tracebacks; reject unknown args via argparse
    - _Requirements: 3.2, 3.3, 3.5, 3.6, 6.5, 6.6, 6.7, 8.1, 8.2, 8.3, 8.4, 8.6_

  - [x] 10.3 Write unit tests for CLI behavior and drift/verify messaging
    - Assert `main([])` defaults to write and returns 0; `main(['--verify'])` verifies only; `main(['--bogus'])` returns non-zero with a stderr message; `--write`/`--verify` are mutually exclusive
    - Assert a forced drift prints the exact runnable `--write` command (Req 3.5) and that verify on a missing `POWER.md` returns non-zero and touches nothing (Req 3.6)
    - _Requirements: 3.5, 3.6, 6.5, 6.6, 6.7, 8.3, 8.4, 8.6_

- [x] 11. Bring-up: add markers to the real POWER.md and regenerate
  - [x] 11.1 Insert marker comment pairs into the existing volatile sections of `POWER.md`
    - Add `BEGIN GENERATED` / `END GENERATED` HTML-comment marker pairs around the existing MCP tools, hooks, steering files, and modules sections in `senzing-bootcamp/POWER.md`, keeping all surrounding hand-written prose intact
    - _Requirements: 2.1, 2.2, 2.3_

  - [x] 11.2 Run Write_Mode and confirm clean state
    - Run `python senzing-bootcamp/scripts/generate_power_docs.py --write`, then `--verify` to confirm exit 0, and confirm `validate_power.py` (`check_mcp_tool_inventory()`) stays green
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 4.2, 9.3_

- [x] 12. Property-based tests for the correctness properties
  - [x] 12.1 Create property test scaffolding and world generators
    - Create `senzing-bootcamp/tests/test_generate_power_docs_properties.py` and shared fixtures/strategies in `senzing-bootcamp/tests/conftest.py`
    - Implement a Hypothesis `make_world(...)` strategy producing a self-consistent set of sources (tool list, hook files + categories, steering index, modules map) plus a `POWER.md` skeleton with the four marker pairs and random surrounding prose, written under `tmp_path`
    - Configure each property test with `@settings(max_examples=100)` (or higher); tag each with a comment `Feature: generated-power-docs, Property N: <text>`
    - _Requirements: 6.4_

  - [x] 12.2 Property 1: Write idempotency
    - **Property 1: Write idempotency** — two successive Write_Mode runs against identical sources produce byte-identical `POWER.md`
    - **Validates: Requirements 4.1, 8.1**

  - [x] 12.3 Property 2: Write-then-verify round-trip is clean
    - **Property 2: Write-then-verify round-trip is clean** — Write then Verify against unchanged sources reports success and exits 0
    - **Validates: Requirements 3.1, 3.3, 4.2, 6.6, 8.2**

  - [x] 12.4 Property 3: Prose preservation
    - **Property 3: Prose preservation** — Write_Mode mutates only region bodies; every byte outside regions (and the marker lines) is unchanged
    - **Validates: Requirements 2.2, 2.3**

  - [x] 12.5 Property 4: Determinism independent of environment and source order
    - **Property 4: Determinism independent of environment and source order** — identical bytes under permuted source enumeration order and mutated `LC_ALL`/`TZ`/monkeypatched glob/clock
    - **Validates: Requirements 4.4, 4.5, 9.2, 12.3**

  - [x] 12.6 Property 5: Per-region content correctness
    - **Property 5: Per-region content correctness** — mcp-tools set equals `set(ALL_TOOLS)` and keeps `check_mcp_tool_inventory()` green; one hook entry per file with correct count and critical marks; one steering row per `file_metadata` entry with recorded `token_count`/`size_category` and budget footer; one module row per recorded module with number/name, ascending order, and matching count
    - **Validates: Requirements 1.1, 1.2, 1.3, 1.4, 9.1, 9.3, 10.1, 10.2, 10.3, 11.1, 11.2, 11.3, 11.4, 12.1, 12.2, 12.3, 12.4**

  - [x] 12.7 Property 6: Drift detection reports exactly the changed regions
    - **Property 6: Drift detection reports exactly the changed regions** — mutating/deleting a subset of regions makes Verify_Mode report exactly that subset, a matching drift count, and exit 1
    - **Validates: Requirements 3.1, 3.2, 3.7, 4.3**

  - [x] 12.8 Property 7: Verify never mutates the filesystem
    - **Property 7: Verify never mutates the filesystem** — for clean or drifted input, Verify_Mode leaves every file's bytes and the directory tree identical
    - **Validates: Requirements 3.4**

  - [x] 12.9 Property 8: Marker integrity violations abort without mutation
    - **Property 8: Marker integrity violations abort without mutation** — any recognized marker violation reports the region id, leaves `POWER.md` byte-for-byte unchanged, and exits non-zero
    - **Validates: Requirements 2.4, 2.5, 2.6, 2.7**

  - [x] 12.10 Property 9: No partial write on any error
    - **Property 9: No partial write on any error** — any aborting Write_Mode error (unreadable/unparseable source, source invariant violation, missing referenced file, CommonMark failure) leaves `POWER.md` byte-for-byte unchanged and exits non-zero
    - **Validates: Requirements 1.5, 1.6, 5.7, 9.4, 12.5**

  - [x] 12.11 Property 10: Output newline normalization
    - **Property 10: Output newline normalization** — for prose with arbitrary CRLF/CR endings, the written document has no carriage returns and exactly one trailing line-feed
    - **Validates: Requirements 5.5, 5.6**

  - [x] 12.12 Property 11: Written output is CommonMark-valid
    - **Property 11: Written output is CommonMark-valid** — the `POWER.md` produced by Write_Mode passes `validate_commonmark.py`
    - **Validates: Requirements 5.1**

- [x] 13. Unit / example and smoke tests
  - [x] 13.1 Write unit and smoke/structure tests
    - Create `senzing-bootcamp/tests/test_generate_power_docs_unit.py` consolidating CLI, marker/format facts, drift message, verify-missing-`POWER.md`, and error-path examples (concrete malformed sources asserting the specific message naming the offending file/field/id and non-zero exit)
    - Smoke/structure: assert the script exists at `senzing-bootcamp/scripts/generate_power_docs.py`; an AST import scan asserts only stdlib top-level imports except `yaml`; assert `senzing-bootcamp/scripts/README.md` documents both the regenerate and verify invocations
    - _Requirements: 2.1, 3.5, 3.6, 5.2, 5.3, 6.1, 6.2, 6.4, 8.5, 9.4, 10.4, 10.5, 11.5, 12.5, 5.4, 1.5_

- [x] 14. CI integration
  - [x] 14.1 Add the `--verify` step to the CI workflow
    - In `.github/workflows/validate-power.yml`, add a Verify_Mode step running `python senzing-bootcamp/scripts/generate_power_docs.py --verify` in the `validate` job immediately before the "Run tests" step, mirroring the `sync_hook_registry.py --verify` wiring (failing branch echoes `::error::` with the exact `--write` regeneration command)
    - Confirm it runs across the existing `['3.11','3.12','3.13']` matrix with `fail-fast: false`
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

  - [x] 14.2 Write a CI-config test
    - Parse `.github/workflows/validate-power.yml` and assert the verify step exists before the pytest step, the failing branch echoes the exact `--write` command as a `::error::` message, and the matrix is `['3.11','3.12','3.13']` with `fail-fast: false`
    - _Requirements: 7.1, 7.4, 7.5_

- [x] 15. Documentation
  - [x] 15.1 Document regenerate and verify commands in the scripts README
    - Add `generate_power_docs.py` to `senzing-bootcamp/scripts/README.md` and document both the Write_Mode (regenerate) and Verify_Mode (verify) command invocations
    - _Requirements: 8.5_

- [x] 16. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional test sub-tasks and can be skipped for a faster MVP, though the property tests (12.2–12.12) are the primary correctness guarantee for this feature.
- Each task references specific requirements for traceability.
- Property tests use Hypothesis with a minimum of 100 examples and in-memory fixtures / `tmp_path` — no real cloud or network access.
- The implementation stays stdlib-only (PyYAML only where YAML is parsed) and ships entirely under `senzing-bootcamp/`.
- Checkpoints (tasks 8 and 16) ensure incremental validation.

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1"] },
    { "id": 1, "tasks": ["1.2", "1.3", "2.1"] },
    { "id": 2, "tasks": ["2.2", "3.1"] },
    { "id": 3, "tasks": ["3.2", "4.1", "5.1", "6.1", "7.1"] },
    { "id": 4, "tasks": ["4.2", "5.2", "6.2", "7.2", "9.1", "9.2"] },
    { "id": 5, "tasks": ["9.3", "10.1"] },
    { "id": 6, "tasks": ["10.2"] },
    { "id": 7, "tasks": ["10.3", "11.1"] },
    { "id": 8, "tasks": ["11.2", "12.1"] },
    { "id": 9, "tasks": ["12.2", "12.3", "12.4", "12.5", "12.6", "12.7", "12.8", "12.9", "12.10", "12.11", "12.12", "13.1"] },
    { "id": 10, "tasks": ["14.1", "15.1"] },
    { "id": 11, "tasks": ["14.2"] }
  ]
}
```
