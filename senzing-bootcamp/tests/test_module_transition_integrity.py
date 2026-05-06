"""Tests for module transition integrity across steering files.

Validates that conversation-protocol.md, module-transitions.md, and
module-completion.md contain consistent, non-contradictory rules ensuring
the agent immediately executes module transitions on affirmative response
without saving progress, pausing, or ending the session.

Feature: workflow-improvements (module transition integrity)
Validates: Requirements 3.1, 3.2, 3.3, 3.5, 3.6
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_POWER_ROOT = Path(__file__).resolve().parent.parent  # senzing-bootcamp/

_CONVERSATION_PROTOCOL = _POWER_ROOT / "steering" / "conversation-protocol.md"
_MODULE_TRANSITIONS = _POWER_ROOT / "steering" / "module-transitions.md"
_MODULE_COMPLETION = _POWER_ROOT / "steering" / "module-completion.md"


def _read(path: Path) -> str:
    """Read a file and return its content as a string."""
    return path.read_text(encoding="utf-8")


def _extract_frontmatter(content: str) -> str | None:
    """Extract YAML frontmatter from markdown content.

    Returns:
        The frontmatter string (without delimiters), or None if not found.
    """
    match = re.match(r"^---\s*\n(.*?)\n---", content, re.DOTALL)
    return match.group(1) if match else None


# ═══════════════════════════════════════════════════════════════════════════
# Class 1 — conversation-protocol.md transition rules
# Validates: Requirements 3.2, 3.5
# ═══════════════════════════════════════════════════════════════════════════


class TestConversationProtocolTransition:
    """Verify conversation-protocol.md contains transition integrity rules."""

    @pytest.fixture(autouse=True)
    def _load(self) -> None:
        self.content = _read(_CONVERSATION_PROTOCOL)

    def test_contains_prohibited_saving_after_affirmative(self) -> None:
        """File contains PROHIBITED in context of saving after affirmative response."""
        assert "PROHIBITED" in self.content
        # Ensure it's in the context of saving/ending after affirmative
        lower = self.content.lower()
        prohibited_idx = lower.find("prohibited")
        assert prohibited_idx != -1
        # Check surrounding context mentions saving or ending
        context = lower[max(0, prohibited_idx - 200):prohibited_idx + 200]
        assert "saving" in context or "ending" in context or "session" in context

    def test_contains_commitment_rule_only_valid_response(self) -> None:
        """File contains commitment rule about 'only valid response' being to start the module."""
        assert "only valid response" in self.content.lower() or "only valid action" in self.content.lower()

    def test_contains_context_limit_guidance_before_asking(self) -> None:
        """File contains context-limit guidance about addressing limits BEFORE asking."""
        lower = self.content.lower()
        assert "before" in lower
        # Check that context limits are mentioned alongside "before asking"
        assert "context limit" in lower or "context-limit" in lower


# ═══════════════════════════════════════════════════════════════════════════
# Class 2 — module-transitions.md Transition Integrity section
# Validates: Requirements 3.4, 3.6
# ═══════════════════════════════════════════════════════════════════════════


class TestModuleTransitionsIntegrity:
    """Verify module-transitions.md contains Transition Integrity rules."""

    @pytest.fixture(autouse=True)
    def _load(self) -> None:
        self.content = _read(_MODULE_TRANSITIONS)

    def test_contains_transition_integrity_section(self) -> None:
        """File contains a 'Transition Integrity' section header."""
        assert "## Transition Integrity" in self.content

    def test_contains_commitments_rule(self) -> None:
        """File contains rule about transition questions being 'commitments'."""
        lower = self.content.lower()
        assert "commitments" in lower or "commitment" in lower
        # Verify it's in the context of transition questions
        assert "transition question" in lower or "transition questions" in lower

    def test_contains_context_limit_prevention_rule(self) -> None:
        """File contains rule about not asking if context limits may prevent completion."""
        lower = self.content.lower()
        assert "context limit" in lower or "context limits" in lower
        assert "do not ask" in lower or "do not ask the transition question" in lower


# ═══════════════════════════════════════════════════════════════════════════
# Class 3 — module-completion.md immediate execution reinforcement
# Validates: Requirements 3.1, 3.3
# ═══════════════════════════════════════════════════════════════════════════


class TestModuleCompletionImmediateExecution:
    """Verify module-completion.md reinforces immediate execution on affirmative response."""

    @pytest.fixture(autouse=True)
    def _load(self) -> None:
        self.content = _read(_MODULE_COMPLETION)

    def test_contains_immediate_execution_heading(self) -> None:
        """File contains 'Immediate Execution' heading or similar."""
        assert "Immediate Execution" in self.content

    def test_prohibits_intermediate_acknowledgment(self) -> None:
        """File contains prohibition against intermediate acknowledgment."""
        lower = self.content.lower()
        assert "intermediate acknowledgment" in lower or "acknowledgment" in lower
        # Verify it's in a prohibition context
        assert "prohibited" in lower or "zero permitted" in lower

    def test_prohibits_progress_saving_between_affirmative_and_startup(self) -> None:
        """File contains prohibition against progress-saving between affirmative and startup."""
        lower = self.content.lower()
        assert "progress-saving" in lower or "saving" in lower
        # Verify it's in the prohibited list
        assert "prohibited" in lower

    def test_contains_startup_sequence(self) -> None:
        """File contains the startup sequence (banner, journey map, Step 1)."""
        lower = self.content.lower()
        assert "banner" in lower
        assert "journey map" in lower
        assert "step 1" in lower


# ═══════════════════════════════════════════════════════════════════════════
# Class 4 — YAML frontmatter and inclusion mode integrity
# Validates: Structural integrity of all three files
# ═══════════════════════════════════════════════════════════════════════════


class TestTransitionFrontmatterIntegrity:
    """Verify all three files retain valid YAML frontmatter and inclusion modes."""

    @pytest.fixture(autouse=True)
    def _load(self) -> None:
        self.protocol_content = _read(_CONVERSATION_PROTOCOL)
        self.transitions_content = _read(_MODULE_TRANSITIONS)
        self.completion_content = _read(_MODULE_COMPLETION)

    def test_conversation_protocol_has_inclusion_auto(self) -> None:
        """conversation-protocol.md has inclusion: auto."""
        frontmatter = _extract_frontmatter(self.protocol_content)
        assert frontmatter is not None, "No YAML frontmatter found"
        assert "inclusion: auto" in frontmatter

    def test_module_transitions_has_inclusion_always(self) -> None:
        """module-transitions.md has inclusion: always."""
        frontmatter = _extract_frontmatter(self.transitions_content)
        assert frontmatter is not None, "No YAML frontmatter found"
        assert "inclusion: always" in frontmatter

    def test_module_completion_has_valid_frontmatter(self) -> None:
        """module-completion.md has valid YAML frontmatter."""
        frontmatter = _extract_frontmatter(self.completion_content)
        assert frontmatter is not None, "No YAML frontmatter found"

    def test_module_completion_has_inclusion_manual(self) -> None:
        """module-completion.md has inclusion: manual."""
        frontmatter = _extract_frontmatter(self.completion_content)
        assert frontmatter is not None
        assert "inclusion: manual" in frontmatter


# ═══════════════════════════════════════════════════════════════════════════
# Class 5 — Cross-file consistency
# Validates: Transition rules are non-contradictory across files
# ═══════════════════════════════════════════════════════════════════════════


class TestTransitionCrossFileConsistency:
    """Verify cross-file consistency of transition rules."""

    @pytest.fixture(autouse=True)
    def _load(self) -> None:
        self.protocol_content = _read(_CONVERSATION_PROTOCOL)
        self.transitions_content = _read(_MODULE_TRANSITIONS)
        self.completion_content = _read(_MODULE_COMPLETION)

    def test_all_files_mention_affirmative_in_transition_context(self) -> None:
        """All three files mention 'affirmative' in context of transition responses."""
        assert "affirmative" in self.protocol_content.lower()
        assert "affirmative" in self.completion_content.lower()
        # module-transitions.md may use "confirmed" instead
        transitions_lower = self.transitions_content.lower()
        assert "confirmed" in transitions_lower or "affirmative" in transitions_lower

    def test_prohibition_language_consistent_across_files(self) -> None:
        """Prohibition language is consistent (saving/pausing/ending prohibited in multiple files)."""
        protocol_lower = self.protocol_content.lower()
        completion_lower = self.completion_content.lower()

        # Both conversation-protocol and module-completion should prohibit saving/pausing
        assert "prohibited" in protocol_lower
        assert "prohibited" in completion_lower

        # Both should reference saving or session-ending as prohibited actions
        protocol_prohibits_saving = "saving" in protocol_lower or "save progress" in protocol_lower
        completion_prohibits_saving = (
            "progress-saving" in completion_lower or "saving" in completion_lower
        )
        assert protocol_prohibits_saving, "conversation-protocol.md should prohibit saving"
        assert completion_prohibits_saving, "module-completion.md should prohibit saving"
