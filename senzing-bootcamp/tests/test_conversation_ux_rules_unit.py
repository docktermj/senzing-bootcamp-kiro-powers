"""Unit tests for conversation UX rules structural requirements.

Verifies that specific structural content exists in the correct steering files
as required by the conversation-ux-rules spec. These are example-based assertions
that complement the property-based tests.

Feature: conversation-ux-rules
"""

from __future__ import annotations

import re
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

_STEERING_DIR: Path = Path(__file__).resolve().parent.parent / "steering"
_CONVERSATION_PROTOCOL: Path = _STEERING_DIR / "conversation-protocol.md"
_SESSION_RESUME: Path = _STEERING_DIR / "session-resume.md"
_AGENT_INSTRUCTIONS: Path = _STEERING_DIR / "agent-instructions.md"
_FEEDBACK_WORKFLOW: Path = _STEERING_DIR / "feedback-workflow.md"


class TestConversationUxRulesStructural:
    """Unit tests for structural requirements of conversation UX rules.

    Each test verifies a specific acceptance criterion by reading the relevant
    steering file and asserting the required content is present.
    """

    def test_conversation_protocol_contains_rule_priority_section(self) -> None:
        """Verify conversation-protocol.md contains 'Rule Priority' section.

        Validates: Requirement 8.2
        """
        content = _CONVERSATION_PROTOCOL.read_text(encoding="utf-8")
        assert re.search(r"^##\s+Rule Priority", content, re.MULTILINE), (
            "conversation-protocol.md must contain a '## Rule Priority' section"
        )

    def test_conversation_protocol_states_question_pending_mandatory(self) -> None:
        """Verify conversation-protocol.md states question_pending is mandatory.

        Validates: Requirement 8.4
        """
        content = _CONVERSATION_PROTOCOL.read_text(encoding="utf-8")
        assert "mandatory" in content.lower(), (
            "conversation-protocol.md must state question_pending is mandatory"
        )
        assert "question_pending" in content, (
            "conversation-protocol.md must reference question_pending file"
        )
        # Verify it explicitly says "not optional"
        assert "not optional" in content.lower(), (
            "conversation-protocol.md must state question_pending is "
            "'not optional'"
        )

    def test_session_resume_references_conversation_protocol(self) -> None:
        """Verify session-resume.md references conversation-protocol.md.

        Validates: Requirement 6.3
        """
        content = _SESSION_RESUME.read_text(encoding="utf-8")
        assert "conversation-protocol.md" in content, (
            "session-resume.md must reference conversation-protocol.md "
            "as authoritative source"
        )

    def test_agent_instructions_communication_conjunction_prohibition(
        self,
    ) -> None:
        """Verify agent-instructions.md Communication section prohibits conjunctions.

        Validates: Requirement 1.5
        """
        content = _AGENT_INSTRUCTIONS.read_text(encoding="utf-8")
        lines = content.splitlines()

        # Find the Communication section
        comm_start: int | None = None
        comm_end: int | None = None
        for idx, line in enumerate(lines):
            if re.match(r"^##\s+Communication", line):
                comm_start = idx
            elif comm_start is not None and re.match(r"^##\s+", line):
                comm_end = idx
                break

        assert comm_start is not None, (
            "agent-instructions.md must have a '## Communication' section"
        )

        if comm_end is None:
            comm_end = len(lines)

        section_content = "\n".join(lines[comm_start:comm_end])

        # Verify conjunction prohibition is present
        assert "and, or, also, but first" in section_content.lower(), (
            "Communication section must prohibit combining questions "
            "with conjunctions (and, or, also, but first)"
        )

    def test_feedback_workflow_has_conversation_rules_preamble(self) -> None:
        """Verify feedback-workflow.md has 'Conversation Rules' preamble section.

        Validates: Requirement 7.1
        """
        content = _FEEDBACK_WORKFLOW.read_text(encoding="utf-8")
        assert re.search(
            r"^##\s+Conversation Rules", content, re.MULTILINE
        ), (
            "feedback-workflow.md must contain a "
            "'## Conversation Rules' preamble section"
        )

    def test_session_resume_self_answering_prohibition_before_step_3(
        self,
    ) -> None:
        """Verify session-resume.md has self-answering prohibition before Step 3.

        Validates: Requirement 5.2
        """
        content = _SESSION_RESUME.read_text(encoding="utf-8")
        lines = content.splitlines()

        # Find the self-answering prohibition text and Step 3
        prohibition_line: int | None = None
        step_3_line: int | None = None

        for idx, line in enumerate(lines):
            if "self-answering" in line.lower() or "self_answering" in line.lower():
                if prohibition_line is None:
                    prohibition_line = idx
            if re.match(r"^##\s+Step 3", line):
                step_3_line = idx

        assert prohibition_line is not None, (
            "session-resume.md must contain self-answering prohibition text"
        )
        assert step_3_line is not None, (
            "session-resume.md must contain a 'Step 3' heading"
        )
        assert prohibition_line < step_3_line, (
            f"Self-answering prohibition (line {prohibition_line + 1}) "
            f"must appear before Step 3 (line {step_3_line + 1})"
        )
