# Requirements Document

## Introduction

The `senzing-bootcamp` power is validated by a single GitHub Actions workflow, `.github/workflows/validate-power.yml`, which currently runs one `validate` job across a `['3.11', '3.12', '3.13']` Python matrix. That single job executes roughly twenty validation, lint, and documentation-sync gates before running the test suite. Most of these gates validate documentation, YAML, markdown, hook registries, links, and steering budgets, and their results do not depend on the Python interpreter version. Running them on all three Python versions triples the work without producing additional signal.

This feature restructures the CI workflow for efficiency and reproducibility while preserving every existing gate and its pass/fail semantics. The restructuring splits the work into a single-version **gates** job (running the Python-version-independent validation, lint, and documentation-sync gates once) and a **tests** job (running pytest across the `3.11`/`3.12`/`3.13` matrix). It also adds pip dependency caching, a concurrency group that cancels superseded runs, and version pinning for CI-installed tools so runs are reproducible. This is a CI-orchestration change only: the behavior of the underlying validation scripts and tests is not modified.

This feature has a relationship to two sibling efforts. The `test-suite-parallelization` spec concerns how the test suite itself is parallelized, and a separate dependency-pinning effort concerns project dependency management. The tool-version-pinning requirement in this feature concerns only the tools that CI installs (ruff, pytest, hypothesis, and similar) and SHALL be defined so that it does not contradict those sibling specs. Exact mechanisms that overlap are captured in the Open Design Decisions section.

## Glossary

- **CI_Workflow**: The GitHub Actions workflow defined at `.github/workflows/validate-power.yml` that validates the senzing-bootcamp power.
- **Gates_Job**: A CI job that runs the Python-version-independent validation, lint, and documentation-sync gates exactly once on a single Python version.
- **Tests_Job**: A CI job that runs the pytest test suite across the Python version matrix.
- **Gate**: A single named validation, lint, or documentation-sync step that can pass or fail and that influences the overall workflow result.
- **Version_Independent_Gate**: A Gate whose pass/fail result does not change with the Python interpreter version (for example: validate_power, measure_steering --check, validate_commonmark, validate_dependencies, compose_hook_prompts --verify, sync_hook_registry --verify, lint_steering, validate_prerequisites, validate_progress_ci, validate_preferences_ci, validate_mandatory_gates, validate_governance_rules, validate_yaml_schemas, validate_links, ruff check, eval_conversations, generate_power_docs --verify, generate_spec_catalog --check, example_coverage_report --check, scan_brittle_assertions --check).
- **Version_Sensitive_Gate**: A Gate whose pass/fail result can change with the Python interpreter version. The pytest test run is the Version_Sensitive_Gate.
- **Python_Version_Matrix**: The set of Python interpreter versions `3.11`, `3.12`, and `3.13` across which the Tests_Job runs.
- **Gates_Python_Version**: The single Python interpreter version on which the Gates_Job runs.
- **Concurrency_Group**: A GitHub Actions concurrency configuration that groups in-progress runs by ref or pull request so that superseded runs can be cancelled.
- **Pinned_Tool_Version**: A specific, reproducible version specifier for a CI-installed tool (ruff, pytest, hypothesis, and any other tool CI installs).
- **Trigger**: A GitHub Actions event condition that starts the CI_Workflow, including pull_request and push events and their associated path filters.
- **Maintainer**: A developer who maintains the senzing-bootcamp power and its CI pipeline.
- **Contributor**: A developer who opens a pull request against the repository.

## Requirements

### Requirement 1: Split CI into a gates job and a tests job

**User Story:** As a Maintainer, I want the CI validation work split into a single-version gates job and a version-matrix tests job, so that version-independent work runs once instead of three times.

#### Acceptance Criteria

1. THE CI_Workflow SHALL define a Gates_Job that is distinct from the Tests_Job.
2. THE CI_Workflow SHALL define a Tests_Job that is distinct from the Gates_Job.
3. THE Gates_Job SHALL execute every Version_Independent_Gate.
4. THE Tests_Job SHALL execute the Version_Sensitive_Gate.
5. THE Gates_Job SHALL exclude the pytest test run from its executed gates.

### Requirement 2: Preserve all existing gates

**User Story:** As a Maintainer, I want every gate that runs today to continue running on every pull request, so that the restructuring does not weaken validation coverage.

#### Acceptance Criteria

1. WHEN the CI_Workflow runs for a pull request, THE CI_Workflow SHALL execute every Gate present in the pre-restructure workflow.
2. THE CI_Workflow SHALL preserve the pass/fail outcome of each Gate such that a Gate that would fail before the restructuring also fails the CI_Workflow after the restructuring.
3. THE CI_Workflow SHALL invoke each validation script using the form `python senzing-bootcamp/scripts/<script>.py` with the same arguments used in the pre-restructure workflow.
4. THE CI_Workflow SHALL preserve the existing GitHub Actions error annotations and remediation messages associated with the compose_hook_prompts, sync_hook_registry, generate_power_docs, and generate_spec_catalog gates.
5. IF any single Gate fails, THEN THE CI_Workflow SHALL report an overall failure result.

### Requirement 3: Run version-independent gates once on a single Python version

**User Story:** As a Maintainer, I want the version-independent gates to run exactly once on one Python version, so that runner minutes are not spent re-running identical checks.

#### Acceptance Criteria

1. THE Gates_Job SHALL run on exactly one Gates_Python_Version.
2. THE Gates_Job SHALL execute each Version_Independent_Gate exactly once per CI_Workflow run.
3. THE Gates_Job SHALL execute the ruff lint Gate using the ruff `target-version` configured for the project.

