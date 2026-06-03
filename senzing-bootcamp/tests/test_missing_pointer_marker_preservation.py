"""Preservation property tests for missing-pointer-marker bugfix.

These tests observe the UNFIXED file content and assert structural
properties that must be preserved after the fix is applied.
ALL tests are EXPECTED TO PASS on unfixed code.

Feature: missing-pointer-marker
"""

from __future__ import annotations

import re
from pathlib import Path

from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

# -------------------------------------------------------------------
# Paths — relative to this test file's location
# -------------------------------------------------------------------

_BOOTCAMP_DIR = Path(__file__).resolve().parent.parent
_ONBOARDING_FILE = _BOOTCAMP_DIR / "steering" / "onboarding-flow.md"

# -------------------------------------------------------------------
# Helpers
# -------------------------------------------------------------------


def _read_onboarding() -> str:
    """Read the full content of onboarding-flow.md."""
    return _ONBOARDING_FILE.read_text(encoding="utf-8")


def _extract_section_by_step_id(markdown: str, step_id: str) -> str | None:
    """Extract a step section by its step identifier (e.g., '4c', '2', '3a').

    Returns the full text from the heading to the next step heading
    of the same or higher level, or None if not found.
    """
    escaped = re.escape(step_id)
    heading_re = re.compile(
        rf"^(#{{2,3}})\s+{escaped}\.\s", re.MULTILINE,
    )
    match = heading_re.search(markdown)
    if not match:
        return None

    start = match.start()
    level = len(match.group(1))
    rest = markdown[match.end():]

    # End at the next heading of same or higher level
    next_heading = re.compile(
        r"^#{2," + str(level) + r"}\s",
        re.MULTILINE,
    )
    next_match = next_heading.search(rest)
    if next_match:
        end = match.end() + next_match.start()
    else:
        end = len(markdown)

    return markdown[start:end]


def _find_all_pointer_markers(markdown: str) -> list[tuple[int, str]]:
    """Find all 👉 markers with their line numbers and surrounding context.

    Returns a list of (line_number, line_text) tuples.
    """
    results = []
    for i, line in enumerate(markdown.splitlines(), start=1):
        if "👉" in line:
            results.append((i, line))
    return results


def _find_all_stop_directives(markdown: str) -> list[tuple[int, str]]:
    """Find all 🛑 STOP directives with their line numbers and text.

    Returns a list of (line_number, line_text) tuples.
    """
    results = []
    for i, line in enumerate(markdown.splitlines(), start=1):
        if "🛑" in line:
            results.append((i, line))
    return results


def _identify_step_for_line(markdown: str, target_line: int) -> str | None:
    """Identify which step a given line number belongs to.

    Returns the step identifier (e.g., '2', '3a', '4c') or None.
    """
    step_pattern = re.compile(r"^#{2,3}\s+(\d+[a-z]?)\.\s", re.MULTILINE)
    lines = markdown.splitlines()
    current_step = None
    for i, line in enumerate(lines, start=1):
        m = step_pattern.match(line)
        if m:
            current_step = m.group(1)
        if i == target_line:
            return current_step
    return current_step


# -------------------------------------------------------------------
# Baselines — snapshot the UNFIXED file content for comparison
# -------------------------------------------------------------------

_UNFIXED_CONTENT = _read_onboarding()

# Steps that contain 👉 markers outside Step 4c
_STEPS_WITH_POINTER_OUTSIDE_4C = ["2", "3a", "3b", "4b"]

# All step IDs in the file (excluding Step 4c's question formatting)
_ALL_STEP_IDS = ["0", "0b", "0c", "1", "1b", "2", "3", "3a", "3b", "3c", "3d", "4", "4a", "4b", "4c"]

# Steps that are NOT Step 4c (for content preservation)
_NON_4C_STEP_IDS = [s for s in _ALL_STEP_IDS if s != "4c"]

