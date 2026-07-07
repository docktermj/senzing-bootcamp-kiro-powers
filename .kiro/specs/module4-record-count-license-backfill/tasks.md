# Implementation Plan: Module 4 Record-Count License Back-fill

## Overview

Implement `senzing-bootcamp/scripts/record_count_backfill.py`, a stdlib-only, pure, non-blocking
helper that Module 4 runs after data collection. It reads the collected registry
(`config/data_sources.yaml`) and the Module-1 license state (`config/bootcamp_preferences.yaml`),
computes the real **Collected_Count** (tracking unknown sources rather than zeroing them), compares
it to the built-in 500-record **Evaluation_Limit**, and decides whether to surface the *existing*
Module 1 Steps 6b–6e license guidance. Guidance wording is delegated verbatim to the canonical
`volume_utils.build_license_framing`; markers are updated through the existing `preferences_utils`
writer — no parallel flow, no new preference key, no re-authored license text.

Work proceeds bottom-up: script scaffolding and dataclasses first, then the pure
counting/comparison/decision functions (each with its property test placed right after
implementation), then rendering and marker updates, then the orchestrating non-blocking `main`,
then the Module 4 Step 8a steering wiring, and finally the structural guardrail and end-to-end
integration tests. All code targets Python 3.11+ stdlib only (no PyYAML) and follows the project
script/test conventions; property tests use the project's registered Hypothesis profiles and all
fixtures are synthetic and PII-free.

## Tasks

- [x] 1. Scaffold the back-fill script
  - [x] 1.1 Create `record_count_backfill.py` skeleton, enum, and dataclasses
    - Create `senzing-bootcamp/scripts/record_count_backfill.py` with shebang,
      `from __future__ import annotations`, a module docstring with usage examples, stdlib-only
      imports, and the `sys.path` insertion needed to import `data_sources`, `preferences_utils`,
      and `volume_utils` (scripts are not a package)
    - Define `EVALUATION_LIMIT: int = 500` (mirroring `volume_utils.TIER_BOUNDARIES[TIER_DEMO]`),
      the `Module1GuidanceState` str-Enum (`DELIVERED` / `DEFERRED` / `SKIPPED`), and the
      `SourceCount`, `CollectedCount` (with `is_complete` property), `LimitComparison`, and
      `BackfillDecision` frozen dataclasses exactly as specified in the design's Components section
    - Add an `argparse`-based `main(argv=None) -> int` stub with `--registry`, `--preferences`,
      `--progress`, `--row-count`, and `--step` options defaulting to the canonical paths, plus an
      `if __name__ == "__main__": main()` entry point
    - _Requirements: 1.1, 4.2_

- [x] 2. Implement the counting functions
  - [x] 2.1 Implement `count_file_rows` and `compute_collected_count`
    - Implement `count_file_rows(file_path: str, fmt: str) -> int | None`: a line tally for `csv`
      (minus one header line) and `jsonl` that never retains field values, returns `None` for
      formats it cannot cheaply count and on any `OSError`/decode error, and never raises
    - Implement `compute_collected_count(registry, *, row_count=False, workspace_root=None) ->
      CollectedCount`: build the per-source breakdown reading only `name`, `record_count`,
      `file_path`, `format`; a non-null count is `counted_from="metadata"`, a null count is
      `"unknown"` unless `row_count` resolves it via `count_file_rows` (`"row_count"`); `known_total`
      sums only resolved counts and unknown sources are listed, never zeroed
    - _Requirements: 1.1, 1.2, 4.2_

  - [x] 2.2 Write property test for Collected_Count summing and unknown-tracking
    - **Property 1: Collected_Count sums known counts and tracks unknowns without zeroing** — for
      any registry of sources with non-negative-integer or `null` `record_count`,
      `compute_collected_count` returns `known_total` equal to the sum of exactly the non-null
      counts and `unknown_sources` equal to exactly the null-count source names; enabling row-count
      only moves a source from unknown to counted, never changing an already-known count
    - Add an `st_registry()` strategy that renders synthetic, PII-free sources to the restricted
      registry YAML so `parse_registry_yaml` round-trips them
    - **Validates: Requirements 1.1, 1.2**

- [x] 3. Implement state classification and limit comparison
  - [x] 3.1 Implement `classify_module1_state` and `compare_to_limit`
    - Implement `classify_module1_state(preferences: dict) -> Module1GuidanceState`: `DELIVERED`
      when `license` is set, else `DEFERRED` when `license_guidance_deferred` is truthy, else
      `SKIPPED` (`DELIVERED` takes precedence over `DEFERRED`)
    - Implement `compare_to_limit(collected, limit=EVALUATION_LIMIT) -> LimitComparison`:
      `over_limit = known_total > limit`; `certain = over_limit or collected.is_complete`
    - _Requirements: 1.2, 2.1, 2.3_

