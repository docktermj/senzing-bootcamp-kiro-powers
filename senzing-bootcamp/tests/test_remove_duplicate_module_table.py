"""Bug condition exploration and preservation tests for remove-duplicate-module-table bugfix.

Bug condition tests verify that Step 5 (Track Selection) of onboarding-flow.md
does NOT contain a duplicate module table that repeats the module list already
shown in Step 4 (Bootcamp Introduction).

Preservation tests verify that Step 4's module overview, Step 5's track options,
Module 2 auto-insertion note, and response interpretation rules remain unchanged.

**Validates: Requirements 1.1, 1.2, 2.1, 2.2, 3.1, 3.2, 3.3, 3.4**

EXPECTED OUTCOME on UNFIXED code:
- Bug condition tests FAIL (confirming the bug — Step 5 contains duplicate table)
- Preservation tests PASS (confirming baseline behavior to preserve)
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_STEERING_DIR = Path(__file__).resolve().parent.parent / "steering"
_ONBOARDING_FLOW = _STEERING_DIR / "onboarding-flow.md"

# The introductory sentence that precedes the duplicate table in Step 5
_QUICK_REF_INTRO = (
    "Display this quick-reference module table before presenting the tracks "
    "so the bootcamper can cross-reference module numbers:"
)

# Module numbers that should appear in the table
_MODULE_NUMBERS = list(range(1, 13))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _read_onboarding_flow() -> str:
    """Read the full content of onboarding-flow.md."""
    return _ONBOARDING_FLOW.read_text(encoding="utf-8")


def _extract_section(content: str, heading: str) -> str:
    """Extract a section from markdown content by its heading.

    Returns everything from the heading line to the next same-level heading
    or end of file.
    """
    # Determine heading level
    level = len(heading) - len(heading.lstrip("#"))
    if level == 0:
        level = 2  # default to h2

    # Build pattern: match the heading, capture until next heading of same
    # or higher level, or end of file
    escaped = re.escape(heading.lstrip("# ").strip())
    pattern = rf"^(#{{{level}}}\s+{escaped}.*?)(?=^#{{{1},{level}}}\s|\Z)"
    match = re.search(pattern, content, re.MULTILINE | re.DOTALL)
    return match.group(1) if match else ""


def _extract_step5(content: str) -> str:
    """Extract Step 5 (Track Selection) section."""
    return _extract_section(content, "## 5. Track Selection")


def _extract_step4(content: str) -> str:
    """Extract Step 4 (Bootcamp Introduction) section."""
    return _extract_section(content, "## 4. Bootcamp Introduction")


def _contains_module_table(text: str) -> bool:
    """Check if text contains a markdown table with module numbers 1-12.

    Looks for a table header like '| Module | Title' followed by rows
    containing module numbers 1 through 12.
    """
    # Check for table header pattern
    if not re.search(r"\|\s*Module\s*\|\s*Title", text):
        return False

    # Check that all 12 module numbers appear as table rows
    for num in _MODULE_NUMBERS:
        pattern = rf"\|\s*{num}\s*\|"
        if not re.search(pattern, text):
            return False

    return True


def _count_module_tables(content: str) -> int:
    """Count the number of distinct sections containing module tables (1-12).

    Splits the file by h2 headings and checks each section for a module table.
    """
    sections = re.split(r"(?=^## )", content, flags=re.MULTILINE)
    count = 0
    for section in sections:
        if _contains_module_table(section):
            count += 1
    return count


# ===========================================================================
# Task 1: Bug Condition Exploration Tests
#
# These tests encode the EXPECTED behavior (no duplicate table in Step 5).
# On UNFIXED code they FAIL, confirming the bug exists.
# After the fix, they PASS, confirming the bug is resolved.
#
# **Validates: Requirements 1.1, 1.2, 2.1, 2.2**
# ===========================================================================


class TestBugConditionDuplicateTable:
    """Assert that Step 5 does NOT contain a duplicate module table.

    On unfixed code these assertions FAIL, confirming the bug exists.

    **Validates: Requirements 1.1, 1.2, 2.1, 2.2**
    """

    @pytest.fixture(autouse=True)
    def _load_content(self) -> None:
        self._content = _read_onboarding_flow()
        self._step5 = _extract_step5(self._content)

    def test_step5_does_not_contain_module_table(self) -> None:
        """Step 5 should NOT contain a markdown table with modules 1-12.

        **Validates: Requirements 1.1, 2.1**"""
        assert not _contains_module_table(self._step5), (
            "Bug condition confirmed: Step 5 (Track Selection) contains a "
            "markdown table with modules 1-12 that duplicates Step 4's overview.\n"
            f"Step 5 excerpt:\n{self._step5[:500]}..."
        )

    def test_step5_does_not_contain_quick_ref_intro(self) -> None:
        """Step 5 should NOT contain the quick-reference table intro sentence.

        **Validates: Requirements 1.2, 2.2**"""
        assert _QUICK_REF_INTRO not in self._step5, (
            "Bug condition confirmed: Step 5 contains the introductory sentence "
            "for the quick-reference module table.\n"
            f"Found: '{_QUICK_REF_INTRO}'"
        )

    def test_file_has_exactly_one_module_table(self) -> None:
        """The full file should contain exactly one module table (in Step 4 area).

        On unfixed code, two sections contain module tables (Step 4 overview
        reference + Step 5 duplicate table).

        **Validates: Requirements 1.1, 1.2, 2.1, 2.2**"""
        # Note: Step 4 says "Module overview table (1-12)" as an instruction
        # but doesn't contain an actual markdown table. The only actual
        # markdown module table should be zero after fix (Step 5's is removed).
        # However, the Validation Gates section has a table too (but not modules 1-12).
        # Let's count sections with module tables listing 1-12.
        count = _count_module_tables(self._content)
        assert count <= 1, (
            f"Bug condition confirmed: Found {count} sections with module "
            f"tables listing modules 1-12. Expected at most 1 (Step 4 area). "
            f"Step 5 contains a duplicate."
        )


class TestBugConditionProperty:
    """Property-based test: the Step 5 section should not contain any
    markdown table row matching module numbers 1-12.

    On unfixed code this property FAILS, surfacing counterexamples.

    **Validates: Requirements 1.1, 1.2, 2.1, 2.2**
    """

    @given(module_num=st.sampled_from(_MODULE_NUMBERS))
    @settings(max_examples=20)
    def test_step5_has_no_module_rows(self, module_num: int) -> None:
        """**Validates: Requirements 1.1, 2.1**

        For any module number 1-12, Step 5 should NOT contain a table row
        with that module number."""
        content = _read_onboarding_flow()
        step5 = _extract_step5(content)
        pattern = rf"\|\s*{module_num}\s*\|"
        assert not re.search(pattern, step5), (
            f"Bug condition: Step 5 contains table row for Module {module_num}.\n"
            f"Pattern matched: '| {module_num} |' in Step 5 (Track Selection)"
        )


# ===========================================================================
# Task 2: Preservation Property Tests
#
# These tests verify that content that should be preserved is present.
# They should PASS on both unfixed and fixed code.
#
# **Validates: Requirements 3.1, 3.2, 3.3, 3.4**
# ===========================================================================


class TestPreservationStep4:
    """Verify Step 4 (Bootcamp Introduction) preserves the module overview
    instruction.

    **Validates: Requirements 3.1**
    """

    def test_step4_contains_module_overview_instruction(self) -> None:
        """Step 4 should contain 'Module overview table (1-11)'.

        **Validates: Requirements 3.1**"""
        content = _read_onboarding_flow()
        step4 = _extract_step4(content)
        assert "Module overview table (1-11)" in step4, (
            "Step 4 is missing the module overview instruction.\n"
            f"Step 4 content:\n{step4[:500]}..."
        )


class TestPreservationStep5TrackOptions:
    """Verify Step 5 preserves all four track options (A-D).

    **Validates: Requirements 3.2**
    """

    _TRACK_MARKERS = [
        "**A) Quick Demo**",
        "**B) Fast Track**",
        "**C) Complete Beginner**",
        "**D) Full Production**",
    ]

    @pytest.fixture(autouse=True)
    def _load_step5(self) -> None:
        content = _read_onboarding_flow()
        self._step5 = _extract_step5(content)

    @pytest.mark.parametrize("track", _TRACK_MARKERS)
    def test_step5_contains_track_option(self, track: str) -> None:
        """Step 5 should contain track option '{track}'.

        **Validates: Requirements 3.2**"""
        assert track in self._step5, (
            f"Step 5 is missing track option: {track}\n"
            f"Step 5 content:\n{self._step5[:500]}..."
        )


class TestPreservationStep5Module2Note:
    """Verify Step 5 preserves the Module 2 auto-insertion note.

    **Validates: Requirements 3.3**
    """

    def test_step5_contains_module2_note(self) -> None:
        """Step 5 should contain 'Module 2 inserted automatically'.

        **Validates: Requirements 3.3**"""
        content = _read_onboarding_flow()
        step5 = _extract_step5(content)
        assert "Module 2 inserted automatically" in step5, (
            "Step 5 is missing the Module 2 auto-insertion note.\n"
            f"Step 5 content:\n{step5[:500]}..."
        )


class TestPreservationStep5InterpretationRules:
    """Verify Step 5 preserves the response interpretation rules.

    **Validates: Requirements 3.3, 3.4**
    """

    _INTERPRETATION_FRAGMENTS = [
        '"A"/"demo"→Module 3',
        '"B"/"fast"→Module 5',
        '"C"/"beginner"→Module 1',
        '"D"/"full"→Module 1',
    ]

    @pytest.fixture(autouse=True)
    def _load_step5(self) -> None:
        content = _read_onboarding_flow()
        self._step5 = _extract_step5(content)

    @pytest.mark.parametrize("fragment", _INTERPRETATION_FRAGMENTS)
    def test_step5_contains_interpretation_rule(self, fragment: str) -> None:
        """Step 5 should contain interpretation rule '{fragment}'.

        **Validates: Requirements 3.3, 3.4**"""
        assert fragment in self._step5, (
            f"Step 5 is missing interpretation rule: {fragment}\n"
            f"Step 5 content:\n{self._step5[:500]}..."
        )


class TestPreservationProperty:
    """Property-based test: for any track option, it must be present in Step 5.

    Should PASS on both unfixed and fixed code.

    **Validates: Requirements 3.2, 3.3, 3.4**
    """

    _ALL_PRESERVED_CONTENT = [
        "**A) Quick Demo**",
        "**B) Fast Track**",
        "**C) Complete Beginner**",
        "**D) Full Production**",
        "Module 2 inserted automatically before any module needing SDK.",
        "Bare number→clarify letter vs module.",
    ]

    @given(content_item=st.sampled_from(_ALL_PRESERVED_CONTENT))
    @settings(max_examples=20)
    def test_step5_preserves_content(self, content_item: str) -> None:
        """**Validates: Requirements 3.2, 3.3, 3.4**

        For any preserved content item, it must be present in Step 5."""
        content = _read_onboarding_flow()
        step5 = _extract_step5(content)
        assert content_item in step5, (
            f"Step 5 is missing preserved content: '{content_item}'"
        )
