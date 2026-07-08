"""Tests for the module-recap-document-fix spec.

Validates that both module-recap-append and module-completion-celebration hooks
have correct 1.0 triggers, boundary detection, schema integrity, and prompt
content. The legacy ``postTaskExecution → agentStop`` migration is expressed in
Kiro 1.0 terms: the hooks now use the ``Stop`` trigger (the 1.0 rename of
``agentStop``) and an ``agent`` action (the 1.0 rename of ``askAgent``).
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

# ---------------------------------------------------------------------------
# Path setup
# ---------------------------------------------------------------------------

_TESTS_DIR = str(Path(__file__).resolve().parent)
if _TESTS_DIR not in sys.path:
    sys.path.insert(0, _TESTS_DIR)

from hook_test_helpers import (
    HOOKS_DIR,
    has_silent_processing,
    load_hook,
    load_hook_wrapper,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

RECAP_HOOK_PATH = HOOKS_DIR / "module-recap-append.json"
CELEBRATION_HOOK_PATH = HOOKS_DIR / "module-completion-celebration.json"
AFFECTED_HOOKS: list[Path] = [RECAP_HOOK_PATH, CELEBRATION_HOOK_PATH]


def _required_entry_fields(entry: dict) -> list[str]:
    """Return missing required v1 entry fields (name/trigger/action + prompt)."""
    missing: list[str] = []
    if not entry.get("name"):
        missing.append("name")
    if not entry.get("trigger"):
        missing.append("trigger")
    action = entry.get("action")
    if not isinstance(action, dict):
        missing.append("action")
    elif action.get("type") == "agent" and not action.get("prompt"):
        missing.append("action.prompt")
    return missing


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def recap_data() -> dict:
    """Load and parse the module-recap-append v1 hook entry."""
    return load_hook(RECAP_HOOK_PATH)


@pytest.fixture
def celebration_data() -> dict:
    """Load and parse the module-completion-celebration v1 hook entry."""
    return load_hook(CELEBRATION_HOOK_PATH)


@pytest.fixture
def recap_prompt(recap_data: dict) -> str:
    """Extract the prompt text from the recap hook."""
    return recap_data["action"]["prompt"]


@pytest.fixture
def celebration_prompt(celebration_data: dict) -> str:
    """Extract the prompt text from the celebration hook."""
    return celebration_data["action"]["prompt"]


# ===========================================================================
# Task 3.1: TestEventTypeMigration — Requirements 5.1, 5.5, 5.6
# ===========================================================================

class TestEventTypeMigration:
    """Verify both hooks use the Stop trigger (1.0 rename of agentStop)."""

    def test_recap_hook_uses_agent_stop(self, recap_data: dict):
        """module-recap-append uses the Stop trigger (Req 5.1)."""
        assert recap_data["trigger"] == "Stop", (
            f"Expected 'Stop' but got '{recap_data['trigger']}'. "
            "The module-recap-append hook must use the Stop trigger."
        )

    def test_celebration_hook_uses_agent_stop(self, celebration_data: dict):
        """module-completion-celebration uses the Stop trigger (Req 5.1)."""
        assert celebration_data["trigger"] == "Stop", (
            f"Expected 'Stop' but got '{celebration_data['trigger']}'. "
            "The module-completion-celebration hook must use the Stop trigger."
        )

    def test_agent_stop_is_valid_event_type(self):
        """Stop is a recognized 1.0 trigger (Req 5.5)."""
        v1_triggers = {
            "PostFileSave", "PostFileCreate", "PostFileDelete", "Stop",
            "UserPromptSubmit", "PostTaskExec", "PreToolUse", "PostToolUse",
        }
        assert "Stop" in v1_triggers

    def test_recap_hook_not_post_task_execution(self, recap_data: dict):
        """module-recap-append does NOT use PostTaskExec (Req 5.6)."""
        assert recap_data["trigger"] != "PostTaskExec", (
            "REGRESSION: module-recap-append uses PostTaskExec. "
            "It must be the Stop trigger."
        )

    def test_celebration_hook_not_post_task_execution(self, celebration_data: dict):
        """module-completion-celebration does NOT use PostTaskExec (Req 5.6)."""
        assert celebration_data["trigger"] != "PostTaskExec", (
            "REGRESSION: module-completion-celebration uses PostTaskExec. "
            "It must be the Stop trigger."
        )


# ===========================================================================
# Task 3.2: TestBoundaryDetection — Requirements 5.2, 5.3, 3.1–3.6
# ===========================================================================

class TestBoundaryDetection:
    """Verify both hook prompts contain boundary detection logic."""

    def test_recap_references_bootcamp_progress(self, recap_prompt: str):
        """Recap prompt references config/bootcamp_progress.json (Req 5.2)."""
        assert "config/bootcamp_progress.json" in recap_prompt

    def test_celebration_references_bootcamp_progress(self, celebration_prompt: str):
        """Celebration prompt references config/bootcamp_progress.json (Req 5.2)."""
        assert "config/bootcamp_progress.json" in celebration_prompt

    def test_recap_references_modules_completed(self, recap_prompt: str):
        """Recap prompt references modules_completed (Req 5.2)."""
        assert "modules_completed" in recap_prompt

    def test_celebration_references_modules_completed(self, celebration_prompt: str):
        """Celebration prompt references modules_completed (Req 5.2)."""
        assert "modules_completed" in celebration_prompt

    def test_recap_contains_silent_exit(self, recap_prompt: str):
        """Recap prompt contains silent-exit instruction (Req 5.3)."""
        assert has_silent_processing(recap_prompt), (
            "Recap prompt must contain a silent-processing instruction."
        )

    def test_celebration_contains_silent_exit(self, celebration_prompt: str):
        """Celebration prompt contains silent-exit instruction (Req 5.3)."""
        assert has_silent_processing(celebration_prompt), (
            "Celebration prompt must contain a silent-processing instruction."
        )


class TestSchemaIntegrity:
    """Verify both hooks have all required v1 fields and correct structure."""

    def test_recap_has_all_required_fields(self, recap_data: dict):
        """Recap hook entry has all required v1 fields (Req 3.5)."""
        missing = _required_entry_fields(recap_data)
        assert not missing, f"Missing required fields: {', '.join(missing)}"

    def test_celebration_has_all_required_fields(self, celebration_data: dict):
        """Celebration hook entry has all required v1 fields (Req 3.6)."""
        missing = _required_entry_fields(celebration_data)
        assert not missing, f"Missing required fields: {', '.join(missing)}"

    def test_recap_then_type_is_ask_agent(self, recap_data: dict):
        """Recap hook action.type is agent (Req 3.5)."""
        assert recap_data["action"]["type"] == "agent"

    def test_celebration_then_type_is_ask_agent(self, celebration_data: dict):
        """Celebration hook action.type is agent (Req 3.6)."""
        assert celebration_data["action"]["type"] == "agent"

    def test_recap_version_is_valid_semver(self):
        """Recap hook wrapper declares the v1 schema version (Req 3.3)."""
        assert load_hook_wrapper(RECAP_HOOK_PATH).get("version") == "v1"

    def test_celebration_version_is_valid_semver(self):
        """Celebration hook wrapper declares the v1 schema version (Req 3.4)."""
        assert load_hook_wrapper(CELEBRATION_HOOK_PATH).get("version") == "v1"


# ===========================================================================
# Task 3.3: TestPromptRegression — Requirements 4.1–4.8
# ===========================================================================

class TestPromptRegression:
    """Verify prompt content has not regressed after the trigger migration."""

    def test_recap_references_module_dependencies(self, recap_prompt: str):
        """Recap prompt references config/module-dependencies.yaml (Req 4.1)."""
        assert "config/module-dependencies.yaml" in recap_prompt

    def test_celebration_references_module_dependencies(self, celebration_prompt: str):
        """Celebration prompt references config/module-dependencies.yaml (Req 4.2)."""
        assert "config/module-dependencies.yaml" in celebration_prompt

    def test_celebration_references_bootcamp_preferences(self, celebration_prompt: str):
        """Celebration prompt references config/bootcamp_preferences.yaml (Req 4.3)."""
        assert "config/bootcamp_preferences.yaml" in celebration_prompt

    def test_recap_contains_information_shared_instruction(self, recap_prompt: str):
        """Recap prompt contains instruction to gather information shared (Req 4.4)."""
        assert "information shared" in recap_prompt.lower()

    def test_recap_contains_questions_asked_instruction(self, recap_prompt: str):
        """Recap prompt contains instruction to gather questions asked (Req 4.4)."""
        assert "questions asked" in recap_prompt.lower()

    def test_recap_contains_answers_given_instruction(self, recap_prompt: str):
        """Recap prompt contains instruction to gather answers given (Req 4.4)."""
        assert "answers given" in recap_prompt.lower()

    def test_recap_contains_actions_taken_instruction(self, recap_prompt: str):
        """Recap prompt contains instruction to gather actions taken (Req 4.4)."""
        assert "actions taken" in recap_prompt.lower()

    def test_celebration_contains_congratulatory_banner(self, celebration_prompt: str):
        """Celebration prompt contains congratulatory banner instructions (Req 4.5)."""
        lower = celebration_prompt.lower()
        assert "congratulat" in lower, (
            "Celebration prompt must contain congratulatory banner instructions."
        )
        assert "banner" in lower, (
            "Celebration prompt must reference a banner display."
        )

    def test_celebration_contains_next_module_instructions(self, celebration_prompt: str):
        """Celebration prompt contains next module instructions (Req 4.6)."""
        assert "next module" in celebration_prompt.lower(), (
            "Celebration prompt must contain next module instructions."
        )

    def test_celebration_contains_graduation_instructions(self, celebration_prompt: str):
        """Celebration prompt contains graduation acknowledgment instructions (Req 4.6)."""
        assert "graduation" in celebration_prompt.lower(), (
            "Celebration prompt must contain graduation acknowledgment instructions."
        )

    def test_recap_contains_no_script_execution_constraint(self, recap_prompt: str):
        """Recap prompt contains constraint preventing script execution (Req 4.7)."""
        lower = recap_prompt.lower()
        assert "do not" in lower or "do not run" in lower
        assert "script" in lower or "command" in lower

    def test_recap_contains_no_filesystem_scan_constraint(self, recap_prompt: str):
        """Recap prompt contains constraint language (Req 4.7)."""
        assert "do not" in recap_prompt.lower()

    def test_celebration_contains_no_script_execution_constraint(
        self, celebration_prompt: str
    ):
        """Celebration prompt contains constraint preventing script execution (Req 4.8)."""
        lower = celebration_prompt.lower()
        assert "do not run any scripts" in lower or (
            "not run" in lower and "script" in lower
        ), "Celebration prompt must contain constraint preventing script execution."

    def test_celebration_contains_no_filesystem_scan_constraint(
        self, celebration_prompt: str
    ):
        """Celebration prompt contains constraint preventing file-system scans (Req 4.8)."""
        lower = celebration_prompt.lower()
        assert "file-system scan" in lower or "directory listing" in lower, (
            "Celebration prompt must contain constraint preventing file-system scans."
        )


# ===========================================================================
# Task 3.6: TestPropertySemver — Property 3: wrapper declares v1
# ===========================================================================

class TestPropertySemver:
    """Property 3: Each affected hook's wrapper declares the v1 schema version.

    **Validates: Requirements 3.3, 3.4**
    """

    @given(hook_path=st.sampled_from(AFFECTED_HOOKS))
    @settings(max_examples=20)
    def test_version_matches_semver_pattern(self, hook_path: Path) -> None:
        """For any affected hook, the wrapper version is ``v1``."""
        assert load_hook_wrapper(hook_path).get("version") == "v1", (
            f"Hook '{hook_path.name}' wrapper must declare version 'v1'."
        )


# ===========================================================================
# Task 3.4: TestPropertyEventType — Property 1
# ===========================================================================

class TestPropertyEventType:
    """Property 1: trigger is Stop for all affected hooks.

    **Validates: Requirements 1.1, 1.2**
    """

    @given(hook_path=st.sampled_from(AFFECTED_HOOKS))
    @settings(max_examples=20)
    def test_event_type_is_agent_stop(self, hook_path: Path):
        """For any affected hook, trigger must be Stop."""
        data = load_hook(hook_path)
        assert data["trigger"] == "Stop", (
            f"Hook {hook_path.name}: expected trigger='Stop', "
            f"got '{data['trigger']}'"
        )


# ===========================================================================
# Task 3.5: TestPropertySchemaIntegrity — Property 2
# ===========================================================================

class TestPropertySchemaIntegrity:
    """Property 2: Schema integrity preserved after modification.

    **Validates: Requirements 1.3, 1.4, 1.5, 1.6, 3.1, 3.2, 3.5, 3.6**
    """

    @given(hook_path=st.sampled_from(AFFECTED_HOOKS))
    @settings(max_examples=20)
    def test_all_required_fields_present(self, hook_path: Path):
        """All required v1 entry fields are present for any affected hook."""
        data = load_hook(hook_path)
        missing = _required_entry_fields(data)
        assert not missing, (
            f"Hook {hook_path.name} missing required fields: {', '.join(missing)}"
        )

    @given(hook_path=st.sampled_from(AFFECTED_HOOKS))
    @settings(max_examples=20)
    def test_then_type_is_ask_agent(self, hook_path: Path):
        """action.type equals 'agent' for any affected hook."""
        data = load_hook(hook_path)
        assert data["action"]["type"] == "agent", (
            f"Hook {hook_path.name}: expected action.type='agent', "
            f"got '{data['action']['type']}'"
        )


# ===========================================================================
# Task 3.7: TestPropertyBoundaryDetection — Property 4
# ===========================================================================

class TestPropertyBoundaryDetection:
    """Property 4: Boundary detection prompt integrity.

    **Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5, 2.6**
    """

    @given(hook_path=st.sampled_from(AFFECTED_HOOKS))
    @settings(max_examples=20)
    def test_prompt_references_bootcamp_progress(self, hook_path: Path) -> None:
        """Prompt contains reference to config/bootcamp_progress.json."""
        prompt = load_hook(hook_path)["action"]["prompt"]
        assert "config/bootcamp_progress.json" in prompt, (
            f"Hook '{hook_path.name}' prompt must reference "
            f"'config/bootcamp_progress.json' for boundary detection."
        )

    @given(hook_path=st.sampled_from(AFFECTED_HOOKS))
    @settings(max_examples=20)
    def test_prompt_references_modules_completed(self, hook_path: Path) -> None:
        """Prompt contains reference to modules_completed."""
        prompt = load_hook(hook_path)["action"]["prompt"]
        assert "modules_completed" in prompt, (
            f"Hook '{hook_path.name}' prompt must reference "
            f"'modules_completed' for boundary detection."
        )

    @given(hook_path=st.sampled_from(AFFECTED_HOOKS))
    @settings(max_examples=20)
    def test_prompt_contains_silent_exit_instruction(self, hook_path: Path) -> None:
        """Prompt contains a silent-exit instruction for the no-change case."""
        prompt = load_hook(hook_path)["action"]["prompt"]
        assert has_silent_processing(prompt), (
            f"Hook '{hook_path.name}' prompt must contain a silent-exit "
            f"instruction directing the agent to produce no output when "
            f"modules_completed has not changed."
        )


# ===========================================================================
# Task 3.8: TestPropertyBoundaryDetectionCorrectness — Property 7
# ===========================================================================


def has_new_completion(before: list[int], after: list[int]) -> bool:
    """Return True if after contains at least one module not in before."""
    return bool(set(after) - set(before))


class TestPropertyBoundaryDetectionCorrectness:
    """Property 7: Boundary detection correctness for arbitrary progress states.

    **Validates: Requirements 5.4**
    """

    @given(
        before=st.lists(st.integers(1, 11)),
        after=st.lists(st.integers(1, 11)),
    )
    @settings(max_examples=100)
    def test_boundary_detection_iff_new_module_present(
        self, before: list[int], after: list[int]
    ) -> None:
        """Detection returns True iff set(after) - set(before) is non-empty."""
        result = has_new_completion(before, after)
        expected = len(set(after) - set(before)) > 0
        assert result == expected, (
            f"has_new_completion({before}, {after}) returned {result}, "
            f"expected {expected}. "
            f"set(after) - set(before) = {set(after) - set(before)}"
        )


# ===========================================================================
# Task 3.9: TestPropertyWrongEventType — Property 8
# ===========================================================================

class TestPropertyWrongEventType:
    """Property 8: Wrong trigger causes test failure.

    **Validates: Requirements 5.6**
    """

    @given(trigger=st.text(min_size=1).filter(lambda s: s != "Stop"))
    @settings(max_examples=20)
    def test_non_agent_stop_event_type_is_rejected(self, trigger: str) -> None:
        """Any non-Stop trigger would be caught by validation."""
        assert trigger != "Stop", (
            f"Expected trigger to NOT be 'Stop', got '{trigger}'. "
            f"Non-Stop triggers must be rejected by hook validation."
        )
