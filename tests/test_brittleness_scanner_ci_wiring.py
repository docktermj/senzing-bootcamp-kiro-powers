"""CI-wiring test for the brittleness scanner validation step.

Validates that the real ``.github/workflows/validate-power.yml`` wires the
brittleness scanner (``scan_brittle_assertions.py``) as a required CI step
that runs *before* the pytest step, using the ``--check`` flag and without a
``continue-on-error`` escape hatch.

Requirements validated: 3.5, 3.6

This is an example test (not property-based). To stay dependency-free (the CI
test environment only installs ``pytest`` and ``hypothesis``, not PyYAML, and
the repo convention is to parse YAML with stdlib only), the workflow is parsed
structurally from its text: the ``steps:`` list is split on ``- name:`` step
boundaries and individual step blocks are inspected.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Path to the CI workflow under test (resolved relative to this file:
# repo root -> .github/workflows/validate-power.yml).
# ---------------------------------------------------------------------------

_REPO_ROOT: Path = Path(__file__).resolve().parent.parent
_WORKFLOW_PATH: Path = _REPO_ROOT / ".github" / "workflows" / "validate-power.yml"

# Step names (the ``name:`` value) identifying the two steps under test.
_SCANNER_STEP_NAME: str = "Scan for brittle test assertions"
_TESTS_STEP_NAME: str = "Run tests"

# Substring identifying the scanner script invocation.
_SCANNER_SCRIPT: str = "scan_brittle_assertions.py"


@dataclass(frozen=True)
class WorkflowStep:
    """A single parsed step from the workflow ``steps:`` list.

    Attributes:
        name: The value of the step's ``name:`` key (empty if unnamed).
        body: The raw text of the step block, including the ``- name:`` line.
        index: The character offset of the step within the workflow text.
    """

    name: str
    body: str
    index: int


def _read_workflow() -> str:
    """Read the CI workflow file as text.

    Returns:
        The full text of validate-power.yml.
    """
    assert _WORKFLOW_PATH.exists(), f"CI workflow not found: {_WORKFLOW_PATH}"
    return _WORKFLOW_PATH.read_text(encoding="utf-8")


def _parse_steps(content: str) -> list[WorkflowStep]:
    """Split a workflow into its ``- name:`` delimited step blocks.

    Each step block runs from its ``- name:`` line up to (but not including)
    the next ``- name:`` line at the same indentation.

    Args:
        content: The full workflow text.

    Returns:
        The ordered list of parsed steps.
    """
    # Match the start of each step: a "- name: <value>" line, capturing the
    # name value and the offset where the step begins.
    pattern = re.compile(r"^[ \t]*-[ \t]+name:[ \t]*(?P<name>.+?)[ \t]*$", re.MULTILINE)
    matches = list(pattern.finditer(content))
    steps: list[WorkflowStep] = []
    for i, match in enumerate(matches):
        start = match.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(content)
        steps.append(
            WorkflowStep(
                name=match.group("name").strip().strip("'\""),
                body=content[start:end],
                index=start,
            )
        )
    return steps


# Module-level parse: the workflow is static during a test run.
_WORKFLOW: str = _read_workflow()
_STEPS: list[WorkflowStep] = _parse_steps(_WORKFLOW)


def _find_step(name: str) -> WorkflowStep | None:
    """Locate the first step whose name matches ``name``.

    Args:
        name: The step name to look for.

    Returns:
        The matching :class:`WorkflowStep`, or ``None`` if not present.
    """
    for step in _STEPS:
        if step.name == name:
            return step
    return None


# ---------------------------------------------------------------------------
# TestBrittlenessScannerCiWiring
# ---------------------------------------------------------------------------


class TestBrittlenessScannerCiWiring:
    """Validate the brittleness scanner CI step wiring and ordering.

    **Validates: Requirements 3.5, 3.6**
    """

    @pytest.fixture(autouse=True)
    def _load_steps(self) -> None:
        """Expose parsed workflow steps to every test in this class."""
        self.steps: list[WorkflowStep] = _STEPS
        self.scanner_step: WorkflowStep | None = _find_step(_SCANNER_STEP_NAME)
        self.tests_step: WorkflowStep | None = _find_step(_TESTS_STEP_NAME)

    def test_scanner_step_present_with_check_flag(self) -> None:
        """Scanner step must run the scanner with --check (Req 3.5).

        The "Scan for brittle test assertions" step must exist and its body
        must invoke ``scan_brittle_assertions.py`` with the ``--check`` flag.
        """
        assert self.scanner_step is not None, (
            f"validate-power.yml must contain a step named "
            f"'{_SCANNER_STEP_NAME}'"
        )
        body = self.scanner_step.body
        assert _SCANNER_SCRIPT in body, (
            f"The '{_SCANNER_STEP_NAME}' step must invoke '{_SCANNER_SCRIPT}'"
        )
        # The --check flag must appear on the same run line as the scanner
        # invocation, so the scanner runs in check mode.
        run_lines = [
            line
            for line in body.splitlines()
            if _SCANNER_SCRIPT in line and "--check" in line
        ]
        assert run_lines, (
            f"The '{_SCANNER_STEP_NAME}' step must invoke "
            f"'{_SCANNER_SCRIPT}' with the '--check' flag"
        )

    def test_scanner_step_has_no_continue_on_error(self) -> None:
        """Scanner step must not soften failures via continue-on-error (Req 3.6).

        A ``continue-on-error`` key within the scanner step block would let a
        non-zero scanner exit pass the run, defeating the gate.
        """
        assert self.scanner_step is not None, (
            f"validate-power.yml must contain a step named "
            f"'{_SCANNER_STEP_NAME}'"
        )
        assert "continue-on-error" not in self.scanner_step.body, (
            f"The '{_SCANNER_STEP_NAME}' step must not set 'continue-on-error'; "
            "a scanner failure must fail the CI run"
        )

    def test_scanner_step_precedes_run_tests(self) -> None:
        """Scanner step must run before the pytest step (Req 3.5).

        The scanner gate must appear earlier in the steps list than the
        "Run tests" step so brittle assertions are blocked before pytest runs.
        """
        assert self.scanner_step is not None, (
            f"validate-power.yml must contain a step named "
            f"'{_SCANNER_STEP_NAME}'"
        )
        assert self.tests_step is not None, (
            f"validate-power.yml must contain a step named '{_TESTS_STEP_NAME}'"
        )
        assert self.scanner_step.index < self.tests_step.index, (
            f"The '{_SCANNER_STEP_NAME}' step (offset "
            f"{self.scanner_step.index}) must precede the '{_TESTS_STEP_NAME}' "
            f"step (offset {self.tests_step.index})"
        )
