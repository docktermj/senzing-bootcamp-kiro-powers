# Design Document

## Overview

This feature adds Python linting via Ruff to the existing CI pipeline. It introduces two artifacts:

1. A `pyproject.toml` at the repository root containing Ruff configuration (target version, rule selection, lint targets).
2. A new step in `.github/workflows/validate-power.yml` that installs Ruff and runs `ruff check` against the designated directories.

The design is intentionally minimal — Ruff is a zero-config-friendly tool, and the implementation consists of a static configuration file plus a two-line CI step.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│  GitHub Actions Workflow (validate-power.yml)            │
│                                                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │ setup-python │→ │ pip install  │→ │ ruff check   │  │
│  │   (3.11)     │  │   ruff       │  │  (lint step) │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
│                                              │          │
│                                              ▼          │
│                                     ┌──────────────┐    │
│                                     │  pytest      │    │
│                                     │  (tests)     │    │
│                                     └──────────────┘    │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│  pyproject.toml (repo root)                             │
│                                                         │
│  [tool.ruff]                                            │
│    target-version = "py311"                             │
│    src = ["senzing-bootcamp/scripts",                   │
│           "senzing-bootcamp/tests", "tests"]            │
│                                                         │
│  [tool.ruff.lint]                                       │
│    select = ["F", "E", "W", "I"]                        │
└─────────────────────────────────────────────────────────┘
```

## Components and Interfaces

### 1. pyproject.toml (New File)

A TOML configuration file at the repository root. It serves as the single source of truth for Ruff settings, ensuring local developer runs and CI produce identical results.

```toml
[tool.ruff]
target-version = "py311"
src = ["senzing-bootcamp/scripts", "senzing-bootcamp/tests", "tests"]

[tool.ruff.lint]
select = ["F", "E", "W", "I"]
```

Key decisions:
- **Line length**: Uses Ruff's default of 88 (not explicitly set, avoiding unnecessary config).
- **Rule prefixes**: F (pyflakes/bugs), E (pycodestyle errors), W (pycodestyle warnings), I (isort imports).
- **No runtime dependency sections**: The file only contains `[tool.ruff]` sections — no `[project.dependencies]` or similar.

### 2. CI Workflow Step (Modified File)

A new step inserted into `.github/workflows/validate-power.yml` between the existing validation steps and the test execution step.

```yaml
- name: Lint Python (ruff)
  run: |
    pip install ruff
    ruff check senzing-bootcamp/scripts/ senzing-bootcamp/tests/ tests/
```

Key decisions:
- **Single step**: Combines install and check in one step for simplicity. The install is fast (ruff is a single binary wheel).
- **Explicit paths**: Targets are listed explicitly in the command rather than relying solely on `src` config, making the CI step self-documenting.
- **No suppression flags**: No `--exit-zero`, `--quiet`, or `continue-on-error`. A violation fails the job.
- **Placement**: After `setup-python` and existing validation steps, before `pytest`.

### Interfaces

This feature has no programmatic interfaces. The two touchpoints are:

| Interface | Type | Consumer |
|-----------|------|----------|
| `pyproject.toml` `[tool.ruff]` | Configuration file | Ruff CLI (local + CI) |
| Workflow step exit code | Process exit code | GitHub Actions runner |

## Data Models

No data models are introduced. The only structured data is the TOML configuration, whose schema is defined by Ruff itself.

## Error Handling

| Scenario | Behavior |
|----------|----------|
| Ruff finds violations | `ruff check` exits non-zero → step fails → workflow fails → PR blocked |
| Ruff installation fails | `pip install ruff` exits non-zero → step fails → workflow fails |
| pyproject.toml has invalid TOML syntax | `ruff check` exits non-zero with parse error → step fails |
| pyproject.toml missing | Ruff runs with defaults (still checks files, just without custom config) |
| Target directory missing | Ruff reports error for missing path → step fails |

All error paths result in a non-zero exit code, which GitHub Actions treats as a job failure. No special error handling logic is needed.

## Testing Strategy

This feature is entirely configuration-based (static TOML and YAML files) with no runtime logic. The testing approach uses example-based tests:

- **Configuration validation tests**: Parse `pyproject.toml` and assert required sections, target version, rule prefixes, and lint target paths are present and correct.
- **Workflow structure tests**: Parse the CI workflow YAML and assert the lint step exists, appears in the correct position (after setup-python, before pytest), and does not use suppression flags.
- **Dependency isolation tests**: Verify ruff does not appear in any runtime dependency section or shipped requirements file.

Property-based testing is not appropriate here because:
1. Configuration values are fixed constants, not functions of varying input.
2. CI step ordering is a static structural property of a YAML file.
3. Running 100+ iterations would not find more bugs than a single assertion.

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system — essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Lint configuration completeness

For any valid pyproject.toml consumed by Ruff, the configuration SHALL contain all four required rule prefixes (F, E, W, I) and target exactly the three specified directories, ensuring that no lint target is accidentally omitted or extra rules silently added.

**Validates: Requirements 1.3, 1.5, 3.1, 3.2, 3.3**
