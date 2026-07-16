"""Hook-prompt validation tests for the demoted Q&A agent hooks.

Feature: durable-qa-capture (task 6.2)

The durable-Q&A-capture bugfix moved the durability guarantee off the two
``type: agent`` Q&A hooks and onto the command-backed hook
``capture-qa-events.json``. Task 6.2 reframed the in-prompt Q&A logging
instructions in ``ask-bootcamper.json`` and ``review-bootcamper-input.json`` so
that running ``log_qa_event.py`` reads as a redundant, best-effort backstop —
NOT the primary durability path — while leaving every non-Q&A behavior of those
hooks untouched.

These example-based structural tests assert three things about the ACTUAL
on-disk prompt text after the task 6.2 edits:

1. Both hooks preserve their non-Q&A behavior: ``ask-bootcamper`` keeps its six
   phases (Phase 0 recap, Phases 1/1.5/2/3/4) plus its feedback reminder logic,
   and ``review-bootcamper-input`` keeps its feedback / status / repeat-request
   triggers.
2. The Q&A logging text now reads as a redundant / best-effort backstop and
   defers the durability guarantee to the command-backed hook
   ``capture-qa-events.json``.
3. Both hooks remain ``type: agent`` hooks — only the durability guarantee moved
   to the command hook; these keep their agent action for their other behavior.

Per the project-structure rule, tests validating real hook files on disk live in
the repo-root ``tests/`` directory (consistent with
``tests/test_answer_processing_hook_prompt.py`` and ``tests/test_ask_once_*``).

**Validates: Requirements 2.1**
"""

from __future__ import annotations

from pathlib import Path

import pytest

from hook_test_helpers import load_hook, load_hook_wrapper

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

_ASK_BOOTCAMPER_HOOK: Path = Path("senzing-bootcamp/hooks/ask-bootcamper.json")
_REVIEW_INPUT_HOOK: Path = Path("senzing-bootcamp/hooks/review-bootcamper-input.json")

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# The command-backed hook that now GUARANTEES durable capture.
_COMMAND_HOOK_NAME: str = "capture-qa-events.json"

# Demotion language that must appear in BOTH reframed Q&A sections.
_DEMOTION_MARKERS: list[str] = [
    "redundant",
    "best-effort backstop",
    "NOT the primary durability path",
    "MAY",
    _COMMAND_HOOK_NAME,
]

# ask-bootcamper's six phase headings (non-Q&A behavior that must be preserved).
_ASK_PHASE_MARKERS: list[str] = [
    "PHASE 0: MODULE RECAP APPEND",
    "PHASE 1: CLOSING QUESTION",
    "PHASE 1.5: LEADING-QUESTION COUNT AUDIT",
    "PHASE 2: STEP SEQUENCING",
    "PHASE 3: MCP-FIRST COMPLIANCE",
    "PHASE 4: QUESTION FORMAT",
]

# ask-bootcamper feedback/status behavior that must be preserved.
_ASK_FEEDBACK_MARKERS: list[str] = [
    "FEEDBACK SUBMISSION REMINDER",
    "bootcamp feedback",
]

# review-bootcamper-input feedback trigger phrases (non-Q&A behavior).
_REVIEW_FEEDBACK_PHRASES: list[str] = [
    "bootcamp feedback",
    "power feedback",
    "submit feedback",
    "provide feedback",
    "I have feedback",
    "report an issue",
]

# review-bootcamper-input status trigger phrases (non-Q&A behavior).
_REVIEW_STATUS_PHRASES: list[str] = [
    "where am I",
    "status",
    "what step am I on",
    "show progress",
    "how far along am I",
]

