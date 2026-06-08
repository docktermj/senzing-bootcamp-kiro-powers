"""Property-based and unit tests for onboarding flow restructuring.

Feature: onboarding-flow-restructuring
"""

from __future__ import annotations

import re
from pathlib import Path

from hypothesis import given, settings
from hypothesis import strategies as st

# ---------------------------------------------------------------------------
# Paths to steering files under test
# ---------------------------------------------------------------------------

_STEERING_DIR = Path(__file__).resolve().parent.parent / "steering"
_ONBOARDING_FLOW = _STEERING_DIR / "onboarding-flow.md"
# After the onboarding split, the Entity Resolution Introduction (Step 3),
# Programming Language Selection (Step 4), Bootcamp Introduction (Step 5),
# Verbosity Preference (Step 5a), and Comprehension Check (Step 5b) live in
# this phase file. onboarding-flow.md keeps Steps 0–2d.
_ONBOARDING_PHASE1B = _STEERING_DIR / "onboarding-phase1b-intro-language.md"
_ER_INTRO = _STEERING_DIR / "entity-resolution-intro.md"
_MODULE_01 = _STEERING_DIR / "module-01-business-problem.md"


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------


def _read_file(path: Path) -> str:
    """Read a file and return its content as a string."""
    return path.read_text(encoding="utf-8")


def _extract_top_level_steps(content: str) -> list[tuple[int, str]]:
    """Extract all top-level step headings (## N. Title) and return (number, title) pairs."""
    pattern = r"^## (\d+)\. (.+)$"
    return [
        (int(m.group(1)), m.group(2).strip())
        for m in re.finditer(pattern, content, re.MULTILINE)
    ]


def _extract_section(content: str, heading_pattern: str) -> str:
    """Extract content from a ## heading until the next ## heading."""
    match = re.search(rf"^(## {heading_pattern}.*)$", content, re.MULTILINE)
    if not match:
        return ""
    start = match.start()
    next_heading = re.search(r"^## ", content[match.end():], re.MULTILINE)
    if next_heading:
        end = match.end() + next_heading.start()
    else:
        end = len(content)
    return content[start:end]


def _find_step_number_for_content(content: str, search_text: str) -> int | None:
    """Find which top-level step number contains the given search text."""
    steps = _extract_top_level_steps(content)
    for i, (step_num, _title) in enumerate(steps):
        # Get section content between this heading and the next
        if i + 1 < len(steps):
            next_step_num = steps[i + 1][0]
            section_pattern = rf"^## {step_num}\."
            next_pattern = rf"^## {next_step_num}\."
            start_match = re.search(section_pattern, content, re.MULTILINE)
            end_match = re.search(next_pattern, content, re.MULTILINE)
            if start_match and end_match:
                section = content[start_match.start():end_match.start()]
            else:
                continue
        else:
            section_pattern = rf"^## {step_num}\."
            start_match = re.search(section_pattern, content, re.MULTILINE)
            if start_match:
                section = content[start_match.start():]
            else:
                continue
        if search_text in section:
            return step_num
    return None


# ---------------------------------------------------------------------------
# Hypothesis strategies
# ---------------------------------------------------------------------------


@st.composite
def st_noise_content(draw: st.DrawFn) -> str:
    """Strategy generating random 'noise' content that could appear between structural markers."""
    lines = draw(st.lists(
        st.text(
            alphabet=st.characters(whitelist_categories=("L", "N", "P", "Z")),
            min_size=0,
            max_size=80,
        ),
        min_size=0,
        max_size=5,
    ))
    return "\n".join(lines)


@st.composite
def st_step_number_pair(draw: st.DrawFn) -> tuple[int, int]:
    """Strategy generating two distinct step numbers where first < second."""
    a = draw(st.integers(min_value=0, max_value=10))
    b = draw(st.integers(min_value=a + 1, max_value=15))
    return (a, b)


# ---------------------------------------------------------------------------
# Property tests
# ---------------------------------------------------------------------------


