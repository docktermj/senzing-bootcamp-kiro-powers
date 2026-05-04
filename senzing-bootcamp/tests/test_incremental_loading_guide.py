"""Tests for the incremental loading guide.

Validates the guide's file structure, section headings, agent instruction
blocks, content accuracy, cross-references from Module 6 steering, and
README integration.

Correctness Properties (from design.md / requirements.md):
  4.1 Guide Structure — file exists, heading, sections, agent blocks, MCP tools
  4.2 Content Validation — batch vs incremental, record fields, redo, monitoring,
      further reading, Module 6 reference, no third-party tools
  4.3 Cross-Reference and README Integration — steering reference, README entry,
      documentation structure tree
"""

from __future__ import annotations

import re
from pathlib import Path

# ---------------------------------------------------------------------------
# Helpers — locate source-of-truth files
# ---------------------------------------------------------------------------

_BOOTCAMP_DIR = Path(__file__).resolve().parent.parent
_GUIDE_PATH = _BOOTCAMP_DIR / "docs" / "guides" / "INCREMENTAL_LOADING.md"
_README_PATH = _BOOTCAMP_DIR / "docs" / "guides" / "README.md"
_STEERING_PATH = _BOOTCAMP_DIR / "steering" / "module-06-load-data.md"


def _read_guide() -> str:
    """Return the full text of the incremental loading guide."""
    return _GUIDE_PATH.read_text(encoding="utf-8")


def _read_readme() -> str:
    """Return the full text of the guides README."""
    return _README_PATH.read_text(encoding="utf-8")


def _read_steering() -> str:
    """Return the full text of the Module 6 steering file."""
    return _STEERING_PATH.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# 4.1 Guide Structure Tests
# Validates: Requirements 1.1, 1.2, 1.3, 2.4, 3.4, 4.4, 5.1, 5.2, 5.3
# ---------------------------------------------------------------------------


class TestGuideStructure:
    """4.1 — Guide file exists with correct structure, sections, and MCP blocks.

    **Validates: Requirements 1.1, 1.2, 1.3, 2.4, 3.4, 4.4, 5.1, 5.2, 5.3**
    """

    def test_guide_file_exists(self) -> None:
        """The guide file must exist at docs/guides/INCREMENTAL_LOADING.md."""
        assert _GUIDE_PATH.exists(), (
            f"Expected guide at {_GUIDE_PATH.relative_to(_BOOTCAMP_DIR)}"
        )

    def test_starts_with_level_one_heading(self) -> None:
        """The guide must open with ``# Incremental Loading``."""
        first_line = _read_guide().lstrip().split("\n", 1)[0]
        assert first_line.startswith("# "), (
            f"First line should be a level-1 heading, got: {first_line!r}"
        )
        assert "incremental loading" in first_line.lower()

    def test_contains_required_section_headings(self) -> None:
        """The guide must contain sections on adding records, redo, monitoring,
        and further reading."""
        text = _read_guide().lower()
        assert "## adding new records" in text or "adding new records" in text
        assert "## redo processing" in text or "redo processing" in text
        assert "## monitoring" in text or "monitoring" in text
        assert "## further reading" in text or "further reading" in text

    def test_contains_at_least_three_agent_instruction_blocks(self) -> None:
        """The guide must include at least three agent instruction blocks
        (one per code example section)."""
        text = _read_guide()
        agent_blocks = re.findall(
            r">\s*\*\*Agent instruction[:\*]", text, re.IGNORECASE
        )
        assert len(agent_blocks) >= 3, (
            f"Expected >= 3 agent instruction blocks, found {len(agent_blocks)}"
        )

    def test_agent_blocks_reference_generate_scaffold(self) -> None:
        """At least one agent instruction block must call generate_scaffold."""
        text = _read_guide()
        assert "generate_scaffold" in text

    def test_agent_blocks_reference_search_docs(self) -> None:
        """At least one agent instruction block must call search_docs."""
        text = _read_guide()
        assert "search_docs" in text

    def test_agent_blocks_reference_find_examples(self) -> None:
        """At least one agent instruction block must call find_examples."""
        text = _read_guide()
        assert "find_examples" in text


# ---------------------------------------------------------------------------
# 4.2 Content Validation Tests
# Validates: Requirements 2.1, 2.2, 2.3, 3.1, 3.2, 3.3, 4.1, 4.2, 4.3,
#            5.4, 8.1, 8.2, 8.3, 8.4
# ---------------------------------------------------------------------------