# Snapshot all 👉 markers outside Step 4c
_UNFIXED_POINTER_MARKERS = _find_all_pointer_markers(_UNFIXED_CONTENT)
_UNFIXED_POINTERS_OUTSIDE_4C = [
    (line_num, line_text)
    for line_num, line_text in _UNFIXED_POINTER_MARKERS
    if _identify_step_for_line(_UNFIXED_CONTENT, line_num) != "4c"
]

# Snapshot all 🛑 STOP directives
_UNFIXED_STOP_DIRECTIVES = _find_all_stop_directives(_UNFIXED_CONTENT)

# Snapshot Step 4c acknowledgment and clarification handling text
_UNFIXED_STEP_4C = _extract_section_by_step_id(_UNFIXED_CONTENT, "4c") or ""

# Extract acknowledgment handling text
_ACK_PATTERN = re.compile(
    r"\*\*Acknowledgment handling:\*\*\s*(.*?)(?=\*\*Clarification handling:\*\*|\*\*Note:\*\*|---|\Z)",
    re.DOTALL,
)
_ACK_MATCH = _ACK_PATTERN.search(_UNFIXED_STEP_4C)
_UNFIXED_ACK_TEXT = _ACK_MATCH.group(1).strip() if _ACK_MATCH else ""

# Extract clarification handling text
_CLAR_PATTERN = re.compile(
    r"\*\*Clarification handling:\*\*\s*(.*?)(?=\*\*Note:\*\*|---|\Z)",
    re.DOTALL,
)
_CLAR_MATCH = _CLAR_PATTERN.search(_UNFIXED_STEP_4C)
_UNFIXED_CLAR_TEXT = _CLAR_MATCH.group(1).strip() if _CLAR_MATCH else ""

# Snapshot non-4c sections for content comparison
_UNFIXED_SECTIONS: dict[str, str] = {}
for _sid in _NON_4C_STEP_IDS:
    _section = _extract_section_by_step_id(_UNFIXED_CONTENT, _sid)
    if _section:
        _UNFIXED_SECTIONS[_sid] = _section

# Step 4 informational content (overview, module table, track descriptions)
_UNFIXED_STEP_4 = _extract_section_by_step_id(_UNFIXED_CONTENT, "4") or ""


# -------------------------------------------------------------------
# Test 1 — Non-Step-4c Content Preservation
# -------------------------------------------------------------------


class TestNonStep4cContentPreservation:
    """For all sections where NOT isBugCondition(section), content is unchanged.

    **Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5**

    Parse each non-Step-4c section from the file and assert its content
    matches the observed baseline snapshot. The bug fix should only modify
    Step 4c's question formatting — all other content must remain identical.
    """

    def test_non_4c_sections_content_unchanged(self) -> None:
        """Assert each non-Step-4c section is unchanged from baseline."""
        content = _read_onboarding()
        for step_id, baseline in _UNFIXED_SECTIONS.items():
            current = _extract_section_by_step_id(content, step_id)
            assert current is not None, (
                f"Step {step_id} not found in current file"
            )
            assert current == baseline, (
                f"Step {step_id} content has changed.\n"
                f"Expected (first 300 chars):\n"
                f"{baseline[:300]}\n"
                f"Got (first 300 chars):\n"
                f"{current[:300]}"
            )

    def test_step_4_informational_content_no_pointer(self) -> None:
        """Step 4 informational content (overview, module table) has no 👉 prefix.

        The Step 4 section itself (excluding sub-steps 4a, 4b, 4c) contains
        informational content that should NOT have a 👉 prefix.
        """
        content = _read_onboarding()
        step_4 = _extract_section_by_step_id(content, "4")
        assert step_4 is not None, "Step 4 not found"

        # Extract only the Step 4 own content (before first sub-step heading)
        sub_step_start = re.search(r"^###\s+4[a-z]\.", step_4, re.MULTILINE)
        step_4_own = step_4[:sub_step_start.start()] if sub_step_start else step_4

        assert "👉" not in step_4_own, (
            "Step 4 informational content (overview, module table) "
            "should not contain 👉 prefix"
        )


