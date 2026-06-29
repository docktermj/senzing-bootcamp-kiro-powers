# Implementation Plan: Test Suite Parallelization

## Overview

This plan implements parallel test execution for the senzing-bootcamp pytest + Hypothesis suite via `pytest-xdist`, following the conservative "execution-mode change, not a semantics change" design. Work proceeds in dependency order: first pin the tooling dependency, then add the `[tool.pytest.ini_options]` configuration (testpaths, addopts, strict markers, marker taxonomy), then register/apply markers across in-use tests so strict collection stays clean, then audit and remediate the handful of non-parallel-safe tests, then wire CI to run `-n auto` on the matrix. Config-level example tests are added alongside each change to lock in correctness, mirroring the repo's existing CI-wiring test convention (`tests/test_ci_profile_wiring_config.py`).

Per the design, **no property-based tests are added** — this is configuration/CI/test-isolation work where the only cross-cutting invariant ("parallel and serial produce the same pass/fail set") is a suite-level integration check, not a fast property. Implementation language is **Python 3.11+ (stdlib only)** with pytest; config parsing uses `tomllib` (stdlib).

## Tasks

- [x] 1. Pin `pytest-xdist` in `requirements-dev.txt`
  - Add `pytest-xdist==3.7.0` to the existing pinned dev tooling in `requirements-dev.txt` (keep `ruff`, `pytest`, `hypothesis` entries unchanged).
  - This is the single source of truth that provisions the plugin for both local and CI runs; no inline `pip install` is added to the workflow.
  - _Requirements: 1.1, 9.1, 9.2, 9.3, 9.4_

  - [x] 1.1 Write dependency-pinning config test
    - Create `tests/test_dependency_pinning.py` asserting `pytest-xdist==<version>` (exact `==`) is present in `requirements-dev.txt`.
    - Add a grep-style assertion that no production script under `senzing-bootcamp/scripts/` imports `xdist` or `pytest_xdist` (production scripts stay dependency-free).
    - _Requirements: 9.2, 9.4_