### Requirement 4: Run tests across the Python version matrix without fail-fast

**User Story:** As a Maintainer, I want the test suite to run across Python 3.11, 3.12, and 3.13 with results from all versions, so that version-specific failures are all visible.

#### Acceptance Criteria

1. THE Tests_Job SHALL run across the Python_Version_Matrix consisting of `3.11`, `3.12`, and `3.13`.
2. THE Tests_Job SHALL run pytest using the command `python -m pytest senzing-bootcamp/tests/ tests/` for each Python version in the Python_Version_Matrix.
3. THE Tests_Job SHALL configure the matrix with `fail-fast: false` so that a failure on one Python version allows the runs on the other Python versions to continue.
4. IF the pytest run fails on any Python version in the Python_Version_Matrix, THEN THE CI_Workflow SHALL report an overall failure result.

### Requirement 5: Cache pip dependencies

**User Story:** As a Maintainer, I want pip dependencies cached between runs, so that CI does not reinstall tooling from scratch on every run.

#### Acceptance Criteria

1. WHERE a job uses the setup-python action, THE CI_Workflow SHALL enable pip dependency caching for that job.
2. WHEN a cached pip environment is available for a job, THE CI_Workflow SHALL restore that cache before installing tools.

### Requirement 6: Cancel superseded in-progress runs via concurrency control

**User Story:** As a Contributor, I want superseded CI runs to be cancelled automatically, so that pushing new commits to a pull request does not waste runner minutes on outdated runs.

#### Acceptance Criteria

1. THE CI_Workflow SHALL define a Concurrency_Group keyed by the workflow ref or pull request identifier.
2. WHEN a new run starts for a ref or pull request that already has an in-progress run in the same Concurrency_Group, THE CI_Workflow SHALL cancel the in-progress run.

### Requirement 7: Pin CI-installed tool versions for reproducibility

**User Story:** As a Maintainer, I want the versions of CI-installed tools pinned, so that CI runs are reproducible and an unpinned tool upgrade cannot silently change results.

#### Acceptance Criteria

1. THE CI_Workflow SHALL install ruff using a Pinned_Tool_Version.
2. THE CI_Workflow SHALL install pytest using a Pinned_Tool_Version.
3. THE CI_Workflow SHALL install hypothesis using a Pinned_Tool_Version.
4. WHERE the CI_Workflow installs any additional tool, THE CI_Workflow SHALL install that tool using a Pinned_Tool_Version.
5. WHEN the CI_Workflow installs CI tools across separate runs without intervening configuration changes, THE CI_Workflow SHALL install identical tool versions on each run.

### Requirement 8: Preserve existing triggers and path filters

**User Story:** As a Maintainer, I want the existing pull_request and push triggers and path filters preserved, so that CI continues to run on the same events as before.

#### Acceptance Criteria

1. THE CI_Workflow SHALL preserve the pull_request Trigger with the existing path filters `senzing-bootcamp/**`, `tests/**`, `.github/workflows/**`, `.kiro/specs/**`, `.kiro/spec-catalog.yaml`, and `.kiro/SPEC_CATALOG.md`.
2. THE CI_Workflow SHALL preserve the push Trigger restricted to the `main` branch.

### Requirement 9: Verify the restructured workflow preserves behavior

**User Story:** As a Maintainer, I want to verify that the restructured workflow runs every gate with unchanged semantics, so that I can trust the restructuring did not drop or weaken any check.

#### Acceptance Criteria

1. THE CI_Workflow SHALL be parseable as a valid GitHub Actions workflow file.
2. WHEN the set of Gates executed after the restructuring is compared to the set of Gates executed before the restructuring, THE comparison SHALL show that no Gate was removed.
3. WHEN the CI_Workflow runs against a change that introduces a Version_Independent_Gate failure, THE CI_Workflow SHALL report an overall failure result.
4. WHEN the CI_Workflow runs against a change that introduces a pytest failure on at least one Python version, THE CI_Workflow SHALL report an overall failure result.

## Open Design Decisions

These decisions are intentionally deferred to the design phase. They are recorded here to keep the requirements solution-free and to surface genuine choices.

1. **Gates_Python_Version**: Which single Python version the Gates_Job runs on (for example `3.11` to match the project's `target-version=py311`, or the newest supported `3.13`). The requirements only mandate "exactly one" version.
2. **Tool-pinning mechanism**: How Pinned_Tool_Versions are expressed — inline pins in `pip install` commands, a `requirements-dev.txt`, a pip constraints file, or another mechanism. This may overlap with the sibling dependency-pinning effort; the chosen mechanism must not contradict it.
3. **Job topology**: Whether the Gates_Job and Tests_Job run in parallel as independent jobs, or whether the Tests_Job depends on the Gates_Job (via `needs:`). Trade-off is fastest total feedback (parallel) versus not spending matrix minutes when gates fail (dependent).
4. **Runner OS**: Whether both jobs continue to use `ubuntu-latest` or pin to a specific Ubuntu runner image version for additional reproducibility.
5. **Relationship to `test-suite-parallelization`**: Whether the Tests_Job's internal pytest invocation should anticipate parallelization (for example pytest-xdist) defined by that sibling spec, or remain a plain `python -m pytest` invocation here to avoid contradiction.
6. **ruff classification confirmation**: Confirm that running ruff once in the Gates_Job (rather than per Python version) is acceptable given its `target-version=py311` configuration, since ruff's analysis is keyed to the configured target rather than the runtime interpreter.
