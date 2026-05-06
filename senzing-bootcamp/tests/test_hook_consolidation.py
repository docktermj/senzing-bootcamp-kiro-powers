"""Tests for hook consolidation: verifying deleted hooks are gone,
registry/onboarding/categories are updated, and correctness properties hold.

Correctness Properties (from design.md):
  Property 1: Silence-first default in agentStop hook
  Property 2: All six trigger phrases preserved in promptSubmit hook
  Property 3: Hook file structural validity
"""

import json
from pathlib import Path

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

# ---------------------------------------------------------------------------
# Paths — relative to this test file's location
# ---------------------------------------------------------------------------

HOOKS_DIR = Path(__file__).resolve().parent.parent / "hooks"
STEERING_DIR = Path(__file__).resolve().parent.parent / "steering"

HOOK_REGISTRY = STEERING_DIR / "hook-registry.md"
ONBOARDING_FLOW = STEERING_DIR / "onboarding-flow.md"
HOOK_CATEGORIES = HOOKS_DIR / "hook-categories.yaml"

ASK_BOOTCAMPER_HOOK = HOOKS_DIR / "ask-bootcamper.kiro.hook"
REVIEW_BOOTCAMPER_INPUT_HOOK = HOOKS_DIR / "review-bootcamper-input.kiro.hook"

# Deleted hook files
DELETED_HOOKS = [
    HOOKS_DIR / "feedback-submission-reminder.kiro.hook",
    HOOKS_DIR / "capture-feedback.kiro.hook",
]

# Deleted hook ids (used in registry/onboarding/categories checks)
DELETED_HOOK_IDS = ["feedback-submission-reminder", "capture-feedback"]

# Valid event types for hook files
VALID_EVENT_TYPES = {
    "agentStop",
    "promptSubmit",
    "fileEdited",
    "fileCreated",
    "fileDeleted",
    "preToolUse",
    "postToolUse",
    "userTriggered",
    "postTaskExecution",
    "preTaskExecution",
}

