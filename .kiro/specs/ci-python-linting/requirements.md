# Requirements Document

## Introduction

Add Python linting via Ruff to the CI pipeline so that style violations, import ordering issues, and likely bugs are caught automatically on every pull request. Ruff configuration lives in `pyproject.toml` at the repository root. Violations block the PR (hard fail). The linter targets three directories: `senzing-bootcamp/scripts/`, `senzing-bootcamp/tests/`, and `tests/`.

## Glossary

- **CI_Pipeline**: The GitHub Actions workflow defined in `.github/workflows/validate-power.yml` that runs validation checks on pull requests and pushes to main.
- **Ruff**: A fast Python linter and formatter used as a development/CI-only tool (not a runtime dependency).
- **Lint_Step**: A job step within the CI_Pipeline that executes Ruff to check Python source files.
- **pyproject.toml**: The repository-root configuration file that holds Ruff settings (rule selection, target version, paths).
- **Lint_Targets**: The three directories subject to linting: `senzing-bootcamp/scripts/`, `senzing-bootcamp/tests/`, and `tests/`.

## Requirements

### Requirement 1: Ruff Configuration

**User Story:** As a developer, I want a single configuration file that defines all linting rules, so that local and CI linting produce identical results.

#### Acceptance Criteria

1. THE pyproject.toml SHALL exist at the repository root and contain a `[tool.ruff]` section.
2. THE pyproject.toml SHALL set the Python target version to 3.11 in the `[tool.ruff]` section.
3. THE pyproject.toml SHALL select rule prefixes F, E, W, and I in the `[tool.ruff.lint]` section.
4. THE pyproject.toml SHALL use the default line length of 88 characters.
5. THE pyproject.toml SHALL specify the Lint_Targets as the `src` paths for Ruff to check.

### Requirement 2: CI Pipeline Integration

**User Story:** As a maintainer, I want the CI pipeline to run Ruff on every PR, so that linting violations are caught before merge.

#### Acceptance Criteria

1. THE CI_Pipeline SHALL install Ruff via pip before the Lint_Step executes.
2. THE CI_Pipeline SHALL execute `ruff check` against the Lint_Targets as a dedicated step.
3. WHEN Ruff reports one or more violations, THE Lint_Step SHALL exit with a non-zero status code causing the workflow to fail.
4. THE Lint_Step SHALL run after the Python environment is set up and before the test execution step.

### Requirement 3: Rule Set Coverage

**User Story:** As a developer, I want the linter to catch bugs, style issues, and import ordering problems, so that code quality remains consistent.

#### Acceptance Criteria

1. THE Ruff configuration SHALL enable pyflakes rules (prefix F) for detecting likely bugs such as undefined names and unused imports.
2. THE Ruff configuration SHALL enable pycodestyle error rules (prefix E) and warning rules (prefix W) for enforcing basic style conventions.
3. THE Ruff configuration SHALL enable isort rules (prefix I) for enforcing consistent import ordering.

### Requirement 4: Hard Fail Enforcement

**User Story:** As a maintainer, I want lint failures to block PR merges, so that no violating code enters the main branch.

#### Acceptance Criteria

1. WHEN the Lint_Step exits with a non-zero status code, THE CI_Pipeline SHALL mark the workflow run as failed.
2. THE Lint_Step SHALL NOT use flags that suppress or downgrade violations to warnings (no `--exit-zero` or equivalent).

### Requirement 5: Development-Only Dependency

**User Story:** As a developer, I want Ruff to remain a CI/dev-only tool, so that it does not affect the distributed power or runtime scripts.

#### Acceptance Criteria

1. THE pyproject.toml SHALL NOT declare Ruff as a runtime dependency.
2. THE CI_Pipeline SHALL install Ruff only within the CI job environment using pip.
3. THE Ruff package SHALL NOT be added to any requirements file that ships with the power.
