






a# Implementation Plan: Steering Budget Headroom

## Overview

This plan reduces the worst-case loaded steering footprint of the four largest
reference-style steering files by slicing each monolith into context-relevant pieces,
across two cooperating workstreams plus an index/budget reconciliation pass:

1. **Generator workstream (automated).** Extend the stdlib-only, deterministic
   `senzing-bootcamp/scripts/sync_hook_registry.py` so `--write` emits one small
   per-module hook slice per non-empty module bucket (`hook-registry-module-NN.md`)
   plus a `hook-registry-module-any.md` slice instead of the single 10,631-token
   `hook-registry-modules.md`. The summary (`hook-registry.md`) is updated to route the
   agent to the correct per-module slice, the critical file's cross-reference is
   updated, the deprecated monolith is handled as an orphan (removed on `--write`,
   flagged on `--verify`), and the `--output-modules` CLI option is replaced by
   steering-dir-derived slice paths.

2. **Content workstream (manual).** Refactor `module-completion.md` into a lightweight
   Module_Completion_Root (ordering overview + slice manifest) plus cohesive slices
   (`module-completion-artifacts.md`, `module-completion-error-handling.md`,
   `module-completion-next-steps.md`, `module-completion-track.md`), each with
   `inclusion: manual` frontmatter, kebab-case naming, under `senzing-bootcamp/steering/`,
   no external URLs.

3. **Index/budget reconciliation.** Update `steering-index.yaml` keyword routes and
   `file_metadata` (remove the monolith, add the slices + root), run `measure_steering.py`
   to rebuild `file_metadata` + `budget.total_tokens`, and confirm CI gates stay green
   (`sync_hook_registry.py --verify`, `measure_steering.py --check`, `validate_commonmark.py`).

The work proceeds test-driven and incrementally: generator slicing functions with their
property tests first, then summary/critical updates and write/verify/CLI wiring, then a
`--write` regeneration, then the hand-authored module-completion refactor, then the
steering-index routing + `file_metadata` updates, then the `measure_steering.py`
reconciliation, then verification checkpoints that all CI gates pass.

The seven correctness properties are scoped to the generator slicing logic and are each
implemented as a Hypothesis property test (≥100 iterations, tagged
`# Feature: steering-budget-headroom, Property N: ...`) in
`senzing-bootcamp/tests/test_sync_hook_registry_properties.py`. Per the testing
convention, all test sub-tasks are marked optional (`*`); core implementation tasks are
never optional. The change is footprint reduction, not content removal, so
`budget.total_tokens` continues to reflect the full corpus.

## Tasks

- [x] 1. Add slice path/naming helper and deprecated-path constant
  - In `senzing-bootcamp/scripts/sync_hook_registry.py`, add
    `module_slice_filename(key: int | str) -> str` returning a deterministic kebab-case
    filename: numbered modules → `hook-registry-module-NN.md` (zero-padded two digits),
    the unmapped group → the distinct `hook-registry-module-any.md`.
  - Add the `DEPRECATED_REGISTRY_PATHS = (REGISTRY_MODULES_PATH,)` constant naming the
    deprecated monolithic `hook-registry-modules.md` for orphan handling.
  - Keep stdlib-only imports, type hints (`X | None`), and Google-style docstrings.
  - _Requirements: 2.5, 8.1, 9.1_

- [x] 2. Implement per-module slice rendering
  - [x] 2.1 Implement `generate_module_slice`
    - Add `generate_module_slice(key, hooks, total_count) -> str` rendering one slice:
      `inclusion: manual` frontmatter, a module-scoped title/label heading, a short
      intro pointing back to `hook-registry.md` and `hook-registry-critical.md`, then the
      full prompt entry for each hook in `hooks` (already sorted by `categorize_hooks`),
      reusing `format_hook_entry` so a hook renders identically across slices. Normalize
      line endings to `\n`.
    - _Requirements: 2.1, 2.6, 3.1, 8.2, 8.4_

  - [x] 2.2 Write property test for slice frontmatter and content integrity
    - **Property 5: Slice frontmatter and content integrity**
    - **Validates: Requirements 8.2, 3.1, 8.4**
    - For any non-empty bucket, assert the slice begins with `---\ninclusion: manual\n---\n`,
      contains the module label heading, and for each member hook contains its bold ID,
      event flow, full prompt text (when present), and id/name/description bullets, with
      only `\n` line endings. `@settings(max_examples=100, ...)`.

  - [x] 2.3 Write property test for slice naming convention
    - **Property 4: Slice naming convention**
    - **Validates: Requirements 2.5, 8.1**
    - For any module bucket key, assert `module_slice_filename` is kebab-case ending in
      `.md`; numbered modules yield `hook-registry-module-NN.md` with a zero-padded
      two-digit number, and the unmapped group yields exactly
      `hook-registry-module-any.md`. `@settings(max_examples=100, ...)`.

  - [x] 2.4 Write property test for slice size composition
    - **Property 6: Slice size is the composition of its members**
    - **Validates: Requirements 2.4, 1.2, 1.4**
    - For any bucket, assert the slice's token estimate equals the sum of its member
      hook-entry renderings plus a fixed bounded header, and is monotonically
      non-decreasing as hooks are added. `@settings(max_examples=100, ...)`.

