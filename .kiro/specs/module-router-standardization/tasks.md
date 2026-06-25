# Implementation Plan: module-router-standardization

## Overview

This plan implements the thin Router_Root convention defined in the design. Work proceeds
in four logical layers: (1) the convention configuration (`router_ceiling`) plus the
measurer change that preserves it, (2) the new enforcement logic in `lint_steering.py`
(router identification, ceiling/doubles-as-phase rules, environment guard) and the
step-range coverage checker, (3) the content relocation that thins each non-compliant root
by MOVING workflow content into phase files (never deleting), and (4) index reconciliation,
loading-guide clarification, CI wiring, and end-state verification.

All changed and created files live under `senzing-bootcamp/` (everything there ships to
users). Steering files stay kebab-case `.md` with valid YAML frontmatter, remain
CommonMark-compliant, and contain no external URLs. Property-based tests use pytest +
Hypothesis (>= 100 iterations) and follow the existing `senzing-bootcamp/tests/` pattern
(`sys.path` insertion of the scripts dir, class-based organization, requirement-tagged
classes).

## Tasks

- [x] 1. Establish the Router_Ceiling configuration and preserve it through measurement
  - [x] 1.1 Add the `router_ceiling` budget key to the steering index
    - In `senzing-bootcamp/steering/steering-index.yaml`, add `router_ceiling: 1000` to the
      `budget` block, alongside the existing keys (`total_tokens`, `reference_window`,
      `warn_threshold_pct`, `critical_threshold_pct`, `split_threshold_tokens`)
    - _Requirements: 1.5, 1.6, 4.5_

  - [x] 1.2 Preserve `router_ceiling` in `measure_steering.update_index`
    - Extend `update_index` in `senzing-bootcamp/scripts/measure_steering.py` to read the
      existing `budget.router_ceiling` (like `split_threshold_tokens`) and re-emit it when
      rebuilding the `budget` block; default to `1000` when absent
    - Keep all other budget keys and behavior byte-identical where unchanged (stdlib-only,
      no PyYAML)
    - _Requirements: 4.5, 1.6_

  - [x] 1.3 Write property test for budget Router_Ceiling preservation
    - **Property 6: Budget Router_Ceiling preservation (round-trip)**
    - **Validates: Requirements 4.5**
    - New file `senzing-bootcamp/tests/test_budget_preservation.py`; generate budget blocks
      with the standard keys plus a `router_ceiling`, run `update_index`, assert every
      original key and the exact `router_ceiling` survive

- [x] 2. Implement router identification and enforcement in `lint_steering.py`
  - [x] 2.1 Add router parsing and ceiling lookup helpers
    - In `senzing-bootcamp/scripts/lint_steering.py`, add the `ModuleRouterInfo` dataclass
      (with `in_scope` and `doubles_as_phase` properties), a `parse_module_phase_files`
      helper that captures each module's `root` and its phase `file` values from the
      `modules:` section only, and `get_router_ceiling` (reads `budget.router_ceiling`,
      defaults to 1000); use the existing minimal YAML parsing style
    - _Requirements: 6.1, 2.1, 2.2_

  - [x] 2.2 Write property test for router identification and scope
    - **Property 1: Router identification and scope**
    - **Validates: Requirements 2.1, 2.2, 2.3, 6.1**
    - New file `senzing-bootcamp/tests/test_router_convention.py`; generate module entries
      (no phases, single phase == root, multiple phases) and assert in-scope iff a phase
      file differs from the root

  - [x] 2.3 Add the Python 3.11+ environment guard
    - Add a shared `require_runtime()` helper that verifies `sys.version_info >= (3, 11)`
      and that required stdlib modules import; call it at the start of `main()` so an
      unsupported runtime prints an environment error to stderr and exits non-zero rather
      than reporting success
    - _Requirements: 6.4, 6.6_

  - [x] 2.4 Implement `check_router_convention` and wire it into `run_all_checks`
    - Implement `check_router_convention(index_data, file_metadata, router_ceiling)` to emit
      an ERROR when an in-scope root's `token_count` exceeds the ceiling (message names root,
      token count, ceiling), an ERROR when the root filename appears among its module's phase
      files ("root-doubles-as-phase"), and an ERROR when an in-scope root has no measured
      `token_count`; register it in `run_all_checks` using `LintViolation` and existing
      exit-code conventions
    - _Requirements: 6.1, 6.2, 6.3, 6.5_

  - [x] 2.5 Write property test for Router_Ceiling enforcement
    - **Property 2: Router_Ceiling enforcement**
    - **Validates: Requirements 1.3, 1.6, 2.3, 2.4, 6.2**
    - Add to `senzing-bootcamp/tests/test_router_convention.py`; generate in-scope roots and
      ceilings (including boundary and one-over), assert a ceiling violation is emitted iff
      `token_count > ceiling` and the message names root, count, and ceiling

  - [x] 2.6 Write property test for root-doubles-as-phase enforcement
    - **Property 3: Root-doubles-as-phase enforcement**
    - **Validates: Requirements 2.5, 4.3, 6.3**
    - Add to `senzing-bootcamp/tests/test_router_convention.py`; assert a violation is
      emitted iff the root filename appears in the module's phase files and names the root

  - [x] 2.7 Write property test for compliant index producing no router violations
    - **Property 4: Compliant index produces no router violations**
    - **Validates: Requirements 6.5**
    - Add to `senzing-bootcamp/tests/test_router_convention.py`; generate indexes where every
      in-scope root is at/below the ceiling and distinct from its phase files, assert
      `check_router_convention` returns no violations

  - [x] 2.8 Write unit/edge tests for ceiling boundary and environment guard
    - New file `senzing-bootcamp/tests/test_router_convention_unit.py`; assert the default
      ceiling resolves to 1000 and classifies 689/571/568 as routers and 1583/1448/1359 as
      requiring remediation; patch `sys.version_info` to `(3, 10)` and assert the linter
      reports an environment error and exits non-zero
    - _Requirements: 1.6, 6.6_