class TestProperty1ERIntroBeforeLanguageSelection:
    """Property 1: Entity Resolution Introduction precedes Programming Language Selection.

    Feature: onboarding-flow-restructuring, Property 1

    Validates: Requirements 1.1
    """

    @given(noise=st_noise_content())
    @settings(max_examples=20)
    def test_er_intro_precedes_language_selection(self, noise: str) -> None:
        """ER intro step number < language selection step number, both > prerequisite check.

        After the onboarding split, the Entity Resolution Introduction
        (Step 3) and Programming Language Selection (Step 4) live in
        onboarding-phase1b-intro-language.md, while the Prerequisite Check
        (Step 2) stays in onboarding-flow.md. The documented step numbering
        is continuous across the two files, so the ordering invariant is
        asserted across both.
        """
        flow_content = _read_file(_ONBOARDING_FLOW)
        phase1b_content = _read_file(_ONBOARDING_PHASE1B)

        # Find step containing the ER intro file directive (phase1b)
        er_intro_step = _find_step_number_for_content(
            phase1b_content,
            "#[[file:senzing-bootcamp/steering/entity-resolution-intro.md]]",
        )
        assert er_intro_step is not None, (
            "Could not find step containing entity-resolution-intro.md directive "
            "in onboarding-phase1b-intro-language.md"
        )

        # Find step containing Programming Language Selection mandatory gate (phase1b)
        lang_selection_step = _find_step_number_for_content(
            phase1b_content, "Programming Language Selection"
        )
        assert lang_selection_step is not None, (
            "Could not find Programming Language Selection step in "
            "onboarding-phase1b-intro-language.md"
        )

        # Find Prerequisite Check step (onboarding-flow.md)
        prereq_step = _find_step_number_for_content(flow_content, "Prerequisite Check")
        assert prereq_step is not None, (
            "Could not find Prerequisite Check step in onboarding-flow.md"
        )

        # Assert ordering: prerequisite < ER intro < language selection
        assert prereq_step < er_intro_step, (
            f"Prerequisite Check (step {prereq_step}) must precede "
            f"ER Introduction (step {er_intro_step})"
        )
        assert er_intro_step < lang_selection_step, (
            f"ER Introduction (step {er_intro_step}) must precede "
            f"Programming Language Selection (step {lang_selection_step})"
        )


class TestProperty2ContiguousStepNumbers:
    """Property 2: Step numbers form a contiguous sequence.

    Feature: onboarding-flow-restructuring, Property 2

    Validates: Requirements 1.4
    """

    @given(noise=st_noise_content())
    @settings(max_examples=20)
    def test_step_numbers_contiguous_from_zero(self, noise: str) -> None:
        """All ## N. headings form a contiguous integer sequence starting from 0."""
        content = _read_file(_ONBOARDING_FLOW)
        steps = _extract_top_level_steps(content)

        step_numbers = [num for num, _title in steps]

        # Must start from 0
        assert step_numbers[0] == 0, f"Step sequence must start from 0, got {step_numbers[0]}"

        # Must be contiguous (no gaps, no duplicates)
        for i in range(1, len(step_numbers)):
            assert step_numbers[i] == step_numbers[i - 1] + 1, (
                f"Gap or duplicate in step sequence: {step_numbers[i - 1]} -> {step_numbers[i]}. "
                f"Full sequence: {step_numbers}"
            )


class TestProperty3VerbosityAndComprehensionPlacement:
    """Property 3: Verbosity Preference and Comprehension Check are sub-steps of \
Bootcamp Introduction.

    Feature: onboarding-flow-restructuring, Property 3

    Validates: Requirements 1.5
    """

    @given(noise=st_noise_content())
    @settings(max_examples=20)
    def test_substeps_under_bootcamp_introduction(self, noise: str) -> None:
        """Verbosity Preference and Comprehension Check are ### headings under \
Bootcamp Introduction.

        After the onboarding split, the Bootcamp Introduction (Step 5) and
        its sub-steps Verbosity Preference (5a) and Comprehension Check (5b)
        live in onboarding-phase1b-intro-language.md.
        """
        content = _read_file(_ONBOARDING_PHASE1B)

        # Find the Bootcamp Introduction section
        bootcamp_intro_section = _extract_section(content, r"\d+\. Bootcamp Introduction")
        assert bootcamp_intro_section, "Bootcamp Introduction section not found"

        # Verify sub-steps are present as ### headings
        assert re.search(r"^### .+Verbosity Preference", bootcamp_intro_section, re.MULTILINE), (
            "Verbosity Preference not found as ### sub-step under Bootcamp Introduction"
        )
        assert re.search(r"^### .+Comprehension Check", bootcamp_intro_section, re.MULTILINE), (
            "Comprehension Check not found as ### sub-step under Bootcamp Introduction"
        )

        # Verify they are NOT under Entity Resolution Introduction
        er_section = _extract_section(content, r"\d+\. Entity Resolution Introduction")
        if er_section:
            assert "Verbosity Preference" not in er_section, (
                "Verbosity Preference should not be under Entity Resolution Introduction"
            )
            assert "Comprehension Check" not in er_section, (
                "Comprehension Check should not be under Entity Resolution Introduction"
            )

        # Verify they are NOT under Programming Language Selection
        lang_section = _extract_section(content, r"\d+\. Programming Language Selection")
        if lang_section:
            assert "Verbosity Preference" not in lang_section, (
                "Verbosity Preference should not be under Programming Language Selection"
            )
            assert "Comprehension Check" not in lang_section, (
                "Comprehension Check should not be under Programming Language Selection"
            )


