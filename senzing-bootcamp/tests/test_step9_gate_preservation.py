"""Preservation tests for the Module 3 Step 9 gate and Governing Rule 15 pin.

Feature: module3-first-visualization-guarantee

The journey-level first-visualization guarantee must NOT weaken the in-module
Module 3 Step 9 mandatory gate, and must NOT modify the canonical Governing
Rule 15 or its pinned assertions. This module hosts:

* Property 2 — the Step 9 in-module gate remains unconditional: reusing the
  real ``validate_mandatory_gates._check_gate`` against the real Step 9 gate,
  any progress state advanced past ``3.9`` without both Step 9 checkpoints
  (``web_service``, ``web_page``) marked ``"passed"`` reports a violation, and a
  ``skipped_steps["3.9"]`` entry never satisfies the gate. (Requirement 1.2)
* Pin/example tests — ``validate_mandatory_gates.NON_SKIPPABLE_GATES == {"3.9"}``
  and the ``rule-15-module3-visualization-gate`` entry in
  ``config/governance-rules.yaml`` retains its pinned assertions (the
  ``NON_SKIPPABLE_GATES = {"3.9"}`` regex assertion and the ``CONDITION B``
  ``substring_absent`` assertion). (Requirement 1.3)
"""

from __future__ import annotations

import copy
import re
import sys
from pathlib import Path

from hypothesis import given
from hypothesis import strategies as st

# Make senzing-bootcamp/scripts/ importable (scripts are not packages).
_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

import validate_mandatory_gates as vmg  # noqa: E402
from validate_governance_rules import load_registry  # noqa: E402

# ---------------------------------------------------------------------------
# Repository paths
# ---------------------------------------------------------------------------

_BOOTCAMP_ROOT = Path(__file__).resolve().parent.parent
_STEERING_DIR = _BOOTCAMP_ROOT / "steering"
_GOVERNANCE_YAML = _BOOTCAMP_ROOT / "config" / "governance-rules.yaml"
_GATES_SCRIPT = _BOOTCAMP_ROOT / "scripts" / "validate_mandatory_gates.py"
_GATE_HOOK = _BOOTCAMP_ROOT / "hooks" / "gate-module3-visualization.kiro.hook"

# The exact decoded regex the Rule 15 pin asserts against
# validate_mandatory_gates.py (after the registry escape table is applied).
_RULE15_NON_SKIPPABLE_PATTERN = r'NON_SKIPPABLE_GATES\s*=\s*\{"3\.9"\}'


def _load_real_step9_gate() -> vmg.MandatoryGate:
    """Parse the shipped steering and return the real Module 3 Step 9 gate.

    Returns:
        The :class:`~validate_mandatory_gates.MandatoryGate` for Module 3
        Step 9, parsed from the real steering files.

    Raises:
        AssertionError: If the Step 9 mandatory gate is not present in steering.
    """
    for gate in vmg.parse_mandatory_gates(_STEERING_DIR):
        if gate.module == 3 and gate.step == 9:
            return gate
    raise AssertionError(
        "Module 3 Step 9 mandatory gate not found in shipped steering — "
        "the unconditional gate appears to have been removed."
    )


# The real Step 9 gate, parsed once from the shipped steering.
_STEP9_GATE = _load_real_step9_gate()

# Checkpoint status possibilities for the two Step 9 checkpoints. Only "passed"
# satisfies a required checkpoint; every other state (including an absent entry
# or an entry with no status) leaves it unsatisfied.
_CHECKPOINT_STATES = ("passed", "failed", "pending", "absent", "no_status")


def _apply_checkpoint(checks: dict, key: str, state: str) -> None:
    """Write a checkpoint entry for ``key`` into ``checks`` for the given state.

    Args:
        checks: The verification ``checks`` mapping being built.
        key: The checkpoint key (e.g. ``"web_service"``).
        state: One of :data:`_CHECKPOINT_STATES`.
    """
    if state == "absent":
        return
    if state == "no_status":
        checks[key] = {}
    else:
        checks[key] = {"status": state}


@st.composite
def st_past_gate_progress(draw: st.DrawFn) -> tuple[dict, bool]:
    """Generate a progress state advanced past Module 3 Step 9.

    Two ways of being "past the gate" are covered: still in Module 3 with a
    ``current_step`` beyond 9, or in a later module with Module 3 recorded in
    ``modules_completed``. The two Step 9 checkpoints vary independently across
    passed / not-passed / absent states, and ``skipped_steps`` may carry a
    ``"3.9"`` entry (plus unrelated skips) to confirm the non-skippable gate is
    never satisfied by a skip.

    Returns:
        A tuple ``(progress, expected_violation)`` where ``expected_violation``
        is ``True`` iff not both Step 9 checkpoints are ``"passed"``.
    """
    ws_state = draw(st.sampled_from(_CHECKPOINT_STATES))
    wp_state = draw(st.sampled_from(_CHECKPOINT_STATES))

    checks: dict = {}
    _apply_checkpoint(checks, "web_service", ws_state)
    _apply_checkpoint(checks, "web_page", wp_state)

    progress: dict = {}

    modules_completed = draw(
        st.lists(st.integers(min_value=1, max_value=11), max_size=5, unique=True)
    )

    if draw(st.booleans()):
        # Past the gate while still inside Module 3.
        progress["current_module"] = 3
        progress["current_step"] = draw(st.integers(min_value=10, max_value=20))
    else:
        # Past the gate by having completed Module 3 and moved on.
        progress["current_module"] = draw(st.integers(min_value=4, max_value=11))
        progress["current_step"] = draw(st.integers(min_value=1, max_value=20))
        if 3 not in modules_completed:
            modules_completed.append(3)

    progress["modules_completed"] = modules_completed

    # Optional skipped_steps, including the non-skippable "3.9" entry.
    skipped: dict = {}
    if draw(st.booleans()):
        skipped["3.9"] = {"reason": "bootcamper attempted skip"}
    for extra in draw(
        st.lists(
            st.sampled_from(["3.5", "4.2", "5.1", "2.5"]), max_size=3, unique=True
        )
    ):
        skipped[extra] = {"reason": "unrelated skip"}
    if skipped:
        progress["skipped_steps"] = skipped

    # The verification block is present whenever any checkpoint was recorded;
    # otherwise it may be omitted entirely (still leaves both unsatisfied).
    if checks or draw(st.booleans()):
        progress["module_3_verification"] = {"status": "skipped", "checks": checks}

    both_passed = ws_state == "passed" and wp_state == "passed"
    return progress, (not both_passed)


