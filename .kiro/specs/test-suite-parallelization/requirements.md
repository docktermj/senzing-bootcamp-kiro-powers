# Requirements Document

## Introduction

The senzing-bootcamp power ships with a large pytest + Hypothesis suite (~5,700 tests across ~349 files in `senzing-bootcamp/tests/` and `tests/`). Today the suite runs serially, taking ~150+ seconds locally and in CI, which is the dominant drag on the developer feedback loop and lengthens every CI run on the 3.11/3.12/3.13 matrix.

This feature introduces parallel test execution (via `pytest-xdist`) and a small marker taxonomy registered in a new `[tool.pytest.ini_options]` section of the root `pyproject.toml`. The goal is a substantial wall-clock reduction while preserving the suite's current pass/fail outcome and determinism, without introducing flakiness from parallelism. Because workers run as separate processes, the suite's filesystem behavior (conftests that snap/recover the working directory, tests that write progress files, temp PDFs, or other fixed-path artifacts) must remain correct under concurrent execution; non-parallel-safe tests must be identified and either fixed or marked.

Centralized Hypothesis example-count profiles are owned by a separate spec (`hypothesis-settings-centralization`) and are out of scope here, except where parallel execution interacts with Hypothesis (database/example caching across workers).

## Glossary

- **Test_Suite**: The complete collection of pytest tests under `senzing-bootcamp/tests/` and `tests/`.
- **Pytest_Config**: The `[tool.pytest.ini_options]` section in the root `pyproject.toml` file.
- **Xdist**: The `pytest-xdist` plugin that distributes test execution across multiple worker processes.
- **Worker**: A separate operating-system process spawned by Xdist that executes a subset of the Test_Suite.
- **Worker_Count**: The number of Xdist Workers used for a run (e.g., a fixed integer or `auto`, which derives the count from available CPUs).
- **Marker**: A pytest marker (e.g., `slow`, `property`) used to categorize tests for selective runs.
- **Marker_Taxonomy**: The set of registered Markers declared in Pytest_Config.
- **Strict_Markers**: The pytest `--strict-markers` option that causes pytest to error on any unregistered Marker.
- **CI_Pipeline**: The GitHub Actions workflow at `.github/workflows/validate-power.yml`, specifically the "Run tests" step.
- **CWD_Fixture**: The conftest behavior that snaps the current working directory to the project root before each test (`tests/conftest.py`) and recovers it afterward (`senzing-bootcamp/tests/conftest.py`).
- **Non_Parallel_Safe_Test**: A test whose correctness depends on isolation that parallel Workers break (e.g., shared cwd assumptions, writes to fixed file paths, shared global state, or order dependence).
- **Hypothesis_Database**: The on-disk example store Hypothesis uses to record and replay failing examples (the `.hypothesis/` directory).
- **Developer**: A contributor running the Test_Suite locally.
- **Maintainer**: A contributor responsible for CI configuration and dependency management.

## Requirements

### Requirement 1: Adopt pytest-xdist for parallel execution

**User Story:** As a Developer, I want the Test_Suite to run across multiple parallel Workers, so that I get faster feedback during local development.

#### Acceptance Criteria

1. THE Test_Suite SHALL declare `pytest-xdist` as a development/test dependency.
2. WHEN a Developer invokes pytest with a parallel Worker_Count option, THE Test_Suite SHALL distribute tests across multiple Workers.
3. WHEN the Test_Suite is executed with parallel Workers, THE Test_Suite SHALL complete in less wall-clock time than the equivalent serial run on the same machine.
4. THE Test_Suite SHALL remain executable serially (a single Worker or no Xdist) for debugging.

### Requirement 2: Add a pytest configuration section to pyproject.toml

**User Story:** As a Maintainer, I want a shared `[tool.pytest.ini_options]` section, so that the project has consistent default pytest options and a registered Marker_Taxonomy.

#### Acceptance Criteria

