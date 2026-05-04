"""Tests for the multi-language entity resolution guide.

Validates the guide's file structure, section headings, content accuracy,
cross-references from Module 5 steering, and README integration.

Correctness Properties (from design.md / requirements.md):
  4.1 Guide Structure — file exists, heading, required sections
  4.2 Content Validation — SGES examples, cross-script pairs, JSON validity,
      UTF-8 validity, Further Reading references
  4.3 Cross-Reference and README Integration — steering reference, README entry,
      documentation structure tree, key topic mentions
"""

from __future__ import annotations

import json
import re
from pathlib import Path

# ---------------------------------------------------------------------------
# Helpers — locate source-of-truth files
# ---------------------------------------------------------------------------

_BOOTCAMP_DIR = Path(__file__).resolve().parent.parent
_GUIDE_PATH = _BOOTCAMP_DIR / "docs" / "guides" / "MULTI_LANGUAGE_DATA.md"
_README_PATH = _BOOTCAMP_DIR / "docs" / "guides" / "README.md"
_STEERING_PATH = _BOOTCAMP_DIR / "steering" / "module-05-data-quality-mapping.md"


def _read_guide() -> str:
    """Return the full text of the multi-language guide."""
    return _GUIDE_PATH.read_text(encoding="utf-8")


def _read_readme() -> str:
    """Return the full text of the guides README."""
    return _README_PATH.read_text(encoding="utf-8")


def _read_steering() -> str:
    """Return the full text of the Module 5 steering file."""
    return _STEERING_PATH.read_text(encoding="utf-8")


def _extract_json_blocks(text: str) -> list[str]:
    """Extract all fenced JSON code blocks from Markdown text."""
    return re.findall(r"```json\s*\n(.*?)```", text, re.DOTALL)


# ---------------------------------------------------------------------------
# 4.2 Guide Structure Tests
# Validates: Requirements 1.1, 1.2, 1.3, 2.1, 3.1, 4.1, 5.1, 6.3
# ---------------------------------------------------------------------------


class TestGuideStructure:
    """4.2 — Guide file exists with correct structure and sections.

    **Validates: Requirements 1.1, 1.2, 1.3, 2.1, 3.1, 4.1, 5.1, 6.3**
    """

    def test_guide_file_exists(self) -> None:
        """The guide file must exist at docs/guides/MULTI_LANGUAGE_DATA.md."""
        assert _GUIDE_PATH.exists(), (
            f"Expected guide at {_GUIDE_PATH.relative_to(_BOOTCAMP_DIR)}"
        )

    def test_starts_with_level_one_heading(self) -> None:
        """The guide must open with a level-1 heading."""
        first_line = _read_guide().lstrip().split("\n", 1)[0]
        assert first_line.startswith("# "), (
            f"First line should be a level-1 heading, got: {first_line!r}"
        )

    def test_contains_required_section_headings(self) -> None:
        """The guide must contain all required section headings."""
        text = _read_guide().lower()
        required_sections = [
            "non-latin character support",
            "utf-8 encoding requirements",
            "transliteration and cross-script name matching",
            "multi-language data quality best practices",
            "further reading",
        ]
        for section in required_sections:
            assert section in text, (
                f"Missing required section heading: {section!r}"
            )


# ---------------------------------------------------------------------------
# 4.3 Content Validation Tests
# Validates: Requirements 2.4, 3.3, 4.3, 6.2, 6.3
# ---------------------------------------------------------------------------