- [x] 3. Implement the bucket-to-slice map builder
  - [x] 3.1 Implement `build_module_slices`
    - Add `build_module_slices(module_hooks, steering_dir, total_count) -> dict[Path, str]`
      mapping each non-empty bucket from `categorize_hooks()` to its slice path
      (`steering_dir / module_slice_filename(key)`) and rendered content via
      `generate_module_slice`. Buckets are already non-empty, so a module with no hooks
      yields no slice (no empty file); `any` maps to `hook-registry-module-any.md`.
    - _Requirements: 2.1, 2.2, 2.3, 3.1, 10.3_

  - [x] 3.2 Write property test for slice coverage matching non-empty buckets
    - **Property 1: Slice coverage matches non-empty buckets**
    - **Validates: Requirements 2.1, 2.2, 10.3**
    - Extend `st_category_mapping` to exercise multi-module membership and the `any`
      bucket; assert the emitted slice key set equals exactly the non-empty buckets from
      `categorize_hooks` and no slice is emitted for a zero-hook bucket.
      `@settings(max_examples=100, ...)`.

  - [x] 3.3 Write property test for hook-ID union completeness and multi-module presence
    - **Property 2: Hook-ID union completeness and multi-module presence**
    - **Validates: Requirements 2.3, 3.1, 3.2**
    - Assert the union of hook IDs across the critical file and all module slices equals
      the source hook-ID set, and any multi-module hook has its full prompt present in
      each associated module's slice. `@settings(max_examples=100, ...)`.

  - [x] 3.4 Write property test for deterministic, order-independent rendering
    - **Property 3: Deterministic, order-independent rendering**
    - **Validates: Requirements 2.6, 6.1**
    - Assert rendering the slice set twice — and again from a reordered input list —
      produces byte-identical content for every slice path.
      `@settings(max_examples=100, ...)`.

- [x] 4. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 5. Update summary and critical generation to route to slices
  - [x] 5.1 Update `generate_registry_summary` routing instruction
    - Update the "Hook Creation" section to instruct the agent to resolve
      `current_module` from `config/bootcamp_progress.json` and load the matching
      `hook-registry-module-<NN>.md` (or `-any.md`) for full module prompts, and to fall
      back to this summary if the slice is missing. Keep listing every hook by ID, event
      flow, module label, and one-line description.
    - _Requirements: 5.1, 5.2, 3.4, 10.1_

  - [x] 5.2 Update `generate_registry_critical` cross-reference
    - Change the cross-reference line referencing `hook-registry-modules.md` to reference
      `hook-registry.md` (the summary/router).
    - _Requirements: 3.1, 5.6_

  - [x] 5.3 Write example test for the summary routing instruction
    - Assert `hook-registry.md` instructs resolving `current_module` from
      `config/bootcamp_progress.json` and loading the matching slice, and that it lists
      every hook. (Concrete example, not iterated.)
    - _Requirements: 5.1, 5.2, 3.4_

