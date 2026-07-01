"""Content tests for the explicit Step-9-vs-journey-guarantee distinction framing.

Task 8.1 of the ``module3-first-visualization-guarantee`` spec. These deterministic,
example-based (pytest, non-Hypothesis) tests assert that the explicit distinction
between the unconditional Module 3 Step 9 gate and the journey-level first-visualization
guarantee is stated in *both* governing artifacts:

1. **Steering** (``steering/module-03-phase1-verification.md``, task 4.1): the framing
   must state that Step 9 is an unconditional gate whenever Module 3 runs AND that the
   journey-level guarantee covers the opt-out case separately.
2. **Governance** (``config/governance-rules.yaml`` ``rule-16``, task 7.1): the rule
   text must state it is separate from / does not weaken the unconditional Step 9 gate
   (``rule-15``).

Assertions target stable substrings/keywords that actually appear in the source docs
and are case-insensitive where sensible, so benign wording changes do not break them
while removal of a whole distinction concept does.

Feature: module3-first-visualization-guarantee
Validates: Requirements 3.3, 4.2
"""

from __future__ import annotations

from pathlib import Path

import yaml

# ---------------------------------------------------------------------------
# Path constants (resolved relative to this test file)
# ---------------------------------------------------------------------------

# This file lives in senzing-bootcamp/tests/; steering and config are siblings.
_BASE_DIR: Path = Path(__file__).resolve().parent.parent
_PHASE1_STEERING: Path = _BASE_DIR / "steering" / "module-03-phase1-verification.md"
_GOVERNANCE_RULES: Path = _BASE_DIR / "config" / "governance-rules.yaml"

_RULE_15_ID: str = "rule-15-module3-visualization-gate"
_RULE_16_ID: str = "rule-16-first-visualization-journey-guarantee"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _read_text(path: Path) -> str:
    """Read a file as UTF-8 text.

    Args:
        path: Path to the file.

    Returns:
        Full text content of the file.
    """
    return path.read_text(encoding="utf-8")


def _load_rules(path: Path) -> list[dict]:
    """Load the governance rule entries from ``governance-rules.yaml``.

    Supports both a top-level list and a mapping with a ``rules`` key.

    Args:
        path: Path to the governance-rules YAML file.

    Returns:
        The list of rule dicts.
    """
    data = yaml.safe_load(_read_text(path))
    if isinstance(data, dict):
        return data.get("rules", []) or []
    return data or []


def _find_rule(rules: list[dict], rule_id: str) -> dict | None:
    """Find a governance rule entry by its ``id``.

    Args:
        rules: List of parsed rule dicts.
        rule_id: The rule identifier to locate.

    Returns:
        The matching rule dict, or ``None`` if not present.
    """
    for entry in rules:
        if isinstance(entry, dict) and entry.get("id") == rule_id:
            return entry
    return None


# ---------------------------------------------------------------------------
# TestSteeringDistinctionFraming
# ---------------------------------------------------------------------------


