"""Structural validation tests for the restructured CI workflow.

Feature: ci-workflow-restructure

This module parses ``.github/workflows/validate-power.yml`` and the repo-root
``requirements-dev.txt`` and asserts the design's Correctness Properties plus
smoke/configuration checks, proving the gates/tests restructuring does not drop
or weaken any gate.

Because the verified artifacts are static configuration files (a GitHub Actions
workflow and a pip requirements file), the Correctness Properties range over
finite enumerable sets (gates, jobs, tool lines) and are implemented as
example-driven structural assertions rather than a randomized Hypothesis
harness.

Property test classes (``TestGatePreservation``, ``TestMatrixCachingPinning``,
``TestWorkflowSmoke``) are added by tasks 3.2-3.4. This module provides the
shared helpers and canonical gate-set fixtures they build on.
"""

from __future__ import annotations

import re
import sys
import tomllib
from pathlib import Path

import yaml

# Make scripts importable (repo test convention), even though this module does
# not import a script today — keeps the path setup consistent with sibling tests.
_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

# ---------------------------------------------------------------------------
# Repo-root path resolution
# ---------------------------------------------------------------------------
# This file lives at <repo>/senzing-bootcamp/tests/test_validate_power_workflow.py
# so the repo root is two parents up from the tests directory.
_REPO_ROOT = Path(__file__).resolve().parents[2]
_WORKFLOW_PATH = _REPO_ROOT / ".github" / "workflows" / "validate-power.yml"
_REQUIREMENTS_DEV_PATH = _REPO_ROOT / "requirements-dev.txt"
_PYPROJECT_PATH = _REPO_ROOT / "pyproject.toml"

# ---------------------------------------------------------------------------
# Canonical gate-set fixtures (from the design's gate-to-job mapping)
# ---------------------------------------------------------------------------
# The 20 version-independent gate command strings, copied verbatim from the
# design. Each must survive the restructuring as a substring of some step's
# ``run:`` in the gates job.
CANONICAL_GATE_COMMANDS: list[str] = [
    "python senzing-bootcamp/scripts/validate_power.py",
    "python senzing-bootcamp/scripts/measure_steering.py --check",
    "python senzing-bootcamp/scripts/validate_commonmark.py",
    "python senzing-bootcamp/scripts/validate_dependencies.py",
    "python senzing-bootcamp/scripts/compose_hook_prompts.py --verify",
    "python senzing-bootcamp/scripts/sync_hook_registry.py --verify",
    "python senzing-bootcamp/scripts/lint_steering.py",
    "python senzing-bootcamp/scripts/validate_prerequisites.py",
    "python senzing-bootcamp/scripts/validate_progress_ci.py",
    "python senzing-bootcamp/scripts/validate_preferences_ci.py",
    "python senzing-bootcamp/scripts/validate_mandatory_gates.py",
    "python senzing-bootcamp/scripts/validate_governance_rules.py",
    "python senzing-bootcamp/scripts/validate_yaml_schemas.py",
    "python senzing-bootcamp/scripts/validate_links.py --timeout 10",
    "ruff check senzing-bootcamp/scripts/ senzing-bootcamp/tests/ tests/",
    "python senzing-bootcamp/scripts/eval_conversations.py",
    "python senzing-bootcamp/scripts/generate_power_docs.py --verify",
    "python senzing-bootcamp/scripts/generate_spec_catalog.py --check",
    "python senzing-bootcamp/scripts/example_coverage_report.py --check",
    "python senzing-bootcamp/scripts/scan_brittle_assertions.py --check",
]

# The single version-sensitive gate (pytest), as a canonical substring.
CANONICAL_PYTEST_COMMAND: str = "python -m pytest senzing-bootcamp/tests/ tests/"

# The four verify-gate ``::error::`` remediation strings that must be preserved
# verbatim (Property 4 / Req 2.4).
CANONICAL_ERROR_ANNOTATIONS: list[str] = [
    "::error::Composed hook prompts drifted. Run: "
    "python senzing-bootcamp/scripts/compose_hook_prompts.py --write",
    "::error::Hook registry is out of sync. Run: "
    "python senzing-bootcamp/scripts/sync_hook_registry.py --write",
    "::error::Generated POWER.md docs are out of sync. Run: "
    "python senzing-bootcamp/scripts/generate_power_docs.py --write",
    "::error::Spec catalog index is out of sync. Run: "
    "python senzing-bootcamp/scripts/generate_spec_catalog.py",
]

