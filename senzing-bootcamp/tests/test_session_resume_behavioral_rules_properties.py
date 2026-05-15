"""Property-based tests for session-resume behavioral rules.

Feature: session-resume-behavioral-rules
"""

import re
import sys
from pathlib import Path

import yaml
from hypothesis import given, settings, HealthCheck
from hypothesis import strategies as st

# Paths to steering files under test
_STEERING_DIR = Path(__file__).resolve().parent.parent / "steering"
_SESSION_RESUME = _STEERING_DIR / "session-resume.md"
_CONVERSATION_PROTOCOL = _STEERING_DIR / "conversation-protocol.md"
_AGENT_INSTRUCTIONS = _STEERING_DIR / "agent-instructions.md"


# ---------------------------------------------------------------------------
# Hypothesis strategies
# ---------------------------------------------------------------------------


def st_tone_descriptor():
    """Strategy for valid tone descriptor values."""
    return st.sampled_from(["concise", "conversational", "detailed"])


def st_verbosity_preset():
    """Strategy for valid verbosity preset names."""
    return st.sampled_from(["concise", "standard", "detailed", "custom"])


def st_pacing_preference():
    """Strategy for valid pacing preference values."""
    return st.sampled_from(["one_concept_per_turn", "grouped_concepts"])


@st.composite
def st_conversation_style_profile(draw):
    """Strategy that builds a valid conversation style profile dict."""
    return {
        "verbosity_preset": draw(st_verbosity_preset()),
        "question_framing": draw(st.sampled_from(["minimal", "moderate", "full"])),
        "tone": draw(st_tone_descriptor()),
        "pacing": draw(st_pacing_preference()),
    }


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------


def _read_file(path: Path) -> str:
    """Read a file and return its content as a string."""
    return path.read_text(encoding="utf-8")


def _extract_section(content: str, heading: str) -> str:
    """Extract content under a ## heading until the next ## heading."""
    pattern = rf"^(## {re.escape(heading)}.*)$"
    match = re.search(pattern, content, re.MULTILINE)
    if not match:
        return ""
    start = match.start()
    # Find the next ## heading after this one
    next_heading = re.search(r"^## ", content[match.end():], re.MULTILINE)
    if next_heading:
        end = match.end() + next_heading.start()
    else:
        end = len(content)
    return content[start:end]


# ---------------------------------------------------------------------------
# Property tests
# ---------------------------------------------------------------------------


class TestProperty1BehavioralRulesCompleteness:
    """Property 1: Behavioral Rules Reload completeness.

    Verify that session-resume.md Step 2b section contains all five rules
    with enforcement mechanisms.

    Feature: session-resume-behavioral-rules, Property 1: Behavioral Rules Reload completeness

    Validates: Requirements 1.1, 1.3
    """

    def test_all_five_rules_present_with_enforcement(self):
        """Step 2b contains all five core rules with enforcement text."""
        content = _read_file(_SESSION_RESUME)
        section = _extract_section(content, "Step 2b: Behavioral Rules Reload")
        assert section, "Step 2b: Behavioral Rules Reload section not found"

        # Rule 1: One-question-per-turn
        assert "One-question-per-turn" in section or "one-question-per-turn" in section.lower()
        assert "enforcement" in section.lower() or "Enforcement" in section

        # Rule 2: 👉-prefix-required
        assert "👉-prefix-required" in section or "👉" in section

        # Rule 3: STOP markers
        assert "STOP marker" in section or "STOP" in section

        # Rule 4: No self-answering
        assert "self-answering" in section.lower() or "No self-answering" in section

        # Rule 5: No dead-end
        assert "dead-end" in section.lower() or "No dead-end" in section

    def test_enforcement_mechanisms_for_each_rule(self):
        """Each rule has an associated enforcement mechanism description."""
        content = _read_file(_SESSION_RESUME)
        section = _extract_section(content, "Step 2b: Behavioral Rules Reload")

        # Check enforcement text appears for each rule
        enforcement_count = section.lower().count("enforcement")
        assert enforcement_count >= 5, (
            f"Expected at least 5 enforcement mechanism descriptions, found {enforcement_count}"
        )


class TestProperty2DocumentOrdering:
    """Property 2: Document ordering — rules before interaction.

    Verify that in session-resume.md, Step 2b appears AFTER Step 1 and BEFORE Step 3.

    Feature: session-resume-behavioral-rules, Property 2: Document ordering

    Validates: Requirements 1.2, 1.4, 6.1
    """

    def test_step_2b_after_step_1_before_step_3(self):
        """Step 2b appears after Step 1 and before Step 3 in the document."""
        content = _read_file(_SESSION_RESUME)

        step1_match = re.search(r"^## Step 1", content, re.MULTILINE)
        step2b_match = re.search(r"^## Step 2b", content, re.MULTILINE)
        step3_match = re.search(r"^## Step 3", content, re.MULTILINE)

        assert step1_match, "Step 1 heading not found"
        assert step2b_match, "Step 2b heading not found"
        assert step3_match, "Step 3 heading not found"

        assert step1_match.start() < step2b_match.start(), (
            "Step 2b must appear after Step 1"
        )
        assert step2b_match.start() < step3_match.start(), (
            "Step 2b must appear before Step 3"
        )