# review-bootcamper-input repeat-request trigger phrases (non-Q&A behavior).
_REVIEW_REPEAT_PHRASES: list[str] = [
    "repeat that",
    "repeat the question",
    "say that again",
    "what was the question",
    "ask me again",
    "come again",
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _hook_prompt(path: Path) -> str:
    """Return the agent-action prompt text from a v1 hook file.

    Args:
        path: Path to the ``<id>.json`` hook file.

    Returns:
        The ``action.prompt`` string of the single v1 hook entry.
    """
    assert path.exists(), f"Hook file not found: {path}"
    entry = load_hook(path)
    return entry["action"]["prompt"]


# ---------------------------------------------------------------------------
# TestAskBootcamperRemainsAgentHook
# ---------------------------------------------------------------------------


class TestAskBootcamperRemainsAgentHook:
    """The ask-bootcamper hook stays a ``type: agent`` Stop hook.

    The durability guarantee moved to the command hook, but this hook remains an
    agent hook for its phase logic and feedback behavior.

    **Validates: Requirements 2.1**
    """

    @pytest.fixture(autouse=True)
    def _load(self) -> None:
        self.wrapper = load_hook_wrapper(_ASK_BOOTCAMPER_HOOK)
        self.entry = self.wrapper["hooks"][0]

    def test_wrapper_declares_version_v1(self) -> None:
        """The hook file declares top-level ``version`` of ``"v1"``."""
        assert self.wrapper.get("version") == "v1", (
            "ask-bootcamper.json must declare version 'v1'"
        )

    def test_trigger_is_stop(self) -> None:
        """The hook fires on the ``Stop`` trigger (Q&A ask cadence)."""
        assert self.entry.get("trigger") == "Stop", (
            "ask-bootcamper must remain a Stop-triggered hook"
        )

    def test_action_type_is_agent(self) -> None:
        """The hook action stays ``type: agent`` (not converted to command)."""
        assert self.entry["action"].get("type") == "agent", (
            "ask-bootcamper must remain a type: agent hook — only the durability "
            "guarantee moved to the command-backed hook"
        )


# ---------------------------------------------------------------------------
# TestAskBootcamperNonQaBehaviorPreserved
# ---------------------------------------------------------------------------


class TestAskBootcamperNonQaBehaviorPreserved:
    """ask-bootcamper keeps all non-Q&A behavior (phases + feedback logic).

    **Validates: Requirements 2.1**
    """

    @pytest.fixture(autouse=True)
    def _load_prompt(self) -> None:
        self.prompt = _hook_prompt(_ASK_BOOTCAMPER_HOOK)

    @pytest.mark.parametrize("phase_marker", _ASK_PHASE_MARKERS)
    def test_phase_headings_present(self, phase_marker: str) -> None:
        """Every phase heading must remain in the prompt after the reframe."""
        assert phase_marker in self.prompt, (
            f"ask-bootcamper prompt is missing phase heading '{phase_marker}' — "
            "the Q&A reframe must not remove phase logic"
        )

    def test_phase_2_subphases_present(self) -> None:
        """Phase 2's three sub-phases (2A/2B/2C) must remain present."""
        for sub_phase in ("SUB-PHASE 2A", "SUB-PHASE 2B", "SUB-PHASE 2C"):
            assert sub_phase in self.prompt, (
                f"ask-bootcamper prompt is missing '{sub_phase}' — Phase 2 "
                "sub-phase logic must be preserved"
            )

    @pytest.mark.parametrize("feedback_marker", _ASK_FEEDBACK_MARKERS)
    def test_feedback_behavior_preserved(self, feedback_marker: str) -> None:
        """The feedback reminder / status behavior must remain present."""
        assert feedback_marker in self.prompt, (
            f"ask-bootcamper prompt is missing feedback marker '{feedback_marker}' "
            "— the Q&A reframe must not remove feedback behavior"
        )

    def test_default_output_period_rule_preserved(self) -> None:
        """The DEFAULT OUTPUT single-period rule must remain intact."""
        assert "DEFAULT OUTPUT: ." in self.prompt, (
            "ask-bootcamper prompt must preserve the DEFAULT OUTPUT period rule"
        )


# ---------------------------------------------------------------------------
# TestAskBootcamperQaCaptureDemoted
# ---------------------------------------------------------------------------


class TestAskBootcamperQaCaptureDemoted:
    """ask-bootcamper's Q&A logging now reads as a redundant backstop.

    **Validates: Requirements 2.1**
    """

    @pytest.fixture(autouse=True)
    def _load_prompt(self) -> None:
        self.prompt = _hook_prompt(_ASK_BOOTCAMPER_HOOK)

    def test_qa_capture_section_present(self) -> None:
        """The Q&A CAPTURE section must still exist (as a backstop)."""
        assert "Q&A CAPTURE" in self.prompt, (
            "ask-bootcamper prompt must retain a 'Q&A CAPTURE' section"
        )

    @pytest.mark.parametrize("marker", _DEMOTION_MARKERS)
    def test_demotion_language_present(self, marker: str) -> None:
        """The reframed section must contain each demotion marker."""
        assert marker in self.prompt, (
            f"ask-bootcamper Q&A CAPTURE section is missing demotion marker "
            f"'{marker}' — the logging step must read as a redundant, best-effort "
            "backstop, not the primary durability path"
        )

    def test_durability_guaranteed_by_command_hook(self) -> None:
        """The section must credit the command-backed hook with the guarantee."""
        assert "GUARANTEED" in self.prompt, (
            "ask-bootcamper Q&A CAPTURE section must state durable capture is "
            "GUARANTEED"
        )
        assert "command-backed hook" in self.prompt, (
            "ask-bootcamper Q&A CAPTURE section must credit the command-backed "
            "hook with the durability guarantee"
        )

    def test_logging_is_optional_may_run(self) -> None:
        """The agent step must be phrased as optional ('you MAY run')."""
        assert "you MAY run the command" in self.prompt, (
            "ask-bootcamper Q&A CAPTURE section must phrase running "
            "log_qa_event.py as optional ('you MAY run the command'), not "
            "mandatory"
        )

    def test_references_record_question_helper(self) -> None:
        """The backstop still references the record-question helper invocation."""
        assert "log_qa_event.py record-question" in self.prompt, (
            "ask-bootcamper Q&A CAPTURE section must still reference the "
            "log_qa_event.py record-question backstop invocation"
        )


# ---------------------------------------------------------------------------
# TestReviewInputRemainsAgentHook
# ---------------------------------------------------------------------------


class TestReviewInputRemainsAgentHook:
    """The review-bootcamper-input hook stays a ``type: agent`` hook.

    **Validates: Requirements 2.1**
    """

    @pytest.fixture(autouse=True)
    def _load(self) -> None:
        self.wrapper = load_hook_wrapper(_REVIEW_INPUT_HOOK)
        self.entry = self.wrapper["hooks"][0]

    def test_wrapper_declares_version_v1(self) -> None:
        """The hook file declares top-level ``version`` of ``"v1"``."""
        assert self.wrapper.get("version") == "v1", (
            "review-bootcamper-input.json must declare version 'v1'"
        )

    def test_trigger_is_userpromptsubmit(self) -> None:
        """The hook fires on ``UserPromptSubmit`` (Q&A answer cadence)."""
        assert self.entry.get("trigger") == "UserPromptSubmit", (
            "review-bootcamper-input must remain a UserPromptSubmit-triggered hook"
        )

    def test_action_type_is_agent(self) -> None:
        """The hook action stays ``type: agent`` (not converted to command)."""
        assert self.entry["action"].get("type") == "agent", (
            "review-bootcamper-input must remain a type: agent hook — only the "
            "durability guarantee moved to the command-backed hook"
        )


# ---------------------------------------------------------------------------
# TestReviewInputNonQaBehaviorPreserved
# ---------------------------------------------------------------------------


class TestReviewInputNonQaBehaviorPreserved:
    """review-bootcamper-input keeps its feedback / status / repeat triggers.

    **Validates: Requirements 2.1**
    """

    @pytest.fixture(autouse=True)
    def _load_prompt(self) -> None:
        self.prompt = _hook_prompt(_REVIEW_INPUT_HOOK)

    @pytest.mark.parametrize("phrase", _REVIEW_FEEDBACK_PHRASES)
    def test_feedback_trigger_phrases_present(self, phrase: str) -> None:
        """Every feedback trigger phrase must remain in the prompt."""
        assert phrase in self.prompt, (
            f"review-bootcamper-input prompt is missing feedback trigger phrase "
            f"'{phrase}' — the Q&A reframe must not remove feedback triggers"
        )

    @pytest.mark.parametrize("phrase", _REVIEW_STATUS_PHRASES)
    def test_status_trigger_phrases_present(self, phrase: str) -> None:
        """Every status trigger phrase must remain in the prompt."""
        assert phrase in self.prompt, (
            f"review-bootcamper-input prompt is missing status trigger phrase "
            f"'{phrase}' — the Q&A reframe must not remove status triggers"
        )

    @pytest.mark.parametrize("phrase", _REVIEW_REPEAT_PHRASES)
    def test_repeat_request_phrases_present(self, phrase: str) -> None:
        """Every repeat-request trigger phrase must remain in the prompt."""
        assert phrase in self.prompt, (
            f"review-bootcamper-input prompt is missing repeat-request phrase "
            f"'{phrase}' — the Q&A reframe must not remove repeat handling"
        )

    def test_status_trigger_detected_marker_present(self) -> None:
        """The STATUS_TRIGGER_DETECTED output contract must remain present."""
        assert "STATUS_TRIGGER_DETECTED" in self.prompt, (
            "review-bootcamper-input prompt must preserve the "
            "STATUS_TRIGGER_DETECTED status output marker"
        )

    def test_feedback_workflow_reference_present(self) -> None:
        """The feedback-workflow steering reference must remain present."""
        assert "feedback-workflow.md" in self.prompt, (
            "review-bootcamper-input prompt must preserve the feedback-workflow.md "
            "reference for the feedback path"
        )


# ---------------------------------------------------------------------------
# TestReviewInputQaCaptureDemoted
# ---------------------------------------------------------------------------


class TestReviewInputQaCaptureDemoted:
    """review-bootcamper-input's answer logging now reads as a backstop.

    **Validates: Requirements 2.1**
    """

    @pytest.fixture(autouse=True)
    def _load_prompt(self) -> None:
        self.prompt = _hook_prompt(_REVIEW_INPUT_HOOK)

    def test_answer_capture_section_present(self) -> None:
        """The ANSWER CAPTURE section must still exist (as a backstop)."""
        assert "ANSWER CAPTURE" in self.prompt, (
            "review-bootcamper-input prompt must retain an 'ANSWER CAPTURE' section"
        )

    @pytest.mark.parametrize("marker", _DEMOTION_MARKERS)
    def test_demotion_language_present(self, marker: str) -> None:
        """The reframed section must contain each demotion marker."""
        assert marker in self.prompt, (
            f"review-bootcamper-input ANSWER CAPTURE section is missing demotion "
            f"marker '{marker}' — the logging step must read as a redundant, "
            "best-effort backstop, not the primary durability path"
        )

    def test_durability_guaranteed_by_command_hook(self) -> None:
        """The section must credit the command-backed hook with the guarantee."""
        assert "GUARANTEED" in self.prompt, (
            "review-bootcamper-input ANSWER CAPTURE section must state durable "
            "answer capture is GUARANTEED"
        )
        assert "command-backed hook" in self.prompt, (
            "review-bootcamper-input ANSWER CAPTURE section must credit the "
            "command-backed hook with the durability guarantee"
        )

    def test_logging_is_optional_may_record(self) -> None:
        """The agent step must be phrased as optional ('you MAY redundantly record')."""
        assert "you MAY redundantly record it" in self.prompt, (
            "review-bootcamper-input ANSWER CAPTURE section must phrase recording "
            "the answer as optional ('you MAY redundantly record it'), not "
            "mandatory"
        )

    def test_references_record_answer_helper(self) -> None:
        """The backstop still references the record-answer helper invocation."""
        assert "log_qa_event.py record-answer" in self.prompt, (
            "review-bootcamper-input ANSWER CAPTURE section must still reference "
            "the log_qa_event.py record-answer backstop invocation"
        )