- [x] 4. Implement the back-fill decision
  - [x] 4.1 Implement `decide_backfill`
    - Implement `decide_backfill(collected, module1_state, limit=EVALUATION_LIMIT, *,
      computable=True) -> BackfillDecision`: `present_guidance` is `True` iff
      `computable and over_limit and certain and module1_state in {SKIPPED, DEFERRED}`;
      `already_guided = (module1_state is DELIVERED)`; populate `reason` with counts and source
      names only
    - _Requirements: 2.1, 2.2, 2.3_

  - [x] 4.2 Write property test for the present/suppress truth table
    - **Property 2: The present/suppress decision matches the exact truth table** — for any
      `CollectedCount` and any `Module1GuidanceState`, `decide_backfill` sets `present_guidance`
      true iff the count certainly exceeds 500 and the state is `SKIPPED`/`DEFERRED`; false whenever
      the state is `DELIVERED` and whenever the certain count is at or below 500 (including exactly
      500)
    - Add `st_collected_count()` (spanning below, exactly at, and above 500 with optional unknowns)
      and `st_module1_state()` strategies; explicitly exercise the exact-500 boundary and the
      `DELIVERED` short-circuit
    - **Validates: Requirements 2.1, 2.2, 2.3**

- [x] 5. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 6. Implement guidance rendering and marker updates
  - [x] 6.1 Implement `render_backfill_guidance`
    - Implement `render_backfill_guidance(decision, ctx: LicenseFramingContext) -> str | None`:
      return `volume_utils.build_license_framing(**ctx-fields)` when `decision.present_guidance`,
      else `None`; add no new license text (the wording is the reused canonical framing)
    - _Requirements: 3.1, 3.2_

  - [x] 6.2 Write property test for reused-framing equivalence
    - **Property 3: Rendered guidance is exactly the reused canonical framing** — for any
      `LicenseFramingContext` and a decision with `present_guidance` true,
      `render_backfill_guidance` returns a string identical to `volume_utils.build_license_framing`
      called with the same context, and returns `None` when `present_guidance` is false
    - Add an `st_framing_context()` strategy (optional capacity/validity, in-flow/existing-license
      flags)
    - **Validates: Requirements 3.1, 3.2**

  - [x] 6.3 Implement `apply_guidance_markers`
    - Implement `apply_guidance_markers(decision, *, preferences_path, progress_path, step_number)
      -> None`: when guidance was presented and acted on, update the same `license` /
      `license_guidance_deferred` markers Module 1 uses through the existing `preferences_utils`
      writer (introducing no new marker key) and write the Step 8a checkpoint to
      `bootcamp_progress.json`; the operation is idempotent and does not raise on write failure
    - _Requirements: 3.3_

  - [x] 6.4 Write property test for idempotent Module-1 marker updates
    - **Property 4: Marker updates are idempotent and use the Module 1 markers** — for any starting
      preferences state and a present-guidance decision, running `apply_guidance_markers` twice
      leaves the preferences and progress files byte-identical to their post-first-run state and
      sets only the existing `license` / `license_guidance_deferred` markers (no new key)
    - **Validates: Requirements 3.3**