# The expected Python version matrix for the tests job (Property 5).
CANONICAL_PYTHON_MATRIX: list[str] = ["3.11", "3.12", "3.13"]

# The six pull_request path globs that must be preserved verbatim (Req 8.1).
CANONICAL_PR_PATHS: list[str] = [
    "senzing-bootcamp/**",
    "tests/**",
    ".github/workflows/**",
    ".kiro/specs/**",
    ".kiro/spec-catalog.yaml",
    ".kiro/SPEC_CATALOG.md",
]

# Pinned-tool line format and required tools (Property 7).
PINNED_LINE_RE = re.compile(r"^\S+==\S+$")
REQUIRED_PINNED_TOOLS: list[str] = ["ruff", "pytest", "hypothesis"]


# ---------------------------------------------------------------------------
# Module helpers
# ---------------------------------------------------------------------------
def load_workflow() -> dict:
    """Load and parse the validate-power workflow.

    Returns:
        The parsed workflow mapping. Returns an empty dict if the file is
        absent or parses to a non-mapping / empty document, so callers can
        assert on structure without crashing at collection time.
    """
    if not _WORKFLOW_PATH.exists():
        return {}
    with _WORKFLOW_PATH.open(encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    return data if isinstance(data, dict) else {}


def collect_run_strings_by_job(workflow: dict | None = None) -> dict[str, list[str]]:
    """Collect every step ``run:`` string, grouped by job name.

    Steps without a ``run`` key (e.g. ``uses:`` action steps) are skipped.

    Args:
        workflow: A pre-parsed workflow mapping. When ``None``, the workflow is
            loaded via :func:`load_workflow`.

    Returns:
        A mapping of ``job_name -> list[str]`` of ``run`` strings in step order.
        Jobs with no run steps map to an empty list. Returns an empty dict when
        the workflow has no ``jobs`` mapping.
    """
    if workflow is None:
        workflow = load_workflow()

    jobs = workflow.get("jobs")
    if not isinstance(jobs, dict):
        return {}

    result: dict[str, list[str]] = {}
    for job_name, job in jobs.items():
        runs: list[str] = []
        steps = job.get("steps") if isinstance(job, dict) else None
        if isinstance(steps, list):
            for step in steps:
                if isinstance(step, dict) and "run" in step:
                    run_value = step["run"]
                    if isinstance(run_value, str):
                        runs.append(run_value)
        result[job_name] = runs
    return result


def read_requirements_dev() -> list[str]:
    """Read the repo-root ``requirements-dev.txt`` lines.

    Returns:
        The file's lines with trailing newlines stripped, preserving order.
        Returns an empty list if the file does not exist.
    """
    if not _REQUIREMENTS_DEV_PATH.exists():
        return []
    return _REQUIREMENTS_DEV_PATH.read_text(encoding="utf-8").splitlines()


# ---------------------------------------------------------------------------
# Property tests: gate-set preservation and placement (Properties 1-4)
# ---------------------------------------------------------------------------
class TestGatePreservation:
    """Gate-set preservation and placement invariants for the restructure.

    These structural assertions protect against silently dropping or weakening
    a gate while splitting the original single job into ``gates`` + ``tests``.
    """

    def test_gate_set_preserved_across_jobs(self) -> None:
        """Property 1: every canonical gate (and pytest) survives the split.

        Feature: ci-workflow-restructure, Property 1: Gate-set preservation
        (no gate removed, args unchanged) — every canonical gate command, plus
        the pytest command, appears as a substring of some step ``run`` across
        the union of the ``gates`` and ``tests`` jobs.

        Validates: Requirements 2.1, 2.2, 2.3, 9.2
        """
        runs_by_job = collect_run_strings_by_job()
        union_runs = [
            run
            for job in ("gates", "tests")
            for run in runs_by_job.get(job, [])
        ]

        for command in CANONICAL_GATE_COMMANDS:
            assert any(command in run for run in union_runs), (
                f"Gate command not found in gates+tests run strings: {command!r}"
            )

        assert any(CANONICAL_PYTEST_COMMAND in run for run in union_runs), (
            f"Pytest command not found in gates+tests run strings: "
            f"{CANONICAL_PYTEST_COMMAND!r}"
        )

    def test_version_independent_gates_in_gates_job(self) -> None:
        """Property 2: all 20 version-independent gates live in ``gates``.

        Feature: ci-workflow-restructure, Property 2: Version-independent gates
        placed in the gates job — each of the 20 commands appears as a substring
        of some ``gates``-job step run string.

        Validates: Requirements 1.3, 1.5
        """
        gates_runs = collect_run_strings_by_job().get("gates", [])

        for command in CANONICAL_GATE_COMMANDS:
            assert any(command in run for run in gates_runs), (
                f"Version-independent gate missing from gates job: {command!r}"
            )

    def test_each_gate_runs_exactly_once_no_matrix(self) -> None:
        """Property 3: each version-independent gate runs once, gates has no matrix.

        Feature: ci-workflow-restructure, Property 3: Each version-independent
        gate runs exactly once / no matrix — each of the 20 commands appears in
        exactly one ``gates`` step run string, and ``jobs.gates`` declares no
        ``strategy`` (or no ``strategy.matrix``).

        Validates: Requirements 3.1, 3.2
        """
        workflow = load_workflow()
        gates_runs = collect_run_strings_by_job(workflow).get("gates", [])

        for command in CANONICAL_GATE_COMMANDS:
            count = sum(1 for run in gates_runs if command in run)
            assert count == 1, (
                f"Gate command must run exactly once in gates job, found "
                f"{count}: {command!r}"
            )

        gates_job = workflow.get("jobs", {}).get("gates", {})
        strategy = gates_job.get("strategy") if isinstance(gates_job, dict) else None
        if strategy is not None:
            assert not (isinstance(strategy, dict) and "matrix" in strategy), (
                "gates job must not declare a strategy.matrix (no version matrix)"
            )

    def test_verify_gate_error_annotations_preserved(self) -> None:
        """Property 4: verify-gate ``::error::`` remediation strings are kept.

        Feature: ci-workflow-restructure, Property 4: Verify-gate error
        annotations preserved — each of the four ``::error::`` remediation
        strings appears verbatim as a substring of some run string in the
        workflow.

        Validates: Requirements 2.4
        """
        all_runs = [
            run
            for runs in collect_run_strings_by_job().values()
            for run in runs
        ]

        for annotation in CANONICAL_ERROR_ANNOTATIONS:
            assert any(annotation in run for run in all_runs), (
                f"Verify-gate error annotation not found in any run string: "
                f"{annotation!r}"
            )


# ---------------------------------------------------------------------------
# Property tests: matrix, caching, and pinning (Properties 5-7)
# ---------------------------------------------------------------------------
class TestMatrixCachingPinning:
    """Matrix, pip-caching, and tool-pinning invariants for the restructure.

    These structural assertions confirm pytest runs across the full Python
    matrix, every ``setup-python`` step enables pip caching, and every
    CI-installed tool is exactly pinned.
    """

    def test_pytest_runs_on_every_matrix_version(self) -> None:
        """Property 5: pytest runs on every matrix version.

        Feature: ci-workflow-restructure, Property 5: pytest runs on every
        matrix version — ``jobs.tests.strategy.matrix.python-version`` equals
        the canonical matrix, ``jobs.tests.strategy.fail-fast`` is ``False``,
        and some ``tests``-job step run string runs the canonical pytest command.

        Validates: Requirements 1.4, 4.1, 4.2, 4.3
        """
        workflow = load_workflow()
        tests_job = workflow.get("jobs", {}).get("tests")
        assert isinstance(tests_job, dict), (
            "jobs.tests must be a defined job mapping"
        )

        strategy = tests_job.get("strategy")
        assert isinstance(strategy, dict), "jobs.tests must declare a strategy"

        matrix = strategy.get("matrix")
        assert isinstance(matrix, dict), "jobs.tests.strategy must declare a matrix"
        assert matrix.get("python-version") == CANONICAL_PYTHON_MATRIX, (
            f"jobs.tests.strategy.matrix.python-version must equal "
            f"{CANONICAL_PYTHON_MATRIX!r}, got "
            f"{matrix.get('python-version')!r}"
        )

        assert strategy.get("fail-fast") is False, (
            "jobs.tests.strategy.fail-fast must be False so every matrix leg runs"
        )

        tests_runs = collect_run_strings_by_job(workflow).get("tests", [])
        assert any(CANONICAL_PYTEST_COMMAND in run for run in tests_runs), (
            f"Pytest command not found in tests-job run strings: "
            f"{CANONICAL_PYTEST_COMMAND!r}"
        )

    def test_every_setup_python_job_enables_pip_caching(self) -> None:
        """Property 6: every setup-python step enables pip caching.

        Feature: ci-workflow-restructure, Property 6: Every setup-python job
        enables pip caching — for every job that has a step whose ``uses``
        starts with ``actions/setup-python@``, that step's ``with.cache`` is
        ``'pip'``.

        Validates: Requirements 5.1, 5.2
        """
        workflow = load_workflow()
        jobs = workflow.get("jobs", {})
        assert isinstance(jobs, dict), "workflow must declare a jobs mapping"

        setup_python_steps_seen = 0
        for job_name, job in jobs.items():
            steps = job.get("steps") if isinstance(job, dict) else None
            if not isinstance(steps, list):
                continue
            for step in steps:
                if not isinstance(step, dict):
                    continue
                uses = step.get("uses")
                if isinstance(uses, str) and uses.startswith("actions/setup-python@"):
                    setup_python_steps_seen += 1
                    with_block = step.get("with")
                    assert isinstance(with_block, dict), (
                        f"setup-python step in job {job_name!r} must have a "
                        f"with: block"
                    )
                    assert with_block.get("cache") == "pip", (
                        f"setup-python step in job {job_name!r} must set "
                        f"with.cache == 'pip', got {with_block.get('cache')!r}"
                    )

        assert setup_python_steps_seen > 0, (
            "expected at least one actions/setup-python step in the workflow"
        )

    def test_every_ci_installed_tool_is_exactly_pinned(self) -> None:
        """Property 7: every CI-installed tool is exactly pinned.

        Feature: ci-workflow-restructure, Property 7: Every CI-installed tool
        is exactly pinned — every non-comment, non-blank line of
        ``requirements-dev.txt`` matches ``PINNED_LINE_RE`` (``^\\S+==\\S+$``),
        and each tool in ``REQUIRED_PINNED_TOOLS`` appears as the package name
        of some line.

        Validates: Requirements 7.1, 7.2, 7.3, 7.4, 7.5
        """
        lines = read_requirements_dev()
        package_names: list[str] = []
        for raw_line in lines:
            stripped = raw_line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            assert PINNED_LINE_RE.match(stripped), (
                f"requirements-dev.txt line is not exactly pinned "
                f"(expected name==version): {stripped!r}"
            )
            package_names.append(stripped.split("==", 1)[0])

        for tool in REQUIRED_PINNED_TOOLS:
            assert tool in package_names, (
                f"required pinned tool {tool!r} not found in requirements-dev.txt "
                f"package names: {package_names!r}"
            )


# ---------------------------------------------------------------------------
# Smoke / configuration checks
# ---------------------------------------------------------------------------
class TestWorkflowSmoke:
    """Smoke and configuration checks for the restructured CI workflow.

    These lightweight assertions confirm the workflow parses, declares the
    expected gates/tests jobs, never swallows failures, preserves triggers and
    concurrency, and that the ruff target-version is unchanged.
    """

    def test_workflow_parses_with_top_level_keys(self) -> None:
        """Workflow loads via ``yaml.safe_load`` with name/on/jobs keys.

        PyYAML parses the bareword ``on:`` key as the boolean ``True``, so the
        triggers block is looked up via ``workflow.get('on', workflow.get(True))``.

        Validates: Requirements 9.1
        """
        workflow = load_workflow()
        assert isinstance(workflow, dict) and workflow, (
            "workflow must parse to a non-empty mapping"
        )
        assert "name" in workflow, "workflow must declare a top-level name key"
        assert "jobs" in workflow, "workflow must declare a top-level jobs key"

        triggers = workflow.get("on", workflow.get(True))
        assert triggers is not None, (
            "workflow must declare an 'on'/triggers block (may parse as True key)"
        )

    def test_two_distinct_jobs(self) -> None:
        """``jobs`` contains distinct ``gates`` and ``tests`` keys.

        Validates: Requirements 1.1, 1.2
        """
        workflow = load_workflow()
        jobs = workflow.get("jobs")
        assert isinstance(jobs, dict), "workflow must declare a jobs mapping"
        assert "gates" in jobs, "jobs must contain a 'gates' job"
        assert "tests" in jobs, "jobs must contain a 'tests' job"

    def test_gates_job_uses_single_python_version(self) -> None:
        """The ``gates`` job's setup-python step pins ``python-version`` 3.11.

        Validates: Requirements 3.1
        """
        workflow = load_workflow()
        gates_job = workflow.get("jobs", {}).get("gates")
        assert isinstance(gates_job, dict), "jobs.gates must be a defined mapping"

        setup_versions: list[str] = []
        for step in gates_job.get("steps", []):
            if not isinstance(step, dict):
                continue
            uses = step.get("uses")
            if isinstance(uses, str) and uses.startswith("actions/setup-python@"):
                with_block = step.get("with")
                assert isinstance(with_block, dict), (
                    "gates setup-python step must have a with: block"
                )
                setup_versions.append(with_block.get("python-version"))

        assert "3.11" in setup_versions, (
            f"gates setup-python step must pin python-version '3.11', got "
            f"{setup_versions!r}"
        )

    def test_gates_job_excludes_pytest(self) -> None:
        """No ``gates`` step run string contains ``pytest``.

        Validates: Requirements 1.5
        """
        gates_runs = collect_run_strings_by_job().get("gates", [])
        for run in gates_runs:
            assert "pytest" not in run, (
                f"gates job must not run pytest, found in run string: {run!r}"
            )

    def test_no_swallowed_failures(self) -> None:
        """No job or step sets ``continue-on-error: true``.

        Walks job-level ``continue-on-error`` and each step's
        ``continue-on-error`` across all jobs.

        Validates: Requirements 2.5, 4.4, 9.3, 9.4
        """
        workflow = load_workflow()
        jobs = workflow.get("jobs", {})
        assert isinstance(jobs, dict), "workflow must declare a jobs mapping"

        for job_name, job in jobs.items():
            if not isinstance(job, dict):
                continue
            assert job.get("continue-on-error") is not True, (
                f"job {job_name!r} must not set continue-on-error: true"
            )
            for step in job.get("steps", []):
                if not isinstance(step, dict):
                    continue
                assert step.get("continue-on-error") is not True, (
                    f"a step in job {job_name!r} must not set "
                    f"continue-on-error: true"
                )

    def test_concurrency_group_and_cancel(self) -> None:
        """Concurrency references workflow/ref and cancels in-progress runs.

        Validates: Requirements 6.1, 6.2
        """
        workflow = load_workflow()
        concurrency = workflow.get("concurrency")
        assert isinstance(concurrency, dict), (
            "workflow must declare a concurrency mapping"
        )

        group = concurrency.get("group")
        assert isinstance(group, str), "concurrency.group must be a string"
        assert "${{ github.workflow }}" in group, (
            f"concurrency.group must reference github.workflow, got {group!r}"
        )
        assert "github.ref" in group, (
            f"concurrency.group must reference github.ref, got {group!r}"
        )

        assert concurrency.get("cancel-in-progress") is True, (
            "concurrency.cancel-in-progress must be True"
        )

    def test_triggers_preserved(self) -> None:
        """Triggers preserve PR paths and the push branch.

        The triggers block is looked up via
        ``workflow.get('on', workflow.get(True))`` to account for PyYAML parsing
        the bareword ``on:`` key as the boolean ``True``.

        Validates: Requirements 8.1, 8.2
        """
        workflow = load_workflow()
        triggers = workflow.get("on", workflow.get(True))
        assert isinstance(triggers, dict), "workflow must declare a triggers block"

        pull_request = triggers.get("pull_request")
        assert isinstance(pull_request, dict), "triggers must declare pull_request"
        assert pull_request.get("paths") == CANONICAL_PR_PATHS, (
            f"pull_request.paths must equal {CANONICAL_PR_PATHS!r}, got "
            f"{pull_request.get('paths')!r}"
        )

        push = triggers.get("push")
        assert isinstance(push, dict), "triggers must declare push"
        assert push.get("branches") == ["main"], (
            f"push.branches must equal ['main'], got {push.get('branches')!r}"
        )

    def test_ruff_target_version_unchanged(self) -> None:
        """The ``[tool.ruff]`` ``target-version`` remains ``py311``.

        Parses ``pyproject.toml`` with stdlib ``tomllib`` and navigates
        ``data['tool']['ruff']['target-version']``.

        Validates: Requirements 3.3
        """
        data = tomllib.loads(_PYPROJECT_PATH.read_text(encoding="utf-8"))
        ruff_config = data.get("tool", {}).get("ruff", {})
        assert ruff_config.get("target-version") == "py311", (
            f"[tool.ruff] target-version must be 'py311', got "
            f"{ruff_config.get('target-version')!r}"
        )
