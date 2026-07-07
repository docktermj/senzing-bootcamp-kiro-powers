"""Content tests for the explicit Step-9-vs-journey-guarantee distinction.

Requirement 3.3 states the feature SHALL keep the distinction explicit: Step 9 is
unconditional whenever Module 3 runs; the journey-level guarantee covers the opt-out
case separately. Requirement 4.2 asks for coverage asserting this framing exists.

These deterministic content checks assert the framing is present in both the Phase 1
Opt-Out Gate steering (task 4.1) and the ``rule-16`` governance rule (task 7.1).

Feature: module3-first-visualization-guarantee
Validates: Requirements 3.3, 4.2
"""

from __future__ import annotations

import re
from pathlib import Path

import yaml

# ---------------------------------------------------------------------------
# Path constants (resolved relative to this test file)
# ---------------------------------------------------------------------------

_BASE_DIR: Path = Path(__file__).resolve().parent.parent
_PHASE1_STEERING: Path = _BASE_DIR / "steering" / "module-03-phase1-verification.md"
_GOVERNANCE_RULES: Path = _BASE_DIR / "config" / "governance-rules.yaml"

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
# Tests
# ---------------------------------------------------------------------------


class TestExplicitDistinctionFraming:
    """The explicit Step-9-vs-journey-guarantee distinction is stated in the docs.

    Validates: Requirements 3.3, 4.2
    """

    def test_phase1_steering_states_step9_unconditional_when_module3_runs(self) -> None:
        """Phase 1 steering asserts Step 9 is unconditional whenever Module 3 runs."""
        content = _read_text(_PHASE1_STEERING).lower()

        assert "unconditional" in content, (
            "module-03-phase1-verification.md does not describe Step 9 as "
            "'unconditional'."
        )
        # The unconditional framing must be tied to Module 3 running, not the
        # opt-out journey guarantee.
        assert re.search(r"unconditional[^.]*whenever module 3 runs", content) or re.search(
            r"whenever module 3 runs[^.]*unconditional", content
        ), (
            "module-03-phase1-verification.md does not tie the unconditional "
            "Step 9 gate to 'whenever Module 3 runs'."
        )

    def test_phase1_steering_states_journey_guarantee_covers_opt_out_separately(
        self,
    ) -> None:
        """Phase 1 steering asserts the journey guarantee covers opt-out separately."""
        content = _read_text(_PHASE1_STEERING).lower()

        assert "journey-level" in content, (
            "module-03-phase1-verification.md does not use 'journey-level' framing "
            "for the first-visualization guarantee."
        )
        assert "opt-out case only" in content, (
            "module-03-phase1-verification.md does not state the guarantee covers "
            "the 'opt-out case only'."
        )
        assert "separate" in content, (
            "module-03-phase1-verification.md does not state the two mechanisms are "
            "separate."
        )

    def test_governance_rule16_states_separate_and_does_not_weaken_step9(self) -> None:
        """rule-16 rule text conveys it is separate from / does not weaken Step 9."""
        rules = yaml.safe_load(_read_text(_GOVERNANCE_RULES))
        # governance-rules.yaml may be a top-level list or a mapping with a
        # ``rules`` key; support both shapes.
        if isinstance(rules, dict):
            rules = rules.get("rules", [])

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
