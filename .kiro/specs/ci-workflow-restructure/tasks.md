# Implementation Plan: CI Workflow Restructure

## Overview

This plan restructures `.github/workflows/validate-power.yml` from a single matrixed
`validate` job into two parallel jobs — a single-version `gates` job (all 20
version-independent gates, run once on Python 3.11) and a matrixed `tests` job (pytest on
3.11/3.12/3.13) — and introduces a pinned `requirements-dev.txt` plus pip caching and a
concurrency group. It then adds a parsing-based validation test that asserts the design's
seven Correctness Properties and the smoke/configuration checks so the restructuring is
proven not to drop or weaken any gate.

Work is ordered so the two deliverable artifacts (`requirements-dev.txt` and the rewritten
workflow) are produced first, then the validation test is finalized against that final
state, then checkpoints confirm the test passes and no regressions are introduced.

Implementation notes carried into every task:
- Scripts stay stdlib-only. The validation test may use **PyYAML** (`import yaml`) — the one
  accepted non-stdlib dependency in this repo (already used by `validate_dependencies.py`).
  Do **not** add any runtime dependency to the scripts.
- Tests are run as single executions (never watch mode). Use `python3` if `python` is
  unavailable.
- The sibling specs `test-suite-parallelization` (owns `pytest-xdist`/`-n` flags) and
  `hypothesis-settings-centralization` (owns Hypothesis profile/env) may later append to
  `requirements-dev.txt` and the tests job. Keep all changes here additive and compatible;
  do **not** pre-implement those specs (the pytest invocation stays plain).
- Pick the current stable `==` versions of `ruff`, `pytest`, and `hypothesis` at task time.
- The test follows the repo convention: class-based, `sys.path` insertion of the scripts
  dir, and property comments tagged `Feature: ci-workflow-restructure, Property N: <text>`.

## Tasks

- [x] 1. Create pinned dev-dependency file
  - [x] 1.1 Create `requirements-dev.txt` at the repo root
    - Create `requirements-dev.txt` at the repository root with exactly three lines, one
      `name==version` per line, using exact (`==`) pins for the current stable releases:
      `ruff==<current>`, `pytest==<current>`, `hypothesis==<current>` (verify the latest
      stable version of each on PyPI at task time, e.g. ruff `0.14.x`, pytest `9.0.x`,
      hypothesis `6.x`).
    - Standard pip requirements format, no version ranges, no extras, no comments required.
    - This file doubles as the `cache-dependency-path` for pip caching in the workflow.
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