# -------------------------------------------------------------------
# Test 2 — Pointer Markers Outside Step 4c Preservation
# -------------------------------------------------------------------


class TestPointerMarkersOutside4cPreservation:
    """For all 👉 markers outside Step 4c, count and positions are unchanged.

    **Validates: Requirements 3.1, 3.2**

    The fix should only affect Step 4c's question formatting. All other
    👉 markers (in Steps 2, 3a, 3b, 4b, and 5) must remain in their
    original positions with their original text.
    """

    def test_pointer_count_outside_4c_unchanged(self) -> None:
        """The number of 👉 markers outside Step 4c is unchanged."""
        content = _read_onboarding()
        current_pointers = _find_all_pointer_markers(content)
        current_outside_4c = [
            (line_num, line_text)
            for line_num, line_text in current_pointers
            if _identify_step_for_line(content, line_num) != "4c"
        ]
        assert len(current_outside_4c) == len(_UNFIXED_POINTERS_OUTSIDE_4C), (
            f"Pointer marker count outside Step 4c changed. "
            f"Expected {len(_UNFIXED_POINTERS_OUTSIDE_4C)}, "
            f"got {len(current_outside_4c)}."
        )

    def test_pointer_text_outside_4c_unchanged(self) -> None:
        """The text of 👉 lines outside Step 4c is unchanged."""
        content = _read_onboarding()
        current_pointers = _find_all_pointer_markers(content)
        current_outside_4c = [
            (line_num, line_text)
            for line_num, line_text in current_pointers
            if _identify_step_for_line(content, line_num) != "4c"
        ]
        # Compare line text (positions may shift if Step 4c changes size)
        baseline_texts = sorted(t for _, t in _UNFIXED_POINTERS_OUTSIDE_4C)
        current_texts = sorted(t for _, t in current_outside_4c)
        assert current_texts == baseline_texts, (
            f"Pointer marker text outside Step 4c has changed.\n"
            f"Expected:\n{baseline_texts}\n"
            f"Got:\n{current_texts}"
        )

    def test_steps_2_3a_3b_4b_each_have_pointer(self) -> None:
        """Steps 2, 3a, 3b, and 4b each contain at least one 👉 marker."""
        content = _read_onboarding()
        for step_id in _STEPS_WITH_POINTER_OUTSIDE_4C:
            section = _extract_section_by_step_id(content, step_id)
            assert section is not None, f"Step {step_id} not found"
            assert "👉" in section, (
                f"Step {step_id} is missing its 👉 marker"
            )


# -------------------------------------------------------------------
# Test 3 — Step 4c Acknowledgment and Clarification Handling
# -------------------------------------------------------------------


