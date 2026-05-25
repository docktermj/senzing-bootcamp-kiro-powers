"""Tests for onboarding UX improvements to steering files.

Validates:
- Requirements 1.1–1.4: Hook files note placement and content in
  onboarding-flow.md (Step 4 Overview_Bullets)
- Requirements 2.1–2.6: Exploration gate placement and content in
  entity-resolution-intro.md

Tests parse the steering markdown files to verify content placement
and structure.
"""

from __future__ import annotations

import re
from pathlib import Path

# ---------------------------------------------------------------------------
# Module-level path constants
# ---------------------------------------------------------------------------
#: Repository root — parent of the ``senzing-bootcamp/`` power directory.
REPO_ROOT: Path = Path(__file__).resolve().parent.parent.parent

#: The onboarding flow steering file containing the hook files note.
ONBOARDING_FLOW: Path = REPO_ROOT / "senzing-bootcamp" / "steering" / "onboarding-flow.md"

#: The entity resolution intro steering file containing the exploration gate.
ENTITY_RESOLUTION_INTRO: Path = (
    REPO_ROOT / "senzing-bootcamp" / "steering" / "entity-resolution-intro.md"
)


# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------

def _read_onboarding_flow() -> str:
    """Read and return the full text of onboarding-flow.md."""
    return ONBOARDING_FLOW.read_text(encoding="utf-8")


def _extract_between_unfamiliar_and_4a(text: str) -> str:
    """Extract text between the 'unfamiliar terms' bullet and '### 4a' heading.

    Returns the content strictly after the unfamiliar terms bullet line
    and before the ### 4a heading line.
    """
    lines = text.splitlines(keepends=True)
    unfamiliar_idx: int | None = None
    heading_4a_idx: int | None = None

    for i, line in enumerate(lines):
        if "unfamiliar terms" in line.lower():
            unfamiliar_idx = i
        if re.match(r"^###\s+4a\b", line):
            heading_4a_idx = i
            break

    assert unfamiliar_idx is not None, (
        "Could not find 'unfamiliar terms' bullet in onboarding-flow.md"
    )
    assert heading_4a_idx is not None, (
        "Could not find '### 4a' heading in onboarding-flow.md"
    )
    assert unfamiliar_idx < heading_4a_idx, (
        "'unfamiliar terms' bullet must appear before '### 4a' heading"
    )

    return "".join(lines[unfamiliar_idx + 1 : heading_4a_idx])


# ---------------------------------------------------------------------------
# Tests: Hook Files Note (Requirement 1)
# ---------------------------------------------------------------------------

class TestHookFilesNotePlacement:
    """Tests for hook files note placement in onboarding-flow.md.

    Validates Requirements 1.1, 1.2, 1.3, 1.4.
    """

    def test_hook_files_note_after_unfamiliar_terms_and_before_4a(self) -> None:
        """Validates: Requirements 1.1

        The hook files note must appear after the 'unfamiliar terms' bullet
        and before the '### 4a' heading.
        """
        text = _read_onboarding_flow()
        between = _extract_between_unfamiliar_and_4a(text)

        assert ".kiro.hook" in between, (
            "Expected hook files note (mentioning '.kiro.hook') to appear "
            "between the 'unfamiliar terms' bullet and '### 4a' heading in "
            f"{ONBOARDING_FLOW.relative_to(REPO_ROOT)}"
        )

    def test_hook_files_note_mentions_automated_quality_checks(self) -> None:
        """Validates: Requirements 1.2

        The hook files note must inform the bootcamper that hook files are
        automated quality checks.
        """
        text = _read_onboarding_flow()
        between = _extract_between_unfamiliar_and_4a(text)
        lowered = between.lower()

        assert "automated quality checks" in lowered, (
            "Expected hook files note to mention 'automated quality checks' "
            f"in {ONBOARDING_FLOW.relative_to(REPO_ROOT)}"
        )

    def test_hook_files_note_mentions_safe_to_close(self) -> None:
        """Validates: Requirements 1.3

        The hook files note must state that hook files can be safely closed.
        """
        text = _read_onboarding_flow()
        between = _extract_between_unfamiliar_and_4a(text)
        lowered = between.lower()

        assert "safely close" in lowered, (
            "Expected hook files note to mention 'safely close' "
            f"in {ONBOARDING_FLOW.relative_to(REPO_ROOT)}"
        )

    def test_hook_files_note_mentions_must_not_delete(self) -> None:
        """Validates: Requirements 1.3

        The hook files note must instruct the bootcamper not to delete
        hook files.
        """
        text = _read_onboarding_flow()
        between = _extract_between_unfamiliar_and_4a(text)
        lowered = between.lower()

        assert "not delete" in lowered or "do not delete" in lowered, (
            "Expected hook files note to mention 'not delete' or "
            f"'do not delete' in {ONBOARDING_FLOW.relative_to(REPO_ROOT)}"
        )

    def test_no_gate_markers_between_hook_note_and_4a(self) -> None:
        """Validates: Requirements 1.4

        No ⛔ or 🛑 markers should exist between the hook files note
        and '### 4a', ensuring the flow continues seamlessly.
        """
        text = _read_onboarding_flow()
        between = _extract_between_unfamiliar_and_4a(text)

        assert "⛔" not in between, (
            "Found ⛔ marker between hook files note and '### 4a' in "
            f"{ONBOARDING_FLOW.relative_to(REPO_ROOT)}. "
            "The flow must continue seamlessly to section 4a."
        )
        assert "🛑" not in between, (
            "Found 🛑 marker between hook files note and '### 4a' in "
            f"{ONBOARDING_FLOW.relative_to(REPO_ROOT)}. "
            "The flow must continue seamlessly to section 4a."
        )