class TestProperty4ProductionReuseHintPlacement:
    """Property 4: Production Reuse Hint is correctly placed in Programming Language Selection.

    Feature: onboarding-flow-restructuring, Property 4

    Validates: Requirements 3.1, 3.2
    """

    _HINT_TEXT = (
        "Tip: If you plan to use these bootcamp artifacts in production, consider choosing "
        "the language your team already uses \u2014 the code we generate here is designed to be "
        "your starting point for real-world use."
    )

    @given(noise=st_noise_content())
    @settings(max_examples=20)
    def test_hint_after_language_list_before_gate(self, noise: str) -> None:
        """Production Reuse Hint appears after language list instruction and before \
mandatory gate."""
        content = _read_file(_ONBOARDING_PHASE1B)

        # Extract Programming Language Selection section
        lang_section = _extract_section(content, r"\d+\. Programming Language Selection")
        assert lang_section, "Programming Language Selection section not found"

        # Find the hint text
        hint_pos = lang_section.find(self._HINT_TEXT)
        assert hint_pos != -1, (
            "Production Reuse Hint verbatim text not found in Programming Language Selection"
        )

        # Find the language list presentation instruction
        lang_list_pos = lang_section.find("Present the MCP-returned programming language list")
        assert lang_list_pos != -1, (
            "Language list presentation instruction not found"
        )

        # Find the mandatory gate marker
        gate_pos = lang_section.find("\u26d4", hint_pos)
        assert gate_pos != -1, "Mandatory gate marker not found after hint"

        # Assert ordering: language list < hint < gate
        assert lang_list_pos < hint_pos, (
            "Hint must appear after the language list presentation instruction"
        )
        assert hint_pos < gate_pos, (
            "Hint must appear before the mandatory gate marker"
        )


class TestProperty5GitAccessibilityPhrasePlacement:
    """Property 5: Git accessibility phrase precedes the existing explanation sentence.

    Feature: onboarding-flow-restructuring, Property 5

    Validates: Requirements 4.1, 4.2, 4.3
    """

    _ACCESSIBILITY_PHRASE = "If you don't know what 'git' is, just skip this."
    _EXPLANATION_SENTENCE = (
        "This is optional, but would you like me to initialize a git repository "
        "for version control? You can skip this without affecting the bootcamp."
    )

    @given(noise=st_noise_content())
    @settings(max_examples=20)
    def test_accessibility_phrase_immediately_before_explanation(self, noise: str) -> None:
        """Accessibility phrase appears in same prompt block, immediately before explanation."""
        content = _read_file(_MODULE_01)

        # Both phrases must exist
        access_pos = content.find(self._ACCESSIBILITY_PHRASE)
        assert access_pos != -1, (
            "Accessibility phrase not found in module-01-business-problem.md"
        )

        explain_pos = content.find(self._EXPLANATION_SENTENCE)
        assert explain_pos != -1, (
            "Explanation sentence not found in module-01-business-problem.md"
        )

        # Accessibility phrase must come before explanation
        assert access_pos < explain_pos, (
            "Accessibility phrase must precede the explanation sentence"
        )

        # They must be in the same prompt block (same quoted line or adjacent)
        text_between = content[access_pos + len(self._ACCESSIBILITY_PHRASE):explain_pos]
        # The text between should be minimal (just whitespace/space)
        assert len(text_between.strip()) == 0, (
            f"Unexpected content between accessibility phrase and explanation: "
            f"'{text_between.strip()}'"
        )


# ---------------------------------------------------------------------------
# Unit tests
# ---------------------------------------------------------------------------