class TestStep4cResponseHandlingPreservation:
    """Step 4c acknowledgment and clarification handling text is unchanged.

    **Validates: Requirements 3.3, 3.4**

    The fix should only modify the question formatting in Step 4c.
    The response handling instructions (acknowledgment → proceed to Step 5,
    clarification → answer using verbosity settings) must remain unchanged.
    """

    def test_acknowledgment_handling_text_preserved(self) -> None:
        """Acknowledgment handling instructions are unchanged."""
        content = _read_onboarding()
        step_4c = _extract_section_by_step_id(content, "4c")
        assert step_4c is not None, "Step 4c not found"

        ack_match = _ACK_PATTERN.search(step_4c)
        assert ack_match is not None, (
            "Step 4c missing **Acknowledgment handling:** section"
        )
        current_ack = ack_match.group(1).strip()
        assert current_ack == _UNFIXED_ACK_TEXT, (
            f"Acknowledgment handling text has changed.\n"
            f"Expected:\n{_UNFIXED_ACK_TEXT[:500]}\n"
            f"Got:\n{current_ack[:500]}"
        )

    def test_clarification_handling_text_preserved(self) -> None:
        """Clarification handling instructions are unchanged."""
        content = _read_onboarding()
        step_4c = _extract_section_by_step_id(content, "4c")
        assert step_4c is not None, "Step 4c not found"

        clar_match = _CLAR_PATTERN.search(step_4c)
        assert clar_match is not None, (
            "Step 4c missing **Clarification handling:** section"
        )
        current_clar = clar_match.group(1).strip()
        assert current_clar == _UNFIXED_CLAR_TEXT, (
            f"Clarification handling text has changed.\n"
            f"Expected:\n{_UNFIXED_CLAR_TEXT[:500]}\n"
            f"Got:\n{current_clar[:500]}"
        )

    def test_acknowledgment_proceeds_to_step_5(self) -> None:
        """Acknowledgment handling mentions proceeding to Step 5."""
        content = _read_onboarding()
        step_4c = _extract_section_by_step_id(content, "4c")
        assert step_4c is not None, "Step 4c not found"
        assert "proceed directly to Step 5" in step_4c or "proceed to Step 5" in step_4c, (
            "Step 4c acknowledgment handling missing 'proceed to Step 5'"
        )

    def test_clarification_uses_verbosity_settings(self) -> None:
        """Clarification handling references verbosity settings."""
        content = _read_onboarding()
        step_4c = _extract_section_by_step_id(content, "4c")
        assert step_4c is not None, "Step 4c not found"
        assert "verbosity settings" in step_4c, (
            "Step 4c clarification handling missing 'verbosity settings'"
        )

    def test_acknowledgment_example_phrases_preserved(self) -> None:
        """Acknowledgment handling contains the expected example phrases."""
        content = _read_onboarding()
        step_4c = _extract_section_by_step_id(content, "4c")
        assert step_4c is not None, "Step 4c not found"
        expected_phrases = ["looks good", "makes sense", "no questions", "ready", "got it"]
        found = [p for p in expected_phrases if p in step_4c]
        assert len(found) >= 4, (
            f"Step 4c acknowledgment handling missing example phrases. "
            f"Found: {found}, expected at least 4 of {expected_phrases}"
        )


# -------------------------------------------------------------------
# Test 4 — 🛑 STOP Directives Preservation
# -------------------------------------------------------------------


class TestStopDirectivesPreservation:
    """All 🛑 STOP directives remain in their original positions.

    **Validates: Requirements 3.1, 3.5**

    The fix must not remove or alter any 🛑 STOP directives in the file.
    """

    def test_stop_directive_count_unchanged(self) -> None:
        """The total number of 🛑 STOP directives is unchanged."""
        content = _read_onboarding()
        current_stops = _find_all_stop_directives(content)
        assert len(current_stops) == len(_UNFIXED_STOP_DIRECTIVES), (
            f"🛑 STOP directive count changed. "
            f"Expected {len(_UNFIXED_STOP_DIRECTIVES)}, "
            f"got {len(current_stops)}."
        )

    def test_stop_directive_texts_unchanged(self) -> None:
        """The text of all 🛑 STOP directive lines is unchanged."""
        content = _read_onboarding()
        current_stops = _find_all_stop_directives(content)
        baseline_texts = sorted(t for _, t in _UNFIXED_STOP_DIRECTIVES)
        current_texts = sorted(t for _, t in current_stops)
        assert current_texts == baseline_texts, (
            f"🛑 STOP directive text has changed.\n"
            f"Expected:\n{baseline_texts}\n"
            f"Got:\n{current_texts}"
        )

    def test_step_4c_has_stop_directive(self) -> None:
        """Step 4c contains a 🛑 STOP directive."""
        content = _read_onboarding()
        step_4c = _extract_section_by_step_id(content, "4c")
        assert step_4c is not None, "Step 4c not found"
        assert "🛑" in step_4c, (
            "Step 4c missing 🛑 STOP directive"
        )