1. THE Pytest_Config SHALL exist as a `[tool.pytest.ini_options]` section in the root `pyproject.toml` file.
2. THE Pytest_Config SHALL register every Marker in the Marker_Taxonomy.
3. THE Pytest_Config SHALL define the default test discovery paths as `senzing-bootcamp/tests/` and `tests/`.
4. WHEN pytest is invoked without explicit path arguments, THE Test_Suite SHALL discover and collect tests from the configured discovery paths.
5. THE Pytest_Config SHALL preserve the current test output behavior equivalent to the existing `-v --tb=short` invocation.

### Requirement 3: Register a marker taxonomy with strict markers

**User Story:** As a Developer, I want a small set of registered Markers with strict enforcement, so that I can run selective subsets (e.g., skip slow or property tests for a quick smoke run) and catch typos in Marker names.

#### Acceptance Criteria

1. THE Marker_Taxonomy SHALL include a Marker that categorizes long-running tests and a Marker that categorizes property-based (Hypothesis) tests.
2. THE Pytest_Config SHALL enable Strict_Markers.
3. WHEN Strict_Markers is enabled and a test uses an unregistered Marker, THE Test_Suite SHALL fail collection with an error identifying the unregistered Marker.
4. WHEN a Developer selects tests by a registered Marker expression, THE Test_Suite SHALL execute only the tests matching that expression.
5. WHEN the Test_Suite is collected with Strict_Markers enabled and no Worker selection, THE Test_Suite SHALL collect without Marker errors (all in-use Markers are registered).

### Requirement 4: Preserve working-directory isolation under parallel workers

**User Story:** As a Developer, I want the CWD_Fixture behavior to remain correct under parallel Workers, so that tests relying on the project-root working directory do not interfere with one another.

#### Acceptance Criteria

1. WHILE the Test_Suite runs under parallel Workers, THE CWD_Fixture SHALL snap the working directory to the project root before each test within each Worker.
2. WHILE the Test_Suite runs under parallel Workers, THE CWD_Fixture SHALL recover the working directory after each test within each Worker.
3. WHEN tests execute concurrently across Workers, THE Test_Suite SHALL produce the same per-test pass/fail outcome as a serial run.

### Requirement 5: Ensure filesystem-write isolation under parallel workers

**User Story:** As a Developer, I want tests that write files to avoid collisions across Workers, so that concurrent execution does not produce false failures.

#### Acceptance Criteria

1. WHEN a test writes to the filesystem during a parallel run, THE Test_Suite SHALL ensure that test does not read or overwrite another concurrently running test's files.
2. IF a test writes to a fixed file path that could collide with another Worker, THEN THE Test_Suite SHALL isolate that path per test or per Worker (e.g., via a unique temporary directory).
3. WHEN the Test_Suite completes a parallel run, THE Test_Suite SHALL leave no shared test-generated artifacts that cause a subsequent run to fail.

### Requirement 6: Identify and remediate non-parallel-safe tests

**User Story:** As a Maintainer, I want non-parallel-safe tests identified and addressed, so that the suite is reliably green under parallel execution.

#### Acceptance Criteria

1. THE Test_Suite SHALL identify each Non_Parallel_Safe_Test prior to enabling parallel execution by default.
2. WHEN a Non_Parallel_Safe_Test is identified, THE Test_Suite SHALL either remediate the test to be parallel-safe or constrain its scheduling so it runs without collision.
3. WHERE a test cannot be made parallel-safe through isolation, THE Test_Suite SHALL group that test so it executes on a single Worker or in a serialized scheduling group.
4. WHEN the full Test_Suite runs under parallel Workers, THE Test_Suite SHALL report zero failures attributable to parallel interference.

### Requirement 7: Preserve Hypothesis behavior under parallel execution

**User Story:** As a Developer, I want Hypothesis property tests to behave correctly under parallel Workers, so that example generation and replay are not corrupted by concurrent access.

#### Acceptance Criteria