class TestERIntroContentIntegrity:
    """Unit tests for entity-resolution-intro.md content integrity.

    Validates: Requirements 1.3, 2.1, 2.2, 2.4, 2.5, 2.6
    """

    def test_mandatory_gate_pattern_exists(self) -> None:
        """The mandatory gate pattern (stop marker + STOP instruction) exists in the file."""
        content = _read_file(_ER_INTRO)

        assert "\u26d4" in content, "Stop marker not found in entity-resolution-intro.md"
        assert "STOP" in content, "STOP instruction not found in entity-resolution-intro.md"
        # Verify they appear together in the gate section
        gate_pos = content.find("\u26d4")
        stop_pos = content.find("\U0001f6d1", gate_pos)
        assert stop_pos != -1, (
            "STOP instruction not found after gate marker"
        )

    def test_discussion_offer_has_at_least_two_example_questions(self) -> None:
        """The discussion offer has at least 2 example questions."""
        content = _read_file(_ER_INTRO)

        # Find the Explore Further section
        explore_pos = content.find("## Explore Further")
        assert explore_pos != -1, "Explore Further section not found"

        explore_section = content[explore_pos:]

        # Count quoted example questions (lines starting with - " pattern)
        example_questions = re.findall(r'^- ".*\?"', explore_section, re.MULTILINE)
        assert len(example_questions) >= 2, (
            f"Expected at least 2 example questions, found {len(example_questions)}"
        )

    def test_acknowledgment_phrases_listed_in_gate_instructions(self) -> None:
        """Acknowledgment phrases are listed in gate instructions."""
        content = _read_file(_ER_INTRO)

        # Check for key acknowledgment phrases in the agent instruction comment
        required_phrases = ["ready", "let's go", "continue", "next"]
        for phrase in required_phrases:
            assert phrase in content, (
                f"Acknowledgment phrase '{phrase}' not found in gate instructions"
            )

    def test_search_docs_instruction_present(self) -> None:
        """search_docs instruction is present in gate handling rules."""
        content = _read_file(_ER_INTRO)

        assert "search_docs" in content, (
            "search_docs instruction not found in entity-resolution-intro.md"
        )

    def test_fallback_instruction_present_for_failed_search(self) -> None:
        """Fallback instruction is present for failed search."""
        content = _read_file(_ER_INTRO)

        # Check for the fallback handling rule
        assert "no relevant results" in content or "no documentation was found" in content, (
            "Fallback instruction for failed search_docs not found"
        )
        assert "rephrase" in content or "different question" in content, (
            "Suggestion to rephrase not found in fallback instruction"
        )


class TestProductionReuseHintBehavior:
    """Unit tests for Production Reuse Hint behavior.

    Validates: Requirements 3.3, 3.4
    """

    _HINT_TEXT = (
        "Tip: If you plan to use these bootcamp artifacts in production, consider choosing "
        "the language your team already uses \u2014 the code we generate here is designed to be "
        "your starting point for real-world use."
    )

    def test_no_stop_instruction_between_hint_and_gate(self) -> None:
        """No STOP instruction appears between the hint and the mandatory gate."""
        content = _read_file(_ONBOARDING_PHASE1B)

        lang_section = _extract_section(content, r"\d+\. Programming Language Selection")
        assert lang_section, "Programming Language Selection section not found"

        hint_pos = lang_section.find(self._HINT_TEXT)
        assert hint_pos != -1, "Hint text not found"

        gate_pos = lang_section.find("\u26d4", hint_pos)
        assert gate_pos != -1, "Mandatory gate not found after hint"

        text_between = lang_section[hint_pos + len(self._HINT_TEXT):gate_pos]
        # No STOP between hint and gate
        assert "\U0001f6d1" not in text_between, (
            "Found a STOP instruction between the hint and the mandatory gate"
        )

    def test_hint_is_unconditional(self) -> None:
        """The hint is not wrapped in IF/condition."""
        content = _read_file(_ONBOARDING_PHASE1B)

        lang_section = _extract_section(content, r"\d+\. Programming Language Selection")
        assert lang_section, "Programming Language Selection section not found"

        hint_pos = lang_section.find(self._HINT_TEXT)
        assert hint_pos != -1, "Hint text not found"

        # Check the 5 lines before the hint for conditional patterns
        lines_before_hint = lang_section[:hint_pos].splitlines()[-5:]
        conditional_patterns = [r"\bIF\b", r"\bif\b.*:", r"\bWHEN\b", r"\bcondition\b"]
        for line in lines_before_hint:
            for pattern in conditional_patterns:
                assert not re.search(pattern, line), (
                    f"Hint appears to be conditional. Found '{line.strip()}' before hint"
                )


class TestGitPromptPreservation:
    """Unit tests for git prompt preservation.

    Validates: Requirements 4.2, 4.4
    """

    _EXPLANATION_SENTENCE = (
        "This is optional, but would you like me to initialize a git repository "
        "for version control? You can skip this without affecting the bootcamp."
    )

    def test_existing_explanation_sentence_preserved_verbatim(self) -> None:
        """The existing explanation sentence is preserved verbatim."""
        content = _read_file(_MODULE_01)

        assert self._EXPLANATION_SENTENCE in content, (
            "Existing explanation sentence not preserved verbatim in "
            "module-01-business-problem.md"
        )

    def test_stop_instruction_preserved_after_git_prompt(self) -> None:
        """The STOP instruction is preserved after the git prompt."""
        content = _read_file(_MODULE_01)

        explain_pos = content.find(self._EXPLANATION_SENTENCE)
        assert explain_pos != -1, "Explanation sentence not found"

        # Look for STOP instruction after the explanation
        after_explanation = content[explain_pos:]
        stop_pos = after_explanation.find("\U0001f6d1 STOP")
        assert stop_pos != -1, (
            "STOP instruction not found after the git prompt"
        )