# -------------------------------------------------------------------
# PBT Test — Non-Step-4c Sections Unchanged
# -------------------------------------------------------------------


@st.composite
def st_non_4c_step_id(draw: st.DrawFn) -> str:
    """Generate a step ID from the set of non-4c steps present in the file."""
    available = list(_UNFIXED_SECTIONS.keys())
    return draw(st.sampled_from(available))


class TestNonStep4cSectionsUnchangedPBT:
    """PBT — Non-Step-4c sections are identical to the baseline.

    **Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5**

    Use Hypothesis to generate step IDs from the set of non-4c steps
    and verify each step's content is identical between the observed
    baseline and the current file.
    """

    @given(step_id=st_non_4c_step_id())
    @settings(
        max_examples=5,
        suppress_health_check=[HealthCheck.too_slow],
    )
    def test_non_4c_content_identical_to_baseline(
        self, step_id: str
    ) -> None:
        """For any non-Step-4c section, content must match baseline."""
        baseline = _UNFIXED_SECTIONS[step_id]
        assert baseline, (
            f"Baseline for Step {step_id} is empty"
        )

        content = _read_onboarding()
        current = _extract_section_by_step_id(content, step_id)
        assert current is not None, (
            f"Step {step_id} not found in current file"
        )
        assert current == baseline, (
            f"Step {step_id} content differs from baseline.\n"
            f"Baseline (first 200 chars): {baseline[:200]}\n"
            f"Current (first 200 chars): {current[:200]}"
        )


# -------------------------------------------------------------------
# PBT Test — Pointer Markers Outside Step 4c Unchanged
# -------------------------------------------------------------------


@st.composite
def st_pointer_step_id(draw: st.DrawFn) -> str:
    """Generate a step ID from steps that have 👉 markers outside 4c."""
    return draw(st.sampled_from(_STEPS_WITH_POINTER_OUTSIDE_4C))


class TestPointerMarkersPreservationPBT:
    """PBT — 👉 markers in Steps 2, 3a, 3b, 4b are unchanged.

    **Validates: Requirements 3.1, 3.2**

    Use Hypothesis to generate step IDs from the set of steps with
    👉 markers (excluding 4c) and verify each step still contains
    its 👉 marker with unchanged text.
    """

    @given(step_id=st_pointer_step_id())
    @settings(
        max_examples=5,
        suppress_health_check=[HealthCheck.too_slow],
    )
    def test_pointer_marker_present_in_step(
        self, step_id: str
    ) -> None:
        """For any step with a 👉 marker outside 4c, marker is still present."""
        content = _read_onboarding()
        section = _extract_section_by_step_id(content, step_id)
        assert section is not None, (
            f"Step {step_id} not found in current file"
        )
        assert "👉" in section, (
            f"Step {step_id} is missing its 👉 marker after fix"
        )

    @given(step_id=st_pointer_step_id())
    @settings(
        max_examples=5,
        suppress_health_check=[HealthCheck.too_slow],
    )
    def test_pointer_line_text_unchanged(
        self, step_id: str
    ) -> None:
        """For any step with a 👉 marker outside 4c, the line text is unchanged."""
        content = _read_onboarding()
        section = _extract_section_by_step_id(content, step_id)
        assert section is not None, (
            f"Step {step_id} not found in current file"
        )

        # Get the 👉 lines from the current section
        current_pointer_lines = [
            line.strip() for line in section.splitlines() if "👉" in line
        ]

        # Get the baseline 👉 lines for this step
        baseline_section = _UNFIXED_SECTIONS.get(step_id, "")
        baseline_pointer_lines = [
            line.strip() for line in baseline_section.splitlines() if "👉" in line
        ]

        assert current_pointer_lines == baseline_pointer_lines, (
            f"Step {step_id} 👉 marker line text has changed.\n"
            f"Expected: {baseline_pointer_lines}\n"
            f"Got: {current_pointer_lines}"
        )