- [x] 3. Implement the step-range coverage and contiguity checker
  - [x] 3.1 Implement the sub-step-aware step-range checker
    - In `senzing-bootcamp/scripts/lint_steering.py`, add a checker that accepts a module's
      ordered phase `step_range`s iff they are contiguous, non-overlapping under the
      `(parent_integer, suffix)` ordering, and together cover exactly the module's full step
      set (integers and lettered sub-steps); emit a `LintViolation` on gap/overlap/uncovered
    - _Requirements: 3.2, 3.3, 3.4, 5.4_

  - [x] 3.2 Write property test for step-range contiguity and coverage
    - **Property 5: Step-range contiguity and coverage**
    - **Validates: Requirements 3.2, 3.3, 3.4, 5.4**
    - New file `senzing-bootcamp/tests/test_step_range_coverage.py`; generate ordered
      partitions of integer and lettered-sub-step sequences, assert acceptance iff
      contiguous/non-overlapping/fully covering, and rejection on injected gaps/overlaps

- [x] 4. Checkpoint - enforcement logic
  - Ensure all tests pass, ask the user if questions arise.

- [x] 5. Remediate content roots into thin routers (move content into existing phase files)
  - [x] 5.1 Thin Module 3 root
    - Move the Opt-Out Gate, Success Criteria, and Agent Rules sections from
      `module-03-system-verification.md` into `module-03-phase1-verification.md` (move, never
      delete); ensure the root retains only Router_Content_Set elements and a Phase_Manifest
      listing every Module 3 phase with its step range and file
    - _Requirements: 1.1, 1.3, 1.4, 2.4, 3.1, 3.5, 2.2, 7.1, 7.2, 7.3_

  - [x] 5.2 Thin Module 6 root
    - Move the Conditional Workflow, Pre-Load Freshness, Agent Workflow, and Advanced Reading
      sections from `module-06-data-processing.md` into `module-06-phaseA-build-loading.md`
      and `module-06-phaseD-validation.md` as appropriate; ensure the root retains only
      Router_Content_Set elements and a complete Phase_Manifest
    - _Requirements: 1.1, 1.3, 1.4, 2.4, 3.1, 3.5, 2.2, 7.1, 7.2, 7.3_

  - [x] 5.3 Thin Module 8 root
    - Move the Deferred Deployment Question section from `module-08-performance.md` into
      `module-08-phaseA-requirements.md`; ensure the root retains only Router_Content_Set
      elements and a complete Phase_Manifest
    - _Requirements: 1.1, 1.3, 1.4, 2.4, 3.1, 3.5, 2.2, 7.1, 7.2, 7.3_

- [x] 6. Remediate root-doubles-as-phase modules (create dedicated phase files, thin roots)
  - [x] 6.1 Convert Module 1 root
    - Create `senzing-bootcamp/steering/module-01-phase1-discovery.md` (kebab-case, valid
      frontmatter, no external URLs) and move the former phase-1 content (steps 1-9) from
      `module-01-business-problem.md` into it; thin the root to Router_Content_Set elements
      plus a Phase_Manifest referencing both phase files
    - _Requirements: 2.5, 1.1, 1.3, 1.4, 3.1, 3.5, 7.1, 7.5_

  - [x] 6.2 Convert Module 7 root
    - Create `senzing-bootcamp/steering/module-07-phase1-query-visualize.md` and move the
      former phase-1 content (steps 1 through "3d") from
      `module-07-query-visualize-discover.md` into it; thin the root to Router_Content_Set
      elements plus a Phase_Manifest referencing every Module 7 phase file
    - _Requirements: 2.5, 1.1, 1.3, 1.4, 3.1, 3.5, 7.1, 7.5_

  - [x] 6.3 Convert Module 11 root
    - Create `senzing-bootcamp/steering/module-11-phase1-packaging.md` and move the former
      phase-1 packaging content (steps 1-12) from `module-11-deployment.md` into it; thin the
      root to Router_Content_Set elements plus a Phase_Manifest referencing both phase files
    - _Requirements: 2.5, 1.1, 1.3, 1.4, 3.1, 3.5, 7.1, 7.5_