- [x] 2. Rewrite the validate-power workflow into gates + tests jobs
  - [x] 2.1 Write workflow-level keys: name, triggers, and concurrency
    - In `.github/workflows/validate-power.yml`, preserve `name: Validate Power` and copy the
      `on:` block byte-for-byte from the current workflow: `pull_request.paths` with the six
      globs (`senzing-bootcamp/**`, `tests/**`, `.github/workflows/**`, `.kiro/specs/**`,
      `.kiro/spec-catalog.yaml`, `.kiro/SPEC_CATALOG.md`) and `push.branches: [main]`.
    - Add a workflow-level `concurrency` block with
      `group: ${{ github.workflow }}-${{ github.ref }}` and `cancel-in-progress: true`.
    - _Requirements: 6.1, 6.2, 8.1, 8.2, 9.1_

  - [x] 2.2 Implement the `gates` job (all 20 version-independent gates, run once)
    - Add `jobs.gates` on `runs-on: ubuntu-latest` with **no** `strategy`/matrix.
    - First steps: `actions/checkout@v4`; then `actions/setup-python@v5` with
      `python-version: '3.11'`, `cache: 'pip'`, and
      `cache-dependency-path: requirements-dev.txt`; then a step
      `run: pip install -r requirements-dev.txt` (the setup-python cache step precedes
      install).
    - Add the 20 gate steps in the same relative order as the current workflow, with commands
      unchanged: `validate_power.py`, `measure_steering.py --check`, `validate_commonmark.py`,
      `validate_dependencies.py`, `compose_hook_prompts.py --verify` (with its
      `|| { echo "::error::..."; exit 1; }` block), `sync_hook_registry.py --verify` (with its
      `::error::` block), `lint_steering.py`, `validate_prerequisites.py`,
      `validate_progress_ci.py`, `validate_preferences_ci.py`, `validate_mandatory_gates.py`,
      `validate_governance_rules.py`, `validate_yaml_schemas.py`,
      `validate_links.py --timeout 10`,
      `ruff check senzing-bootcamp/scripts/ senzing-bootcamp/tests/ tests/` (no inline
      `pip install ruff` — ruff comes from the pinned file), `eval_conversations.py`,
      `generate_power_docs.py --verify` (with its `::error::` block),
      `generate_spec_catalog.py --check` (with its `::error::` block),
      `example_coverage_report.py --check`, `scan_brittle_assertions.py --check`.
    - Do not include any pytest step in this job. Set no `continue-on-error` anywhere.
    - Preserve all four `::error::` remediation strings verbatim.
    - _Requirements: 1.1, 1.3, 1.5, 2.1, 2.2, 2.3, 2.4, 2.5, 3.1, 3.2, 3.3, 5.1, 5.2, 9.2, 9.3_

  - [x] 2.3 Implement the `tests` job (pytest across the matrix)
    - Add `jobs.tests` on `runs-on: ubuntu-latest` with
      `strategy.fail-fast: false` and `strategy.matrix.python-version: ['3.11', '3.12', '3.13']`,
      and no `needs:` (independent parallel job alongside `gates`).
    - Steps: `actions/checkout@v4`; `actions/setup-python@v5` with
      `python-version: ${{ matrix.python-version }}`, `cache: 'pip'`,
      `cache-dependency-path: requirements-dev.txt`; `run: pip install -r requirements-dev.txt`;
      then `run: python -m pytest senzing-bootcamp/tests/ tests/ -v --tb=short`
      (no inline `pip install pytest hypothesis`).
    - Set no `continue-on-error` anywhere.
    - _Requirements: 1.2, 1.4, 4.1, 4.2, 4.3, 4.4, 5.1, 5.2, 9.4_

