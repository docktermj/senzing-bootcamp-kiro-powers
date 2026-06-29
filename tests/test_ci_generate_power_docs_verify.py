"""CI-config test for the generate_power_docs.py --verify gate.

Feature: generated-power-docs

Validates that the real ``.github/workflows/validate-power.yml`` wires the
generated-POWER.md drift gate (``generate_power_docs.py --verify``) into the
``gates`` job as a required step, that pytest ("Run tests") runs in the separate
matrixed ``tests`` job, that the failing branch echoes the exact ``--write``
regeneration command as a ``::error::`` message, and that the ``tests`` job runs
across the ``['3.11', '3.12', '3.13']`` matrix with ``fail-fast: false``.

Requirements validated: 7.1, 7.4, 7.5

This is an example test (not property-based). The workflow YAML is parsed with
PyYAML (mirroring ``test_ci_python_linting.py``) for step ordering and matrix
structure; the multi-line ``run`` block is inspected as text for the
``::error::`` failing branch and the exact regeneration command.
"""

from __future__ import annotations

from pathlib import Path

import yaml

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent
WORKFLOW_PATH = PROJECT_ROOT / ".github" / "workflows" / "validate-power.yml"

# The script invocations under test. Searching for these substrings keeps the
# assertions robust against step renames, reformatting, or indentation changes.
VERIFY_CMD = "python senzing-bootcamp/scripts/generate_power_docs.py --verify"
WRITE_CMD = "python senzing-bootcamp/scripts/generate_power_docs.py --write"

# The exact regeneration command emitted as a GitHub Actions error annotation
# when the verify step fails (Req 7.4).
EXPECTED_ERROR_LINE = (
    "::error::Generated POWER.md docs are out of sync. Run: " + WRITE_CMD
)

EXPECTED_PYTHON_MATRIX = ["3.11", "3.12", "3.13"]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def load_workflow() -> dict:
    """Parse the CI workflow YAML and return the full dict."""
    with open(WORKFLOW_PATH, encoding="utf-8") as f:
        return yaml.safe_load(f)


def get_gates_job() -> dict:
    """Return the ``gates`` job definition from the workflow."""
    return load_workflow()["jobs"]["gates"]


def get_gates_steps() -> list[dict]:
    """Return the list of steps from the ``gates`` job."""
    return get_gates_job()["steps"]


def get_tests_job() -> dict:
    """Return the ``tests`` job definition from the workflow."""
    return load_workflow()["jobs"]["tests"]


def get_tests_steps() -> list[dict]:
    """Return the list of steps from the matrixed ``tests`` job."""
    return get_tests_job()["steps"]


def find_pytest_step(steps: list[dict]) -> dict | None:
    """Return the step that runs pytest ("Run tests"), if any."""
    for step in steps:
        if step.get("name") == "Run tests" or "pytest" in step.get("run", ""):
            return step
    return None


def find_verify_step(steps: list[dict]) -> dict | None:
    """Return the step whose ``run`` invokes the generator --verify, if any."""
    for step in steps:
        if VERIFY_CMD in step.get("run", ""):
            return step
    return None


# ===========================================================================
# Tests: generate_power_docs --verify CI step
# Validates: Requirements 7.1, 7.4, 7.5
# ===========================================================================


class TestCiGeneratePowerDocsVerify:
    """Validate the generate_power_docs --verify CI step wiring.

    **Validates: Requirements 7.1, 7.4, 7.5**
    """

    def test_workflow_file_exists(self) -> None:
        """The CI workflow file exists at the expected path."""
        assert WORKFLOW_PATH.is_file(), (
            f"CI workflow not found: {WORKFLOW_PATH}"
        )

    def test_verify_step_present_in_gates_job(self) -> None:
        """The gates job runs generate_power_docs.py --verify (Req 7.1).

        **Validates: Requirements 7.1**
        """
        steps = get_gates_steps()
        assert find_verify_step(steps) is not None, (
            "validate-power.yml must run "
            f"'{VERIFY_CMD}' as a step in the gates job"
        )

    def test_verify_step_is_required_gate(self) -> None:
        """The verify step is a required gate in the gates job and pytest lives in
        the tests job (Req 7.1).

        The CI workflow was split into a single-run ``gates`` job (which owns the
        verify gate) and a matrixed ``tests`` job (which owns pytest). They run
        independently because the gates job declares no ``needs:`` dependency.
        The preserved invariant: the verify gate still runs as a required
        (non-continue-on-error) step, and a pytest step still exists in the tests job.

        **Validates: Requirements 7.1**
        """
        gates_steps = get_gates_steps()
        verify_step = find_verify_step(gates_steps)
        assert verify_step is not None, (
            f"'{VERIFY_CMD}' step not found in the gates job"
        )

        # The verify gate must be required (not soft-failed).
        assert verify_step.get("continue-on-error") is not True, (
            "verify step must be a required gate (continue-on-error must not be true)"
        )

        # The gates job runs independently of tests: it declares no `needs:`.
        assert "needs" not in get_gates_job(), (
            "gates job must not declare a `needs:` dependency so it runs independently"
        )

        # pytest now lives in the tests job.
        assert find_pytest_step(get_tests_steps()) is not None, (
            'pytest / "Run tests" step not found in the tests job'
        )

    def test_failing_branch_echoes_exact_write_command_as_error(self) -> None:
        """The verify step's failing branch echoes the exact --write command
        as a ``::error::`` message (Req 7.4).

        **Validates: Requirements 7.4**
        """
        steps = get_gates_steps()
        verify_step = find_verify_step(steps)
        assert verify_step is not None, (
            f"'{VERIFY_CMD}' step not found in the gates job"
        )

        run_content = verify_step.get("run", "")

        # The failing branch must be wired: `--verify || { ... exit 1; }`.
        assert "||" in run_content, (
            "verify step must guard --verify with a failing branch (`||`)"
        )
        assert "exit 1" in run_content, (
            "verify step failing branch must exit 1 to fail the build"
        )

        # The exact GitHub Actions error annotation containing the runnable
        # --write regeneration command must be emitted.
        assert EXPECTED_ERROR_LINE in run_content, (
            "verify step failing branch must echo the exact error annotation:\n"
            f"  {EXPECTED_ERROR_LINE}\n"
            f"actual run block:\n{run_content}"
        )

        # The annotation must be an ::error:: level message carrying --write.
        assert "::error::" in run_content, (
            "failing branch must emit a GitHub Actions ::error:: annotation"
        )
        assert WRITE_CMD in run_content, (
            "failing branch error message must contain the exact regeneration "
            f"command '{WRITE_CMD}'"
        )

    def test_matrix_is_three_python_versions_with_fail_fast_false(self) -> None:
        """The tests job runs the 3.11/3.12/3.13 matrix with
        fail-fast: false (Req 7.5).

        **Validates: Requirements 7.5**
        """
        job = get_tests_job()
        strategy = job.get("strategy", {})

        assert strategy.get("fail-fast") is False, (
            "tests job strategy must set fail-fast: false so each matrix "
            f"job reports independently; got {strategy.get('fail-fast')!r}"
        )

        matrix = strategy.get("matrix", {})
        python_versions = matrix.get("python-version")
        assert python_versions == EXPECTED_PYTHON_MATRIX, (
            f"Expected python-version matrix {EXPECTED_PYTHON_MATRIX}, "
            f"got {python_versions!r}"
        )
