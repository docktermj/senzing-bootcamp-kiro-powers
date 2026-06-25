# Implementation Plan: Hypothesis Settings Centralization

## Overview

This plan implements a single shared `hypothesis_profiles.py` module at the repo
root that registers a `fast`/`thorough`/`bootcamp`-alias profile hierarchy and
selects the active profile from the `HYPOTHESIS_PROFILE` environment variable.
The two `conftest.py` files are rewired to consume the shared module (removing
their duplicated inline `bootcamp` registrations), CI is set to force the
`thorough` profile across the 3.11/3.12/3.13 matrix, the Python conventions
steering file is reconciled, and the one hand-lowered test is restored.

Implementation language is **Python 3.11+, stdlib + Hypothesis only** (per the
design and the tech-stack rule). Work proceeds bottom-up: build and test the
pure registry module first, then wire the consumers (conftests, CI, docs), then
restore the regression test, then run config-scan/example tests and the full
suite.

## Tasks

- [x] 1. Create the shared profile registry module
  - [x] 1.1 Implement `hypothesis_profiles.py` at the repo root
    - Create `hypothesis_profiles.py` with `from __future__ import annotations`, type hints, Google-style docstrings, line length 100
    - Define constants: `FAST="fast"`, `THOROUGH="thorough"`, `LEGACY_ALIAS="bootcamp"`, `DEFAULT_PROFILE=FAST`, `ENV_VAR="HYPOTHESIS_PROFILE"`, `BASELINE_EXAMPLE_COUNT=20`, `FAST_MAX_EXAMPLES=10`, `THOROUGH_MAX_EXAMPLES=100`
    - Implement `register_profiles()`: register `fast` (max_examples=10), `thorough` (max_examples=100), and `bootcamp` (alias of thorough settings); every profile sets `deadline=None` and suppresses `HealthCheck.too_slow`; idempotent (later calls overwrite with identical settings, never raise)
    - Implement `registered_profile_names() -> tuple[str, ...]`
    - Implement `resolve_profile_name(env_value: str | None) -> str` as a pure function: `None`/empty → `DEFAULT_PROFILE`; registered name → same name; otherwise raise `ValueError` whose message contains the offending value and the list of valid names
    - Implement `load_active_profile(env_value: str | None = None) -> str`: read `os.environ[ENV_VAR]` when `env_value` is None, register all profiles, resolve the active name, load exactly one profile, and return it
    - Import only stdlib (`os`) plus `hypothesis`
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 2.3, 2.4, 3.1, 3.2, 3.3, 3.4, 6.4_

  - [x] 1.2 Write property test for registered-name resolution
    - In `tests/test_hypothesis_profiles_properties.py`, draw names with `st.sampled_from(registered_profile_names())` and assert `resolve_profile_name(n) == n`; run ≥100 iterations
    - Tag: `# Feature: hypothesis-settings-centralization, Property 1: A registered profile name resolves to itself, for both roots`
    - **Property 1: A registered profile name resolves to itself, for both roots**
    - **Validates: Requirements 3.1, 3.5, 8.4**

  - [x] 1.3 Write property test for unrecognized-value error
    - Draw arbitrary non-empty strings with `st.text()` filtered to exclude registered names and the empty string; assert `resolve_profile_name(s)` raises `ValueError` whose message contains `s` verbatim; run ≥100 iterations
    - Tag: `# Feature: hypothesis-settings-centralization, Property 2: An unrecognized profile value raises an error naming the value`
    - **Property 2: An unrecognized profile value raises an error naming the value**
    - **Validates: Requirements 3.3, 8.6**

  - [x] 1.4 Write property test for preserved timing settings
    - For each name in `registered_profile_names()` (sampled across ≥100 iterations), assert the registered profile has `deadline is None` and `HealthCheck.too_slow` in its `suppress_health_check`
    - Tag: `# Feature: hypothesis-settings-centralization, Property 3: Every registered profile preserves the timing settings`
    - **Property 3: Every registered profile preserves the timing settings**
    - **Validates: Requirements 1.1, 1.6**

  - [x] 1.5 Write property test for idempotent registration
    - Call `register_profiles()` a Hypothesis-chosen number of times (≥100 iterations over counts) and assert no error is raised and the registered profiles/settings match those after a single call
    - Tag: `# Feature: hypothesis-settings-centralization, Property 4: Profile registration is idempotent`
    - **Property 4: Profile registration is idempotent**
    - **Validates: Requirements 2.4**

  - [x] 1.6 Write example/unit tests for counts, default, and single-load
    - Assert `fast` and `thorough` are registered; `fast` max_examples `== 10`; `thorough` max_examples `== 100`; `thorough >= BASELINE_EXAMPLE_COUNT (20)`; `fast < thorough`
    - Assert `resolve_profile_name(None)` and `resolve_profile_name("")` both return `fast`; assert `load_active_profile` returns exactly the resolved name (single load per call)
    - Assert `hypothesis_profiles` imports only stdlib plus `hypothesis`
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 3.2, 3.4, 6.4, 8.1, 8.2, 8.3, 8.5_