class TestGuideContent:
    """4.3 — Guide content covers required topics accurately.

    **Validates: Requirements 2.4, 3.3, 4.3, 6.2, 6.3**
    """

    def test_json_block_with_non_ascii_and_sges_attributes(self) -> None:
        """At least one JSON code block must contain non-ASCII characters
        and SGES attributes (DATA_SOURCE, RECORD_ID, NAME_FULL)."""
        blocks = _extract_json_blocks(_read_guide())
        assert blocks, "Guide must contain at least one JSON code block"

        found = False
        for block in blocks:
            has_non_ascii = any(ord(ch) > 127 for ch in block)
            has_data_source = "DATA_SOURCE" in block
            has_record_id = "RECORD_ID" in block
            has_name_full = "NAME_FULL" in block
            if has_non_ascii and has_data_source and has_record_id and has_name_full:
                found = True
                break

        assert found, (
            "At least one JSON code block must contain non-ASCII characters "
            "and SGES attributes (DATA_SOURCE, RECORD_ID, NAME_FULL)"
        )

    def test_at_least_three_cross_script_examples(self) -> None:
        """At least three cross-script matching examples must exist with
        different script pairs."""
        text = _read_guide()
        # The guide uses "Example N:" headings for cross-script pairs
        example_headings = re.findall(
            r"###\s+Example\s+\d+.*?matching", text, re.IGNORECASE
        )
        assert len(example_headings) >= 3, (
            f"Expected >= 3 cross-script matching examples, "
            f"found {len(example_headings)}"
        )

    def test_further_reading_contains_search_docs(self) -> None:
        """The Further Reading section must contain search_docs references."""
        text = _read_guide()
        further_idx = text.lower().find("## further reading")
        assert further_idx != -1, "Guide must have a Further Reading section"
        further_section = text[further_idx:]
        assert "search_docs" in further_section, (
            "Further Reading section must reference search_docs"
        )

    def test_all_json_blocks_are_valid_json(self) -> None:
        """All JSON code blocks in the guide must be valid JSON."""
        blocks = _extract_json_blocks(_read_guide())
        assert blocks, "Guide must contain at least one JSON code block"

        for i, block in enumerate(blocks):
            try:
                json.loads(block)
            except json.JSONDecodeError as exc:
                raise AssertionError(
                    f"JSON code block {i + 1} is not valid JSON: {exc}\n"
                    f"Block content:\n{block[:200]}"
                ) from exc

    def test_guide_is_valid_utf8(self) -> None:
        """The guide file must be valid UTF-8."""
        raw = _GUIDE_PATH.read_bytes()
        try:
            raw.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise AssertionError(
                f"Guide file is not valid UTF-8: {exc}"
            ) from exc


# ---------------------------------------------------------------------------
# 4.4 Cross-Reference and README Integration Tests
# Validates: Requirements 7.1, 7.2, 7.3, 8.1, 8.2, 8.3
# ---------------------------------------------------------------------------


class TestCrossReferences:
    """4.4 — Module 5 steering and guides README reference the new guide.

    **Validates: Requirements 7.1, 7.2, 7.3, 8.1, 8.2, 8.3**
    """

    # -- Module 5 steering cross-reference --

    def test_steering_references_multi_language_guide(self) -> None:
        """Module 5 steering must reference MULTI_LANGUAGE_DATA.md as
        optional supplementary reading."""
        text = _read_steering()
        assert "MULTI_LANGUAGE_DATA.md" in text, (
            "Module 5 steering must reference MULTI_LANGUAGE_DATA.md"
        )

    # -- Guides README entry --

    def test_readme_contains_multi_language_entry_with_link(self) -> None:
        """The guides README must contain MULTI_LANGUAGE_DATA.md in the
        Reference Documentation section with a Markdown link."""
        text = _read_readme()
        ref_idx = text.lower().find("reference documentation")
        assert ref_idx != -1, (
            "README must have a Reference Documentation section"
        )
        ref_section = text[ref_idx:]
        assert "[MULTI_LANGUAGE_DATA.md](MULTI_LANGUAGE_DATA.md)" in ref_section, (
            "README Reference Documentation section must include a Markdown "
            "link to MULTI_LANGUAGE_DATA.md"
        )

    def test_readme_documentation_structure_includes_guide(self) -> None:
        """MULTI_LANGUAGE_DATA.md must appear in the Documentation Structure
        tree in the guides README."""
        text = _read_readme()
        struct_idx = text.lower().find("documentation structure")
        assert struct_idx != -1, (
            "README must have a Documentation Structure section"
        )
        structure_section = text[struct_idx:]
        assert "MULTI_LANGUAGE_DATA.md" in structure_section, (
            "Documentation Structure tree must include MULTI_LANGUAGE_DATA.md"
        )

    def test_readme_entry_mentions_key_topics(self) -> None:
        """The README entry description must mention key topics: non-Latin,
        UTF-8, and cross-script."""
        text = _read_readme()
        idx = text.find("MULTI_LANGUAGE_DATA.md")
        assert idx != -1, "README must contain MULTI_LANGUAGE_DATA.md"
        # Grab a generous window after the first occurrence for the description
        entry_window = text[idx:idx + 600].lower()
        assert "non-latin" in entry_window, (
            "README entry must mention non-Latin"
        )
        assert "utf-8" in entry_window, (
            "README entry must mention UTF-8"
        )
        assert "cross-script" in entry_window, (
            "README entry must mention cross-script"
        )
