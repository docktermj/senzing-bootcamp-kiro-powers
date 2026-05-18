"""Prompt logic verification for enforce-gate-on-stop hook.

Verifies that the agentStop hook prompt contains all 4 required logic checks:
1. Checks current_module equal to 3
2. Checks current_step greater than or equal to 9
3. Checks CONDITION A (web_service + web_page passed) and CONDITION B (skipped_steps "3.9")
4. Outputs blocking/violation message only when NEITHER condition A nor B is met
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

_TESTS_DIR = str(Path(__file__).resolve().parent)
if _TESTS_DIR not in sys.path:
    sys.path.insert(0, _TESTS_DIR)

from hook_test_helpers import HOOKS_DIR, load_hook

HOOK_FILE = HOOKS_DIR / "enforce-gate-on-stop.kiro.hook"


@pytest.fixture
def prompt() -> str:
    """Load the prompt text from the enforce-gate-on-stop hook."""
    assert HOOK_FILE.exists(), f"Hook file not found: {HOOK_FILE}"
    data = load_hook(HOOK_FILE)
    return data["then"]["prompt"]


class TestEnforceGateOnStopPromptLogic:
    """Verify enforce-gate-on-stop prompt contains all 4 required logic checks."""

    # ------------------------------------------------------------------
    # Check 1: current_module = 3
    # ------------------------------------------------------------------

    def test_checks_current_module_equals_3(self, prompt: str):
        """Prompt checks that current_module is equal to 3."""
        assert "current_module" in prompt, (
            "Prompt does not reference 'current_module'"
        )
        # Must check for equality to 3 (not just mention the field)
        assert "3" in prompt, "Prompt does not reference module number 3"
        # Verify it's checking equality (equal/equals/= 3)
        prompt_lower = prompt.lower()
        has_equality_check = (
            "equal to 3" in prompt_lower
            or "equals 3" in prompt_lower
            or "= 3" in prompt_lower
            or "≠ 3" in prompt_lower  # negated form also valid
        )
        assert has_equality_check, (
            "Prompt does not check current_module equality to 3"
        )

    # ------------------------------------------------------------------
    # Check 2: current_step >= 9
    # ------------------------------------------------------------------

    def test_checks_current_step_gte_9(self, prompt: str):
        """Prompt checks that current_step is greater than or equal to 9."""
        assert "current_step" in prompt, (
            "Prompt does not reference 'current_step'"
        )
        prompt_lower = prompt.lower()
        has_gte_check = (
            "greater than or equal to 9" in prompt_lower
            or ">= 9" in prompt_lower
            or "≥ 9" in prompt_lower
            or "< 9" in prompt_lower  # negated form also valid
        )
        assert has_gte_check, (
            "Prompt does not check current_step >= 9"
        )

    # ------------------------------------------------------------------
    # Check 3: CONDITION A and CONDITION B
    # ------------------------------------------------------------------

    def test_checks_condition_a_web_service_passed(self, prompt: str):
        """Prompt checks web_service.status equals passed (part of Condition A)."""
        assert "web_service" in prompt, (
            "Prompt does not reference 'web_service'"
        )
        assert "passed" in prompt.lower(), (
            "Prompt does not reference 'passed' status"
        )

    def test_checks_condition_a_web_page_passed(self, prompt: str):
        """Prompt checks web_page.status equals passed (part of Condition A)."""
        assert "web_page" in prompt, (
            "Prompt does not reference 'web_page'"
        )

    def test_checks_condition_b_skipped_steps(self, prompt: str):
        """Prompt checks skipped_steps contains 3.9 (Condition B)."""
        assert "skipped_steps" in prompt, (
            "Prompt does not reference 'skipped_steps'"
        )
        assert "3.9" in prompt, (
            "Prompt does not reference step '3.9' in skipped_steps check"
        )

    def test_labels_conditions_a_and_b(self, prompt: str):
        """Prompt explicitly labels CONDITION A and CONDITION B."""
        prompt_upper = prompt.upper()
        assert "CONDITION A" in prompt_upper, (
            "Prompt does not label 'CONDITION A'"
        )
        assert "CONDITION B" in prompt_upper, (
            "Prompt does not label 'CONDITION B'"
        )

    # ------------------------------------------------------------------
    # Check 4: Blocking message only when NEITHER condition is met
    # ------------------------------------------------------------------

    def test_outputs_blocking_message_when_neither_condition_met(self, prompt: str):
        """Prompt outputs violation message only when neither A nor B is met."""
        prompt_lower = prompt.lower()
        # Must have "neither" logic
        has_neither = (
            "neither" in prompt_lower
            or ("not" in prompt_lower and "condition" in prompt_lower)
        )
        assert has_neither, (
            "Prompt does not express 'neither condition met' logic"
        )
        # Must contain the blocking/violation message
        assert "violation" in prompt_lower or "mandatory gate" in prompt_lower, (
            "Prompt does not contain a blocking/violation message"
        )

    def test_blocking_message_contains_enforcement_action(self, prompt: str):
        """Blocking message instructs the agent to execute Step 9 immediately."""
        prompt_lower = prompt.lower()
        assert "step 9" in prompt_lower, (
            "Blocking message does not reference Step 9"
        )
        has_enforcement = (
            "execute step 9" in prompt_lower
            or "execute step 9 now" in prompt_lower
            or "load" in prompt_lower and "module-03" in prompt_lower
        )
        assert has_enforcement, (
            "Blocking message does not instruct agent to execute Step 9"
        )

    def test_blocking_message_contains_violation_marker(self, prompt: str):
        """Blocking message contains the ⛔ violation marker."""
        assert "⛔" in prompt, (
            "Blocking message does not contain ⛔ violation marker"
        )

    def test_no_output_when_conditions_satisfied(self, prompt: str):
        """Prompt instructs to produce no output when conditions are satisfied."""
        prompt_lower = prompt.lower()
        assert "no output" in prompt_lower or "do nothing" in prompt_lower, (
            "Prompt does not instruct to produce no output when gate is satisfied"
        )