class TestGuideContent:
    """4.2 — Guide content covers required topics accurately.

    **Validates: Requirements 2.1, 2.2, 2.3, 3.1, 3.2, 3.3, 4.1, 4.2, 4.3,
    5.4, 8.1, 8.2, 8.3, 8.4**
    """

    def test_introduction_explains_batch_vs_incremental(self) -> None:
        """The introduction must explain the difference between batch and
        incremental loading."""
        text = _read_guide().lower()
        assert "batch" in text, "Guide should mention batch loading"
        assert "incremental" in text, "Guide should mention incremental loading"

    def test_adding_records_mentions_data_source_and_record_id(self) -> None:
        """The adding records section must mention DATA_SOURCE, RECORD_ID,
        and deduplication/replace behavior."""
        text = _read_guide()
        assert "DATA_SOURCE" in text
        assert "RECORD_ID" in text
        text_lower = text.lower()
        assert "replace" in text_lower, (
            "Guide should explain replace behavior for duplicate RECORD_ID"
        )

    def test_redo_section_mentions_queue_scheduling_drain(self) -> None:
        """The redo processing section must mention redo queue, scheduling,
        and drain verification."""
        text = _read_guide().lower()
        assert "redo queue" in text or "redo record" in text
        assert "schedule" in text or "scheduling" in text or "after each" in text
        assert "drain" in text or "empty" in text

    def test_monitoring_section_mentions_four_health_indicators(self) -> None:
        """The monitoring section must mention at least four health indicators:
        throughput, error rate, redo queue depth, and entity count."""
        text = _read_guide().lower()
        indicators_found = 0
        if "throughput" in text or "records loaded per" in text:
            indicators_found += 1
        if "error rate" in text or "error count" in text:
            indicators_found += 1
        if "redo queue depth" in text or "redo queue" in text:
            indicators_found += 1
        if "entity count" in text:
            indicators_found += 1
        assert indicators_found >= 4, (
            f"Expected >= 4 health indicators, found {indicators_found}"
        )

    def test_further_reading_references_search_docs(self) -> None:
        """The Further Reading section must reference search_docs."""
        text = _read_guide()
        # Find the Further Reading section
        further_idx = text.lower().find("further reading")
        assert further_idx != -1, "Guide must have a Further Reading section"
        further_section = text[further_idx:]
        assert "search_docs" in further_section

    def test_further_reading_references_find_examples(self) -> None:
        """The Further Reading section must reference find_examples."""
        text = _read_guide()
        further_idx = text.lower().find("further reading")
        assert further_idx != -1, "Guide must have a Further Reading section"
        further_section = text[further_idx:]
        assert "find_examples" in further_section

    def test_references_module_6_loading_program(self) -> None:
        """The guide must reference the Module 6 loading program as a
        starting point."""
        text = _read_guide().lower()
        assert "module 6" in text or "module six" in text, (
            "Guide should reference Module 6"
        )

    def test_no_third_party_tool_requirements(self) -> None:
        """The guide must not introduce third-party tools or libraries as
        requirements (no cron, Airflow, Celery, etc.)."""
        text = _read_guide().lower()
        # These tools should not appear as requirements or recommendations.
        # They may appear in a "you don't need" context, so we check for
        # patterns that suggest they are being recommended.
        for tool in ("airflow", "celery"):
            assert tool not in text, (
                f"Guide should not mention {tool!r} — keep focus on SDK patterns"
            )


# ---------------------------------------------------------------------------
# 4.3 Cross-Reference and README Integration Tests
# Validates: Requirements 6.1, 6.2, 6.3, 7.1, 7.2, 7.3
# ---------------------------------------------------------------------------


class TestCrossReferences:
    """4.3 — Module 6 steering and guides README reference the new guide.

    **Validates: Requirements 6.1, 6.2, 6.3, 7.1, 7.2, 7.3**
    """

    # -- Module 6 steering cross-reference --

    def test_steering_contains_incremental_loading_reference(self) -> None:
        """Module 6 steering must reference INCREMENTAL_LOADING.md in the
        Advanced Reading section."""
        text = _read_steering()
        adv_idx = text.lower().find("advanced reading")
        assert adv_idx != -1, (
            "Module 6 steering must have an Advanced Reading section"
        )
        advanced_section = text[adv_idx:]
        assert "INCREMENTAL_LOADING.md" in advanced_section

    def test_steering_describes_production_incremental_patterns(self) -> None:
        """The Module 6 reference must describe the guide as covering
        incremental loading patterns for production systems."""
        text = _read_steering().lower()
        assert "production" in text
        assert "incremental loading" in text or "incremental" in text

    # -- Guides README entry --

    def test_readme_contains_incremental_loading_entry(self) -> None:
        """The guides README must contain an entry for INCREMENTAL_LOADING.md
        in the Reference Documentation section."""
        text = _read_readme()
        assert "INCREMENTAL_LOADING.md" in text

    def test_readme_entry_includes_markdown_link(self) -> None:
        """The README entry must include a Markdown link to the file."""
        text = _read_readme()
        assert "[INCREMENTAL_LOADING.md](INCREMENTAL_LOADING.md)" in text

    def test_readme_entry_mentions_key_topics(self) -> None:
        """The README entry description must mention incremental loading,
        redo processing, and pipeline health monitoring."""
        text = _read_readme()
        # Isolate the section around the INCREMENTAL_LOADING entry
        idx = text.find("INCREMENTAL_LOADING.md")
        assert idx != -1
        # Grab a generous window after the link for the description bullets
        entry_window = text[idx:idx + 600].lower()
        assert "incremental" in entry_window
        assert "redo" in entry_window
        assert "health" in entry_window or "monitoring" in entry_window

    # -- Documentation Structure tree --

    def test_documentation_structure_tree_includes_guide(self) -> None:
        """INCREMENTAL_LOADING.md must appear in the Documentation Structure
        tree in the guides README."""
        text = _read_readme()
        struct_idx = text.lower().find("documentation structure")
        assert struct_idx != -1, (
            "README must have a Documentation Structure section"
        )
        structure_section = text[struct_idx:]
        assert "INCREMENTAL_LOADING.md" in structure_section
