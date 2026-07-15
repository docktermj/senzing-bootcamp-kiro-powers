"""Content/hook tests for the Single-Ask Question (Ask-Once) Guarantee.

Asserts that the steering and hook changes made for the
``single-ask-question-guarantee`` spec are present:

- ``conversation-protocol.md`` is the single normative home of the
  "Ask-Once Guarantee" rule (heading + key normative content).
- ``agent-instructions.md`` and ``module-transitions.md`` *reference* the
  guarantee in ``conversation-protocol.md`` rather than restating the full
  normative rule.
- ``ask-bootcamper.json`` prompt contains the ledger-consult instruction
  (consult the Question_Ledger / ``is-answered`` before emitting a step-tied
  closing question).
- ``review-bootcamper-input.json`` prompt lists the Repeat_Request trigger
  phrases.

Requirements validated: 6.2, 6.3
"""

from __future__ import annotations

from pathlib import Path

import pytest

from hook_test_helpers import load_hook

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

_REPO_ROOT: Path = Path(__file__).resolve().parent.parent
_STEERING_DIR: Path = _REPO_ROOT / "senzing-bootcamp" / "steering"

_CONVERSATION_PROTOCOL: Path = _STEERING_DIR / "conversation-protocol.md"
_AGENT_INSTRUCTIONS: Path = _STEERING_DIR / "agent-instructions.md"
_MODULE_TRANSITIONS: Path = _STEERING_DIR / "module-transitions.md"

_ASK_BOOTCAMPER_HOOK: Path = Path("senzing-bootcamp/hooks/ask-bootcamper.json")
_REVIEW_INPUT_HOOK: Path = Path("senzing-bootcamp/hooks/review-bootcamper-input.json")

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# The section heading that owns the single normative rule.
GUARANTEE_HEADING: str = "## The Ask-Once Guarantee"

# A distinctive fragment of the *normative* sentence. It should appear only in
# the single home (conversation-protocol.md) and NOT be restated verbatim in the
# files that merely reference the guarantee.
NORMATIVE_FRAGMENT: str = "asked at most once"

# How referencing files point back to the single home.
REFERENCE_TARGET: str = "conversation-protocol.md"
REFERENCE_POINTER: str = "The Ask-Once Guarantee"

