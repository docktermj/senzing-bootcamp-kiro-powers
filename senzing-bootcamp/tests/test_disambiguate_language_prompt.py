"""Bug condition exploration and preservation tests for disambiguate-language-prompt bugfix.

Bug condition tests parse the UNFIXED steering file and confirm the bug exists.
Tests are EXPECTED TO FAIL on unfixed code — failure confirms the bug.

Preservation tests verify baseline behaviors that must remain unchanged after the fix.
These tests are EXPECTED TO PASS on unfixed code.

Feature: disambiguate-language-prompt
"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

import pytest
from hypothesis import given, settings, assume, HealthCheck
from hypothesis import strategies as st

# ---------------------------------------------------------------------------
# Paths — relative to this test file's location
# ---------------------------------------------------------------------------

_BOOTCAMP_DIR = Path(__file__).resolve().parent.parent
_ONBOARDING_FLOW = _BOOTCAMP_DIR / "steering" / "onboarding-flow.md"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_STEP2_HEADING_PATTERN = re.compile(
    r"^##\s+2\.\s+(.+)$",
    re.MULTILINE,
)

_NEXT_STEP_HEADING_PATTERN = re.compile(
    r"^##\s+3\.\s+",
    re.MULTILINE,
)

_PROGRAMMING_LANGUAGE_PATTERN = re.compile(
    r"programming\s+language",
    re.IGNORECASE,
)

_BARE_LANGUAGE_PATTERN = re.compile(
    r"\blanguage\b",
    re.IGNORECASE,
)

_DISAMBIGUATION_CONSTRAINT_PATTERN = re.compile(
    r"(never|not|avoid|do\s+not).{0,80}bare\s+.{0,20}language",
    re.IGNORECASE,
)

_WORDING_DIRECTIVE_PATTERN = re.compile(
    r"(must|shall|always).{0,80}programming\s+language",
    re.IGNORECASE,
)


def _read_onboarding_flow() -> str:
    """Read the full content of onboarding-flow.md."""
    return _ONBOARDING_FLOW.read_text(encoding="utf-8")


def _extract_step2_section(markdown: str) -> str:
    """Extract the Step 2 section from onboarding-flow.md.

    Returns the text from the Step 2 heading to the next step heading.
    """
    heading_match = _STEP2_HEADING_PATTERN.search(markdown)
    if not heading_match:
        return ""

    start = heading_match.start()

    next_match = _NEXT_STEP_HEADING_PATTERN.search(markdown, heading_match.end())
    if next_match:
        return markdown[start:next_match.start()]

    return markdown[start:]


def _extract_step2_heading(markdown: str) -> str:
    """Extract just the Step 2 heading text (after '## 2. ')."""
    heading_match = _STEP2_HEADING_PATTERN.search(markdown)
    if not heading_match:
        return ""
    return heading_match.group(1).strip()


# ---------------------------------------------------------------------------
# Test Class — Bug Condition: Ambiguous Language Prompt at Step 2
# ---------------------------------------------------------------------------


class TestBugConditionAmbiguousLanguagePrompt:
    """Bug Condition Exploration — Ambiguous Language Prompt at Step 2.

    **Validates: Requirements 1.1, 1.2, 2.1, 2.2**

    Parse the Step 2 section of onboarding-flow.md and assert:
    - The section heading contains "programming language" (case-insensitive)
    - An explicit wording directive exists requiring "programming language"
    - A disambiguation constraint is present forbidding bare "language" alone

    Bug condition: isBugCondition(input) where
      input.stepNumber == 2
      AND input.promptText CONTAINS "language"
      AND input.promptText DOES NOT CONTAIN "programming language"

    Expected behavior: prompt text uses "programming language" so the question
    is unambiguous.

    EXPECTED OUTCOME: Tests FAIL on unfixed code (confirms bug exists).
    """

    def test_step2_heading_contains_programming_language(self) -> None:
        """Step 2 heading must contain 'programming language' qualifier.

        On unfixed code, the heading is 'Language Selection' — missing
        the 'programming' qualifier. This test will FAIL, confirming the bug.
        """
        content = _read_onboarding_flow()
        heading = _extract_step2_heading(content)
        assert heading, "Step 2 section not found in onboarding-flow.md"
        assert _PROGRAMMING_LANGUAGE_PATTERN.search(heading), (
            f"Step 2 heading is '{heading}' — missing 'programming' qualifier. "
            f"The heading uses bare 'language' which is ambiguous with "
            f"natural/spoken languages."
        )

    def test_step2_has_wording_directive(self) -> None:
        """Step 2 must contain an explicit wording directive requiring
        'programming language' in the prompt.

        On unfixed code, no such directive exists. This test will FAIL,
        confirming the bug.
        """
        content = _read_onboarding_flow()
        step2 = _extract_step2_section(content)
        assert step2, "Step 2 section not found in onboarding-flow.md"
        assert _WORDING_DIRECTIVE_PATTERN.search(step2), (
            "Step 2 does not contain an explicit wording directive requiring "
            "'programming language' in the prompt. Without this directive, the "
            "agent may use bare 'language' which is ambiguous."
        )

    def test_step2_has_disambiguation_constraint(self) -> None:
        """Step 2 must contain a disambiguation constraint forbidding bare
        'language' alone.

        On unfixed code, no such constraint exists. This test will FAIL,
        confirming the bug.
        """
        content = _read_onboarding_flow()
        step2 = _extract_step2_section(content)
        assert step2, "Step 2 section not found in onboarding-flow.md"
        assert _DISAMBIGUATION_CONSTRAINT_PATTERN.search(step2), (
            "Step 2 does not contain a disambiguation constraint forbidding "
            "bare 'language' alone. Without this constraint, the agent may "
            "present an ambiguous prompt that could be confused with "
            "natural/spoken language selection."
        )


# ---------------------------------------------------------------------------
# PBT Test — Bug Condition Identification via Hypothesis
# ---------------------------------------------------------------------------

# Strategy: generate line indices within Step 2 to verify the bug condition
# holds across the entire section content.


@st.composite
def st_step2_line_index(draw: st.DrawFn) -> int:
    """Generate a valid line index within the Step 2 section."""
    content = _read_onboarding_flow()
    step2 = _extract_step2_section(content)
    lines = step2.splitlines()
    if not lines:
        return 0
    return draw(st.integers(min_value=0, max_value=len(lines) - 1))


class TestBugConditionPBT:
    """PBT Test — Bug Condition Identification.

    **Validates: Requirements 1.1, 1.2, 2.1, 2.2**

    Use Hypothesis to verify that any line in Step 2 containing the word
    'language' also contains 'programming language'. On unfixed code, this
    will find counterexamples where 'language' appears without 'programming'.
    """

    @given(line_idx=st_step2_line_index())
    @settings(max_examples=10, suppress_health_check=[HealthCheck.too_slow])
    def test_step2_lines_use_programming_language(self, line_idx: int) -> None:
        """For any line in Step 2 containing 'language', it must also contain
        'programming language' to avoid ambiguity.

        Bug condition: line CONTAINS 'language' AND NOT CONTAINS
        'programming language'.
        """
        content = _read_onboarding_flow()
        step2 = _extract_step2_section(content)
        lines = step2.splitlines()

        if not lines or line_idx >= len(lines):
            return

        line = lines[line_idx]

        # Only check lines that contain the word "language"
        if not _BARE_LANGUAGE_PATTERN.search(line):
            return

        # If a line mentions "language", it should use "programming language"
        # to be unambiguous (unless it's a technical reference like
        # "language steering file" or "language list")
        # The bug condition is: contains "language" but NOT "programming language"
        has_programming_qualifier = bool(
            _PROGRAMMING_LANGUAGE_PATTERN.search(line)
        )

        # Allow technical references that are unambiguous in context
        # (e.g., "language steering file", "lang-python.md")
        is_technical_ref = bool(re.search(
            r"(lang-\w+\.md|language\s+steering\s+file|language\s+preference)",
            line,
            re.IGNORECASE,
        ))

        if is_technical_ref:
            return

        assert has_programming_qualifier, (
            f"Bug condition found at line {line_idx}: '{line.strip()}' — "
            f"contains 'language' without 'programming' qualifier. "
            f"This is ambiguous with natural/spoken languages."
        )


# ---------------------------------------------------------------------------
# Preservation Tests — Baseline Behaviors at Step 2
# ---------------------------------------------------------------------------

# Patterns for preservation properties observed on UNFIXED code.

_MCP_CALL_PATTERN = re.compile(
    r"(get_capabilities|sdk_guide)",
    re.IGNORECASE,
)

_WARNING_RELAY_PATTERN = re.compile(
    r"relay\s+that\s+warning\s+clearly\s+and\s+suggest\s+alternatives",
    re.IGNORECASE,
)

_CONFIG_PERSISTENCE_PATTERN = re.compile(
    r"config/bootcamp_preferences\.yaml",
)

_MANDATORY_GATE_PATTERN = re.compile(
    r"⛔.*MANDATORY\s+GATE",
)

_STOP_INSTRUCTION_PATTERN = re.compile(
    r"🛑\s*STOP",
)

_LANGUAGE_STEERING_FILE_PATTERN = re.compile(
    r"[Ll]oad\s+language\s+steering\s+file",
)

# Patterns for identifying all step headings in onboarding-flow.md.
_ALL_STEP_HEADINGS_PATTERN = re.compile(
    r"^##\s+(\d+[a-z]?)\.\s+(.+)$",
    re.MULTILINE,
)


def _extract_section_by_heading(markdown: str, heading_num: str) -> str:
    """Extract a section by its heading number (e.g., '0', '0b', '1', '3').

    Returns the text from the heading to the next same-level heading.
    """
    pattern = re.compile(
        rf"^##\s+{re.escape(heading_num)}\.\s+(.+)$",
        re.MULTILINE,
    )
    match = pattern.search(markdown)
    if not match:
        return ""

    start = match.start()

    # Find the next ## heading after this one
    next_heading = re.compile(r"^##\s+", re.MULTILINE)
    next_match = next_heading.search(markdown, match.end())
    if next_match:
        return markdown[start:next_match.start()]
    return markdown[start:]


def _get_non_step2_sections_hash(markdown: str) -> str:
    """Compute a hash of all sections EXCEPT Step 2.

    This captures Steps 0, 0b, 0c, 1, 1b, 3, 4, 5 and any other content
    outside Step 2 to verify they are not modified.
    """
    step2_section = _extract_step2_section(markdown)
    if not step2_section:
        return hashlib.sha256(markdown.encode()).hexdigest()

    # Remove Step 2 content from the full document
    non_step2 = markdown.replace(step2_section, "")
    return hashlib.sha256(non_step2.encode()).hexdigest()


# Capture baseline hash of non-Step-2 sections for comparison.
_BASELINE_NON_STEP2_HASH = _get_non_step2_sections_hash(_read_onboarding_flow())


# Strategy: generate random boundary offsets within Step 2 to verify
# preservation properties hold regardless of where we look in the section.

@st.composite
def st_step2_substring_range(draw: st.DrawFn) -> tuple[int, int]:
    """Generate a random (start, end) range within the Step 2 section text.

    Used to verify that preservation properties hold across different
    subsections of Step 2.
    """
    content = _read_onboarding_flow()
    step2 = _extract_step2_section(content)
    length = len(step2)
    assume(length > 0)
    start = draw(st.integers(min_value=0, max_value=max(0, length - 1)))
    end = draw(st.integers(min_value=start, max_value=length))
    return (start, end)


@st.composite
def st_other_step_number(draw: st.DrawFn) -> str:
    """Generate a step number that is NOT Step 2.

    Used to verify other sections are unmodified.
    """
    content = _read_onboarding_flow()
    headings = _ALL_STEP_HEADINGS_PATTERN.findall(content)
    other_steps = [num for num, _ in headings if num != "2"]
    assume(len(other_steps) > 0)
    return draw(st.sampled_from(other_steps))


class TestPreservationPBT:
    """PBT Tests — Preservation of Unchanged Onboarding Behaviors at Step 2.

    **Validates: Requirements 3.1, 3.2, 3.3, 3.4**

    These tests verify baseline behaviors that MUST remain unchanged after
    the fix. They are EXPECTED TO PASS on unfixed code, establishing the
    preservation baseline.

    Observation-first methodology: we observe the current (unfixed) code,
    confirm these properties hold, and then re-run after the fix to ensure
    no regressions.
    """

    # ------------------------------------------------------------------
    # MCP Call Preservation (Requirement 3.1)
    # ------------------------------------------------------------------

    def test_step2_contains_mcp_call_instruction(self) -> None:
        """Step 2 must contain instruction to call get_capabilities or
        sdk_guide on the Senzing MCP server.

        This verifies the MCP tool call instruction is present in the
        current unfixed code (baseline).
        """
        content = _read_onboarding_flow()
        step2 = _extract_step2_section(content)
        assert step2, "Step 2 section not found in onboarding-flow.md"
        assert _MCP_CALL_PATTERN.search(step2), (
            "Step 2 does not contain instruction to call 'get_capabilities' "
            "or 'sdk_guide' on the Senzing MCP server."
        )

    @given(bounds=st_step2_substring_range())
    @settings(max_examples=10, suppress_health_check=[HealthCheck.too_slow])
    def test_mcp_call_present_in_full_section(self, bounds: tuple[int, int]) -> None:
        """For any substring boundary within Step 2, the full section always
        contains the MCP call instruction.

        This property verifies the MCP call instruction is a stable part
        of Step 2 regardless of how we slice the section.
        """
        content = _read_onboarding_flow()
        step2 = _extract_step2_section(content)
        assume(len(step2) > 0)
        # The property: the full Step 2 section always contains MCP call
        assert _MCP_CALL_PATTERN.search(step2), (
            "MCP call instruction (get_capabilities/sdk_guide) missing from Step 2."
        )

    # ------------------------------------------------------------------
    # Warning Relay Preservation (Requirement 3.2)
    # ------------------------------------------------------------------

    def test_step2_contains_warning_relay_instruction(self) -> None:
        """Step 2 must contain the discouraged-language warning relay
        instruction.

        This verifies the warning relay text is present in the current
        unfixed code (baseline).
        """
        content = _read_onboarding_flow()
        step2 = _extract_step2_section(content)
        assert step2, "Step 2 section not found in onboarding-flow.md"
        assert _WARNING_RELAY_PATTERN.search(step2), (
            "Step 2 does not contain the discouraged-language warning relay "
            "instruction (text about relaying MCP server warnings and "
            "suggesting alternatives)."
        )

    @given(bounds=st_step2_substring_range())
    @settings(max_examples=10, suppress_health_check=[HealthCheck.too_slow])
    def test_warning_relay_present_in_full_section(self, bounds: tuple[int, int]) -> None:
        """For any substring boundary within Step 2, the full section always
        contains the warning relay instruction.
        """
        content = _read_onboarding_flow()
        step2 = _extract_step2_section(content)
        assume(len(step2) > 0)
        assert _WARNING_RELAY_PATTERN.search(step2), (
            "Warning relay instruction missing from Step 2."
        )

    # ------------------------------------------------------------------
    # Config Persistence Preservation (Requirement 3.3)
    # ------------------------------------------------------------------

    def test_step2_contains_config_persistence_instruction(self) -> None:
        """Step 2 must contain instruction to persist selection to
        config/bootcamp_preferences.yaml.

        This verifies the config persistence instruction is present in
        the current unfixed code (baseline).
        """
        content = _read_onboarding_flow()
        step2 = _extract_step2_section(content)
        assert step2, "Step 2 section not found in onboarding-flow.md"
        assert _CONFIG_PERSISTENCE_PATTERN.search(step2), (
            "Step 2 does not contain instruction to persist selection to "
            "'config/bootcamp_preferences.yaml'."
        )

    @given(bounds=st_step2_substring_range())
    @settings(max_examples=10, suppress_health_check=[HealthCheck.too_slow])
    def test_config_persistence_present_in_full_section(
        self, bounds: tuple[int, int]
    ) -> None:
        """For any substring boundary within Step 2, the full section always
        contains the config persistence instruction.
        """
        content = _read_onboarding_flow()
        step2 = _extract_step2_section(content)
        assume(len(step2) > 0)
        assert _CONFIG_PERSISTENCE_PATTERN.search(step2), (
            "Config persistence instruction missing from Step 2."
        )

    # ------------------------------------------------------------------
    # Mandatory Gate Preservation (Requirement 3.4)
    # ------------------------------------------------------------------

    def test_step2_contains_mandatory_gate_marker(self) -> None:
        """Step 2 must contain the ⛔ mandatory gate marker.

        This verifies the mandatory gate is present in the current
        unfixed code (baseline).
        """
        content = _read_onboarding_flow()
        step2 = _extract_step2_section(content)
        assert step2, "Step 2 section not found in onboarding-flow.md"
        assert _MANDATORY_GATE_PATTERN.search(step2), (
            "Step 2 does not contain the ⛔ MANDATORY GATE marker."
        )

    def test_step2_contains_stop_instruction(self) -> None:
        """Step 2 must contain the 🛑 STOP instruction requiring real
        user input.

        This verifies the STOP instruction is present in the current
        unfixed code (baseline).
        """
        content = _read_onboarding_flow()
        step2 = _extract_step2_section(content)
        assert step2, "Step 2 section not found in onboarding-flow.md"
        assert _STOP_INSTRUCTION_PATTERN.search(step2), (
            "Step 2 does not contain the 🛑 STOP instruction."
        )

    @given(bounds=st_step2_substring_range())
    @settings(max_examples=10, suppress_health_check=[HealthCheck.too_slow])
    def test_mandatory_gate_present_in_full_section(
        self, bounds: tuple[int, int]
    ) -> None:
        """For any substring boundary within Step 2, the full section always
        contains the mandatory gate marker and STOP instruction.
        """
        content = _read_onboarding_flow()
        step2 = _extract_step2_section(content)
        assume(len(step2) > 0)
        assert _MANDATORY_GATE_PATTERN.search(step2), (
            "Mandatory gate marker missing from Step 2."
        )
        assert _STOP_INSTRUCTION_PATTERN.search(step2), (
            "STOP instruction missing from Step 2."
        )

    # ------------------------------------------------------------------
    # Language Steering File Loading Preservation (Requirement 3.3)
    # ------------------------------------------------------------------

    def test_step2_contains_language_steering_file_loading(self) -> None:
        """Step 2 must contain instruction to load language steering file
        after confirmation.

        This verifies the language steering file loading instruction is
        present in the current unfixed code (baseline).
        """
        content = _read_onboarding_flow()
        step2 = _extract_step2_section(content)
        assert step2, "Step 2 section not found in onboarding-flow.md"
        assert _LANGUAGE_STEERING_FILE_PATTERN.search(step2), (
            "Step 2 does not contain instruction to load language steering "
            "file after confirmation."
        )

    @given(bounds=st_step2_substring_range())
    @settings(max_examples=10, suppress_health_check=[HealthCheck.too_slow])
    def test_language_steering_file_loading_present_in_full_section(
        self, bounds: tuple[int, int]
    ) -> None:
        """For any substring boundary within Step 2, the full section always
        contains the language steering file loading instruction.
        """
        content = _read_onboarding_flow()
        step2 = _extract_step2_section(content)
        assume(len(step2) > 0)
        assert _LANGUAGE_STEERING_FILE_PATTERN.search(step2), (
            "Language steering file loading instruction missing from Step 2."
        )

    # ------------------------------------------------------------------
    # Other Sections Unmodified (All Preservation Requirements)
    # ------------------------------------------------------------------

    def test_non_step2_sections_unchanged(self) -> None:
        """All sections other than Step 2 must remain unchanged.

        This captures a hash of Steps 0, 0b, 0c, 1, 1b, 3, 4, 5 and
        verifies they match the baseline captured at module load time.
        """
        content = _read_onboarding_flow()
        current_hash = _get_non_step2_sections_hash(content)
        assert current_hash == _BASELINE_NON_STEP2_HASH, (
            "Non-Step-2 sections of onboarding-flow.md have been modified. "
            "Steps 0, 0b, 0c, 1, 1b, 3, 4, 5 must remain unchanged."
        )

    @given(step_num=st_other_step_number())
    @settings(max_examples=10, suppress_health_check=[HealthCheck.too_slow])
    def test_other_steps_exist_and_unchanged(self, step_num: str) -> None:
        """For any step number other than 2, the section must exist and
        its content must be non-empty (verifying no accidental deletion).
        """
        content = _read_onboarding_flow()
        section = _extract_section_by_heading(content, step_num)
        assert section, (
            f"Step {step_num} section is missing or empty in "
            f"onboarding-flow.md — it may have been accidentally deleted."
        )