- [x] 3. Create the workflow validation test
  - [x] 3.1 Scaffold the test module and canonical gate-set fixtures
    - Create `senzing-bootcamp/tests/test_validate_power_workflow.py` using PyYAML
      (`import yaml`) and stdlib, following the repo convention (`sys.path` insert of the
      scripts dir if needed; class-based organization).
    - Add a module helper that loads `.github/workflows/validate-power.yml` via
      `yaml.safe_load` and collects every step `run:` string per job, plus a helper to read
      repo-root `requirements-dev.txt`.
    - Define a hardcoded canonical list of the 20 version-independent gate command strings
      (exact `python senzing-bootcamp/scripts/<script>.py ...` invocations from the design's
      gate-to-job mapping) and the canonical pytest command
      `python -m pytest senzing-bootcamp/tests/ tests/`.
    - _Requirements: 9.1, 9.2_

  - [x] 3.2 Implement Properties 1–4 (gate-set preservation and placement)
    - Add a `TestGatePreservation` class with assertions tagged in comments:
      - **Property 1: Gate-set preservation** — every canonical gate command (and the pytest
        command) is a substring of some step `run:` across the `gates` + `tests` jobs.
        **Validates: Requirements 2.1, 2.2, 2.3, 9.2**
      - **Property 2: Version-independent gates placed in the gates job** — each of the 20
        commands appears in a `gates`-job step. **Validates: Requirements 1.3, 1.5**
      - **Property 3: Each version-independent gate runs exactly once / no matrix** — each of
        the 20 commands appears in exactly one `gates` step and `jobs.gates` has no
        `strategy.matrix`. **Validates: Requirements 3.1, 3.2**
      - **Property 4: Verify-gate error annotations preserved** — each of the four
        `echo "::error::..."` remediation strings (compose_hook_prompts, sync_hook_registry,
        generate_power_docs, generate_spec_catalog) is present verbatim.
        **Validates: Requirements 2.4**
    - _Requirements: 1.3, 1.5, 2.1, 2.2, 2.3, 2.4, 3.1, 3.2, 9.2_

  - [x] 3.3 Implement Properties 5–7 (matrix, caching, pinning)
    - Add a `TestMatrixCachingPinning` class with assertions tagged in comments:
      - **Property 5: pytest runs on every matrix version** —
        `jobs.tests.strategy.matrix.python-version == ['3.11','3.12','3.13']`,
        `jobs.tests.strategy.fail-fast is False`, and a `tests` step runs
        `python -m pytest senzing-bootcamp/tests/ tests/`.
        **Validates: Requirements 1.4, 4.1, 4.2, 4.3**
      - **Property 6: Every setup-python job enables pip caching** — for every job whose step
        `uses: actions/setup-python@...`, that step's `with.cache == 'pip'`.
        **Validates: Requirements 5.1, 5.2**
      - **Property 7: Every CI-installed tool is exactly pinned** — every non-comment line of
        `requirements-dev.txt` matches `^\S+==\S+$`, and `ruff`, `pytest`, `hypothesis` are
        each present. **Validates: Requirements 7.1, 7.2, 7.3, 7.4, 7.5**
    - _Requirements: 1.4, 4.1, 4.2, 4.3, 5.1, 5.2, 7.1, 7.2, 7.3, 7.4, 7.5_

  - [x] 3.4 Implement smoke / configuration checks
    - Add a `TestWorkflowSmoke` class asserting:
      - Parseability: file loads via `yaml.safe_load` with top-level `name`, `on`, `jobs`
        (Req 9.1).
      - Two distinct jobs: `jobs` contains distinct `gates` and `tests` keys (Req 1.1, 1.2).
      - Gates single version: `gates` setup-python `python-version == '3.11'` (Req 3.1).
      - Gates excludes pytest: no `gates` step `run` contains `pytest` (Req 1.5).
      - No swallowed failures: no step or job sets `continue-on-error: true`
        (Req 2.5, 4.4, 9.3, 9.4).
      - Concurrency: `concurrency.group` references `github.workflow` and `github.ref`;
        `concurrency.cancel-in-progress is True` (Req 6.1, 6.2).
      - Triggers preserved: `on.pull_request.paths` equals the six globs exactly;
        `on.push.branches == ['main']` (Req 8.1, 8.2).
      - ruff target-version unchanged: `pyproject.toml [tool.ruff] target-version` remains
        `py311` (Req 3.3).
    - _Requirements: 1.1, 1.2, 1.5, 2.5, 3.1, 3.3, 4.4, 6.1, 6.2, 8.1, 8.2, 9.1, 9.3, 9.4_

- [x] 4. Checkpoint - Validate the restructured workflow
  - Run `python -m pytest senzing-bootcamp/tests/test_validate_power_workflow.py -v`
    (use `python3` if `python` is unavailable) and ensure all property and smoke assertions
    pass. Ensure all tests pass, ask the user if questions arise.

- [x] 5. Final checkpoint - Confirm no regressions
  - Run `python -m pytest senzing-bootcamp/tests/ tests/ -v --tb=short` to confirm the new
    test integrates cleanly and no existing test regressed. Ensure all tests pass, ask the
    user if questions arise.

## Notes

- Each task references specific requirements clauses for traceability.
- This spec's verification deliverable is the parsing-based validation test
  (`test_validate_power_workflow.py`). Per the design's Testing Strategy, the Correctness
  Properties range over finite enumerable sets (gates, jobs, tool lines), so they are
  implemented as example-driven structural assertions rather than a randomized Hypothesis
  harness; they are core deliverables, not optional.
- Requirements 9.3 and 9.4 (a real failing gate / failing test leg yields an overall
  failure) are GitHub Actions platform behaviors verified structurally via the
  "no `continue-on-error`" assertion plus `fail-fast: false`; full end-to-end confirmation on
  a real PR is a manual observation outside automated unit scope.
- Keep `requirements-dev.txt` and the tests-job invocation additive so the sibling specs
  (`test-suite-parallelization`, `hypothesis-settings-centralization`) can extend them
  without conflict.
- Checkpoints ensure incremental validation at the natural break points.

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1"] },
    { "id": 1, "tasks": ["2.1", "3.1"] },
    { "id": 2, "tasks": ["2.2", "3.2"] },
    { "id": 3, "tasks": ["2.3", "3.3"] },
    { "id": 4, "tasks": ["3.4"] }
  ]
}
```
