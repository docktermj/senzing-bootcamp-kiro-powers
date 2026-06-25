"""Tests for answer-processing priority directives in steering files.

Validates that the steering files contain the required answer-processing
priority content as specified in the design document.

Requirements validated: 1.1, 1.2, 1.3, 2.1, 2.2, 2.3, 5.1, 5.2
"""

from __future__ import annotations

from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Paths to steering files under test
# ---------------------------------------------------------------------------

_STEERING_DIR: Path = (
    Path(__file__).resolve().parent.parent
    / "senzing-bootcamp"
    / "steering"
)

_AGENT_INSTRUCTIONS: Path = _STEERING_DIR / "agent-instructions.md"
_CONVERSATION_PROTOCOL: Path = _STEERING_DIR / "conversation-protocol.md"


# ---------------------------------------------------------------------------
# TestAgentInstructionsPriority
# ---------------------------------------------------------------------------


class TestAgentInstructionsPriority:
    """Validate answer-processing priority directive in agent-instructions.md.

    **Validates: Requirements 1.1, 1.2, 1.3**
    """

    @pytest.fixture(autouse=True)
    def _load_content(self) -> None:
        """Load agent-instructions.md content for all tests in this class."""
        assert _AGENT_INSTRUCTIONS.exists(), (
            f"Steering file not found: {_AGENT_INSTRUCTIONS}"
        )
        self.content = _AGENT_INSTRUCTIONS.read_text(encoding="utf-8")

    def test_contains_absolute_precedence_directive(self) -> None:
        """Agent instructions must state absolute precedence for answer processing.

        Validates Requirement 1.1: processing a pending answer takes absolute
        precedence over all other agent actions.
        """
        assert "absolute precedence" in self.content, (
            "agent-instructions.md must contain 'absolute precedence' directive "
            "about processing pending answers"
        )

    def test_contains_delete_and_process_instruction(self) -> None:
        """Agent instructions must contain delete-and-process rule.

        Validates Requirement 1.2: when .question_pending exists and bootcamper
        responded, delete the file and process the answer first.
        """
        content_lower = self.content.lower()
        assert "delete" in content_lower and ".question_pending" in self.content, (
            "agent-instructions.md must mention deleting .question_pending "
            "and processing the answer first"
        )
        assert "first action" in content_lower or "process the answer" in content_lower, (
            "agent-instructions.md must instruct processing the answer as the "
            "first action of the turn"
        )

    def test_contains_protocol_violation_statement(self) -> None:
        """Agent instructions must state minimal output is a mandatory gate violation.

        Validates Requirement 1.3: minimal output after a pending answer equals
        a ⛔ mandatory gate violation.
        """
        assert "⛔" in self.content or "mandatory gate violation" in self.content, (
            "agent-instructions.md must mention ⛔ mandatory gate violation "
            "for minimal output after a pending answer"
        )
        assert "protocol violation" in self.content.lower(), (
            "agent-instructions.md must contain 'protocol violation' statement"
        )


# ---------------------------------------------------------------------------
# TestConversationProtocolPriority
# ---------------------------------------------------------------------------


class TestConversationProtocolPriority:
    """Validate answer-processing priority section in conversation-protocol.md.

    **Validates: Requirements 2.1, 2.2, 2.3**
    """

    @pytest.fixture(autouse=True)
    def _load_content(self) -> None:
        """Load conversation-protocol.md content for all tests in this class."""
        assert _CONVERSATION_PROTOCOL.exists(), (
            f"Steering file not found: {_CONVERSATION_PROTOCOL}"
        )
        self.content = _CONVERSATION_PROTOCOL.read_text(encoding="utf-8")

    def test_contains_answer_processing_priority_heading(self) -> None:
        """Conversation protocol must have an 'Answer Processing Priority' section.

        Validates Requirement 2.1: the section heading must exist.
        """
        assert "## Answer Processing Priority" in self.content, (
            "conversation-protocol.md must contain '## Answer Processing Priority' "
            "section heading"
        )

    def test_contains_highest_priority_declaration(self) -> None:
        """Conversation protocol must declare answer processing as highest priority.

        Validates Requirement 2.1: highest-priority action declaration.
        """
        assert "highest-priority action" in self.content, (
            "conversation-protocol.md must contain 'highest-priority action' "
            "declaration for answer processing"
        )

    def test_contains_substantive_output_requirement(self) -> None:
        """Conversation protocol must require substantive output for answers.

        Validates Requirement 2.2: agent SHALL produce substantive output that
        acknowledges and acts upon the answer.
        """
        content_lower = self.content.lower()
        assert "substantive output" in content_lower, (
            "conversation-protocol.md must contain 'substantive output' requirement "
            "when processing a pending answer"
        )

    def test_contains_treat_as_answer_rule(self) -> None:
        """Conversation protocol must contain the treat-as-answer rule.

        Validates Requirement 2.3: if .question_pending exists, treat any
        bootcamper message as an answer regardless of content.
        """
        assert "treat" in self.content.lower() and "answer" in self.content.lower(), (
            "conversation-protocol.md must contain treat-as-answer rule"
        )
        assert ".question_pending" in self.content, (
            "conversation-protocol.md must reference .question_pending in the "
            "treat-as-answer rule"
        )


# ---------------------------------------------------------------------------
# TestQuestionPendingSchema
# ---------------------------------------------------------------------------


class TestQuestionPendingSchema:
    """Validate .question_pending schema documentation in conversation-protocol.md.

    **Validates: Requirements 5.1, 5.2**
    """

    @pytest.fixture(autouse=True)
    def _load_content(self) -> None:
        """Load conversation-protocol.md content for all tests in this class."""
        assert _CONVERSATION_PROTOCOL.exists(), (
            f"Steering file not found: {_CONVERSATION_PROTOCOL}"
        )
        self.content = _CONVERSATION_PROTOCOL.read_text(encoding="utf-8")

    def test_documents_structured_question_pending_format(self) -> None:
        """Protocol must document the structured .question_pending file format.

        Validates Requirement 5.1: the file includes a type field on the first line.
        """
        assert ".question_pending" in self.content, (
            "conversation-protocol.md must document the .question_pending format"
        )
        # Must mention the structured format with type on first line
        content_lower = self.content.lower()
        assert "type" in content_lower and "first line" in content_lower, (
            "conversation-protocol.md must specify type on the first line of "
            ".question_pending"
        )

    def test_documents_valid_question_types(self) -> None:
        """Protocol must list the valid question types.

        Validates Requirement 5.1: valid types are track_selection,
        module_transition, step_question, confirmation, choice.
        """
        valid_types = [
            "track_selection",
            "module_transition",
            "step_question",
            "confirmation",
            "choice",
        ]
        for qtype in valid_types:
            assert qtype in self.content, (
                f"conversation-protocol.md must mention question type '{qtype}'"
            )

    def test_documents_question_text_on_subsequent_lines(self) -> None:
        """Protocol must specify question text goes on subsequent lines.

        Validates Requirement 5.2: full question text on subsequent lines
        after the type field.
        """
        content_lower = self.content.lower()
        assert "subsequent line" in content_lower or "lines 2" in content_lower, (
            "conversation-protocol.md must specify question text on subsequent "
            "lines after the type"
        )