- [x] 2. Add the `[tool.pytest.ini_options]` section to `pyproject.toml`
  - Append a new `[tool.pytest.ini_options]` section to the root `pyproject.toml` (which currently holds only `[tool.ruff]`).
  - Set `testpaths = ["senzing-bootcamp/tests", "tests"]` so a bare `pytest` collects exactly the two roots.
  - Set `addopts = "-v --tb=short --strict-markers"` (preserves today's output behavior; enables strict markers; deliberately excludes `-n` to keep serial-by-default for debugging).
  - Register the marker taxonomy: `slow`, `property`, `serial` with descriptions.
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 3.1, 3.2, 1.4_

  - [x] 2.1 Write pytest-config example test
    - Create `tests/test_pytest_config.py` that parses `pyproject.toml` with `tomllib` and asserts: section `[tool.pytest.ini_options]` exists; `testpaths == ["senzing-bootcamp/tests", "tests"]`; `addopts` contains `-v`, `--tb=short`, and `--strict-markers`; `markers` registers `slow`, `property`, and `serial`; and `addopts` does NOT contain `-n` (encodes serial-by-default design decision).
    - _Requirements: 2.1, 2.3, 2.5, 3.1, 3.2_

- [x] 3. Make strict-marker collection clean across the suite
  - With `--strict-markers` active, run a collection-only pass (`pytest --collect-only -q`) over both roots and identify any unregistered marker that errors collection.
  - For every marker already used in the suite, ensure it is registered in `pyproject.toml` (add to the `markers` list if a legitimate in-use marker is missing) or remove the typo'd marker usage in the offending test.
  - Apply `@pytest.mark.slow` to the long-running tests and `@pytest.mark.property` to Hypothesis (`@given`) tests so the taxonomy is meaningful for selective runs.
  - _Requirements: 3.1, 3.3, 3.5_

  - [x] 3.1 Write strict-marker collection test
    - In `tests/test_pytest_config.py` (or a focused module), assert a `--collect-only` run over both roots exits cleanly (every in-use marker registered, Req 3.5), and add a negative check: a deliberately mis-marked throwaway test written into a `tmp_path` fails collection under strict mode (Req 3.3).
    - _Requirements: 3.3, 3.5_

  - [x] 3.2 Write marker-selection test
    - Assert `pytest -m "not slow and not property" --collect-only` excludes tests bearing those markers, and a complementary `-m "slow or property"` selection includes them.
    - _Requirements: 3.4_

- [x] 4. Checkpoint - Ensure all tests pass
  - Ensure all tests pass and strict-marker collection is clean, ask the user if questions arise.

- [x] 5. Audit and remediate non-parallel-safe tests
  - [x] 5.1 Audit the suite for shared-path filesystem writes
    - Grep both test roots for fixed, repo-relative writes (`write_text`/`open(..., "w")`/`os.chdir`) that are NOT guarded by `tmp_path`, `monkeypatch.chdir`, `tempfile.mkdtemp`, or `TemporaryDirectory`.
    - Produce a list of flagged Non_Parallel_Safe_Test candidates; confirm the known-safe patterns are excluded.
    - _Requirements: 6.1, 5.1, 10.3_

  - [x] 5.2 Remediate flagged tests via per-test path isolation
    - For each flagged test, convert shared-path writes to `tmp_path` / `tmp_path_factory` (worker-unique under xdist) or use `monkeypatch.chdir(tmp_path)` so concurrent workers cannot collide.
    - _Requirements: 5.1, 5.2, 6.2_

  - [x] 5.3 Pin residual non-isolable tests to a serial group
    - For any flagged test that cannot be isolated, apply `@pytest.mark.serial` plus `@pytest.mark.xdist_group("serial")` so it lands on a single worker under `--dist loadgroup`; add a short comment documenting why isolation was infeasible.
    - _Requirements: 6.3_

  - [x] 5.4 Add targeted isolation assertions for remediated tests
    - For remediated file-writing tests, add/confirm an assertion that the test writes only under its temp dir, and verify a parallel run leaves no new tracked artifacts (`git status --porcelain` clean after run).
    - _Requirements: 5.2, 5.3, 6.2_

  - [x] 5.5 Confirm CWD-fixture and Hypothesis behavior under workers
    - Verify the autouse `CWD_Fixture` (snap-to-root in `tests/conftest.py`, recover in `senzing-bootcamp/tests/conftest.py`) needs no change because workers are process-local; document this conclusion in the conftest if a clarifying comment helps.
    - Confirm the shared `.hypothesis/` directory-based store is left as-is (concurrent-safe, no per-worker config, profiles untouched).
    - _Requirements: 4.1, 4.2, 7.1, 7.3_

- [x] 6. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 7. Wire CI to run the suite in parallel on the matrix
  - Change the `tests` job "Run tests" step in `.github/workflows/validate-power.yml` to invoke `python -m pytest senzing-bootcamp/tests/ tests/ -n auto` (drop the now-redundant `-v --tb=short`, which come from `addopts`).
  - Add `--dist loadgroup` so `xdist_group("serial")` pins are honored.
  - Keep `HYPOTHESIS_PROFILE: thorough` and the unchanged `['3.11', '3.12', '3.13']` matrix; the plugin is provisioned by the existing `pip install -r requirements-dev.txt` step.
  - _Requirements: 8.1, 8.2, 8.3, 1.2, 1.3, 6.3_

  - [x] 7.1 Write CI parallel-wiring config test
    - Create `tests/test_ci_parallel_wiring.py` that parses `.github/workflows/validate-power.yml` and asserts: the "Run tests" step invokes pytest with `-n`; `requirements-dev.txt` pins `pytest-xdist` at an exact version; and the matrix still lists `'3.11'`, `'3.12'`, `'3.13'`.
    - _Requirements: 8.2, 8.3, 9.1, 9.2_

- [x] 8. Document and verify parallel-vs-serial equivalence
  - Add a short developer note (in the spec or a `CONTRIBUTING`-style location the repo already uses) describing how to verify equivalence: run the full suite serially and under `-n auto` for the same commit and diff the passing/failing set; run the parallel suite twice on an unchanged commit and confirm identical results.
  - This equivalence is the standing guarantee enforced by the green parallel CI matrix; any divergent test is treated as a Non_Parallel_Safe_Test and remediated under Task 5.
  - _Requirements: 4.3, 6.4, 7.2, 8.4, 10.1, 10.2, 10.3_

- [x] 9. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass under both serial and parallel (`-n auto --dist loadgroup`) execution, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional test/verification sub-tasks and can be skipped for a faster MVP; core implementation tasks are never optional.
- Each task references specific granular requirements clauses for traceability.
- No property-based tests are included by design: this is config/CI/test-isolation work, and the one cross-cutting invariant (parallel ≡ serial outcome) is a suite-level integration check (~150s per full run), verified by the standing parallel CI matrix rather than a fast property test.
- Config/CI tests live in repo-root `tests/` per the structure rule that CI/config-validation tests belong at repo root.
- `-n` is intentionally kept out of `addopts` (serial-by-default) so local debugging keeps clean tracebacks and `pdb`; parallelism is opted into explicitly by CI and by developers.

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1"] },
    { "id": 1, "tasks": ["1.1", "2"] },
    { "id": 2, "tasks": ["2.1", "3"] },
    { "id": 3, "tasks": ["3.1", "3.2", "5.1"] },
    { "id": 4, "tasks": ["5.2", "5.3", "5.5"] },
    { "id": 5, "tasks": ["5.4", "7"] },
    { "id": 6, "tasks": ["7.1", "8"] }
  ]
}
```
