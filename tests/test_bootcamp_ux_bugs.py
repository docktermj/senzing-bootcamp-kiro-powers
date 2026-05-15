"""
Bug condition exploration tests for Senzing Bootcamp UX steering file defects.

These tests encode the EXPECTED (fixed) behavior. They are designed to FAIL on
the current unfixed steering files, confirming the bugs exist.

Validates: Requirements 1.1, 1.2, 1.3, 1.4
"""

import re
from pathlib import Path

import pytest

STEERING_DIR = Path("senzing-bootcamp/steering")

MODULE_03 = STEERING_DIR / "module-03-system-verification.md"
MODULE_TRANSITIONS = STEERING_DIR / "module-transitions.md"
MODULE_COMPLETION = STEERING_DIR / "module-completion.md"


@pytest.fixture
def module_03_content():
    return MODULE_03.read_text()


@pytest.fixture
def module_transitions_content():
    return MODULE_TRANSITIONS.read_text()


@pytest.fixture
def module_completion_content():
    return MODULE_COMPLETION.read_text()


# ---------------------------------------------------------------------------
# Bug 1 — Visualization step ordering
# NOTE: The original TestBug1VisualizationStepOrdering class validated UX
# behavior specific to the old "Quick Demo" Module 3. The module was
# redesigned as deterministic TruthSet verification; visualization is now
# handled by the `enforce-visualization-offers` hook instead of inline
# workflow steps. These tests no longer apply and have been removed.
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Bug 2 — Missing module start banner (module-transitions.md)
# Validates: Requirements 1.3, 2.3
# ---------------------------------------------------------------------------

class TestBug2ModuleStartBanner:
    """module-transitions.md must contain a Module Start Banner section with
    a bold banner template using ━━━ borders and 🚀🚀🚀 emojis."""

    def test_banner_section_exists(self, module_transitions_content):
        """The file must contain a 'Module Start Banner' section."""
        assert re.search(
            r"(?i)#.*module\s+start\s+banner", module_transitions_content
        ), "No 'Module Start Banner' section found in module-transitions.md"

    def test_banner_template_format(self, module_transitions_content):
        """The banner template must include ━━━ line borders and 🚀🚀🚀 emojis."""
        assert "━━━" in module_transitions_content, (
            "Banner template missing ━━━ line borders"
        )
        assert "🚀🚀🚀" in module_transitions_content, (
            "Banner template missing 🚀🚀🚀 emojis"
        )

    def test_banner_before_journey_map(self, module_transitions_content):
        """The banner section must appear before the Journey Map section."""
        banner_pos = re.search(
            r"(?i)#.*module\s+start\s+banner", module_transitions_content
        )
        journey_pos = re.search(
            r"(?i)#.*journey\s+map", module_transitions_content
        )
        assert banner_pos is not None, "Module Start Banner section not found"
        assert journey_pos is not None, "Journey Map section not found"
        assert banner_pos.start() < journey_pos.start(), (
            "Module Start Banner must appear before the Journey Map section"
        )


# ---------------------------------------------------------------------------
# Bug 3 — Non-tabular journey map (module-transitions.md)
# Validates: Requirements 1.4, 2.4
# ---------------------------------------------------------------------------

class TestBug3TabularJourneyMap:
    """The journey map section must contain a markdown table with
    Module, Name, Status columns and proper status icons."""

    def _journey_section(self, content: str) -> str:
        """Extract the Journey Map section text."""
        match = re.search(
            r"(?i)##\s*journey\s+map.*?(?=\n##\s|\Z)", content, re.DOTALL
        )
        assert match, "Journey Map section not found"
        return match.group()

    def test_journey_map_has_table_header(self, module_transitions_content):
        """Journey map must contain a markdown table with
        '| Module | Name | Status |' header."""
        section = self._journey_section(module_transitions_content)
        assert re.search(
            r"\|\s*Module\s*\|\s*Name\s*\|\s*Status\s*\|", section
        ), "Journey map section missing markdown table with '| Module | Name | Status |' header"

    def test_journey_map_has_status_icons(self, module_transitions_content):
        """Journey map section must contain ✅, 🔄, and ⬜ status icons."""
        section = self._journey_section(module_transitions_content)
        assert "✅" in section, "Journey map missing ✅ (completed) icon"
        assert "🔄" in section, "Journey map missing 🔄 (current) icon"
        assert "⬜" in section, "Journey map missing ⬜ (upcoming) icon"


# ---------------------------------------------------------------------------
# Bug 4 — Vague Explore option (module-completion.md)
# Validates: Requirements 1.2, 2.2
# ---------------------------------------------------------------------------

class TestBug4VagueExploreOption:
    """The Explore option must mention visualization, entity examination,
    or attribute search for Module 3, and a Module 3 special-case note
    must exist."""

    def test_explore_mentions_visualization(self, module_completion_content):
        """The Explore option must mention visualization, entity examination,
        or attribute search."""
        assert re.search(
            r"(?i)(visualiz|entity|entities|match\s+explanation|attribute\s+search|search\s+by\s+attribute)",
            module_completion_content,
        ), (
            "Explore option does not mention visualization, entity examination, "
            "or attribute search"
        )

    def test_module3_special_case_note(self, module_completion_content):
        """A Module 3 special-case note must exist in the next-step options
        section."""
        assert re.search(
            r"(?i)module\s+3\s+special\s+case", module_completion_content
        ), "No Module 3 special-case note found in the next-step options section"
