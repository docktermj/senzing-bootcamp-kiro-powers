"""Tests validating pyproject.toml Ruff configuration and CI workflow structure.

Feature: ci-python-linting
Validates that the Ruff linter is correctly configured and integrated into CI.
"""

from __future__ import annotations

import tomllib
from pathlib import Path

import yaml


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PYPROJECT_PATH = PROJECT_ROOT / "pyproject.toml"
WORKFLOW_PATH = PROJECT_ROOT / ".github" / "workflows" / "validate-power.yml"

EXPECTED_RULE_PREFIXES = ["F", "E", "W", "I"]
EXPECTED_SRC_DIRS = [
    "senzing-bootcamp/scripts",
    "senzing-bootcamp/tests",
    "tests",
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def load_pyproject() -> dict:
    """Parse pyproject.toml and return the full dict."""
    with open(PYPROJECT_PATH, "rb") as f:
        return tomllib.load(f)


def load_workflow() -> dict:
    """Parse the CI workflow YAML and return the full dict."""
    with open(WORKFLOW_PATH, encoding="utf-8") as f:
        return yaml.safe_load(f)


def get_workflow_steps() -> list[dict]:
    """Return the list of steps from the validate job."""
    workflow = load_workflow()
    return workflow["jobs"]["validate"]["steps"]


# ===========================================================================
# Tests: pyproject.toml Ruff configuration
# Validates: Requirements 1.1, 1.2, 1.3, 1.5, 5.1
# ===========================================================================


class TestPyprojectRuffConfiguration:
    """Tests verifying pyproject.toml exists and contains correct Ruff settings.

    Validates: Requirements 1.1, 1.2, 1.3, 1.5, 5.1
    """

    def test_pyproject_exists_with_tool_ruff_section(self):
        """pyproject.toml exists at repo root and contains [tool.ruff].

        **Validates: Requirements 1.1**
        """
        assert PYPROJECT_PATH.is_file(), (
            f"pyproject.toml not found at {PYPROJECT_PATH}"
        )
        data = load_pyproject()
        assert "tool" in data, "pyproject.toml missing [tool] section"
        assert "ruff" in data["tool"], "pyproject.toml missing [tool.ruff] section"

    def test_target_version_is_py311(self):
        """target-version is set to "py311" in [tool.ruff].

        **Validates: Requirements 1.2**
        """
        data = load_pyproject()
        ruff = data["tool"]["ruff"]
        assert "target-version" in ruff, (
            "[tool.ruff] missing target-version"
        )
        assert ruff["target-version"] == "py311", (
            f'Expected target-version "py311", got "{ruff["target-version"]}"'
        )

    def test_select_contains_exact_rule_prefixes(self):
        """select contains exactly ["F", "E", "W", "I"] in [tool.ruff.lint].

        **Validates: Requirements 1.3**
        """
        data = load_pyproject()
        lint = data["tool"]["ruff"]["lint"]
        assert "select" in lint, "[tool.ruff.lint] missing select"
        assert lint["select"] == EXPECTED_RULE_PREFIXES, (
            f"Expected select {EXPECTED_RULE_PREFIXES}, got {lint['select']}"
        )

    def test_src_contains_lint_target_directories(self):
        """src contains the three lint target directories.

        **Validates: Requirements 1.5**
        """
        data = load_pyproject()
        ruff = data["tool"]["ruff"]
        assert "src" in ruff, "[tool.ruff] missing src"
        assert ruff["src"] == EXPECTED_SRC_DIRS, (
            f"Expected src {EXPECTED_SRC_DIRS}, got {ruff['src']}"
        )

    def test_no_runtime_dependency_on_ruff(self):
        """pyproject.toml does not declare ruff as a runtime dependency.

        **Validates: Requirements 5.1**
        """
        data = load_pyproject()
        # Check [project.dependencies] if it exists
        project = data.get("project", {})
        dependencies = project.get("dependencies", [])
        for dep in dependencies:
            assert "ruff" not in dep.lower(), (
                f"ruff found in [project.dependencies]: {dep}"
            )
        # Check [project.optional-dependencies] if it exists
        optional_deps = project.get("optional-dependencies", {})
        for group, deps in optional_deps.items():
            for dep in deps:
                assert "ruff" not in dep.lower(), (
                    f"ruff found in [project.optional-dependencies.{group}]: {dep}"
                )


# ===========================================================================
# Tests: CI workflow lint step structure
# Validates: Requirements 2.1, 2.2, 2.4, 4.2, 5.3
# ===========================================================================


class TestWorkflowLintStep:
    """Tests verifying the CI workflow contains a correctly placed lint step.

    Validates: Requirements 2.1, 2.2, 2.4, 4.2, 5.3
    """

    def test_workflow_contains_lint_step(self):
        """Workflow YAML contains a step named "Lint Python (ruff)".

        **Validates: Requirements 2.1, 2.2**
        """
        steps = get_workflow_steps()
        step_names = [s.get("name", "") for s in steps]
        assert "Lint Python (ruff)" in step_names, (
            f'"Lint Python (ruff)" step not found. Steps: {step_names}'
        )

    def test_lint_step_after_setup_python_before_tests(self):
        """Lint step appears after setup-python and before "Run tests".

        **Validates: Requirements 2.4**
        """
        steps = get_workflow_steps()
        step_names = [s.get("name", "") for s in steps]

        # Find setup-python by its uses field
        setup_python_idx = None
        for i, step in enumerate(steps):
            uses = step.get("uses", "")
            if "setup-python" in uses:
                setup_python_idx = i
                break

        assert setup_python_idx is not None, "setup-python step not found"

        lint_idx = step_names.index("Lint Python (ruff)")
        assert lint_idx > setup_python_idx, (
            f"Lint step (index {lint_idx}) must appear after "
            f"setup-python (index {setup_python_idx})"
        )

        # Find "Run tests" step
        assert "Run tests" in step_names, '"Run tests" step not found'
        test_idx = step_names.index("Run tests")
        assert lint_idx < test_idx, (
            f"Lint step (index {lint_idx}) must appear before "
            f"Run tests (index {test_idx})"
        )

    def test_lint_step_no_suppression_flags(self):
        """Lint step does not contain --exit-zero or continue-on-error.

        **Validates: Requirements 4.2**
        """
        steps = get_workflow_steps()
        lint_step = None
        for step in steps:
            if step.get("name") == "Lint Python (ruff)":
                lint_step = step
                break

        assert lint_step is not None, "Lint step not found"

        run_content = lint_step.get("run", "")
        assert "--exit-zero" not in run_content, (
            "Lint step must not use --exit-zero"
        )
        assert lint_step.get("continue-on-error") is not True, (
            "Lint step must not set continue-on-error: true"
        )


# ===========================================================================
# Property-Based Tests: Lint configuration completeness
# Validates: Requirements 1.3, 1.5, 3.1, 3.2, 3.3
# ===========================================================================

from hypothesis import given, settings
from hypothesis import strategies as st


def _has_all_rule_prefixes(prefixes: list[str]) -> bool:
    """Return True if prefixes contains all four required rule prefixes."""
    return set(EXPECTED_RULE_PREFIXES).issubset(set(prefixes))


def _has_all_src_dirs(dirs: list[str]) -> bool:
    """Return True if dirs contains all three required lint target directories."""
    return set(EXPECTED_SRC_DIRS).issubset(set(dirs))


@st.composite
def st_rule_subset(draw: st.DrawFn) -> list[str]:
    """Generate a random proper subset of the required rule prefixes (missing at least one)."""
    included = draw(
        st.lists(
            st.sampled_from(EXPECTED_RULE_PREFIXES),
            min_size=0,
            max_size=len(EXPECTED_RULE_PREFIXES) - 1,
            unique=True,
        )
    )
    return included


@st.composite
def st_src_subset(draw: st.DrawFn) -> list[str]:
    """Generate a random proper subset of the required src directories (missing at least one)."""
    included = draw(
        st.lists(
            st.sampled_from(EXPECTED_SRC_DIRS),
            min_size=0,
            max_size=len(EXPECTED_SRC_DIRS) - 1,
            unique=True,
        )
    )
    return included


class TestLintConfigCompletenessProperty:
    """Property-based tests for lint configuration completeness.

    **Validates: Requirements 1.3, 1.5, 3.1, 3.2, 3.3**

    Property: For any valid pyproject.toml consumed by Ruff, the configuration
    SHALL contain all four required rule prefixes (F, E, W, I) and target exactly
    the three specified directories, ensuring that no lint target is accidentally
    omitted or extra rules silently added.
    """

    @given(subset=st_rule_subset())
    @settings(max_examples=20)
    def test_incomplete_rule_prefixes_fail_completeness(self, subset: list[str]):
        """Any proper subset of required rule prefixes is incomplete.

        **Validates: Requirements 1.3, 3.1, 3.2, 3.3**
        """
        assert not _has_all_rule_prefixes(subset), (
            f"Subset {subset} should not satisfy completeness "
            f"(missing at least one of {EXPECTED_RULE_PREFIXES})"
        )

    @given(subset=st_src_subset())
    @settings(max_examples=20)
    def test_incomplete_src_dirs_fail_completeness(self, subset: list[str]):
        """Any proper subset of required src directories is incomplete.

        **Validates: Requirements 1.5**
        """
        assert not _has_all_src_dirs(subset), (
            f"Subset {subset} should not satisfy completeness "
            f"(missing at least one of {EXPECTED_SRC_DIRS})"
        )

    def test_actual_config_satisfies_rule_completeness(self):
        """The real pyproject.toml always contains all required rule prefixes.

        **Validates: Requirements 1.3, 3.1, 3.2, 3.3**
        """
        data = load_pyproject()
        actual_rules = data["tool"]["ruff"]["lint"]["select"]
        assert _has_all_rule_prefixes(actual_rules), (
            f"Actual config rules {actual_rules} missing required prefixes "
            f"{EXPECTED_RULE_PREFIXES}"
        )

    def test_actual_config_satisfies_src_completeness(self):
        """The real pyproject.toml always contains all required src directories.

        **Validates: Requirements 1.5**
        """
        data = load_pyproject()
        actual_src = data["tool"]["ruff"]["src"]
        assert _has_all_src_dirs(actual_src), (
            f"Actual config src {actual_src} missing required directories "
            f"{EXPECTED_SRC_DIRS}"
        )