class TestProperty3SelfAnsweringProhibition:
    """Property 3: Self-Answering Prohibition examples.

    Verify that the Self-Answering Prohibition subsection contains both
    WRONG and CORRECT example patterns.

    Feature: session-resume-behavioral-rules, Property 3: Self-Answering Prohibition

    Validates: Requirements 2.1, 2.2
    """

    def test_wrong_and_correct_examples_present(self):
        """Self-Answering Prohibition contains both WRONG and CORRECT patterns."""
        content = _read_file(_SESSION_RESUME)
        section = _extract_section(content, "Step 2b: Behavioral Rules Reload")

        # Find the Self-Answering Prohibition subsection
        assert "Self-Answering Prohibition" in section, (
            "Self-Answering Prohibition subsection not found in Step 2b"
        )

        # Extract from Self-Answering Prohibition heading onwards within the section
        prohibition_start = section.find("Self-Answering Prohibition")
        prohibition_text = section[prohibition_start:]

        assert "WRONG" in prohibition_text, (
            "WRONG example pattern not found in Self-Answering Prohibition"
        )
        assert "CORRECT" in prohibition_text, (
            "CORRECT example pattern not found in Self-Answering Prohibition"
        )


class TestProperty4QuestionPendingAfterWelcomeBack:
    """Property 4: Question pending after welcome-back.

    Verify that Step 3 contains an instruction to write config/.question_pending
    after the 👉 question.

    Feature: session-resume-behavioral-rules, Property 4: Question pending after welcome-back

    Validates: Requirements 2.3, 6.3
    """

    def test_question_pending_instruction_in_step_3(self):
        """Step 3 contains instruction to write config/.question_pending."""
        content = _read_file(_SESSION_RESUME)
        section = _extract_section(content, "Step 3: Summarize and Confirm")
        assert section, "Step 3: Summarize and Confirm section not found"

        assert ".question_pending" in section, (
            "Instruction to write config/.question_pending not found in Step 3"
        )


class TestProperty5ConversationStyleYAMLRoundTrip:
    """Property 5: Conversation style profile YAML round-trip.

    Use Hypothesis strategies to generate random conversation style profiles,
    serialize them to YAML, deserialize, and verify all fields are preserved.

    Feature: session-resume-behavioral-rules, Property 5: Conversation style profile round-trip

    Validates: Requirements 4.2, 4.4
    """

    @given(profile=st_conversation_style_profile())
    @settings(max_examples=10)
    def test_yaml_round_trip_preserves_all_fields(self, profile):
        """Serializing and deserializing a conversation style profile preserves all fields."""
        data = {"conversation_style": profile}
        yaml_text = yaml.safe_dump(data, default_flow_style=False)
        restored = yaml.safe_load(yaml_text)

        assert restored["conversation_style"]["verbosity_preset"] == profile["verbosity_preset"]
        assert restored["conversation_style"]["question_framing"] == profile["question_framing"]
        assert restored["conversation_style"]["tone"] == profile["tone"]
        assert restored["conversation_style"]["pacing"] == profile["pacing"]


class TestProperty6AuthoritativeReferenceAsSummary:
    """Property 6: Authoritative reference as summary.

    Verify that Step 2b references conversation-protocol.md and that the
    Step 2b section is shorter than the full conversation-protocol.md file.

    Feature: session-resume-behavioral-rules, Property 6: Authoritative reference as summary

    Validates: Requirements 5.1, 5.4
    """

    def test_references_conversation_protocol(self):
        """Step 2b references conversation-protocol.md."""
        content = _read_file(_SESSION_RESUME)
        section = _extract_section(content, "Step 2b: Behavioral Rules Reload")
        assert "conversation-protocol.md" in section, (
            "Step 2b does not reference conversation-protocol.md"
        )

    def test_step_2b_shorter_than_conversation_protocol(self):
        """Step 2b is shorter (fewer characters) than the full conversation-protocol.md."""
        resume_content = _read_file(_SESSION_RESUME)
        section = _extract_section(resume_content, "Step 2b: Behavioral Rules Reload")
        protocol_content = _read_file(_CONVERSATION_PROTOCOL)

        assert len(section) < len(protocol_content), (
            f"Step 2b ({len(section)} chars) should be shorter than "
            f"conversation-protocol.md ({len(protocol_content)} chars)"
        )