1. WHILE the Test_Suite runs under parallel Workers, THE Test_Suite SHALL execute Hypothesis-based tests without corrupting the Hypothesis_Database.
2. WHEN Hypothesis tests run across multiple Workers, THE Test_Suite SHALL produce the same pass/fail outcome for those tests as a serial run.
3. THE Test_Suite SHALL NOT change Hypothesis example-count profiles or centralized Hypothesis settings, which are owned by the `hypothesis-settings-centralization` spec.

### Requirement 8: Wire CI to run tests in parallel on the matrix

**User Story:** As a Maintainer, I want the CI_Pipeline to run the Test_Suite in parallel across the Python version matrix, so that CI completes faster while still validating all supported versions.

#### Acceptance Criteria

1. THE CI_Pipeline SHALL install `pytest-xdist` in the "Run tests" step before invoking pytest.
2. WHEN the "Run tests" step executes, THE CI_Pipeline SHALL invoke pytest with a parallel Worker_Count.
3. THE CI_Pipeline SHALL run the parallel Test_Suite on each of the Python 3.11, 3.12, and 3.13 matrix entries.
4. WHEN the parallel Test_Suite passes locally, THE CI_Pipeline SHALL produce the same overall pass/fail result for an equivalent commit.

### Requirement 9: Install and pin test tooling dependencies

**User Story:** As a Maintainer, I want test tooling dependencies installed explicitly and pinned, so that CI runs are reproducible and mirror the existing `pip install pytest hypothesis` pattern.

#### Acceptance Criteria

1. THE CI_Pipeline SHALL install `pytest-xdist` explicitly in the "Run tests" step alongside `pytest` and `hypothesis`.
2. THE CI_Pipeline SHALL install `pytest-xdist` at a pinned version.
3. THE Test_Suite SHALL continue to rely on Python 3.11 or later.
4. THE production scripts SHALL remain free of new runtime dependencies (the new dependency is test/dev tooling only).

### Requirement 10: Preserve determinism and avoid new flakiness

**User Story:** As a Developer, I want parallel execution to preserve the current outcome and not introduce flakiness, so that I can trust a green run.

#### Acceptance Criteria

1. WHEN the Test_Suite runs under parallel Workers, THE Test_Suite SHALL report the same set of passing and failing tests as the serial run for the same commit.
2. WHEN the parallel Test_Suite is run repeatedly on an unchanged commit, THE Test_Suite SHALL produce the same pass/fail result on each run.
3. IF a test produces a different outcome under parallel Workers than under serial execution, THEN THE Test_Suite SHALL treat that test as a Non_Parallel_Safe_Test for remediation under Requirement 6.

## Open Design Decisions

These decisions are intentionally deferred to the design phase:

1. **Worker count strategy**: Whether to use `-n auto`, a fixed integer, or `-n logical`, and whether CI and local defaults should differ (e.g., `auto` capped to a maximum to avoid oversubscription on shared CI runners).
2. **Default location of `-n`**: Whether parallel execution (`-n auto`) is baked into `addopts` in Pytest_Config (parallel-by-default everywhere) or specified only in the CI invocation (config stays serial-by-default, CI opts in). This affects local debugging ergonomics.
3. **Marker names and scope**: The exact Marker names beyond `slow` and `property` (e.g., whether to add `integration`, `smoke`, or `serial`), and whether a dedicated Marker is used to pin Non_Parallel_Safe_Tests to a single Worker.
4. **Non-parallel-safe scheduling mechanism**: Whether to use Xdist load-distribution modes (`--dist loadgroup` / `--dist loadscope`), an `xdist_group` marker, or per-test temp-dir isolation to handle tests with shared-path writes.
5. **Dependency pinning specifics**: The exact pinned version of `pytest-xdist` and whether to introduce a dev-dependency group / constraints file versus inline `pip install` pinning in CI.
6. **Hypothesis + xdist interaction**: Whether the Hypothesis_Database needs per-worker configuration or can be left shared/read-only during parallel runs, coordinated with the `hypothesis-settings-centralization` spec.
7. **`addopts` contents**: Which default options (e.g., `-v`, `--tb=short`, `--strict-markers`) move into Pytest_Config `addopts` versus remaining explicit in CI.