- [x] 6. Wire write/verify and replace the CLI option
  - [x] 6.1 Update `--write` to emit slices and remove the deprecated monolith
    - In `main`, replace the single `generate_registry_modules` write with iterating the
      `build_module_slices` map: write the summary, the critical file, and every slice;
      delete any `DEPRECATED_REGISTRY_PATHS` file that still exists; write the lockfile.
      Any `OSError`/`PermissionError` during write or delete causes a non-zero exit.
    - _Requirements: 6.1, 6.2, 6.6, 9.4, 10.3_

  - [x] 6.2 Update `--verify` with slice comparison and orphan detection
    - Regenerate the summary, critical, and slice set; compare each on disk byte-for-byte
      via `verify_registry`; additionally fail if any `DEPRECATED_REGISTRY_PATHS` file
      still exists (orphan) or a freshly generated slice is missing on disk. Exit 0 only
      when all match and no orphan exists; otherwise non-zero with a `FAIL:` line naming
      the offending path.
    - _Requirements: 6.3, 6.4, 6.5, 6.7, 9.4_

  - [x] 6.3 Replace the `--output-modules` CLI option with steering-dir derivation
    - Remove the `--output-modules` single-path option; derive slice paths from the
      steering directory (default `senzing-bootcamp/steering/`). Add a `--steering-dir`
      option (defaulting to the registry files' parent) so tests can target a temp
      directory. Keep `--write`/`--verify` semantics intact.
    - _Requirements: 6.2, 6.3, 9.1, 8.5_

  - [x] 6.4 Write property test for verify semantics including orphan detection
    - **Property 7: Verify semantics including orphan detection**
    - **Validates: Requirements 6.3, 6.4, 6.5**
    - For any generated content and on-disk state, assert `--verify` reports a match iff
      the file exists and is byte-identical, a non-match when missing or differing, and a
      non-match (orphan) when a deprecated registry path still exists.
      `@settings(max_examples=100, ...)`.

  - [x] 6.5 Write example test for deprecated-monolith handling
    - Assert `--write` removes a pre-existing `hook-registry-modules.md` and `--verify`
      fails when it is present. (Concrete example against a temp `--steering-dir`.)
    - _Requirements: 6.2, 6.3_

- [x] 7. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 8. Regenerate the sliced registry from source
  - Run `python senzing-bootcamp/scripts/sync_hook_registry.py --write` to emit
    `hook-registry.md` (updated router), `hook-registry-critical.md` (updated
    cross-reference), every `hook-registry-module-NN.md` and
    `hook-registry-module-any.md` slice, and the lockfile, and to remove the deprecated
    `hook-registry-modules.md`.
  - _Requirements: 6.2, 2.1, 2.2, 8.5, 10.3_

- [x] 9. Write the real-corpus slice size-bound example test
  - Run the generator against the actual `hooks/` + `hook-categories.yaml` and assert
    every emitted slice is ≤ 5,000 tokens (chars/4) and the largest is ≤ 5,315 (50% of
    10,631). (Data-dependent, so an example test, not iterated over random hooks.)
  - _Requirements: 2.4, 1.2, 1.4_

- [x] 10. Refactor module-completion into a root plus cohesive slices
  - [x] 10.1 Create the module-completion concern slices
    - Create `module-completion-artifacts.md` (Backfill, Recap Append, Bootcamp Journal,
      Module Completion Certificate, Summary Index), `module-completion-error-handling.md`
      (Non-Blocking Error Handling: per-step, 30s timeout, predecessor-failure, retry),
      `module-completion-next-steps.md` (Next-Step Options, Immediate Execution on
      Affirmative Response), and `module-completion-track.md` (Path Completion Detection,
      Path Completion Celebration). Move (do not delete) content from `module-completion.md`.
      Each begins with `inclusion: manual` frontmatter, uses kebab-case naming, lives
      under `senzing-bootcamp/steering/`, contains no external `http(s)` URLs, and stays
      ≤ 5,000 tokens.
    - _Requirements: 3.3, 3.5, 4.3, 4.4, 8.1, 8.2, 8.4, 8.5_

  - [x] 10.2 Rewrite `module-completion.md` as the Module_Completion_Root
    - Replace its body with the completion-step ordering overview, the Shared
      Boundary-Detection Trigger rules, and a manifest naming each slice and its single
      concern; instruct the agent to fall back to the Root if a referenced slice is
      missing. Keep `inclusion: manual` frontmatter; keep ≤ 5,000 tokens.
    - _Requirements: 4.1, 4.2, 4.5, 10.2, 8.2, 8.4_

  - [x] 10.3 Write example test for module-completion reachability
    - Assert each pre-refactor `##` section of `module-completion.md` is present in the
      Root or exactly one slice, and the Root manifest names each slice with its concern.
      (Concrete example against the refactored corpus.)
    - _Requirements: 3.3, 4.1, 4.4, 4.5_

- [x] 11. Update steering-index routing for the new slices
  - In `senzing-bootcamp/steering/steering-index.yaml` `keywords`: keep `hook`/`hooks` →
    `hook-registry.md` and `completion` → `module-completion.md`; add completion-concern
    routes (e.g. `recap`, `journal`, `certificate`, `artifact backfill` →
    `module-completion-artifacts.md`; `completion error` →
    `module-completion-error-handling.md`; `next step` → `module-completion-next-steps.md`;
    `track complete`, `path completion`, `celebration` → `module-completion-track.md`)
    using keys that do not collide with existing entries. Ensure every keyword route
    target names a file that exists in the corpus.
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.6_

- [x] 12. Reconcile file_metadata and budget
  - [x] 12.1 Rebuild `file_metadata` + `budget.total_tokens`
    - Run `python senzing-bootcamp/scripts/measure_steering.py` (update mode) to remove
      the `hook-registry-modules.md` entry, add entries for each
      `hook-registry-module-NN.md`, `hook-registry-module-any.md`, the
      Module_Completion_Root (updated count), and each Module_Completion_Slice, and set
      `budget.total_tokens` to the sum of `file_metadata` counts. Confirm
      `reference_window: 200000`, `warn_threshold_pct: 60`, `critical_threshold_pct: 80`,
      and `split_threshold_tokens: 5000` are retained.
    - _Requirements: 5.5, 7.1, 7.2, 7.4, 7.5_

  - [x] 12.2 Write config check that routes resolve and slices contain no external URLs
    - Assert every keyword route target in `steering-index.yaml` exists on disk and no
      new steering slice/root contains an external `http://` or `https://` URL.
    - _Requirements: 5.6, 8.4, 8.5_

- [x] 13. Final checkpoint - Verify all CI gates pass
  - Run `python senzing-bootcamp/scripts/sync_hook_registry.py --verify` (exit 0, no
    orphan), `python senzing-bootcamp/scripts/measure_steering.py --check` (exit 0), and
    `python senzing-bootcamp/scripts/validate_commonmark.py` (no violations) against the
    refactored corpus, then run the pytest suite. Ensure all tests pass, ask the user if
    questions arise.
  - _Requirements: 6.7, 7.3, 8.3, 9.3_

## Notes

- Tasks marked with `*` are optional test sub-tasks and can be skipped for a faster MVP;
  core implementation tasks are never optional.
- Each task references specific requirement clauses for traceability.
- The seven property tests cover only the generator slicing logic (Properties 1–7); the
  module-completion split, index routing, and budget reconciliation are content/config
  edits verified by `measure_steering.py --check`, `validate_commonmark.py`, and example
  tests, per the design's Testing Strategy.
- Each property test sub-task names the correctness property and the requirements it
  validates, runs ≥100 iterations (`@settings(max_examples=100, ...)`), and is tagged
  `# Feature: steering-budget-headroom, Property N: ...`.
- Tests extend `senzing-bootcamp/tests/test_sync_hook_registry_properties.py` and follow
  existing conventions: `sys.path` import shim, `st_`-prefixed strategies (`st_hook_id`,
  `st_hook_entry`, `st_unique_hook_entries`, `st_category_mapping` extended for
  multi-module membership and the `any` bucket).
- The generator stays stdlib-only (Python 3.11+), deterministic, and uses the existing
  minimal in-script YAML parsing approach.
- The refactor is footprint reduction, not content removal: `budget.total_tokens`
  continues to reflect the full corpus.

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1"] },
    { "id": 1, "tasks": ["2.1"] },
    { "id": 2, "tasks": ["2.2", "2.3", "2.4", "3.1"] },
    { "id": 3, "tasks": ["3.2", "3.3", "3.4", "5.1", "5.2"] },
    { "id": 4, "tasks": ["5.3", "6.1", "6.2", "6.3"] },
    { "id": 5, "tasks": ["6.4", "6.5"] },
    { "id": 6, "tasks": ["8"] },
    { "id": 7, "tasks": ["9", "10.1"] },
    { "id": 8, "tasks": ["10.2"] },
    { "id": 9, "tasks": ["10.3", "11"] },
    { "id": 10, "tasks": ["12.1"] },
    { "id": 11, "tasks": ["12.2"] }
  ]
}
```
