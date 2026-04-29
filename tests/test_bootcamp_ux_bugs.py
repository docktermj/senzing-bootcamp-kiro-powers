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

MODULE_03 = STEERING_DIR / "module-03-quick-demo.md"
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
# Bug 1 — Visualization step ordering (module-03-quick-demo.md)
# Validates: Requirements 1.1, 2.1
# ---------------------------------------------------------------------------

class TestBug1VisualizationStepOrdering:
    """The visualization offer must be its own numbered Phase 2 step,
    sequenced BEFORE the module-close step."""

    def _phase2_steps(self, content: str) -> list[tuple[int, str]]:
        """Return (step_number, step_text) pairs from Phase 2."""
        phase2_match = re.search(r"## Phase 2.*?(?=## |$)", content, re.DOTALL)
        assert phase2_match, "Phase 2 section not found"
        phase2 = phase2_match.group()
        # Match numbered steps like "1. **...**" or "1. ..."
        return [
            (int(m.group(1)), m.group(2))
            for m in re.finditer(r"^(\d+)\.\s+(.+?)(?=\n\d+\.\s|\Z)", phase2, re.MULTILINE | re.DOTALL)
        ]

    def test_visualization_is_own_numbered_step(self, module_03_content):
        """Visualization offer must be a separate numbered step, not a
        sub-point of the 'Explain results' step."""
        steps = self._phase2_steps(module_03_content)
        # Find a step whose primary text is about offering visualization
        # (not one where visualization is buried as a sub-point of another step)
        viz_steps = [
            (num, txt) for num, txt in steps
            if re.search(r"(?i)(offer\s+visualization|create\s+a\s+web\s+page)", txt)
            and not re.search(r"(?i)^.*explain\s+results", txt[:80])
        ]
        assert viz_steps, (
            "No standalone numbered step found for the visualization offer. "
            "It appears to be embedded as a sub-point of another step."
        )

    def test_visualization_step_before_module_close(self, module_03_content):
        """The visualization step number must be less than the module-close
        step number."""
        steps = self._phase2_steps(module_03_content)

        viz_num = None
        close_num = None
        for num, txt in steps:
            if re.search(r"(?i)(offer\s+visualization|create\s+a\s+web\s+page)", txt) \
               and not re.search(r"(?i)^.*explain\s+results", txt[:80]):
                viz_num = num
            if re.search(r"(?i)close\s+module\s+3", txt):
                close_num = num

        assert viz_num is not None, "Visualization step not found as its own step"
        assert close_num is not None, "Module close step not found"
        assert viz_num < close_num, (
            f"Visualization step ({viz_num}) must come before module close step ({close_num})"
        )

    def test_visualization_must_complete_before_close(self, module_03_content):
        """The file must contain instruction text requiring visualization to
        complete before module close."""
        assert re.search(
            r"(?i)must\s+complete\s+before\s+(closing|close)", module_03_content
        ) or re.search(
            r"(?i)MUST\s+complete\s+before\s+closing", module_03_content
        ), (
            "Missing instruction requiring visualization to complete before "
            "closing the module."
        )


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
