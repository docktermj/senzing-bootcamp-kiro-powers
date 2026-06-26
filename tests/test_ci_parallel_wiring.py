"""Config-scan tests validating CI wiring for parallel test execution.

Feature: test-suite-parallelization

Validates that ``.github/workflows/validate-power.yml`` runs the test suite in
parallel (pytest ``-n``), that ``requirements-dev.txt`` pins ``pytest-xdist`` at
an exact version, and that the Python matrix still covers 3.11/3.12/3.13.

Per the tech-stack rule (scripts/tests favor stdlib-only parsing over PyYAML),
these assertions read the workflow YAML as text and match against
whitespace/quoting-tolerant regular expressions rather than parsing structured
YAML.

Validates: Requirements 8.2, 8.3, 9.1, 9.2
"""

from __future__ import annotations

import re
from pathlib import Path

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent
WORKFLOW_PATH = PROJECT_ROOT / ".github" / "workflows" / "validate-power.yml"
REQUIREMENTS_DEV_PATH = PROJECT_ROOT / "requirements-dev.txt"

EXPECTED_PYTHON_VERSIONS = ("3.11", "3.12", "3.13")
XDIST_PACKAGE = "pytest-xdist"


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
# Tests: CI parallel wiring
# Validates: Requirements 8.2, 8.3, 9.1, 9.2
# ===========================================================================


class TestCIParallelWiring:
    """Tests verifying the CI workflow runs the suite in parallel on the matrix.

    Validates: Requirements 8.2, 8.3, 9.1, 9.2
    """

    def test_workflow_file_exists(self):
        """The CI workflow file exists at the expected repo-relative path.

        **Validates: Requirements 8.2**
        """
        assert WORKFLOW_PATH.is_file(), f"CI workflow not found at {WORKFLOW_PATH}"

    def test_run_tests_step_invokes_pytest_in_parallel(self):
        """The "Run tests" step invokes pytest with a parallel worker count (``-n``).

        Tolerates reasonable whitespace and either ``-n auto`` or ``-n <N>``.

        **Validates: Requirements 8.2**
        """
        text = load_workflow_text()
        pytest_line = find_pytest_invocation_line(text)
        assert pytest_line is not None, (
            f"No pytest invocation line found in {WORKFLOW_PATH}"
        )
        pattern = re.compile(r"-n\s+\S+")
        assert pattern.search(pytest_line), (
            f"pytest invocation must run in parallel with '-n'. Line: {pytest_line!r}"
        )

    def test_requirements_dev_pins_pytest_xdist_exactly(self):
        """``requirements-dev.txt`` pins ``pytest-xdist`` at an exact version (``==``).

        **Validates: Requirements 9.1, 9.2**
        """
        text = REQUIREMENTS_DEV_PATH.read_text(encoding="utf-8")
        pattern = re.compile(
            rf"^{re.escape(XDIST_PACKAGE)}\s*==\s*\S+", re.MULTILINE
        )
        assert pattern.search(text), (
            f"Expected '{XDIST_PACKAGE}==<version>' (exact pin) in {REQUIREMENTS_DEV_PATH}"
        )

    def test_matrix_lists_all_python_versions(self):
        """The workflow matrix still lists Python 3.11, 3.12, and 3.13.

        Each version is matched as a quoted string token so substrings like a
        bare ``3.1`` cannot satisfy the check.

        **Validates: Requirements 8.3**
        """
        text = load_workflow_text()
        for version in EXPECTED_PYTHON_VERSIONS:
            pattern = re.compile(rf"['\"]{re.escape(version)}['\"]")
            assert pattern.search(text), (
                f"Expected quoted Python version '{version}' in {WORKFLOW_PATH}"
            )