class TestProperty7SingleWelcomeBackQuestion:
    """Property 7: Single welcome-back question.

    Verify that Step 3 contains exactly one line with 👉 and that no
    substantive content appears after the 👉 question line before the
    next ## Step heading.

    Feature: session-resume-behavioral-rules, Property 7: Single welcome-back question

    Validates: Requirements 6.2, 6.4
    """

    def test_exactly_one_pointing_question(self):
        """Step 3 contains exactly one line with 👉."""
        content = _read_file(_SESSION_RESUME)
        section = _extract_section(content, "Step 3: Summarize and Confirm")
        assert section, "Step 3: Summarize and Confirm section not found"

        lines_with_pointer = [
            line for line in section.splitlines()
            if "👉" in line
        ]
        assert len(lines_with_pointer) == 1, (
            f"Expected exactly 1 line with 👉, found {len(lines_with_pointer)}"
        )

    def test_no_substantive_content_after_question(self):
        """No substantive content after the 👉 question before next ## Step."""
        content = _read_file(_SESSION_RESUME)
        section = _extract_section(content, "Step 3: Summarize and Confirm")
        lines = section.splitlines()

        # Find the 👉 question line
        question_idx = None
        for i, line in enumerate(lines):
            if "👉" in line:
                question_idx = i
                break

        assert question_idx is not None, "No 👉 question found in Step 3"

        # Check lines after the question
        after_question = lines[question_idx + 1:]
        for line in after_question:
            stripped = line.strip()
            # Allow empty lines, STOP markers, question_pending instructions,
            # code block markers (the question may be inside a code block),
            # and lines that are part of the protocol enforcement
            if not stripped:
                continue
            if "STOP" in stripped:
                continue
            if ".question_pending" in stripped:
                continue
            if stripped.startswith("Write ") and "question_pending" in stripped:
                continue
            if stripped.startswith("```"):
                continue
            # Any other non-empty line is substantive content — violation
            assert False, (
                f"Substantive content found after 👉 question: '{stripped}'"
            )


class TestProperty8Step1ReadsConversationStyle:
    """Property 8: Step 1 reads conversation_style.

    Verify that Step 1 in session-resume.md contains text about reading
    conversation_style from the preferences file.

    Feature: session-resume-behavioral-rules, Property 8: Step 1 reads conversation_style

    Validates: Requirements 3.1
    """

    def test_step_1_mentions_conversation_style(self):
        """Step 1 contains instruction to read conversation_style."""
        content = _read_file(_SESSION_RESUME)
        section = _extract_section(content, "Step 1: Read All State Files")
        assert section, "Step 1: Read All State Files section not found"

        assert "conversation_style" in section, (
            "Step 1 does not mention reading conversation_style"
        )


class TestProperty9ToneDescriptorMappingCompleteness:
    """Property 9: Tone descriptor mapping completeness.

    Verify that the Step 2c section contains a mapping/table with all three
    tone values: concise, conversational, detailed.

    Feature: session-resume-behavioral-rules, Property 9: Tone descriptor mapping completeness

    Validates: Requirements 7.2
    """

    def test_all_three_tone_values_in_mapping(self):
        """Step 2c contains mapping entries for concise, conversational, and detailed."""
        content = _read_file(_SESSION_RESUME)
        section = _extract_section(content, "Step 2c: Restore Conversation Style")
        assert section, "Step 2c: Restore Conversation Style section not found"

        # All three tone descriptors must appear in the section
        assert "concise" in section.lower(), (
            "Tone descriptor 'concise' not found in Step 2c"
        )
        assert "conversational" in section.lower(), (
            "Tone descriptor 'conversational' not found in Step 2c"
        )
        assert "detailed" in section.lower(), (
            "Tone descriptor 'detailed' not found in Step 2c"
        )


class TestProperty10AgentInstructionsPersistence:
    """Property 10: agent-instructions.md persistence instruction.

    Verify that agent-instructions.md contains an instruction about writing
    conversation_style to config/bootcamp_preferences.yaml.

    Feature: session-resume-behavioral-rules, Property 10: agent-instructions persistence

    Validates: Requirements 4.1
    """

    def test_conversation_style_persistence_instruction(self):
        """agent-instructions.md contains instruction to write conversation_style."""
        content = _read_file(_AGENT_INSTRUCTIONS)

        assert "conversation_style" in content, (
            "agent-instructions.md does not mention conversation_style"
        )
        assert "bootcamp_preferences.yaml" in content, (
            "agent-instructions.md does not mention bootcamp_preferences.yaml"
        )