class TestSteeringDistinctionFraming:
    """The Phase 1 steering keeps the Step-9-vs-journey distinction explicit.

    Requirement 3.3: the framing SHALL state that Step 9 is unconditional whenever
    Module 3 runs, and that the journey-level guarantee covers the opt-out case
    separately.

    Validates: Requirements 3.3, 4.2
    """

    def test_steering_file_present_and_nonempty(self) -> None:
        """The Module 3 Phase 1 steering file exists and has content."""
        assert _PHASE1_STEERING.is_file(), f"Missing steering file: {_PHASE1_STEERING}"
        assert _read_text(_PHASE1_STEERING).strip(), (
            f"Steering file is empty: {_PHASE1_STEERING}"
        )

    def test_step9_framed_as_unconditional_when_module3_runs(self) -> None:
        """Steering states Step 9 is unconditional whenever Module 3 runs."""
        content = _read_text(_PHASE1_STEERING).lower()

        assert "unconditional" in content, (
            "Phase 1 steering does not describe Step 9 as 'unconditional'."
        )
        # The unconditional framing must be tied to Module 3 running (not to the
        # opt-out journey guarantee).
        assert "whenever module 3 runs" in content, (
            "Phase 1 steering does not tie the unconditional Step 9 gate to "
            "'whenever Module 3 runs'."
        )

    def test_journey_guarantee_covers_opt_out_case_separately(self) -> None:
        """Steering states the journey guarantee covers the opt-out case separately."""
        content = _read_text(_PHASE1_STEERING).lower()

        assert "journey-level" in content, (
            "Phase 1 steering does not use 'journey-level' framing for the "
            "first-visualization guarantee."
        )
        assert "opt-out case only" in content, (
            "Phase 1 steering does not state the guarantee covers the "
            "'opt-out case only'."
        )
        # The two mechanisms must be explicitly called out as distinct/separate.
        assert "separate" in content, (
            "Phase 1 steering does not state the two mechanisms are separate."
        )

    def test_distinction_does_not_weaken_step9(self) -> None:
        """Steering states the opt-out flow does not weaken/alter/replace Step 9."""
        content = _read_text(_PHASE1_STEERING).lower()

        assert "does not weaken" in content, (
            "Phase 1 steering does not state the opt-out flow 'does NOT weaken' "
            "the Step 9 gate."
        )


# ---------------------------------------------------------------------------
# TestGovernanceDistinctionFraming
# ---------------------------------------------------------------------------


class TestGovernanceDistinctionFraming:
    """rule-16 states it is separate from / does not weaken the Step 9 gate.

    Requirement 3.3: governance framing SHALL keep the distinction explicit. rule-16
    (journey guarantee) must reference rule-15 (the unconditional Step 9 gate) and
    state the separation.

    Validates: Requirements 3.3, 4.2
    """

    def test_rule16_present(self) -> None:
        """The rule-16 journey-guarantee entry exists in governance-rules.yaml."""
        rules = _load_rules(_GOVERNANCE_RULES)
        assert _find_rule(rules, _RULE_16_ID) is not None, (
            f"governance-rules.yaml is missing the '{_RULE_16_ID}' entry."
        )

    def test_rule16_states_separate_and_does_not_weaken_step9(self) -> None:
        """rule-16 rule text conveys it is separate from / does not weaken Step 9."""
        rules = _load_rules(_GOVERNANCE_RULES)
        rule_16 = _find_rule(rules, _RULE_16_ID)
        assert rule_16 is not None, (
            f"governance-rules.yaml is missing the '{_RULE_16_ID}' entry."
        )

        rule_text = str(rule_16.get("rule", "")).lower()
        assert rule_text, f"'{_RULE_16_ID}' has no 'rule' text."

        assert "separate from" in rule_text, (
            f"'{_RULE_16_ID}' rule text does not state it is 'separate from' the "
            "Step 9 gate."
        )
        assert "does not weaken" in rule_text, (
            f"'{_RULE_16_ID}' rule text does not state it 'does not weaken' the "
            "Step 9 gate."
        )
        assert "unconditional step 9 gate" in rule_text, (
            f"'{_RULE_16_ID}' rule text does not reference the 'unconditional "
            "Step 9 gate'."
        )

    def test_rule16_references_the_step9_gate_rule(self) -> None:
        """rule-16 explicitly cross-references the rule-15 Step 9 gate entry."""
        rules = _load_rules(_GOVERNANCE_RULES)
        rule_16 = _find_rule(rules, _RULE_16_ID)
        assert rule_16 is not None, (
            f"governance-rules.yaml is missing the '{_RULE_16_ID}' entry."
        )

        rule_text = str(rule_16.get("rule", ""))
        assert _RULE_15_ID in rule_text, (
            f"'{_RULE_16_ID}' rule text does not cross-reference the Step 9 gate "
            f"rule id '{_RULE_15_ID}'."
        )