- [x] 2. Checkpoint - registry module verified
  - Ensure all tests pass, ask the user if questions arise.

- [x] 3. Wire conftest files to the shared module
  - [x] 3.1 Update `Power_Conftest` (`senzing-bootcamp/tests/conftest.py`)
    - Remove the inline `settings.register_profile("bootcamp", ...)` / `settings.load_profile("bootcamp")` block
    - Ensure repo root (`Path(__file__).resolve().parents[2]`) is on `sys.path`, `import hypothesis_profiles`, then call `hypothesis_profiles.load_active_profile()`
    - Preserve the existing `scripts/` `sys.path` insert, the `_recover_stale_cwd` autouse fixture, and all existing fixtures/strategy helpers
    - _Requirements: 2.1, 2.5, 3.5, 6.2, 6.3_

  - [x] 3.2 Update `Repo_Conftest` (`tests/conftest.py`)
    - Remove the inline `bootcamp` registration/load block
    - `import hypothesis_profiles` (repo root already on `sys.path` via the existing `_PROJECT_ROOT` insert) and call `hypothesis_profiles.load_active_profile()`
    - Preserve the `_restore_project_root_cwd` autouse fixture and the `tests/` and project-root `sys.path` inserts
    - _Requirements: 2.2, 2.5, 3.5, 6.1, 6.3_

  - [x] 3.3 Write config-scan test for de-duplication
    - Scan both `conftest.py` files and assert neither contains an inline `settings.register_profile(` call (registration lives only in `hypothesis_profiles.py`)
    - _Requirements: 2.3, 2.5_

  - [x] 3.4 Write tests for override semantics and preserved conftest behavior
    - Confirm an un-decorated `@given` test inherits the active profile's `max_examples`, and a test with `@settings(max_examples=v)` reports effective `max_examples == v` under both profiles
    - Confirm the cwd-restoring autouse fixtures still snap back to the project root and that script/helper imports still resolve
    - _Requirements: 5.1, 5.2, 5.3, 6.1, 6.2, 6.3_

- [x] 4. Configure CI to force the thorough profile
  - [x] 4.1 Update `.github/workflows/validate-power.yml`
    - In the `tests` job's "Run tests" step, set step-level `env: HYPOTHESIS_PROFILE: thorough`
    - Confirm the matrix lists Python `3.11`, `3.12`, `3.13` so the selection applies to all three entries
    - Keep the pytest invocation targeting both `senzing-bootcamp/tests/` and `tests/`
    - _Requirements: 4.1, 4.2, 4.3, 4.4_

  - [x] 4.2 Write config-scan test for CI wiring
    - Parse `validate-power.yml` and assert the "Run tests" step sets `HYPOTHESIS_PROFILE: thorough`, the matrix lists `3.11`/`3.12`/`3.13`, and the pytest command still targets both `senzing-bootcamp/tests/` and `tests/`
    - _Requirements: 4.1, 4.3, 4.4_

- [x] 5. Reconcile documentation and restore the hand-lowered test
  - [x] 5.1 Update `Python_Conventions` (`.kiro/steering/python-conventions.md`)
    - Replace the fixed `@settings(max_examples=20)` guidance with profile-based baselines: `fast=10`, `thorough=100`, default `fast`, selected via `HYPOTHESIS_PROFILE`
    - Document that inline `@settings` are overrides used only when a test needs a non-baseline count
    - Document the registered profile names, the env var name, the default profile, and the local commands (default run uses `fast`; `HYPOTHESIS_PROFILE=thorough python -m pytest ...` for a full local run)
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

  - [x] 5.2 Restore the hand-lowered test in `senzing-bootcamp/tests/test_version_frontmatter_properties.py`
    - Confirm the ad-hoc `@settings(max_examples=10)` decorator against git history, then remove the inline `max_examples=10` override so the test inherits the active profile baseline
    - _Requirements: 5.1, 7.5_

  - [x] 5.3 Write documentation config-scan test
    - Scan `python-conventions.md` and assert it documents the profile names, the env var, the default profile, and the override semantics
    - _Requirements: 7.1, 7.2, 7.3, 7.4_

- [x] 6. Final checkpoint - full-suite verification
  - Run `HYPOTHESIS_PROFILE=thorough python -m pytest senzing-bootcamp/tests/ tests/ -v --tb=short` and a default (fast) run via automated test invocation; run `ruff check` over the new module and edited files
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP.
- Each task references specific requirements for traceability.
- Checkpoints ensure incremental validation.
- Property tests (1.2–1.5) validate the four universal correctness properties from the design against the pure logic in `hypothesis_profiles.py`; each runs ≥100 iterations and is tagged with its property number.
- Unit/example and config-scan tests validate fixed configuration values, CI wiring, de-duplication, override semantics, and documentation.
- No new runtime or test dependencies are introduced — only the already-present `pytest` and `hypothesis`.

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1"] },
    { "id": 1, "tasks": ["1.2", "1.3", "1.4", "1.5", "1.6", "3.1", "3.2", "4.1", "5.1", "5.2"] },
    { "id": 2, "tasks": ["3.3", "3.4", "4.2", "5.3"] }
  ]
}
```