# ---------------------------------------------------------------------------
# Tests: Exploration Gate (Requirement 2)
# ---------------------------------------------------------------------------


class TestExplorationGatePlacement:
    """Tests for exploration gate placement in entity-resolution-intro.md.

    Validates Requirements 2.1: The gate must appear after the
    "What entity resolution produces" section and before the Sources comment.
    """

    def test_gate_exists_after_what_er_produces_section(self) -> None:
        """Validates: Requirements 2.1

        The ⛔ gate must appear after the "What entity resolution produces"
        section content and before the Sources comment/heading.
        """
        content = ENTITY_RESOLUTION_INTRO.read_text(encoding="utf-8")

        # Find the "What entity resolution produces" heading
        produces_match = re.search(
            r"^## What entity resolution produces\s*$", content, re.MULTILINE
        )
        assert produces_match is not None, (
            "Expected '## What entity resolution produces' heading in "
            f"{ENTITY_RESOLUTION_INTRO.relative_to(REPO_ROOT)}"
        )

        # Find the Sources section (heading or comment)
        sources_match = re.search(r"^## Sources\s*$", content, re.MULTILINE)
        assert sources_match is not None, (
            "Expected '## Sources' heading in "
            f"{ENTITY_RESOLUTION_INTRO.relative_to(REPO_ROOT)}"
        )

        # Find the ⛔ MANDATORY GATE marker
        gate_match = re.search(r"⛔ \*\*MANDATORY GATE\*\*", content)
        assert gate_match is not None, (
            "Expected '⛔ **MANDATORY GATE**' marker in "
            f"{ENTITY_RESOLUTION_INTRO.relative_to(REPO_ROOT)}"
        )

        # Verify ordering: produces section < gate < sources
        assert produces_match.start() < gate_match.start() < sources_match.start(), (
            "Expected the ⛔ gate to appear after '## What entity resolution "
            "produces' and before '## Sources'. Positions: "
            f"produces={produces_match.start()}, gate={gate_match.start()}, "
            f"sources={sources_match.start()}"
        )


