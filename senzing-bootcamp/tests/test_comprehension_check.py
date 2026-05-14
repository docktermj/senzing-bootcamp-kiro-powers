"""Tests for the onboarding comprehension check feature (Step 4c).

This module verifies structural placement and content preservation for the
comprehension check sub-step added between Step 4b (Verbosity Preference)
and Step 5 (Track Selection) in onboarding-flow.md.

Feature: onboarding-comprehension-check
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest
from hypothesis import assume, given, settings
from hypothesis import strategies as st

# ---------------------------------------------------------------------------
# Make scripts importable
# ---------------------------------------------------------------------------
_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_ONBOARDING_FILE = (
    Path(__file__).resolve().parent.parent / "steering" / "onboarding-flow.md"
)


def _read_onboarding() -> str:
    """Return the full text of onboarding-flow.md."""
    return _ONBOARDING_FILE.read_text(encoding="utf-8")


def _extract_step_headings(text: str) -> list[str]:
    """Extract step identifiers from ## and ### headings in order.

    Parses headings like ``## 0. Setup Preamble`` → ``"0"`` and
    ``### 4b. Verbosity Preference`` → ``"4b"``.  Non-numbered headings
    (e.g. ``## Switching Tracks``) are returned as their full text.

    Returns:
        Ordered list of step identifiers or heading titles.
    """
    headings: list[str] = []
    for match in re.finditer(r"^(#{2,3})\s+(.+)$", text, re.MULTILINE):
        title = match.group(2).strip()
        # Try to extract a step number like "4b." or "5."
        step_match = re.match(r"^(\d+[a-z]?)\.\s", title)
        if step_match:
            headings.append(step_match.group(1))
        else:
            headings.append(title)
    return headings


def _extract_section(text: str, heading_pattern: str) -> str:
    """Extract a section from the markdown by its heading regex.

    Returns everything from the matched heading up to (but not including)
    the next heading of the same or higher level.
    """
    pattern = r"^(#{2,3})\s+" + heading_pattern
    match = re.search(pattern, text, re.MULTILINE)
    if not match:
        pytest.fail(f"Could not find section matching: {heading_pattern}")

    level = len(match.group(1))  # 2 for ##, 3 for ###
    start = match.start()

    # Find the next heading of same or higher (fewer #) level
    rest = text[match.end():]
    next_heading = re.search(
        r"^#{1," + str(level) + r"}\s",
        rest,
        re.MULTILINE,
    )
    if next_heading:
        end = match.end() + next_heading.start()
    else:
        end = len(text)

    return text[start:end]


def _parse_numbered_steps(text: str) -> dict[str, str]:
    """Parse onboarding-flow.md into a dict of step-id → section content.

    Handles both ``## N.`` and ``### Nb.`` style headings.

    Returns:
        Dict like ``{"0": "## 0. Setup …", "4b": "### 4b. Verbosity …"}``.
    """
    steps: dict[str, str] = {}
    step_pattern = re.compile(r"^(#{2,3})\s+(\d+[a-z]?)\.\s", re.MULTILINE)
    matches = list(step_pattern.finditer(text))
    for i, m in enumerate(matches):
        step_id = m.group(2)
        start = m.start()
        level = len(m.group(1))
        # End at the next heading of same or higher level
        end = len(text)
        for j in range(i + 1, len(matches)):
            next_level = len(matches[j].group(1))
            if next_level <= level:
                end = matches[j].start()
                break
        # Also check for non-numbered ## headings after this step
        rest = text[m.end():]
        non_numbered = re.search(r"^#{2}\s+(?!\d+[a-z]?\.\s)", rest, re.MULTILINE)
        if non_numbered:
            candidate = m.end() + non_numbered.start()
            if candidate < end:
                end = candidate
        steps[step_id] = text[start:end]
    return steps


# ---------------------------------------------------------------------------
# Test 1 — Step heading sequence (Task 1.1)
# ---------------------------------------------------------------------------


class TestStepHeadingSequence:
    """Assert the heading list includes 4c between 4b and 5.

    **Validates: Requirements 1.1, 1.2, 5.1**

    Step 4c (Comprehension Check) must appear in the heading sequence
    after 4b (Verbosity Preference) and before 5 (Track Selection).
    """

    def test_heading_sequence_contains_4c(self) -> None:
        """The heading list must include step 4c."""
        text = _read_onboarding()
        headings = _extract_step_headings(text)
        assert "4c" in headings, (
            f"Step 4c not found in heading sequence.\nHeadings: {headings}"
        )

    def test_4c_appears_between_4b_and_5(self) -> None:
        """Step 4c must appear after 4b and before 5 in the heading order."""
        text = _read_onboarding()
        headings = _extract_step_headings(text)
        assert "4b" in headings, f"Step 4b not found. Headings: {headings}"
        assert "4c" in headings, f"Step 4c not found. Headings: {headings}"
        assert "5" in headings, f"Step 5 not found. Headings: {headings}"

        idx_4b = headings.index("4b")
        idx_4c = headings.index("4c")
        idx_5 = headings.index("5")

        assert idx_4b < idx_4c < idx_5, (
            f"Step 4c is not between 4b and 5.\n"
            f"  4b at index {idx_4b}, 4c at index {idx_4c}, 5 at index {idx_5}\n"
            f"  Headings: {headings}"
        )

    def test_heading_sequence_preserves_existing_order(self) -> None:
        """The existing step order (0, 1, 1b, 2, 3, 4, 4b, ..., 5) is preserved."""
        text = _read_onboarding()
        headings = _extract_step_headings(text)

        expected_numbered = ["0", "1", "1b", "2", "3", "4", "4b", "5"]
        actual_numbered = [h for h in headings if re.match(r"^\d+[a-z]?$", h)]

        for step in expected_numbered:
            assert step in actual_numbered, (
                f"Step {step} missing from numbered headings: {actual_numbered}"
            )

        # Verify relative order of existing steps
        indices = [actual_numbered.index(s) for s in expected_numbered]
        assert indices == sorted(indices), (
            f"Existing step order is not preserved.\n"
            f"  Expected order: {expected_numbered}\n"
            f"  Actual numbered headings: {actual_numbered}"
        )


# ---------------------------------------------------------------------------
# Test 2 — Existing step preservation (Task 1.1)
# ---------------------------------------------------------------------------


class TestExistingStepPreservation:
    """Assert existing steps retain their key content after modifications.

    **Validates: Requirements 1.1, 1.2, 5.1**

    Each existing step must preserve its essential informational content.
    This captures the baseline before any edits are made.
    """

    # -- Step 0: Setup Preamble --

    def test_step_0_welcome_banner_reference(self) -> None:
        """Step 0 references the WELCOME TO THE SENZING BOOTCAMP banner."""
        text = _read_onboarding()
        section = _extract_section(text, r"0\.\s+Setup Preamble")
        assert "WELCOME TO THE SENZING BOOTCAMP" in section, (
            "Step 0 missing welcome banner reference"
        )

    def test_step_0_administrative_setup(self) -> None:
        """Step 0 mentions administrative setup."""
        text = _read_onboarding()
        section = _extract_section(text, r"0\.\s+Setup Preamble")
        assert "administrative setup" in section, (
            "Step 0 missing 'administrative setup' content"
        )

    # -- Step 1: Directory Structure --

    def test_step_1_project_structure(self) -> None:
        """Step 1 references project-structure.md and critical hooks."""
        text = _read_onboarding()
        section = _extract_section(text, r"1\.\s+Directory Structure")
        assert "project-structure.md" in section
        assert "Install Critical Hooks" in section

    def test_step_1_steering_files(self) -> None:
        """Step 1 references foundational steering files."""
        text = _read_onboarding()
        section = _extract_section(text, r"1\.\s+Directory Structure")
        for name in ("product.md", "tech.md", "structure.md"):
            assert name in section, f"Step 1 missing reference to {name}"

    # -- Step 1b: Team Detection --

    def test_step_1b_team_config(self) -> None:
        """Step 1b references team.yaml and team_config_validator."""
        text = _read_onboarding()
        section = _extract_section(text, r"1b\.\s+Team Detection")
        assert "config/team.yaml" in section
        assert "team_config_validator" in section

    def test_step_1b_team_modes(self) -> None:
        """Step 1b describes co-located and distributed team modes."""
        text = _read_onboarding()
        section = _extract_section(text, r"1b\.\s+Team Detection")
        assert "co-located" in section
        assert "distributed" in section
        assert "progress_{member_id}.json" in section

    # -- Step 2: Language Selection (mandatory gate) --

    def test_step_2_language_detection(self) -> None:
        """Step 2 references platform detection and MCP server query."""
        text = _read_onboarding()
        section = _extract_section(text, r"2\.\s+Programming Language Selection")
        assert "platform.system()" in section
        assert "MCP server" in section

    def test_step_2_gate_marker(self) -> None:
        """Step 2 contains the mandatory gate marker ⛔."""
        text = _read_onboarding()
        section = _extract_section(text, r"2\.\s+Programming Language Selection")
        assert "⛔" in section, "Step 2 missing mandatory gate marker ⛔"
        assert "MANDATORY GATE" in section

    # -- Step 3: Prerequisite Check --

    def test_step_3_preflight(self) -> None:
        """Step 3 references preflight.py and verdict handling."""
        text = _read_onboarding()
        section = _extract_section(text, r"3\.\s+Prerequisite Check")
        assert "preflight.py" in section
        for verdict in ("FAIL:", "WARN:", "PASS:"):
            assert verdict in section, f"Step 3 missing verdict '{verdict}'"

    # -- Step 4: Bootcamp Introduction --

    def test_step_4_welcome_banner(self) -> None:
        """Step 4 contains the welcome banner text."""
        text = _read_onboarding()
        section = _extract_section(text, r"4\.\s+Bootcamp Introduction")
        assert "WELCOME TO THE SENZING BOOTCAMP" in section

    def test_step_4_guided_discovery(self) -> None:
        """Step 4 describes guided discovery framing."""
        text = _read_onboarding()
        section = _extract_section(text, r"4\.\s+Bootcamp Introduction")
        assert "guided discovery" in section

    def test_step_4_test_data_and_license(self) -> None:
        """Step 4 mentions test data / sample data cities and eval license."""
        text = _read_onboarding()
        section = _extract_section(text, r"4\.\s+Bootcamp Introduction")
        assert "test data" in section.lower() or "sample data" in section.lower(), (
            "Step 4 missing 'test data' or 'sample data' terminology"
        )
        assert "Las Vegas, London, Moscow" in section
        assert "500-record eval license" in section

    def test_step_4_glossary_reference(self) -> None:
        """Step 4 provides term-definition guidance (ask the agent)."""
        text = _read_onboarding()
        section = _extract_section(text, r"4\.\s+Bootcamp Introduction")
        assert "unfamiliar terms" in section

    # -- Step 4b: Verbosity Preference --

    def test_step_4b_verbosity_presets(self) -> None:
        """Step 4b describes the three verbosity presets."""
        text = _read_onboarding()
        section = _extract_section(text, r"4b\.\s+Verbosity Preference")
        for preset in ("concise", "standard", "detailed"):
            assert preset in section, (
                f"Step 4b missing verbosity preset '{preset}'"
            )

    def test_step_4b_preferences_persistence(self) -> None:
        """Step 4b references preferences file persistence."""
        text = _read_onboarding()
        section = _extract_section(text, r"4b\.\s+Verbosity Preference")
        assert "bootcamp_preferences.yaml" in section

    def test_step_4b_not_mandatory_gate(self) -> None:
        """Step 4b explicitly states it is NOT a mandatory gate."""
        text = _read_onboarding()
        section = _extract_section(text, r"4b\.\s+Verbosity Preference")
        assert "NOT a mandatory gate" in section

    # -- Step 5: Track Selection (mandatory gate) --

    def test_step_5_track_descriptions(self) -> None:
        """Step 5 contains both track descriptions."""
        text = _read_onboarding()
        section = _extract_section(text, r"5\.\s+Track Selection")
        for track in ("Core Bootcamp", "Advanced Topics"):
            assert track in section, (
                f"Step 5 missing track description '{track}'"
            )

    def test_step_5_all_modules_track(self) -> None:
        """Step 5 mentions the Modules 1-11 range for advanced_topics."""
        text = _read_onboarding()
        section = _extract_section(text, r"5\.\s+Track Selection")
        assert "1–11" in section or "1-11" in section, (
            "Step 5 missing the modules 1-11 range for advanced_topics track"
        )

    def test_step_5_gate_marker(self) -> None:
        """Step 5 contains the mandatory gate marker ⛔."""
        text = _read_onboarding()
        section = _extract_section(text, r"5\.\s+Track Selection")
        assert "⛔" in section, "Step 5 missing mandatory gate marker ⛔"
        assert "MANDATORY GATE" in section

    def test_step_5_interpreting_responses(self) -> None:
        """Step 5 contains the interpreting responses mapping."""
        text = _read_onboarding()
        section = _extract_section(text, r"5\.\s+Track Selection")
        assert "Interpreting responses" in section

    # -- Appendix sections --

    def test_switching_tracks_section_exists(self) -> None:
        """The Switching Tracks section exists."""
        text = _read_onboarding()
        assert "## Switching Tracks" in text

    def test_validation_gates_section_exists(self) -> None:
        """The Validation Gates section exists."""
        text = _read_onboarding()
        assert "## Validation Gates" in text

    def test_hook_registry_section_exists(self) -> None:
        """The Hook Registry section exists."""
        text = _read_onboarding()
        assert "## Hook Registry" in text


# ---------------------------------------------------------------------------
# Test 3 — Step 4c content markers (Task 1.2)
# ---------------------------------------------------------------------------


class TestStep4cContentMarkers:
    """Assert Step 4c contains the required content markers.

    **Validates: Requirements 2.1, 2.2, 2.3, 2.4, 3.1, 3.2, 3.3,
    4.1, 4.2, 4.3, 4.4, 5.2, 5.3**

    Each test method checks for a specific content marker that must be
    present in the Step 4c (Comprehension Check) section of
    onboarding-flow.md.
    """

    def test_prompt_contains_makes_sense_phrasing(self) -> None:
        """Step 4c prompt asks whether the introduction makes sense."""
        text = _read_onboarding()
        section = _extract_section(text, r"4c\.\s+Comprehension Check")
        section_lower = section.lower()
        assert "makes sense" in section_lower, (
            "Step 4c missing 'makes sense' phrasing in prompt"
        )

    def test_prompt_contains_questions_phrasing(self) -> None:
        """Step 4c prompt invites the bootcamper to ask questions."""
        text = _read_onboarding()
        section = _extract_section(text, r"4c\.\s+Comprehension Check")
        section_lower = section.lower()
        assert "question" in section_lower, (
            "Step 4c missing 'question(s)' phrasing in prompt"
        )

    def test_prompt_references_track_selection(self) -> None:
        """Step 4c references the upcoming track selection step."""
        text = _read_onboarding()
        section = _extract_section(text, r"4c\.\s+Comprehension Check")
        section_lower = section.lower()
        assert "track" in section_lower, (
            "Step 4c missing reference to upcoming track selection"
        )

    def test_acknowledgment_handling_instructions(self) -> None:
        """Step 4c contains acknowledgment handling with example phrases."""
        text = _read_onboarding()
        section = _extract_section(text, r"4c\.\s+Comprehension Check")
        section_lower = section.lower()

        # Must contain acknowledgment handling instructions
        assert "acknowledge" in section_lower or "acknowledgment" in section_lower, (
            "Step 4c missing acknowledgment handling instructions"
        )

        # Must include representative example phrases per Req 3.2
        example_phrases = [
            "looks good",
            "ready",
            "no questions",
        ]
        found = [p for p in example_phrases if p in section_lower]
        assert len(found) >= 2, (
            f"Step 4c should include acknowledgment example phrases. "
            f"Found: {found}, expected at least 2 of {example_phrases}"
        )

    def test_clarification_handling_instructions(self) -> None:
        """Step 4c contains clarification handling with check-for-more logic."""
        text = _read_onboarding()
        section = _extract_section(text, r"4c\.\s+Comprehension Check")
        section_lower = section.lower()

        # Must contain clarification handling instructions
        assert "clarif" in section_lower, (
            "Step 4c missing clarification handling instructions"
        )

        # Must describe checking for more questions before proceeding
        has_more_questions_check = (
            "more question" in section_lower
            or "additional question" in section_lower
            or "further question" in section_lower
        )
        assert has_more_questions_check, (
            "Step 4c missing check-for-more-questions logic in "
            "clarification handling"
        )

    def test_references_verbosity_settings(self) -> None:
        """Step 4c references verbosity settings for answering clarifications."""
        text = _read_onboarding()
        section = _extract_section(text, r"4c\.\s+Comprehension Check")
        section_lower = section.lower()
        assert "verbosity" in section_lower, (
            "Step 4c missing reference to verbosity settings "
            "for answering clarifications"
        )

    def test_not_mandatory_gate_note(self) -> None:
        """Step 4c notes it is NOT a mandatory gate."""
        text = _read_onboarding()
        section = _extract_section(text, r"4c\.\s+Comprehension Check")
        section_lower = section.lower()
        # Accept either the exact phrase "NOT a mandatory gate" or the
        # split phrasing "NOT a gate" + "not mandatory" which avoids the
        # literal substring "mandatory gate" (forbidden by the non-gate
        # contract test).
        has_combined = "not a mandatory gate" in section_lower
        has_split = "not a gate" in section_lower and "not mandatory" in section_lower
        assert has_combined or has_split, (
            "Step 4c missing note about not being a mandatory gate"
        )

    def test_hook_handles_closing_question_note(self) -> None:
        """Step 4c notes that the ask-bootcamper hook handles closing questions."""
        text = _read_onboarding()
        section = _extract_section(text, r"4c\.\s+Comprehension Check")
        section_lower = section.lower()
        assert "ask-bootcamper" in section_lower or "hook" in section_lower, (
            "Step 4c missing note about hook handling closing questions"
        )


# ---------------------------------------------------------------------------
# Test 4 — Step 4c non-gate contract (Task 1.3)
# ---------------------------------------------------------------------------


class TestStep4cNonGate:
    """Assert Step 4c contains no gate markers and respects question limits.

    **Validates: Requirements 1.3, 2.4**

    Step 4c (Comprehension Check) is explicitly NOT a mandatory gate.
    Its section must not contain any gate keywords (⛔, "MUST stop",
    "mandatory gate", "MUST NOT proceed") or WAIT instructions.
    Per conversation-ux-rules spec (Requirements 4.1, 7.4), a 👉 prefix
    IS expected on the bootcamper-directed question.
    """

    # -- Gate keyword absence --

    def test_no_gate_emoji(self) -> None:
        """Step 4c must not contain the ⛔ mandatory gate marker."""
        text = _read_onboarding()
        section = _extract_section(text, r"4c\.\s+Comprehension Check")
        assert "⛔" not in section, (
            "Step 4c contains ⛔ gate marker but is not a mandatory gate"
        )

    def test_no_must_stop_keyword(self) -> None:
        """Step 4c must not contain 'MUST stop' gate language."""
        text = _read_onboarding()
        section = _extract_section(text, r"4c\.\s+Comprehension Check")
        assert "MUST stop" not in section, (
            "Step 4c contains 'MUST stop' gate language "
            "but is not a mandatory gate"
        )

    def test_no_mandatory_gate_keyword(self) -> None:
        """Step 4c must not contain 'mandatory gate' language."""
        text = _read_onboarding()
        section = _extract_section(text, r"4c\.\s+Comprehension Check")
        section_lower = section.lower()
        assert "mandatory gate" not in section_lower, (
            "Step 4c contains 'mandatory gate' language "
            "but is not a mandatory gate"
        )

    def test_no_must_not_proceed_keyword(self) -> None:
        """Step 4c must not contain 'MUST NOT proceed' gate language."""
        text = _read_onboarding()
        section = _extract_section(text, r"4c\.\s+Comprehension Check")
        assert "MUST NOT proceed" not in section, (
            "Step 4c contains 'MUST NOT proceed' gate language "
            "but is not a mandatory gate"
        )

    # -- Inline question / WAIT marker absence --

    def test_no_inline_closing_question_marker(self) -> None:
        """Step 4c may contain a 👉 prefix (per conversation-ux-rules spec).

        The conversation-ux-rules spec (Requirements 4.1, 7.4) requires 👉
        prefixes on ALL bootcamper-directed questions, including non-gate
        steps. This supersedes the older module-closing-question-ownership
        assertion that non-gate steps must not have 👉.
        """
        text = _read_onboarding()
        section = _extract_section(text, r"4c\.\s+Comprehension Check")
        # 👉 is now expected per conversation-ux-rules spec.
        # Verify it appears at most once (one-question-per-turn rule).
        count = section.count("👉")
        assert count <= 1, (
            f"Step 4c contains {count} 👉 markers but should have at most 1 "
            "(one-question-per-turn rule)"
        )

    def test_no_wait_instruction(self) -> None:
        """Step 4c must not contain WAIT instructions."""
        text = _read_onboarding()
        section = _extract_section(text, r"4c\.\s+Comprehension Check")
        assert "WAIT" not in section, (
            "Step 4c contains WAIT instruction "
            "but the ask-bootcamper hook handles closing questions"
        )


# ---------------------------------------------------------------------------
# Test 5 — PBT: Non-gate step contract (Task 1.4)
# ---------------------------------------------------------------------------

# Gate markers and inline question/WAIT patterns that must be absent
# from any non-gate step section.
_GATE_MARKERS = ("⛔", "MUST stop", "mandatory gate", "MUST NOT proceed")
_INLINE_QUESTION_MARKERS = ("👉",)
_WAIT_KEYWORDS = ("WAIT",)

# Non-gate step identifiers — these steps must never contain gate
# markers or WAIT instructions.
# Note: 4c is excluded because the conversation-ux-rules spec (Requirements
# 4.1, 7.4) requires 👉 prefixes on ALL bootcamper-directed questions,
# including non-gate steps like 4c.
_NON_GATE_STEP_IDS: list[str] = ["0", "1", "1b", "4"]


@st.composite
def st_non_gate_step_id(draw: st.DrawFn) -> str:
    """Generate a non-gate step identifier.

    Samples from steps that are explicitly NOT mandatory gates:
    0 (Setup Preamble), 1 (Directory Structure), 1b (Team Detection),
    4 (Bootcamp Introduction), and 4c (Comprehension Check).
    """
    return draw(st.sampled_from(_NON_GATE_STEP_IDS))


def _extract_own_section(text: str, step_id: str) -> str | None:
    """Extract a step's own section content, excluding any sub-steps.

    Unlike ``_parse_numbered_steps`` which includes sub-step content
    within a parent step, this function returns only the content that
    belongs to the step itself — from its heading up to the next
    numbered step heading of any level.

    Args:
        text: Full markdown text of onboarding-flow.md.
        step_id: Step identifier like ``"4"`` or ``"4c"``.

    Returns:
        The section text, or ``None`` if the step is not found.
    """
    escaped = re.escape(step_id)
    heading_re = re.compile(
        rf"^(#{{2,3}})\s+{escaped}\.\s", re.MULTILINE,
    )
    match = heading_re.search(text)
    if not match:
        return None

    start = match.start()
    rest = text[match.end():]

    # End at the next numbered step heading (## N. or ### Nb.)
    next_step = re.search(r"^#{2,3}\s+\d+[a-z]?\.\s", rest, re.MULTILINE)
    if next_step:
        end = match.end() + next_step.start()
    else:
        # Also check for non-numbered ## headings (appendix sections)
        next_heading = re.search(r"^#{2}\s+(?!\d+[a-z]?\.\s)", rest, re.MULTILINE)
        end = match.end() + next_heading.start() if next_heading else len(text)

    return text[start:end]


class TestNonGateStepContractProperty:
    """PBT — Non-gate steps contain no gate markers, inline questions, or WAIT.

    **Validates: Requirements 1.3, 2.4**

    For any non-gate onboarding step (excluding 4c which has a legitimate
    👉 per conversation-ux-rules spec), the section content SHALL contain
    no mandatory gate markers (⛔, "MUST stop", "mandatory gate",
    "MUST NOT proceed") AND no inline 👉 closing questions or WAIT
    instructions.

    Note: Step 4c is excluded from the inline-question property test because
    the conversation-ux-rules spec (Requirements 4.1, 7.4) explicitly requires
    👉 prefixes on ALL bootcamper-directed questions, including non-gate steps.
    Step 4c's gate-marker and WAIT-instruction absence is still verified by
    the TestStep4cNonGate unit tests.

    Tag: Feature: onboarding-comprehension-check,
         Property 1: Non-gate step contract
    """

    @given(step_id=st_non_gate_step_id())
    @settings(max_examples=100)
    def test_non_gate_step_has_no_gate_markers(
        self, step_id: str,
    ) -> None:
        """No non-gate step contains mandatory gate markers."""
        text = _read_onboarding()
        section = _extract_own_section(text, step_id)

        # Skip step IDs not yet in the file (e.g. 4c before implementation)
        assume(section is not None)

        section_lower = section.lower()

        for marker in _GATE_MARKERS:
            assert marker not in section and marker.lower() not in section_lower, (
                f"Non-gate step {step_id} contains gate marker "
                f"'{marker}'.\nSection preview:\n{section[:300]}"
            )

    @given(step_id=st_non_gate_step_id())
    @settings(max_examples=100)
    def test_non_gate_step_has_no_inline_questions(
        self, step_id: str,
    ) -> None:
        """No non-gate step contains inline 👉 closing questions."""
        text = _read_onboarding()
        section = _extract_own_section(text, step_id)

        assume(section is not None)

        for marker in _INLINE_QUESTION_MARKERS:
            assert marker not in section, (
                f"Non-gate step {step_id} contains inline question "
                f"marker '{marker}'.\n"
                f"Section preview:\n{section[:300]}"
            )

    @given(step_id=st_non_gate_step_id())
    @settings(max_examples=100)
    def test_non_gate_step_has_no_wait_instructions(
        self, step_id: str,
    ) -> None:
        """No non-gate step contains WAIT instructions."""
        text = _read_onboarding()
        section = _extract_own_section(text, step_id)

        assume(section is not None)

        for keyword in _WAIT_KEYWORDS:
            assert keyword not in section, (
                f"Non-gate step {step_id} contains WAIT instruction "
                f"'{keyword}'.\n"
                f"Section preview:\n{section[:300]}"
            )


# ---------------------------------------------------------------------------
# Test 6 — Token count consistency (Task 1.5)
# ---------------------------------------------------------------------------

_STEERING_INDEX = (
    Path(__file__).resolve().parent.parent
    / "steering"
    / "steering-index.yaml"
)


def _parse_onboarding_token_count(index_text: str) -> int | None:
    """Extract the stored token_count for onboarding-flow.md.

    Parses the file_metadata section of steering-index.yaml using
    simple regex matching (no PyYAML), consistent with the project's
    custom minimal YAML parsing convention.

    Args:
        index_text: Raw text content of steering-index.yaml.

    Returns:
        The stored token count, or None if not found.
    """
    # Find the onboarding-flow.md entry under file_metadata
    pattern = re.compile(
        r"^\s{2}onboarding-flow\.md:\s*\n"
        r"\s+token_count:\s*(\d+)",
        re.MULTILINE,
    )
    match = pattern.search(index_text)
    if match:
        return int(match.group(1))
    return None


class TestTokenCountConsistency:
    """Assert steering-index.yaml token count for onboarding-flow.md is fresh.

    **Validates: Requirements 5.4**

    The token count stored in steering-index.yaml must match the actual
    file content when calculated using the same formula as
    measure_steering.py: ``round(len(content) / 4)``.  A tolerance of
    10% is allowed (matching the ``--check`` mode threshold).
    """

    def test_stored_count_matches_calculated(self) -> None:
        """Stored token count is within 10% of the calculated value."""
        from measure_steering import calculate_token_count

        calculated = calculate_token_count(_ONBOARDING_FILE)

        index_text = _STEERING_INDEX.read_text(encoding="utf-8")
        stored = _parse_onboarding_token_count(index_text)

        assert stored is not None, (
            "onboarding-flow.md token_count not found in "
            "steering-index.yaml file_metadata section"
        )

        denominator = max(calculated, 1)
        drift = abs(stored - calculated) / denominator

        assert drift <= 0.10, (
            f"Token count for onboarding-flow.md is stale.\n"
            f"  Stored in steering-index.yaml: {stored}\n"
            f"  Calculated from file content:  {calculated}\n"
            f"  Drift: {drift:.1%} (threshold: 10%)\n"
            f"  Run: python3 senzing-bootcamp/scripts/"
            f"measure_steering.py to update"
        )

    def test_stored_count_is_positive(self) -> None:
        """Stored token count must be a positive integer."""
        index_text = _STEERING_INDEX.read_text(encoding="utf-8")
        stored = _parse_onboarding_token_count(index_text)

        assert stored is not None, (
            "onboarding-flow.md token_count not found in "
            "steering-index.yaml"
        )
        assert stored > 0, (
            f"Token count should be positive, got {stored}"
        )

    def test_size_category_matches_count(self) -> None:
        """Size category is consistent with the stored token count."""
        from measure_steering import classify_size

        index_text = _STEERING_INDEX.read_text(encoding="utf-8")
        stored = _parse_onboarding_token_count(index_text)
        assert stored is not None, (
            "onboarding-flow.md token_count not found"
        )

        expected_category = classify_size(stored)

        # Parse the size_category for onboarding-flow.md
        cat_pattern = re.compile(
            r"^\s{2}onboarding-flow\.md:\s*\n"
            r"\s+token_count:\s*\d+\s*\n"
            r"\s+size_category:\s*(\w+)",
            re.MULTILINE,
        )
        cat_match = cat_pattern.search(index_text)
        assert cat_match is not None, (
            "onboarding-flow.md size_category not found in "
            "steering-index.yaml"
        )
        actual_category = cat_match.group(1)

        assert actual_category == expected_category, (
            f"Size category mismatch for onboarding-flow.md.\n"
            f"  Stored: {actual_category}\n"
            f"  Expected for {stored} tokens: {expected_category}"
        )