# The six feedback trigger phrases
TRIGGER_PHRASES = [
    "bootcamp feedback",
    "power feedback",
    "submit feedback",
    "provide feedback",
    "I have feedback",
    "report an issue",
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _load_hook(path: Path) -> dict:
    """Parse a .kiro.hook JSON file and return the dict."""
    return json.loads(path.read_text(encoding="utf-8"))


def _get_all_hook_files() -> list[Path]:
    """Return all .kiro.hook files in the hooks directory."""
    return sorted(HOOKS_DIR.glob("*.kiro.hook"))


# ===========================================================================
# 6.4.1 Example tests verifying deleted hook files do not exist
# ===========================================================================


class TestDeletedHookFilesDoNotExist:
    """Verify that consolidated (deleted) hook files no longer exist on disk.

    **Validates: Requirements 3.2, 3.3**
    """

    def test_feedback_submission_reminder_hook_deleted(self):
        """feedback-submission-reminder.kiro.hook must not exist.

        **Validates: Requirement 3.2**
        """
        path = HOOKS_DIR / "feedback-submission-reminder.kiro.hook"
        assert not path.exists(), (
            f"Deleted hook file still exists: {path}"
        )

    def test_capture_feedback_hook_deleted(self):
        """capture-feedback.kiro.hook must not exist.

        **Validates: Requirement 3.3**
        """
        path = HOOKS_DIR / "capture-feedback.kiro.hook"
        assert not path.exists(), (
            f"Deleted hook file still exists: {path}"
        )


# ===========================================================================
# 6.4.2 Example tests verifying hook-registry.md does not contain removed entries
# ===========================================================================


class TestHookRegistryNoRemovedEntries:
    """Verify hook-registry.md does not reference deleted hooks.

    **Validates: Requirements 4.3, 4.4**
    """

    def test_registry_does_not_contain_feedback_submission_reminder(self):
        """hook-registry.md must not contain a feedback-submission-reminder entry.

        **Validates: Requirement 4.3**
        """
        text = HOOK_REGISTRY.read_text(encoding="utf-8")
        assert "feedback-submission-reminder" not in text, (
            "hook-registry.md still contains 'feedback-submission-reminder'"
        )

    def test_registry_does_not_contain_capture_feedback(self):
        """hook-registry.md must not contain a capture-feedback entry.

        **Validates: Requirement 4.4**
        """
        text = HOOK_REGISTRY.read_text(encoding="utf-8")
        assert "capture-feedback" not in text, (
            "hook-registry.md still contains 'capture-feedback'"
        )


# ===========================================================================
# 6.4.3 Example tests verifying onboarding-flow.md does not contain removed entries
# ===========================================================================


class TestOnboardingFlowNoRemovedEntries:
    """Verify onboarding-flow.md does not reference deleted hooks in its tables.

    **Validates: Requirements 5.1, 5.2**
    """

    def test_onboarding_flow_no_feedback_submission_reminder(self):
        """onboarding-flow.md must not contain feedback-submission-reminder row.

        **Validates: Requirement 5.1**
        """
        text = ONBOARDING_FLOW.read_text(encoding="utf-8")
        assert "feedback-submission-reminder" not in text, (
            "onboarding-flow.md still contains 'feedback-submission-reminder'"
        )

    def test_onboarding_flow_no_capture_feedback(self):
        """onboarding-flow.md must not contain capture-feedback row.

        **Validates: Requirement 5.2**
        """
        text = ONBOARDING_FLOW.read_text(encoding="utf-8")
        assert "capture-feedback" not in text, (
            "onboarding-flow.md still contains 'capture-feedback'"
        )


# ===========================================================================
# 6.4.4 Example tests verifying hook-categories.yaml does not list deleted hooks
# ===========================================================================


class TestHookCategoriesNoDeletedHooks:
    """Verify hook-categories.yaml does not list deleted hooks.

    **Validates: Requirement 3.1**
    """

    def test_categories_no_feedback_submission_reminder(self):
        """hook-categories.yaml must not list feedback-submission-reminder.

        **Validates: Requirement 3.1**
        """
        text = HOOK_CATEGORIES.read_text(encoding="utf-8")
        assert "feedback-submission-reminder" not in text, (
            "hook-categories.yaml still lists 'feedback-submission-reminder'"
        )

    def test_categories_no_capture_feedback(self):
        """hook-categories.yaml must not list capture-feedback.

        **Validates: Requirement 3.1**
        """
        text = HOOK_CATEGORIES.read_text(encoding="utf-8")
        assert "capture-feedback" not in text, (
            "hook-categories.yaml still lists 'capture-feedback'"
        )


# ===========================================================================
# 6.4.5 Property test: silence-first default in ask-bootcamper prompt (Property 1)
# ===========================================================================


class TestSilenceFirstDefault:
    """Property 1: Silence-first default in agentStop hook.

    For any valid ask-bootcamper.kiro.hook file, the then.prompt field SHALL
    contain an explicit "produce no output" instruction as the dominant default
    before any conditional output logic.

    **Validates: Requirements 1.4, 7.1**
    """

    @given(start_idx=st.integers(min_value=0, max_value=200))
    @settings(max_examples=100)
    def test_silence_instruction_precedes_conditional_output(self, start_idx: int):
        """The silence instruction must appear before any conditional output logic.

        Generate random start positions into the prompt and verify that the
        silence instruction always appears at or before the first conditional
        output keyword found after that position.

        **Validates: Requirements 1.4, 7.1**
        """
        prompt = _load_hook(ASK_BOOTCAMPER_HOOK)["then"]["prompt"]
        prompt_upper = prompt.upper()

        # The silence instruction must be at the very start
        silence_pos = prompt_upper.find("PRODUCE NO OUTPUT")
        assert silence_pos != -1, "Prompt missing 'PRODUCE NO OUTPUT' instruction"

        # Conditional output keywords that indicate non-silent behavior
        conditional_keywords = ["RECAP", "CLOSING QUESTION", "PHASE 1", "PHASE 2"]

        for keyword in conditional_keywords:
            keyword_pos = prompt_upper.find(keyword)
            if keyword_pos != -1:
                assert silence_pos < keyword_pos, (
                    f"Silence instruction (pos {silence_pos}) must precede "
                    f"conditional keyword '{keyword}' (pos {keyword_pos})"
                )

    @given(substring_len=st.integers(min_value=10, max_value=100))
    @settings(max_examples=100)
    def test_first_line_is_silence_instruction(self, substring_len: int):
        """The very first line of the prompt must be a silence/no-output instruction.

        **Validates: Requirements 1.4, 7.1**
        """
        prompt = _load_hook(ASK_BOOTCAMPER_HOOK)["then"]["prompt"]
        first_line = prompt.split("\n")[0].strip().upper()

        assert "PRODUCE NO OUTPUT" in first_line, (
            f"First line of prompt is not a silence instruction: {first_line!r}"
        )


# ===========================================================================
# 6.4.6 Property test: all six trigger phrases preserved (Property 2)
# ===========================================================================


# Strategy: generate random case variations of trigger phrases
def _random_case(phrase: str) -> st.SearchStrategy[str]:
    """Generate random case variations of a phrase."""
    return st.builds(
        lambda chars: "".join(chars),
        st.tuples(
            *[st.sampled_from([c.lower(), c.upper()]) for c in phrase]
        ),
    )


st_trigger_phrase = st.sampled_from(TRIGGER_PHRASES)


class TestTriggerPhrasesPreserved:
    """Property 2: All six trigger phrases preserved with case-insensitive matching.

    For any case variation of the six feedback trigger phrases, the
    review-bootcamper-input.kiro.hook prompt SHALL contain all six phrases
    and instruct case-insensitive matching.

    **Validates: Requirements 2.2, 7.4**
    """

    @given(phrase=st_trigger_phrase, upper_flag=st.booleans())
    @settings(max_examples=100)
    def test_all_trigger_phrases_present_case_insensitive(
        self, phrase: str, upper_flag: bool
    ):
        """Each trigger phrase must appear in the prompt regardless of case variation.

        **Validates: Requirements 2.2, 7.4**
        """
        prompt = _load_hook(REVIEW_BOOTCAMPER_INPUT_HOOK)["then"]["prompt"]
        prompt_lower = prompt.lower()

        # Verify the phrase (in any case) is present in the prompt
        test_phrase = phrase.upper() if upper_flag else phrase.lower()
        assert test_phrase.lower() in prompt_lower, (
            f"Trigger phrase '{phrase}' not found in review-bootcamper-input prompt"
        )

    @given(phrase=st_trigger_phrase)
    @settings(max_examples=100)
    def test_prompt_instructs_case_insensitive_matching(self, phrase: str):
        """The prompt must instruct case-insensitive matching for trigger phrases.

        **Validates: Requirements 2.2, 7.4**
        """
        prompt = _load_hook(REVIEW_BOOTCAMPER_INPUT_HOOK)["then"]["prompt"]
        prompt_lower = prompt.lower()

        assert "case-insensitive" in prompt_lower, (
            "Prompt does not instruct case-insensitive matching"
        )

    def test_all_six_phrases_present(self):
        """All six trigger phrases must be present in the prompt.

        **Validates: Requirements 2.2, 7.4**
        """
        prompt = _load_hook(REVIEW_BOOTCAMPER_INPUT_HOOK)["then"]["prompt"]
        prompt_lower = prompt.lower()

        for phrase in TRIGGER_PHRASES:
            assert phrase.lower() in prompt_lower, (
                f"Trigger phrase '{phrase}' not found in prompt"
            )


# ===========================================================================
# 6.4.7 Property test: all hook files are valid JSON with required keys (Property 3)
# ===========================================================================


# Strategy: select from actual hook files on disk
st_hook_file = st.sampled_from(_get_all_hook_files())


class TestHookFileStructuralValidity:
    """Property 3: Hook file structural validity.

    For any .kiro.hook file in senzing-bootcamp/hooks/, the file SHALL parse
    as valid JSON containing all required keys (name, version, description,
    when, then) with when.type being a valid event type and then.type being
    askAgent.

    **Validates: Requirements 1.5, 2.4, 6.2, 6.3**
    """

    @given(hook_path=st_hook_file)
    @settings(max_examples=100)
    def test_hook_file_parses_as_valid_json(self, hook_path: Path):
        """Each hook file must parse as valid JSON.

        **Validates: Requirements 1.5, 6.2**
        """
        text = hook_path.read_text(encoding="utf-8")
        data = json.loads(text)
        assert isinstance(data, dict), (
            f"{hook_path.name} root is not a JSON object"
        )

    @given(hook_path=st_hook_file)
    @settings(max_examples=100)
    def test_hook_file_has_required_keys(self, hook_path: Path):
        """Each hook file must contain name, version, description, when, then.

        **Validates: Requirements 1.5, 6.2**
        """
        data = _load_hook(hook_path)
        required_keys = {"name", "version", "description", "when", "then"}
        missing = required_keys - set(data.keys())
        assert not missing, (
            f"{hook_path.name} missing required keys: {missing}"
        )

    @given(hook_path=st_hook_file)
    @settings(max_examples=100)
    def test_hook_when_type_is_valid(self, hook_path: Path):
        """Each hook's when.type must be a valid event type.

        **Validates: Requirements 6.2, 6.3**
        """
        data = _load_hook(hook_path)
        event_type = data["when"]["type"]
        assert event_type in VALID_EVENT_TYPES, (
            f"{hook_path.name} has invalid when.type: {event_type!r}"
        )

    @given(hook_path=st_hook_file)
    @settings(max_examples=100)
    def test_hook_then_type_is_ask_agent(self, hook_path: Path):
        """Each hook's then.type must be 'askAgent'.

        **Validates: Requirements 2.4, 6.3**
        """
        data = _load_hook(hook_path)
        then_type = data["then"]["type"]
        assert then_type == "askAgent", (
            f"{hook_path.name} has then.type={then_type!r}, expected 'askAgent'"
        )