class TestExplorationGateContent:
    """Tests for exploration gate content in entity-resolution-intro.md.

    Validates Requirements 2.2, 2.3, 2.4, 2.5, 2.6.
    """

    def test_gate_contains_all_three_example_questions(self) -> None:
        """Validates: Requirements 2.2

        The gate must present three specific example questions.
        """
        content = ENTITY_RESOLUTION_INTRO.read_text(encoding="utf-8")

        expected_questions = [
            "How does Senzing match records without rules?",
            "What's the difference between matching and relating?",
            "What kinds of data does entity resolution work with?",
        ]

        for question in expected_questions:
            assert question in content, (
                f"Expected example question {question!r} in "
                f"{ENTITY_RESOLUTION_INTRO.relative_to(REPO_ROOT)}"
            )

    def test_gate_contains_agent_instruction_with_search_docs(self) -> None:
        """Validates: Requirements 2.4

        The gate must contain an HTML comment with AGENT INSTRUCTION
        that mentions search_docs for answering follow-up questions.
        """
        content = ENTITY_RESOLUTION_INTRO.read_text(encoding="utf-8")

        # Extract the gate section (between "## Explore Further" and "## Sources")
        explore_match = re.search(r"^## Explore Further\s*$", content, re.MULTILINE)
        sources_match = re.search(r"^## Sources\s*$", content, re.MULTILINE)
        assert explore_match is not None, (
            "Expected '## Explore Further' heading in "
            f"{ENTITY_RESOLUTION_INTRO.relative_to(REPO_ROOT)}"
        )
        assert sources_match is not None, (
            "Expected '## Sources' heading in "
            f"{ENTITY_RESOLUTION_INTRO.relative_to(REPO_ROOT)}"
        )

        gate_section = content[explore_match.start():sources_match.start()]

        # Verify HTML comment with AGENT INSTRUCTION exists in the gate section
        agent_comment_match = re.search(
            r"<!--.*?AGENT INSTRUCTION.*?-->", gate_section, re.DOTALL
        )
        assert agent_comment_match is not None, (
            "Expected an HTML comment containing 'AGENT INSTRUCTION' in the "
            f"Explore Further section of {ENTITY_RESOLUTION_INTRO.relative_to(REPO_ROOT)}"
        )

        # Verify search_docs is mentioned in the agent instruction
        agent_comment = agent_comment_match.group(0)
        assert "search_docs" in agent_comment, (
            "Expected 'search_docs' to be mentioned in the AGENT INSTRUCTION "
            f"comment within the Explore Further section of "
            f"{ENTITY_RESOLUTION_INTRO.relative_to(REPO_ROOT)}"
        )

    def test_gate_contains_stop_instruction(self) -> None:
        """Validates: Requirements 2.3

        The gate must contain the 🛑 **STOP** instruction telling the
        agent to end its response and wait for bootcamper input.
        """
        content = ENTITY_RESOLUTION_INTRO.read_text(encoding="utf-8")

        # Find the gate section
        explore_match = re.search(r"^## Explore Further\s*$", content, re.MULTILINE)
        sources_match = re.search(r"^## Sources\s*$", content, re.MULTILINE)
        assert explore_match is not None
        assert sources_match is not None

        gate_section = content[explore_match.start():sources_match.start()]

        # Verify 🛑 STOP instruction exists
        assert "🛑" in gate_section, (
            "Expected '🛑' stop emoji in the Explore Further section of "
            f"{ENTITY_RESOLUTION_INTRO.relative_to(REPO_ROOT)}"
        )
        assert re.search(r"🛑 \*\*STOP", gate_section), (
            "Expected '🛑 **STOP' marker in the Explore Further section of "
            f"{ENTITY_RESOLUTION_INTRO.relative_to(REPO_ROOT)}"
        )

    def test_agent_instruction_handles_ambiguous_responses(self) -> None:
        """Validates: Requirements 2.6

        The agent instruction must specify that ambiguous responses are
        treated as follow-up questions.
        """
        content = ENTITY_RESOLUTION_INTRO.read_text(encoding="utf-8")

        # Extract the gate section
        explore_match = re.search(r"^## Explore Further\s*$", content, re.MULTILINE)
        sources_match = re.search(r"^## Sources\s*$", content, re.MULTILINE)
        assert explore_match is not None
        assert sources_match is not None

        gate_section = content[explore_match.start():sources_match.start()]

        # Extract the agent instruction comment
        agent_comment_match = re.search(
            r"<!--.*?AGENT INSTRUCTION.*?-->", gate_section, re.DOTALL
        )
        assert agent_comment_match is not None, (
            "Expected AGENT INSTRUCTION comment in the Explore Further section"
        )

        agent_comment = agent_comment_match.group(0).lower()

        # Verify ambiguous response handling is specified
        assert "ambiguous" in agent_comment, (
            "Expected the AGENT INSTRUCTION to mention 'ambiguous' response "
            f"handling in {ENTITY_RESOLUTION_INTRO.relative_to(REPO_ROOT)}"
        )
        assert "follow-up" in agent_comment or "follow up" in agent_comment, (
            "Expected the AGENT INSTRUCTION to specify treating ambiguous "
            "responses as follow-up questions in "
            f"{ENTITY_RESOLUTION_INTRO.relative_to(REPO_ROOT)}"
        )