- [x] 7. Update references and reconcile the steering index
  - [x] 7.1 Update cross-references to renamed/new files
    - Update all `#[[file:]]` and backtick filename references across steering files and docs
      that point to the changed Module 1/7/11 roots and new phase files, so no orphaned
      reference remains
    - _Requirements: 7.4_

  - [x] 7.2 Reconcile `steering-index.yaml`
    - Repoint the Module 1/7/11 first-phase `file:` entries from the root to the new phase
      files so every in-scope module's `root` is distinct from each phase `file`; run
      `measure_steering.py` to update `token_count`/`size_category` for all changed and new
      files; ensure each phase `step_range` stays contiguous and non-overlapping and that
      every steering `.md` on disk has a `file_metadata` entry
    - _Requirements: 4.1, 4.2, 4.3, 3.3, 3.5_

  - [x] 7.3 Verify measured counts via `measure_steering.py --check`
    - Run `measure_steering.py --check` and assert it exits 0 (no stored count drifts > 10%)
    - _Requirements: 4.1, 4.4_

- [x] 8. Clarify the phase-loading guide
  - [x] 8.1 Update `phase-loading-guide.md`
    - State that the Router_Root provides navigation/overview content while substantive steps
      live in Phase_Files; describe phase resolution for Modules 1/7/11 using the new
      router/phase names; preserve the load-root-first then resolve-phase then
      load-matching-phase behavior and the "load root only" fallback verbatim
    - _Requirements: 5.1, 5.2, 5.3, 5.4_

  - [x] 8.2 Write unit test for loading-guide content
    - New file `senzing-bootcamp/tests/test_phase_loading_guide.py`; assert the guide states
      the router role and references the new Module 1/7/11 names
    - _Requirements: 5.2, 5.3_

- [x] 9. Final verification and CI wiring
  - [x] 9.1 Ensure the router rule runs in CI
    - Confirm `lint_steering.py` (now including the router rule) runs in
      `.github/workflows/validate-power.yml` on the Python 3.11/3.12/3.13 matrix so a
      regressing root fails the pull-request checks; add or adjust the step if needed
    - _Requirements: 6.7, 6.5_

  - [x] 9.2 Write end-state verification tests on the real repo files
    - Assert every in-scope root's measured token count <= 1000, every in-scope module's
      `root` differs from all its phase files, each in-scope router contains a Phase_Manifest
      referencing every phase file in the index, every steering `.md` has a `file_metadata`
      entry, and `lint_steering.py` emits no router violation and exits 0
    - _Requirements: 2.4, 2.5, 4.3, 4.2, 1.2, 3.5, 6.5, 7.1, 7.5_

  - [x] 9.3 Validate formatting and link constraints over changed files
    - Run `validate_commonmark.py` and `validate_links.py` over the changed/new steering files
      and assert CommonMark compliance and no external URLs
    - _Requirements: 7.2, 7.3_

- [x] 10. Final checkpoint
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional test sub-tasks and can be skipped for a faster MVP.
- Each task references specific requirement sub-clauses for traceability.
- Content is always MOVED into phase files, never deleted, preserving all step coverage.
- Property tests (Properties 1-6) validate the pure decision logic; content relocation,
  formatting, documentation, and CI wiring are verified by example tests, existing
  validators, and review per the design's Testing Strategy.
- Property-based tests run with Hypothesis at >= 100 iterations, consistent with project
  conventions.

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1", "2.1"] },
    { "id": 1, "tasks": ["1.2", "2.3", "2.2", "5.1", "5.2", "5.3"] },
    { "id": 2, "tasks": ["2.4", "1.3", "6.1", "6.2", "6.3"] },
    { "id": 3, "tasks": ["3.1", "2.5", "2.8", "7.1"] },
    { "id": 4, "tasks": ["3.2", "2.6", "7.2", "8.1"] },
    { "id": 5, "tasks": ["2.7", "7.3", "8.2", "9.1"] },
    { "id": 6, "tasks": ["9.2", "9.3"] }
  ]
}
```
