"""Config-scan tests validating CI wiring for the thorough Hypothesis profile.

Feature: hypothesis-settings-centralization

Validates that ``.github/workflows/validate-power.yml`` forces the ``thorough``
Hypothesis profile for the "Run tests" step, runs across the Python 3.11/3.12/3.13
matrix, and still targets both pytest collection roots.

Per the tech-stack rule (scripts/tests favor stdlib-only parsing over PyYAML),
these assertions read the workflow YAML as text and match against
whitespace/quoting-tolerant regular expressions rather than parsing structured
YAML.

Validates: Requirements 4.1, 4.3, 4.4
"""

from __future__ import annotations

import re
from pathlib import Path

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent
WORKFLOW_PATH = PROJECT_ROOT / ".github" / "workflows" / "validate-power.yml"

EXPECTED_PYTHON_VERSIONS = ("3.11", "3.12", "3.13")
THOROUGH_PROFILE_NAME = "thorough"
ENV_VAR_NAME = "HYPOTHESIS_PROFILE"
PYTEST_ROOTS = ("senzing-bootcamp/tests/", "tests/")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def load_workflow_text() -> str:
    """Read the CI workflow file as raw text.

    Returns:
        The full contents of ``validate-power.yml`` as a string.
    """
    return WORKFLOW_PATH.read_text(encoding="utf-8")


def find_pytest_invocation_line(text: str) -> str | None:
    """Return the first line that invokes pytest, if present.

    Args:
        text: The raw workflow YAML text.

    Returns:
        The matching line (stripped), or ``None`` when no pytest invocation is found.
    """
    for line in text.splitlines():
        if "pytest" in line and "python" in line:
            return line.strip()
    return None


# ===========================================================================
# Tests: CI profile wiring
# Validates: Requirements 4.1, 4.3, 4.4
# ===========================================================================


class TestCIProfileWiring:
    """Tests verifying the CI workflow forces the thorough profile correctly.

    Validates: Requirements 4.1, 4.3, 4.4
    """

    def test_workflow_file_exists(self):
        """The CI workflow file exists at the expected repo-relative path.

        **Validates: Requirements 4.1**
        """
        assert WORKFLOW_PATH.is_file(), (
            f"CI workflow not found at {WORKFLOW_PATH}"
        )

    def test_run_tests_step_sets_thorough_profile(self):
        """The workflow sets ``HYPOTHESIS_PROFILE: thorough`` for the test run.

        Tolerates reasonable whitespace and optional quoting around the value
        (e.g. ``thorough``, ``"thorough"``, ``'thorough'``).

        **Validates: Requirements 4.1**
        """
        text = load_workflow_text()
        pattern = re.compile(
            rf"{re.escape(ENV_VAR_NAME)}\s*:\s*['\"]?{re.escape(THOROUGH_PROFILE_NAME)}['\"]?",
        )
        assert pattern.search(text), (
            f"Expected '{ENV_VAR_NAME}: {THOROUGH_PROFILE_NAME}' in {WORKFLOW_PATH}"
        )

    def test_matrix_lists_all_python_versions(self):
        """The workflow matrix lists Python 3.11, 3.12, and 3.13.

        Each version is matched as a quoted string token so substrings like a
        bare ``3.1`` cannot satisfy the check.

        **Validates: Requirements 4.3**
        """
        text = load_workflow_text()
        for version in EXPECTED_PYTHON_VERSIONS:
            pattern = re.compile(rf"['\"]{re.escape(version)}['\"]")
            assert pattern.search(text), (
                f"Expected quoted Python version '{version}' in {WORKFLOW_PATH}"
            )

    def test_pytest_invocation_targets_both_roots(self):
        """The pytest command still targets both collection roots.

        **Validates: Requirements 4.4**
        """
        text = load_workflow_text()
        pytest_line = find_pytest_invocation_line(text)
        assert pytest_line is not None, (
            f"No pytest invocation line found in {WORKFLOW_PATH}"
        )
        for root in PYTEST_ROOTS:
            assert root in pytest_line, (
                f"pytest invocation must target '{root}'. Line: {pytest_line!r}"
            )
