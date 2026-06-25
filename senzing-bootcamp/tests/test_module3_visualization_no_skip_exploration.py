"""Bug condition exploration tests for the module3-visualization-no-skip bugfix.

These tests encode Property 1 (Fix Checking) from the design: the Module 3 Step 9
("Web Service + Visualization") ⛔ mandatory gate can be satisfied ONLY by CONDITION A
(both Step 9 checkpoints `"passed"`). A `skipped_steps["3.9"]` entry (CONDITION B) must
NEVER satisfy the gate.

They are EXPECTED TO FAIL on the unfixed code — failure confirms the bug:
- The three enforcement hooks still contain a CONDITION B / `skipped_steps["3.9"]`
  satisfaction branch.
- `validate_mandatory_gates._check_gate` still short-circuits to `None` when a
  `skipped_steps["3.9"]` entry is present, even with no Step 9 checkpoints.

Feature: module3-visualization-no-skip

**Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5**
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path

from hypothesis import assume, given, settings
from hypothesis import strategies as st

# ---------------------------------------------------------------------------
# Import validate_mandatory_gates via sys.path manipulation (scripts aren't packages)
# ---------------------------------------------------------------------------

_BOOTCAMP_DIR = Path(__file__).resolve().parent.parent
_SCRIPTS_DIR = str(_BOOTCAMP_DIR / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

import validate_mandatory_gates as vmg  # noqa: E402

# ---------------------------------------------------------------------------
# Paths — the three enforcement hooks holding the Module 3 Step 9 gate
# ---------------------------------------------------------------------------

_HOOKS_DIR = _BOOTCAMP_DIR / "hooks"
_GATE_HOOK_PATH = _HOOKS_DIR / "gate-module3-visualization.kiro.hook"
_ENFORCE_GATE_PATH = _HOOKS_DIR / "enforce-mandatory-gate.kiro.hook"
_ENFORCE_STOP_PATH = _HOOKS_DIR / "enforce-gate-on-stop.kiro.hook"

# The skip key for the Module 3 Step 9 visualization gate ({module}.{step} form)
_STEP9_SKIP_KEY = "3.9"

# A non-credentialed local service host used only to make synthetic checkpoints
# look realistic. Assembled from parts so no literal external URL is embedded.
_LOCAL_HOST = "localhost"
_LOCAL_PORT = 8080
_LOCAL_URL = f"http://{_LOCAL_HOST}:{_LOCAL_PORT}/"

# ---------------------------------------------------------------------------
# Shared domain model — mirrors isBugCondition from bugfix.md
# ---------------------------------------------------------------------------


@dataclass
class GateState:
    """A Module 3 Step 9 gate-crossing scenario.

    Attributes:
        checkpoints_passed: Whether both Step 9 checkpoints (web_service, web_page)
            are `"passed"` (CONDITION A).
        skip_present: Whether a `skipped_steps["3.9"]` entry is present (CONDITION B).
        operation: The triggering operation that crosses the gate
            ("complete" | "advance" | "stop" | "validate").
    """

    checkpoints_passed: bool
    skip_present: bool
    operation: str


def is_bug_condition(x: GateState) -> bool:
    """Return whether the input triggers the bug (isBugCondition from bugfix.md).

    The bug fires when the Module 3 Step 9 gate is crossed without checkpoints,
    yet a `skipped_steps["3.9"]` entry would (incorrectly) satisfy it.

    Args:
        x: The gate-crossing scenario.

    Returns:
        True when the gate is crossed, checkpoints are not both passed, and a
        skip entry is present.
    """
    gate_crossed = x.operation in {"complete", "advance", "stop", "validate"}
    return gate_crossed and (not x.checkpoints_passed) and x.skip_present


# ---------------------------------------------------------------------------
# Hypothesis strategies
# ---------------------------------------------------------------------------

_OPERATIONS = ["complete", "advance", "stop", "validate"]


@st.composite
def st_gate_state(draw: st.DrawFn) -> GateState:
    """Generate a GateState across the full gate-crossing input space.

    Returns:
        A GateState with freely drawn checkpoints_passed, skip_present, and operation.
    """
    return GateState(
        checkpoints_passed=draw(st.booleans()),
        skip_present=draw(st.booleans()),
        operation=draw(st.sampled_from(_OPERATIONS)),
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _load_hook_prompt(path: Path) -> str:
    """Load a hook file and return its askAgent prompt text.

    Args:
        path: Path to the `.kiro.hook` JSON file.

    Returns:
        The `then.prompt` string from the hook.
    """
    data = json.loads(path.read_text(encoding="utf-8"))
    return data.get("then", {}).get("prompt", "")


def _prompt_has_condition_b(prompt: str) -> bool:
    """Return whether a hook prompt still carries a CONDITION B skip branch.

    A CONDITION B branch lets `skipped_steps["3.9"]` satisfy the gate. After the
    fix, neither the literal "CONDITION B" label nor the `"3.9"` skip reference
    should appear in the prompt.

    Args:
        prompt: The hook prompt text.

    Returns:
        True if a CONDITION B / `skipped_steps["3.9"]` satisfaction branch is present.
    """
    return "CONDITION B" in prompt or _STEP9_SKIP_KEY in prompt


def _module3_step9_gate() -> vmg.MandatoryGate:
    """Build the Module 3 Step 9 visualization MandatoryGate.

    Returns:
        A MandatoryGate for module 3 step 9 requiring the web_service/web_page checks.
    """
    return vmg.MandatoryGate(
        module=3,
        step=9,
        source_file="module-03-system-verification.md",
        required_checkpoints=["web_service", "web_page"],
    )


def _build_progress(state: GateState) -> dict:
    """Build a bootcamp_progress.json state equivalent to a GateState.

    The gate is crossed (current_module=3, current_step past 9). Checkpoints are
    present only when `state.checkpoints_passed`; a `skipped_steps["3.9"]` entry is
    present only when `state.skip_present`.

    Args:
        state: The gate-crossing scenario to materialize.

    Returns:
        A progress dict suitable for `validate_mandatory_gates._check_gate`.
    """
    checks: dict = {}
    if state.checkpoints_passed:
        checks["web_service"] = {"status": "passed", "port": _LOCAL_PORT}
        checks["web_page"] = {"status": "passed", "url": _LOCAL_URL}

    progress: dict = {
        "current_module": 3,
        "modules_completed": [1, 2],
        "current_step": 10,
        "language": "python",
        "module_3_verification": {"checks": checks},
    }
    if state.skip_present:
        progress["skipped_steps"] = {
            _STEP9_SKIP_KEY: {
                "reason": "a",
                "note": "synthetic skip entry",
                "skipped_at": "2026-05-13T10:00:00Z",
            }
        }
    return progress


# ---------------------------------------------------------------------------
# Test 1 — gate-module3-visualization has no CONDITION B
# ---------------------------------------------------------------------------


class TestGateHookHasNoConditionB:
    """The gate-module3-visualization hook prompt has no CONDITION B branch.

    On UNFIXED code this FAILS — the prompt still contains "CONDITION B" and a
    `skipped_steps["3.9"]` satisfaction branch.

    **Validates: Requirements 2.1, 2.5**
    """

    def test_gate_hook_prompt_has_no_condition_b(self) -> None:
        """The gate hook prompt must not satisfy the gate via a "3.9" skip."""
        prompt = _load_hook_prompt(_GATE_HOOK_PATH)
        assert "CONDITION B" not in prompt, (
            "gate-module3-visualization prompt still contains a 'CONDITION B' "
            "branch — a skip can satisfy the Step 9 visualization gate."
        )
        assert _STEP9_SKIP_KEY not in prompt, (
            "gate-module3-visualization prompt still references a "
            f'skipped_steps["{_STEP9_SKIP_KEY}"] satisfaction branch.'
        )


# ---------------------------------------------------------------------------
# Test 2 — enforce-mandatory-gate has no CONDITION B
# ---------------------------------------------------------------------------


class TestEnforceMandatoryGateHasNoConditionB:
    """The enforce-mandatory-gate hook prompt has no CONDITION B branch.

    On UNFIXED code this FAILS.

    **Validates: Requirements 2.2, 2.5**
    """

    def test_enforce_mandatory_gate_prompt_has_no_condition_b(self) -> None:
        """The enforce-mandatory-gate prompt must not satisfy the gate via a "3.9" skip."""
        prompt = _load_hook_prompt(_ENFORCE_GATE_PATH)
        assert "CONDITION B" not in prompt, (
            "enforce-mandatory-gate prompt still contains a 'CONDITION B' branch — "
            "a skip can satisfy advancement past the Step 9 visualization gate."
        )
        assert _STEP9_SKIP_KEY not in prompt, (
            "enforce-mandatory-gate prompt still references a "
            f'skipped_steps["{_STEP9_SKIP_KEY}"] satisfaction branch.'
        )


# ---------------------------------------------------------------------------
# Test 3 — enforce-gate-on-stop has no CONDITION B
# ---------------------------------------------------------------------------


class TestEnforceGateOnStopHasNoConditionB:
    """The enforce-gate-on-stop hook prompt has no CONDITION B branch.

    On UNFIXED code this FAILS.

    **Validates: Requirements 2.3, 2.5**
    """

    def test_enforce_gate_on_stop_prompt_has_no_condition_b(self) -> None:
        """The enforce-gate-on-stop prompt must not satisfy the gate via a "3.9" skip."""
        prompt = _load_hook_prompt(_ENFORCE_STOP_PATH)
        assert "CONDITION B" not in prompt, (
            "enforce-gate-on-stop prompt still contains a 'CONDITION B' branch — "
            "a skip suppresses the ⛔ violation at agentStop past Step 9."
        )
        assert _STEP9_SKIP_KEY not in prompt, (
            "enforce-gate-on-stop prompt still references a "
            f'skipped_steps["{_STEP9_SKIP_KEY}"] satisfaction branch.'
        )


# ---------------------------------------------------------------------------
# Test 4 — _check_gate reports a violation under skip + no checkpoints
# ---------------------------------------------------------------------------


class TestCheckGateReportsViolationUnderSkip:
    """`_check_gate` reports a violation for the Step 9 gate under a "3.9" skip.

    For a progress state past the gate with no web_service/web_page checkpoints and
    a `skipped_steps["3.9"]` entry, `_check_gate` must return a non-None Violation.

    On UNFIXED code this FAILS — `_check_gate` short-circuits to `None` because the
    skip key is present.

    **Validates: Requirements 2.4**
    """

    def test_check_gate_returns_violation_when_skip_present_no_checkpoints(self) -> None:
        """A "3.9" skip must NOT exempt the visualization gate from a violation."""
        progress = {
            "current_module": 3,
            "modules_completed": [1, 2],
            "current_step": 10,
            "language": "python",
            "module_3_verification": {"checks": {}},
            "skipped_steps": {
                _STEP9_SKIP_KEY: {
                    "reason": "a",
                    "note": "synthetic skip entry",
                    "skipped_at": "2026-05-13T10:00:00Z",
                }
            },
        }
        gate = _module3_step9_gate()

        violation = vmg._check_gate(progress, gate)

        assert violation is not None, (
            "_check_gate returned None for current_step=10 with "
            f'skipped_steps["{_STEP9_SKIP_KEY}"] and no web_service/web_page '
            "checkpoints — the skip is wrongly satisfying the unconditional gate."
        )
        assert isinstance(violation, vmg.Violation), (
            "_check_gate must return a Violation instance for the Step 9 gate."
        )


# ---------------------------------------------------------------------------
# Property 1 — Fix Checking: every bug-condition input is blocked / reported
# ---------------------------------------------------------------------------


class TestVisualizationGateCannotBeSatisfiedBySkip:
    """Property 1: Bug Condition — Visualization Gate Cannot Be Satisfied By A Skip.

    For every GateState where `is_bug_condition` holds, the fixed logic SHALL block
    the write (none of the three hooks carry a CONDITION B branch) AND report a
    violation (`_check_gate` returns a Violation for the equivalent progress state),
    regardless of the `skipped_steps["3.9"]` entry.

    Authored to FAIL on the unfixed code (CONDITION B still present, `_check_gate`
    returns None) and PASS after the fix.

    **Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5**
    """

    @given(state=st_gate_state())
    @settings(max_examples=20)
    def test_bug_condition_inputs_are_blocked_and_reported(self, state: GateState) -> None:
        """For every bug-condition input, no hook accepts the skip and a Violation is reported.

        Args:
            state: A generated gate-crossing scenario, constrained to the bug condition.
        """
        assume(is_bug_condition(state))

        # 1. None of the three enforcement hooks may carry a CONDITION B skip branch.
        for path in (_GATE_HOOK_PATH, _ENFORCE_GATE_PATH, _ENFORCE_STOP_PATH):
            prompt = _load_hook_prompt(path)
            assert not _prompt_has_condition_b(prompt), (
                f"{path.name} still carries a CONDITION B / "
                f'skipped_steps["{_STEP9_SKIP_KEY}"] branch — a skip can satisfy '
                f"the Module 3 Step 9 visualization gate (bug input: {state})."
            )

        # 2. validate_mandatory_gates must report a violation for the equivalent state.
        progress = _build_progress(state)
        violation = vmg._check_gate(progress, _module3_step9_gate())
        assert violation is not None, (
            "_check_gate returned None for a bug-condition state "
            f"(skip present, no checkpoints): {state}. The skip is wrongly "
            "satisfying the unconditional Step 9 visualization gate."
        )