# The Repeat_Request trigger phrases the Review_Input_Hook must recognize
# (design.md → review-bootcamper-input Hook Changes).
REPEAT_REQUEST_PHRASES: list[str] = [
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


def _read(path: Path) -> str:
    """Return the UTF-8 text of a steering file, asserting it exists."""
    assert path.exists(), f"Steering file not found: {path}"
    return path.read_text(encoding="utf-8")


def _hook_prompt(path: Path) -> str:
    """Return the agent-action prompt text from a v1 hook file."""
    assert path.exists(), f"Hook file not found: {path}"
    entry = load_hook(path)
    return entry["action"]["prompt"]


# ---------------------------------------------------------------------------
# TestConversationProtocolAskOnceGuarantee
# ---------------------------------------------------------------------------


class TestConversationProtocolAskOnceGuarantee:
    """The single normative Ask-Once Guarantee lives in conversation-protocol.md.

    **Validates: Requirements 6.2**
    """

    @pytest.fixture(autouse=True)
    def _load_content(self) -> None:
        self.content = _read(_CONVERSATION_PROTOCOL)

    def test_guarantee_heading_present(self) -> None:
        """conversation-protocol.md must contain the Ask-Once Guarantee heading."""
        assert GUARANTEE_HEADING in self.content, (
            f"conversation-protocol.md must contain the '{GUARANTEE_HEADING}' "
            "section heading"
        )

    def test_guarantee_heading_is_single_home(self) -> None:
        """The normative heading must appear exactly once (a single home)."""
        count = self.content.count(GUARANTEE_HEADING)
        assert count == 1, (
            f"Expected exactly one '{GUARANTEE_HEADING}' heading in "
            f"conversation-protocol.md, found {count}"
        )

    def test_contains_ask_at_most_once_rule(self) -> None:
        """The section must state the 'asked at most once' normative rule."""
        assert NORMATIVE_FRAGMENT in self.content, (
            "conversation-protocol.md must state the normative "
            f"'{NORMATIVE_FRAGMENT}' rule"
        )

    def test_contains_repeat_request_exception(self) -> None:
        """The rule must carve out the explicit Repeat_Request exception."""
        assert "Repeat_Request" in self.content, (
            "conversation-protocol.md must reference Repeat_Request as the only "
            "way a question may be re-presented"
        )

    def test_references_ledger_as_source_of_truth(self) -> None:
        """The rule must name the Question_Ledger and Question_Key mechanism."""
        assert "Question_Ledger" in self.content, (
            "conversation-protocol.md must reference the Question_Ledger"
        )
        assert "Question_Key" in self.content, (
            "conversation-protocol.md must reference the stable Question_Key"
        )

    def test_holds_across_compaction_and_resume(self) -> None:
        """The rule must declare durability across compaction and session resume."""
        assert "context compaction and session resume" in self.content, (
            "conversation-protocol.md must state the guarantee holds across "
            "context compaction and session resume"
        )


# ---------------------------------------------------------------------------
# TestReferencingFilesDoNotDuplicate
# ---------------------------------------------------------------------------


class TestReferencingFilesDoNotDuplicate:
    """The other rule files reference — but do not restate — the guarantee.

    ``agent-instructions.md`` and ``module-transitions.md`` must point to the
    normative rule in ``conversation-protocol.md`` rather than duplicating the
    full normative statement.

    **Validates: Requirements 6.2**
    """

    @pytest.fixture(autouse=True)
    def _load_content(self) -> None:
        self.agent_instructions = _read(_AGENT_INSTRUCTIONS)
        self.module_transitions = _read(_MODULE_TRANSITIONS)

    def test_agent_instructions_references_guarantee(self) -> None:
        """agent-instructions.md must reference the guarantee by name."""
        assert "Ask-Once Guarantee" in self.agent_instructions, (
            "agent-instructions.md must reference the Ask-Once Guarantee"
        )

    def test_agent_instructions_points_to_conversation_protocol(self) -> None:
        """agent-instructions.md must point at conversation-protocol.md as home."""
        assert REFERENCE_TARGET in self.agent_instructions, (
            "agent-instructions.md must point to conversation-protocol.md"
        )
        assert REFERENCE_POINTER in self.agent_instructions, (
            "agent-instructions.md must name 'The Ask-Once Guarantee' section"
        )

    def test_agent_instructions_does_not_restate_normative_rule(self) -> None:
        """agent-instructions.md must not restate the full normative sentence."""
        assert NORMATIVE_FRAGMENT not in self.agent_instructions, (
            "agent-instructions.md should REFERENCE the guarantee, not restate "
            f"the normative '{NORMATIVE_FRAGMENT}' rule"
        )

    def test_module_transitions_references_guarantee(self) -> None:
        """module-transitions.md must reference the guarantee by name."""
        assert "Ask-Once Guarantee" in self.module_transitions, (
            "module-transitions.md must reference the Ask-Once Guarantee"
        )

    def test_module_transitions_points_to_conversation_protocol(self) -> None:
        """module-transitions.md must point at conversation-protocol.md as home."""
        assert REFERENCE_TARGET in self.module_transitions, (
            "module-transitions.md must point to conversation-protocol.md"
        )
        assert REFERENCE_POINTER in self.module_transitions, (
            "module-transitions.md must name 'The Ask-Once Guarantee' section"
        )

    def test_module_transitions_does_not_restate_normative_rule(self) -> None:
        """module-transitions.md must not restate the full normative sentence."""
        assert NORMATIVE_FRAGMENT not in self.module_transitions, (
            "module-transitions.md should REFERENCE the guarantee, not restate "
            f"the normative '{NORMATIVE_FRAGMENT}' rule"
        )


# ---------------------------------------------------------------------------
# TestAskBootcamperLedgerConsult
# ---------------------------------------------------------------------------


class TestAskBootcamperLedgerConsult:
    """The ask-bootcamper hook consults the ledger before a step-tied question.

    **Validates: Requirements 6.2**
    """

    @pytest.fixture(autouse=True)
    def _load_prompt(self) -> None:
        self.prompt = _hook_prompt(_ASK_BOOTCAMPER_HOOK)

    def test_prompt_has_ledger_consult_step(self) -> None:
        """The prompt must contain an explicit ledger-consult step."""
        assert "LEDGER CONSULT" in self.prompt, (
            "ask-bootcamper prompt must contain a 'LEDGER CONSULT' step"
        )

    def test_prompt_consults_question_ledger(self) -> None:
        """The consult must reference the Question_Ledger."""
        assert "Question_Ledger" in self.prompt, (
            "ask-bootcamper prompt must instruct consulting the Question_Ledger"
        )

    def test_prompt_uses_is_answered_query(self) -> None:
        """The consult must use the is-answered query before re-asking."""
        assert "is-answered" in self.prompt, (
            "ask-bootcamper prompt must consult 'is-answered' before emitting a "
            "step-tied closing question"
        )

    def test_prompt_is_step_tied_via_question_key(self) -> None:
        """The consult must be scoped to a step's Question_Key."""
        assert "Question_Key" in self.prompt, (
            "ask-bootcamper prompt must scope the consult to a step's Question_Key"
        )

    def test_prompt_ties_to_ask_once_guarantee(self) -> None:
        """The consult must name the Ask-Once Guarantee it enforces."""
        assert "Ask-Once Guarantee" in self.prompt, (
            "ask-bootcamper prompt must reference the Ask-Once Guarantee"
        )


# ---------------------------------------------------------------------------
# TestReviewInputRepeatRequestPhrases
# ---------------------------------------------------------------------------


class TestReviewInputRepeatRequestPhrases:
    """The review-bootcamper-input hook lists the Repeat_Request trigger phrases.

    **Validates: Requirements 6.3**
    """

    @pytest.fixture(autouse=True)
    def _load_prompt(self) -> None:
        self.prompt = _hook_prompt(_REVIEW_INPUT_HOOK)

    def test_prompt_names_repeat_request(self) -> None:
        """The prompt must recognize the Repeat_Request concept."""
        assert "Repeat_Request" in self.prompt, (
            "review-bootcamper-input prompt must name Repeat_Request trigger phrases"
        )

    @pytest.mark.parametrize("phrase", REPEAT_REQUEST_PHRASES)
    def test_prompt_lists_each_repeat_phrase(self, phrase: str) -> None:
        """The prompt must list every Repeat_Request trigger phrase."""
        assert phrase in self.prompt, (
            f"review-bootcamper-input prompt must list the Repeat_Request phrase "
            f"'{phrase}'"
        )

    def test_prompt_repeats_pending_question_verbatim(self) -> None:
        """A repeat must re-present the current Pending_Question verbatim."""
        assert "Pending_Question" in self.prompt, (
            "review-bootcamper-input prompt must re-present the Pending_Question "
            "on a Repeat_Request"
        )

    def test_prompt_creates_no_new_ledger_entry(self) -> None:
        """A repeat must not create a new Question_Ledger entry."""
        assert "do NOT create a new Question_Ledger entry" in self.prompt, (
            "review-bootcamper-input prompt must state that a Repeat_Request "
            "creates no new Question_Ledger entry"
        )
