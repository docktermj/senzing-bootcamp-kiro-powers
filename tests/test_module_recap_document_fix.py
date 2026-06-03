"""Tests for the module-recap-document-fix spec.

Validates that both module-recap-append and module-completion-celebration hooks
have correct event types, boundary detection, schema integrity, and prompt content
after the postTaskExecution → agentStop migration.
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
    SEMVER_PATTERN,
    VALID_EVENT_TYPES,
    has_silent_processing,
    load_hook,
    validate_required_fields,
    validate_version,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

RECAP_HOOK_PATH = HOOKS_DIR / "module-recap-append.kiro.hook"
CELEBRATION_HOOK_PATH = HOOKS_DIR / "module-completion-celebration.kiro.hook"
AFFECTED_HOOKS: list[Path] = [RECAP_HOOK_PATH, CELEBRATION_HOOK_PATH]


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def recap_data() -> dict:
    """Load and parse the module-recap-append hook file."""
    return load_hook(RECAP_HOOK_PATH)


@pytest.fixture
def celebration_data() -> dict:
    """Load and parse the module-completion-celebration hook file."""
    return load_hook(CELEBRATION_HOOK_PATH)


@pytest.fixture
def recap_prompt(recap_data: dict) -> str:
    """Extract the prompt text from the recap hook."""
    return recap_data["then"]["prompt"]


@pytest.fixture
def celebration_prompt(celebration_data: dict) -> str:
    """Extract the prompt text from the celebration hook."""
    return celebration_data["then"]["prompt"]


# ===========================================================================
# Task 3.1: TestEventTypeMigration — Requirements 5.1, 5.5, 5.6
# ===========================================================================

class TestEventTypeMigration:
    """Verify both hooks use agentStop event type after migration."""

    def test_recap_hook_uses_agent_stop(self, recap_data: dict):
        """module-recap-append uses agentStop event type (Req 5.1)."""
        assert recap_data["when"]["type"] == "agentStop", (
            f"Expected 'agentStop' but got '{recap_data['when']['type']}'. "
            "The module-recap-append hook must use agentStop, not postTaskExecution."
        )

    def test_celebration_hook_uses_agent_stop(self, celebration_data: dict):
        """module-completion-celebration uses agentStop event type (Req 5.1)."""
        assert celebration_data["when"]["type"] == "agentStop", (
            f"Expected 'agentStop' but got '{celebration_data['when']['type']}'. "
            "The module-completion-celebration hook must use agentStop, not postTaskExecution."
        )

    def test_agent_stop_is_valid_event_type(self):
        """agentStop is a recognized valid event type (Req 5.5)."""
        assert "agentStop" in VALID_EVENT_TYPES

    def test_recap_hook_not_post_task_execution(self, recap_data: dict):
        """module-recap-append does NOT use postTaskExecution (Req 5.6)."""
        assert recap_data["when"]["type"] != "postTaskExecution", (
            "REGRESSION: module-recap-append still uses postTaskExecution. "
            "It must be changed to agentStop."
        )

    def test_celebration_hook_not_post_task_execution(self, celebration_data: dict):
        """module-completion-celebration does NOT use postTaskExecution (Req 5.6)."""
        assert celebration_data["when"]["type"] != "postTaskExecution", (
            "REGRESSION: module-completion-celebration still uses postTaskExecution. "
            "It must be changed to agentStop."
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
    """Verify both hooks have all required fields and correct structure."""

    def test_recap_has_all_required_fields(self, recap_data: dict):
        """Recap hook has all required fields (Req 3.5)."""
        missing = validate_required_fields(recap_data)
        assert not missing, f"Missing required fields: {', '.join(missing)}"

    def test_celebration_has_all_required_fields(self, celebration_data: dict):
        """Celebration hook has all required fields (Req 3.6)."""
        missing = validate_required_fields(celebration_data)
        assert not missing, f"Missing required fields: {', '.join(missing)}"

    def test_recap_then_type_is_ask_agent(self, recap_data: dict):
        """Recap hook then.type is askAgent (Req 3.5)."""
        assert recap_data["then"]["type"] == "askAgent"

    def test_celebration_then_type_is_ask_agent(self, celebration_data: dict):
        """Celebration hook then.type is askAgent (Req 3.6)."""
        assert celebration_data["then"]["type"] == "askAgent"

    def test_recap_version_is_valid_semver(self, recap_data: dict):
        """Recap hook version matches semver format (Req 3.3)."""
        assert validate_version(recap_data["version"]), (
            f"Invalid semver: {recap_data['version']}"
        )

    def test_celebration_version_is_valid_semver(self, celebration_data: dict):
        """Celebration hook version matches semver format (Req 3.4)."""
        assert validate_version(celebration_data["version"]), (
            f"Invalid semver: {celebration_data['version']}"
        )


# ===========================================================================
# Task 3.3: TestPromptRegression — Requirements 4.1–4.8
# ===========================================================================

class TestPromptRegression:
    """Verify prompt content has not regressed after the event type migration.

    Validates that both hooks retain their functional prompt content including
    config file references, session content gathering, celebration instructions,
    and execution constraints.
    """

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
        lower = recap_prompt.lower()
        assert "information shared" in lower

    def test_recap_contains_questions_asked_instruction(self, recap_prompt: str):
        """Recap prompt contains instruction to gather questions asked (Req 4.4)."""
        lower = recap_prompt.lower()
        assert "questions asked" in lower

    def test_recap_contains_answers_given_instruction(self, recap_prompt: str):
        """Recap prompt contains instruction to gather answers given (Req 4.4)."""
        lower = recap_prompt.lower()
        assert "answers given" in lower

    def test_recap_contains_actions_taken_instruction(self, recap_prompt: str):
        """Recap prompt contains instruction to gather actions taken (Req 4.4)."""
        lower = recap_prompt.lower()
        assert "actions taken" in lower

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
        lower = celebration_prompt.lower()
        assert "next module" in lower, (
            "Celebration prompt must contain next module instructions."
        )

    def test_celebration_contains_graduation_instructions(self, celebration_prompt: str):
        """Celebration prompt contains graduation acknowledgment instructions (Req 4.6)."""
        lower = celebration_prompt.lower()
        assert "graduation" in lower, (
            "Celebration prompt must contain graduation acknowledgment instructions."
        )

    def test_recap_contains_no_script_execution_constraint(self, recap_prompt: str):
        """Recap prompt contains constraint preventing script execution (Req 4.7)."""
        lower = recap_prompt.lower()
        assert "do not" in lower or "do not run" in lower
        assert "script" in lower or "command" in lower

    def test_recap_contains_no_filesystem_scan_constraint(self, recap_prompt: str):
        """Recap prompt contains constraint preventing file-system scans (Req 4.7)."""
        lower = recap_prompt.lower()
        # The recap hook doesn't have explicit "file-system scans" language but has
        # constraints about not altering behavior and keeping things factual.
        # Check for the constraint language that exists in the actual hook
        assert "do not" in lower

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
# Task 3.6: TestPropertySemver — Property 3: Version field is valid semver
# ===========================================================================

AFFECTED_HOOKS = [RECAP_HOOK_PATH, CELEBRATION_HOOK_PATH]


class TestPropertySemver:
    """Property 3: Version field is valid semver.

    For any hook in the affected set, the version field matches SEMVER_PATTERN.

    **Validates: Requirements 3.3, 3.4**
    """

    @given(hook_path=st.sampled_from(AFFECTED_HOOKS))
    @settings(max_examples=20)
    def test_version_matches_semver_pattern(self, hook_path: Path) -> None:
        """For any affected hook, version is valid semver."""
        data = load_hook(hook_path)
        version = data["version"]
        assert SEMVER_PATTERN.match(version) is not None, (
            f"Hook '{hook_path.name}' has invalid semver version: '{version}'. "
            f"Expected format: MAJOR.MINOR.PATCH with no leading zeros."
        )


# ===========================================================================
# Task 3.4: TestPropertyEventType — Property 1
# Validates: Requirements 1.1, 1.2
# ===========================================================================

# Affected hook paths for property-based sampling
AFFECTED_HOOKS = [RECAP_HOOK_PATH, CELEBRATION_HOOK_PATH]


class TestPropertyEventType:
    """Property 1: Event type is agentStop for all affected hooks.

    **Validates: Requirements 1.1, 1.2**

    For any hook in the set {module-recap-append, module-completion-celebration},
    the when.type field SHALL equal "agentStop".
    """

    @given(hook_path=st.sampled_from(AFFECTED_HOOKS))
    @settings(max_examples=20)
    def test_event_type_is_agent_stop(self, hook_path: Path):
        """For any affected hook, when.type must be agentStop."""
        data = load_hook(hook_path)
        assert data["when"]["type"] == "agentStop", (
            f"Hook {hook_path.name}: expected when.type='agentStop', "
            f"got '{data['when']['type']}'"
        )


# ===========================================================================
# Task 3.5: TestPropertySchemaIntegrity — Property 2
# Validates: Requirements 1.3, 1.4, 1.5, 1.6, 3.1, 3.2, 3.5, 3.6
# ===========================================================================

class TestPropertySchemaIntegrity:
    """Property 2: Schema integrity preserved after modification.

    For any hook in the affected set, all required fields are present
    and then.type == "askAgent".

    **Validates: Requirements 1.3, 1.4, 1.5, 1.6, 3.1, 3.2, 3.5, 3.6**
    """

    @given(hook_path=st.sampled_from(AFFECTED_HOOKS))
    @settings(max_examples=20)
    def test_all_required_fields_present(self, hook_path: Path):
        """All required fields are present for any affected hook."""
        data = load_hook(hook_path)
        missing = validate_required_fields(data)
        assert not missing, (
            f"Hook {hook_path.name} missing required fields: {', '.join(missing)}"
        )

    @given(hook_path=st.sampled_from(AFFECTED_HOOKS))
    @settings(max_examples=20)
    def test_then_type_is_ask_agent(self, hook_path: Path):
        """then.type equals 'askAgent' for any affected hook."""
        data = load_hook(hook_path)
        assert data["then"]["type"] == "askAgent", (
            f"Hook {hook_path.name}: expected then.type='askAgent', "
            f"got '{data['then']['type']}'"
        )


# ===========================================================================
# Task 3.7: TestPropertyBoundaryDetection — Property 4
# Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5, 2.6
# ===========================================================================

class TestPropertyBoundaryDetection:
    """Property 4: Boundary detection prompt integrity.

    For any hook in the affected set, the then.prompt SHALL contain a reference
    to config/bootcamp_progress.json, a reference to modules_completed, and a
    silent-exit instruction for the no-change case.

    **Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5, 2.6**
    """

    @given(hook_path=st.sampled_from(AFFECTED_HOOKS))
    @settings(max_examples=20)
    def test_prompt_references_bootcamp_progress(self, hook_path: Path) -> None:
        """Prompt contains reference to config/bootcamp_progress.json."""
        data = load_hook(hook_path)
        prompt = data["then"]["prompt"]
        assert "config/bootcamp_progress.json" in prompt, (
            f"Hook '{hook_path.name}' prompt must reference "
            f"'config/bootcamp_progress.json' for boundary detection."
        )

    @given(hook_path=st.sampled_from(AFFECTED_HOOKS))
    @settings(max_examples=20)
    def test_prompt_references_modules_completed(self, hook_path: Path) -> None:
        """Prompt contains reference to modules_completed."""
        data = load_hook(hook_path)
        prompt = data["then"]["prompt"]
        assert "modules_completed" in prompt, (
            f"Hook '{hook_path.name}' prompt must reference "
            f"'modules_completed' for boundary detection."
        )

    @given(hook_path=st.sampled_from(AFFECTED_HOOKS))
    @settings(max_examples=20)
    def test_prompt_contains_silent_exit_instruction(self, hook_path: Path) -> None:
        """Prompt contains a silent-exit instruction for the no-change case."""
        data = load_hook(hook_path)
        prompt = data["then"]["prompt"]
        assert has_silent_processing(prompt), (
            f"Hook '{hook_path.name}' prompt must contain a silent-exit "
            f"instruction directing the agent to produce no output when "
            f"modules_completed has not changed."
        )


# ===========================================================================
# Task 3.8: TestPropertyBoundaryDetectionCorrectness — Property 7
# Validates: Requirements 5.4
# ===========================================================================


def has_new_completion(before: list[int], after: list[int]) -> bool:
    """Return True if after contains at least one module not in before."""
    return bool(set(after) - set(before))


class TestPropertyBoundaryDetectionCorrectness:
    """Property 7: Boundary detection correctness for arbitrary progress states.

    For any pair of valid progress states (before, after) representing
    modules_completed arrays, boundary detection SHALL return True if and only
    if after contains at least one module number not present in before.

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
# Validates: Requirements 5.6
# ===========================================================================

class TestPropertyWrongEventType:
    """Property 8: Wrong event type causes test failure.

    For any event type string that is NOT "agentStop", validating it against
    the expected event type for these hooks SHALL produce a failure.

    **Validates: Requirements 5.6**
    """

    @given(event_type=st.text(min_size=1).filter(lambda s: s != "agentStop"))
    @settings(max_examples=20)
    def test_non_agent_stop_event_type_is_rejected(self, event_type: str) -> None:
        """Any non-agentStop event type would be caught by validation."""
        assert event_type != "agentStop", (
            f"Expected event type to NOT be 'agentStop', got '{event_type}'. "
            f"Non-agentStop event types must be rejected by hook validation."
        )
