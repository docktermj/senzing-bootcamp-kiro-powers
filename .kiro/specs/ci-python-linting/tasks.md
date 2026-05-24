# Implementation Plan: CI Python Linting

## Overview

Add Ruff linting to the CI pipeline by creating a `pyproject.toml` configuration file at the repository root and inserting a lint step into the existing GitHub Actions workflow. The implementation is two files: one new (pyproject.toml) and one modified (validate-power.yml).

## Tasks

- [x] 1. Create pyproject.toml with Ruff configuration
  - [x] 1.1 Create `pyproject.toml` at the repository root with `[tool.ruff]` and `[tool.ruff.lint]` sections
    - Set `target-version = "py311"`
    - Set `src = ["senzing-bootcamp/scripts", "senzing-bootcamp/tests", "tests"]`
    - Set `select = ["F", "E", "W", "I"]` under `[tool.ruff.lint]`
    - Do NOT include any `[project]`, `[project.dependencies]`, or runtime dependency sections
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 5.1_

- [x] 2. Add Ruff lint step to CI workflow
  - [x] 2.1 Insert a "Lint Python (ruff)" step into `.github/workflows/validate-power.yml`
    - Place the step after the existing validation steps and before the "Run tests" step
    - Step should run: `pip install ruff` then `ruff check senzing-bootcamp/scripts/ senzing-bootcamp/tests/ tests/`
    - Do NOT use `--exit-zero`, `--quiet`, or `continue-on-error`
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 4.1, 4.2, 5.2_

- [x] 3. Checkpoint - Verify configuration locally
  - Ensure all tests pass, ask the user if questions arise.

- [x] 4. Add configuration validation tests
  - [x] 4.1 Create `tests/test_ci_python_linting.py` with tests that validate pyproject.toml and workflow structure
    - Test that `pyproject.toml` exists and contains `[tool.ruff]` section
    - Test that `target-version` is set to `"py311"`
    - Test that `select` contains exactly `["F", "E", "W", "I"]`
    - Test that `src` contains the three lint target directories
    - Test that `pyproject.toml` does not declare ruff as a runtime dependency
    - Test that the workflow YAML contains a lint step named "Lint Python (ruff)"
    - Test that the lint step appears after setup-python and before the test step
    - Test that the lint step does not contain `--exit-zero` or `continue-on-error`
    - _Requirements: 1.1, 1.2, 1.3, 1.5, 2.1, 2.2, 2.4, 4.2, 5.1, 5.3_

  - [x] 4.2 Write property test for lint configuration completeness
    - **Property 1: Lint configuration completeness**
    - **Validates: Requirements 1.3, 1.5, 3.1, 3.2, 3.3**

- [x] 5. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- The implementation language is Python (pytest + Hypothesis for tests) per the project's tech stack
- `pyproject.toml` must NOT include runtime dependencies — Ruff is CI/dev-only

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1"] },
    { "id": 1, "tasks": ["2.1"] },
    { "id": 2, "tasks": ["4.1"] },
    { "id": 3, "tasks": ["4.2"] }
  ]
}
```