class TestStep9GatePreservation:
    """Property 2 + Rule 15 pin: the Step 9 gate is preserved unchanged.

    Validates: Requirements 1.2, 1.3
    """

    @given(case=st_past_gate_progress())
    def test_property_2_step9_gate_unconditional(
        self, case: tuple[dict, bool]
    ) -> None:
        """Property 2: The Step 9 in-module gate remains unconditional.

        Feature: module3-first-visualization-guarantee, Property 2: For any
        bootcamp_progress state advanced past Module 3 Step 9 without both Step 9
        checkpoints (web_service, web_page) marked "passed", the mandatory-gate
        check reports a violation — and a skipped_steps["3.9"] entry never
        satisfies the "3.9" gate.

        **Validates: Requirements 1.2**
        """
        progress, expected_violation = case

        result = vmg._check_gate(progress, _STEP9_GATE)

        if expected_violation:
            assert result is not None, (
                "expected a Step 9 gate violation when the checkpoints are not "
                f"both passed, but none was reported for progress={progress!r}"
            )
            assert isinstance(result, vmg.Violation)
        else:
            assert result is None, (
                "expected NO Step 9 gate violation when both checkpoints are "
                f"passed, but got {result!r} for progress={progress!r}"
            )

        # A skipped_steps["3.9"] entry must NEVER satisfy the non-skippable gate:
        # forcing the skip in must not flip a violation into a pass.
        with_skip = copy.deepcopy(progress)
        with_skip.setdefault("skipped_steps", {})["3.9"] = {
            "reason": "explicit bootcamper skip"
        }
        result_with_skip = vmg._check_gate(with_skip, _STEP9_GATE)

        assert (result_with_skip is None) == (result is None), (
            "adding skipped_steps['3.9'] changed the Step 9 gate outcome — the "
            "non-skippable gate was satisfied by a skip entry"
        )
        if expected_violation:
            assert result_with_skip is not None, (
                "skipped_steps['3.9'] satisfied the non-skippable Step 9 gate"
            )

    def test_non_skippable_gates_pinned(self) -> None:
        """NON_SKIPPABLE_GATES is exactly {"3.9"} (Governing Rule 15 unchanged).

        **Validates: Requirements 1.3**
        """
        assert vmg.NON_SKIPPABLE_GATES == {"3.9"}

    def test_rule15_pinned_assertions_present(self) -> None:
        """rule-15 retains its NON_SKIPPABLE_GATES regex + CONDITION B absent pins.

        **Validates: Requirements 1.3**
        """
        rules = {entry["id"]: entry for entry in load_registry(_GOVERNANCE_YAML)}

        assert "rule-15-module3-visualization-gate" in rules, (
            "the canonical rule-15-module3-visualization-gate entry is missing "
            "from governance-rules.yaml"
        )
        rule15 = rules["rule-15-module3-visualization-gate"]
        assert rule15["category"] == "mandatory-gate"

        assertions = rule15["assertions"]

        assert any(
            a.get("type") == "regex_present"
            and a.get("file")
            == "senzing-bootcamp/scripts/validate_mandatory_gates.py"
            and a.get("pattern") == _RULE15_NON_SKIPPABLE_PATTERN
            for a in assertions
        ), (
            "rule-15 lost its pinned NON_SKIPPABLE_GATES regex_present assertion "
            f"(expected pattern {_RULE15_NON_SKIPPABLE_PATTERN!r})"
        )

        assert any(
            a.get("type") == "substring_absent"
            and a.get("file")
            == "senzing-bootcamp/hooks/gate-module3-visualization.kiro.hook"
            and a.get("value") == "CONDITION B"
            for a in assertions
        ), "rule-15 lost its pinned 'CONDITION B' substring_absent assertion"

    def test_rule15_pins_match_reality(self) -> None:
        """The pinned assertions still hold against the real enforcement points.

        **Validates: Requirements 1.3**
        """
        source = _GATES_SCRIPT.read_text(encoding="utf-8")
        assert re.search(_RULE15_NON_SKIPPABLE_PATTERN, source), (
            "the NON_SKIPPABLE_GATES = {\"3.9\"} definition pinned by rule-15 is "
            "no longer present in validate_mandatory_gates.py"
        )

        hook_text = _GATE_HOOK.read_text(encoding="utf-8")
        assert "CONDITION B" not in hook_text, (
            "'CONDITION B' (a skip escape hatch) reappeared in the "
            "gate-module3-visualization hook, weakening Rule 15"
        )