- [x] 7. Implement `main` orchestration with non-blocking error handling
  - [x] 7.1 Wire read → compute → decide → emit in `main`
    - In `main`, read the registry (`data_sources.parse_registry_yaml` + `apply_migrations` +
      `validate_registry` + `_dict_to_registry`) and preferences
      (`preferences_utils.load_preferences`), call `compute_collected_count`, `classify_module1_state`,
      `compare_to_limit`, and `decide_backfill`, and print the `BackfillDecision` as machine-readable
      JSON (counts and source names only) on stdout
    - Wrap the body in a top-level guard that, on any failure (missing/unreadable/malformed registry
      or preferences), warns to stderr, emits a `computable=false` decision, and returns 0 so
      Module 4 falls back to Prose_Count behavior
    - _Requirements: 2.1, 4.1, 4.2_

  - [x] 7.2 Write property test for non-blocking fallback on bad input
    - **Property 5: Uncomputable or malformed input warns and continues (non-blocking)** — for any
      missing, unreadable, or malformed registry or preferences input, `main` never raises, returns
      exit code 0, and emits a decision with `computable` false
    - Add an `st_malformed_input()` strategy (absent files, invalid YAML, schema-invalid registries)
    - **Validates: Requirements 4.1**

  - [x] 7.3 Write property test for no-PII output
    - **Property 6: Only counts and source names leave the helper (no PII)** — for any registry
      whose entries embed arbitrary sentinel values in fields the helper does not read, the emitted
      `BackfillDecision` JSON and the preference/progress markers contain only source names, counts,
      and fixed guidance text — never any sentinel value
    - Extend `st_registry()` with a sentinel-seeding variant
    - **Validates: Requirements 4.2**

  - [x] 7.4 Write unit / example tests for the named scenarios
    - Cover the scenarios Requirement 5.1 names: over-limit + Module 1 skipped → `present_guidance:
      true`; under-limit and exactly 500 → `present_guidance: false`; guidance already delivered →
      `present_guidance: false`, `already_guided: true`; missing/unreadable metadata →
      `computable: false`, exit 0; and row-count resolution of an unknown source from a small
      synthetic `csv`/`jsonl` fixture
    - _Requirements: 5.1_

- [x] 8. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 9. Wire the back-fill into the Module 4 steering flow
  - [x] 9.1 Add Step 8a to `module-04-data-collection.md`
    - Insert a new **Step 8a** after Step 8 (Update data source tracking) and before Step 9
      (Transition to Module 5) that invokes `python senzing-bootcamp/scripts/record_count_backfill.py`
      after collection; on `present_guidance: true` surface the existing Module 1 Steps 6b–6e
      guidance using the canonical framing and the Senzing MCP server, then update the same
      `license` / `license_guidance_deferred` markers; on `false` do not re-present; on
      `computable: false` note the warning and continue on Prose_Count behavior
    - Document that the step is non-blocking and always proceeds to Step 9, and add the Step 8a
      checkpoint to `config/bootcamp_progress.json`; introduce no hook and no per-write invocation
    - _Requirements: 2.1, 2.2, 2.3, 3.3_

  - [x] 9.2 Write structural guardrail tests
    - Assert the helper introduces no new preference key and renders guidance through
      `volume_utils.build_license_framing` (no duplicated license text), and that
      `module-04-data-collection.md` Step 8a invokes `record_count_backfill.py` after collection
      and before the Module 5 transition
    - _Requirements: 3.1, 3.3_

- [x] 10. End-to-end integration
  - [x] 10.1 Write the end-to-end integration test
    - Wire the real registry parser, real `preferences_utils`, real
      `volume_utils.build_license_framing`, and the real back-fill script against a temp workspace:
      seed a `data_sources.yaml` whose collected counts exceed 500 plus a deferred-state
      preferences file, run `main`, and assert the emitted decision presents guidance and that
      `apply_guidance_markers` updates the same Module 1 markers — with no fixture PII appearing in
      any output. Use synthetic, PII-free fixtures only
    - _Requirements: 5.1, 5.2, 4.2_

- [x] 11. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional test sub-tasks and can be skipped for a faster MVP.
- Property tests use Hypothesis with the project's registered profiles (`fast` locally, `thorough`
  in CI); do not hand-set `@settings(max_examples=...)` to restate the baseline.
- Tests live in `senzing-bootcamp/tests/` (suggested `test_record_count_backfill.py`), are
  class-based, and import scripts via the `sys.path` convention.
- Each property task references its property number and the requirement clause it validates for
  traceability; custom strategies are prefixed `st_`.
- Python 3.11+ stdlib only (no PyYAML): reuse `data_sources`, `preferences_utils`, and `volume_utils`
  for all registry/preferences/framing plumbing — no new preference key and no duplicated license
  text.
- All fixtures are synthetic and PII-free (Requirement 4.2 and the power-distribution safety rule);
  only counts and source names ever leave the helper.

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1"] },
    { "id": 1, "tasks": ["2.1", "9.1"] },
    { "id": 2, "tasks": ["3.1", "2.2"] },
    { "id": 3, "tasks": ["4.1", "9.2"] },
    { "id": 4, "tasks": ["6.1", "4.2"] },
    { "id": 5, "tasks": ["6.3", "6.2"] },
    { "id": 6, "tasks": ["7.1", "6.4"] },
    { "id": 7, "tasks": ["7.2"] },
    { "id": 8, "tasks": ["7.3"] },
    { "id": 9, "tasks": ["7.4"] },
    { "id": 10, "tasks": ["10.1"] }
  ]
}
```
