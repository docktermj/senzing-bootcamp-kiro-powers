"""Property-based tests for the consolidated ask-bootcamper.json v1 hook.

Property 1: Consolidated hook contains all four phase markers.
Property 2: Consolidated hook structural validity.

Verifies that the `action.prompt` field contains identifiable section markers
for all four phases: PHASE 1 (Closing_Question_Phase), PHASE 2
(Step_Sequencing_Phase), PHASE 3 (MCP_First_Phase), and PHASE 4
(Question_Format_Phase).

Also verifies the hook entry has all required keys, trigger == "Stop",
action.type == "agent", and a non-empty action.prompt.

**Validates: Requirements 1.1, 1.3, 9.1, 9.2, 9.3, 9.4**
"""

from __future__ import annotations

from pathlib import Path

from hypothesis import given, settings
from hypothesis import strategies as st

from hook_test_helpers import load_hook

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

HOOK_PATH = Path("senzing-bootcamp/hooks/ask-bootcamper.json")

# Phase markers that must appear in the consolidated prompt.
# Each tuple is (phase_number_marker, phase_name_marker) — both must be present.
PHASE_MARKERS: list[tuple[str, str]] = [
    ("PHASE 1", "Closing_Question_Phase"),
    ("PHASE 2", "Step_Sequencing_Phase"),
    ("PHASE 3", "MCP_First_Phase"),
    ("PHASE 4", "Question_Format_Phase"),
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def load_hook_prompt() -> str:
    """Load and return the action.prompt field from the consolidated v1 hook entry."""
    data = load_hook(HOOK_PATH)
    return data["action"]["prompt"]


# ---------------------------------------------------------------------------
# Property 1: Consolidated hook contains all four phase markers
# ---------------------------------------------------------------------------


class TestConsolidatedHookPhaseMarkers:
    """For any phase in the consolidated hook, identifiable section markers exist.

    **Validates: Requirements 1.1, 9.4**

    Property 1: For any valid Ask_Bootcamper_Hook file, the `action.prompt` field
    SHALL contain identifiable section markers for all four phases:
    Closing_Question_Phase (PHASE 1), Step_Sequencing_Phase (PHASE 2),
    MCP_First_Phase (PHASE 3), and Question_Format_Phase (PHASE 4).
    """

    @given(phase=st.sampled_from(PHASE_MARKERS))
    @settings(max_examples=20)
    def test_prompt_contains_phase_number_marker(
        self, phase: tuple[str, str]
    ):
        """For any phase, the prompt SHALL contain its numbered marker."""
        phase_number, phase_name = phase
        prompt = load_hook_prompt()
        assert phase_number in prompt, (
            f"Consolidated hook prompt does not contain phase marker "
            f"'{phase_number}' (expected for {phase_name})"
        )

    @given(phase=st.sampled_from(PHASE_MARKERS))
    @settings(max_examples=20)
    def test_prompt_contains_phase_name_marker(
        self, phase: tuple[str, str]
    ):
        """For any phase, the prompt SHALL contain its descriptive name marker."""
        phase_number, phase_name = phase
        prompt = load_hook_prompt()
        assert phase_name in prompt, (
            f"Consolidated hook prompt does not contain phase name "
            f"'{phase_name}' (expected in {phase_number} section)"
        )

    @given(phase=st.sampled_from(PHASE_MARKERS))
    @settings(max_examples=20)
    def test_prompt_has_then_prompt_field(
        self, phase: tuple[str, str]
    ):
        """The hook SHALL have a non-empty action.prompt field containing phases."""
        prompt = load_hook_prompt()
        assert isinstance(prompt, str), (
            "action.prompt is not a string"
        )
        assert len(prompt) > 0, (
            "action.prompt is empty"
        )


# ---------------------------------------------------------------------------
# Constants for Property 2
# ---------------------------------------------------------------------------

REQUIRED_TOP_KEYS: list[str] = ["name", "trigger", "action"]


# ---------------------------------------------------------------------------
# Property 2: Consolidated hook structural validity
# ---------------------------------------------------------------------------


class TestConsolidatedHookStructuralValidity:
    """Consolidated hook structural validity.

    **Validates: Requirements 1.3, 9.1, 9.2, 9.3**

    Property 2: For any valid Ask_Bootcamper_Hook file, it SHALL parse as valid
    JSON containing all required keys (name, trigger, action), with trigger
    equal to "Stop" and action.type equal to "agent", and the action.prompt
    field SHALL be a non-empty string.
    """

    @given(key=st.sampled_from(REQUIRED_TOP_KEYS))
    @settings(max_examples=20)
    def test_hook_contains_required_key(self, key: str):
        """For any required key, the hook JSON SHALL contain that key.

        **Validates: Requirements 9.1**
        """
        data = load_hook(HOOK_PATH)
        assert key in data, (
            f"Consolidated hook is missing required top-level key '{key}'"
        )

    @given(key=st.sampled_from(REQUIRED_TOP_KEYS))
    @settings(max_examples=20)
    def test_hook_parses_as_valid_json(self, key: str):
        """The hook file SHALL parse as valid JSON without errors.

        **Validates: Requirements 9.1**
        """
        # If load_hook succeeds, the file is valid JSON.
        # We use the key parameter to satisfy Hypothesis but the real
        # assertion is that load_hook does not raise.
        data = load_hook(HOOK_PATH)
        assert isinstance(data, dict), "Hook file did not parse as a JSON object"

    @given(data=st.just(None))
    @settings(max_examples=20)
    def test_trigger_is_stop(self, data):
        """The hook SHALL have trigger set to "Stop" (1.0 rename of agentStop).

        **Validates: Requirements 9.2**
        """
        hook_data = load_hook(HOOK_PATH)
        assert "trigger" in hook_data, "Hook is missing 'trigger' field"
        assert hook_data.get("trigger") == "Stop", (
            f"Expected trigger == 'Stop', got '{hook_data.get('trigger')}'"
        )

    @given(data=st.just(None))
    @settings(max_examples=20)
    def test_action_type_is_agent(self, data):
        """The hook SHALL have action.type set to "agent" (1.0 rename of askAgent).

        **Validates: Requirements 9.3**
        """
        hook_data = load_hook(HOOK_PATH)
        assert "action" in hook_data, "Hook is missing 'action' field"
        assert isinstance(hook_data["action"], dict), "'action' is not a dict"
        assert hook_data["action"].get("type") == "agent", (
            f"Expected action.type == 'agent', "
            f"got '{hook_data['action'].get('type')}'"
        )

    @given(data=st.just(None))
    @settings(max_examples=20)
    def test_action_prompt_is_non_empty_string(self, data):
        """The hook SHALL have an action.prompt field that is a non-empty string.

        **Validates: Requirements 1.3, 9.3**
        """
        hook_data = load_hook(HOOK_PATH)
        action = hook_data.get("action", {})
        prompt = action.get("prompt")
        assert isinstance(prompt, str), (
            f"Expected action.prompt to be a string, got {type(prompt).__name__}"
        )
        assert len(prompt) > 0, "action.prompt is empty"
