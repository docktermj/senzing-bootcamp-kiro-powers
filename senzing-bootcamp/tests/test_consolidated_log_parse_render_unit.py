"""Unit tests for Consolidated_Log parsing and rendering.

Feature: journal-recap-consolidation — task 1.2.

Example-based and edge-case coverage for the parse/render pair added to
``senzing-bootcamp/scripts/completion_artifacts.py``:

    parse_recap_sections        splits a Consolidated_Log into structured
                                ParsedRecapSection objects, degrading gracefully
                                over missing subsections, empty fields, and
                                headings with or without a timestamp.
    render_recap_section        renders one structured section back to canonical
                                Markdown; it is the structural inverse of the
                                parser (design Property 1).
    _extract_journal_subsection parses the ### Journal block into JournalFields,
                                returning None when the subsection is absent.

The Hypothesis round-trip property (Property 1) is exercised separately in the
property suite; these tests pin concrete behavior and edge cases.

Validates: Requirements 1.3, 1.4, 1.6, 2.7, 13.1
"""

from __future__ import annotations

import sys
from pathlib import Path

_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

import completion_artifacts as planner  # noqa: E402

JournalFields = planner.JournalFields
ParsedRecapSection = planner.ParsedRecapSection
parse_recap_sections = planner.parse_recap_sections
render_recap_section = planner.render_recap_section
_extract_journal_subsection = planner._extract_journal_subsection


EM_DASH = "\u2014"


def _full_section_markdown() -> str:
    """Return a complete, canonical single-module Consolidated_Log section."""
    return (
        f"## Module 1: Business Problem {EM_DASH} 2025-01-10T10:12:00Z\n"
        "\n"
        "### Information Shared\n"
        "- Identified duplicate customers\n"
        "- Chose SQLite\n"
        "\n"
        "### Questions & Responses\n"
        "\n"
        "- **Q:** What is the goal?\n"
        "    - **R:** Resolve duplicate customer records\n"
        "\n"
        "### Actions Taken\n"
        "- Ran first demo\n"
        "\n"
        "### Duration\n"
        "1h 12m\n"
        "\n"
        "### Journal\n"
        "**What we did:** Framed the business problem\n"
        "**What was produced:** docs/problem.md\n"
        "**Why it matters:** Sets the baseline\n"
        "**Bootcamper's takeaway:** N/A\n"
        "\n"
        "---\n"
    )


def _render_all(sections: list) -> str:
    """Render every section and concatenate, as the workflow would."""
    return "".join(render_recap_section(section) for section in sections)


class TestParseRecapSections:
    """Structured parsing of the Consolidated_Log.

    Validates: Requirements 1.3, 1.4, 1.6
    """

    def test_parses_all_fields_of_a_full_section(self) -> None:
        """Every subsection is mapped to the matching structured field."""
        sections = parse_recap_sections(_full_section_markdown())
        assert len(sections) == 1
        section = sections[0]
        assert section.module_number == 1
        assert section.module_name == "Business Problem"
        assert section.timestamp == "2025-01-10T10:12:00Z"
        assert section.information_shared == [
            "Identified duplicate customers",
            "Chose SQLite",
        ]
        assert section.questions_responses == [
            ("What is the goal?", "Resolve duplicate customer records")
        ]
        assert section.actions_taken == ["Ran first demo"]
        assert section.duration == "1h 12m"
        assert section.journal == JournalFields(
            what_we_did="Framed the business problem",
            what_was_produced="docs/problem.md",
            why_it_matters="Sets the baseline",
            bootcamper_takeaway="N/A",
        )

    def test_ignores_header_block_and_returns_empty_without_headings(self) -> None:
        """Content with no ``## Module`` heading yields no sections."""
        assert parse_recap_sections("# Senzing Bootcamp Recap\n\ntext\n") == []

    def test_parses_multiple_sections_in_document_order(self) -> None:
        """Two module headings produce two sections in order."""
        content = (
            "# Senzing Bootcamp Recap\n\n"
            f"## Module 1: Intro {EM_DASH} t1\n\n### Information Shared\n- a\n\n---\n\n"
            f"## Module 8: Perf {EM_DASH} t8\n\n### Information Shared\n- b\n\n---\n"
        )
        sections = parse_recap_sections(content)
        assert [s.module_number for s in sections] == [1, 8]
        assert sections[0].information_shared == ["a"]
        assert sections[1].information_shared == ["b"]

    def test_heading_without_timestamp_yields_empty_timestamp(self) -> None:
        """A ``## Module N: Name`` heading (no em-dash) parses with empty timestamp."""
        sections = parse_recap_sections("## Module 5: Query\n\n### Actions Taken\n- x\n")
        assert sections[0].timestamp == ""
        assert sections[0].module_name == "Query"

    def test_missing_duration_yields_none(self) -> None:
        """An absent ``### Duration`` subsection leaves duration None."""
        sections = parse_recap_sections(
            f"## Module 3: Load {EM_DASH} t\n\n### Actions Taken\n- y\n"
        )
        assert sections[0].duration is None

    def test_empty_questions_responses_yields_no_pairs(self) -> None:
        """A ``- None`` Q&R body parses to zero pairs."""
        content = (
            f"## Module 4: Search {EM_DASH} t\n\n"
            "### Questions & Responses\n\n- None\n\n### Actions Taken\n- z\n"
        )
        assert parse_recap_sections(content)[0].questions_responses == []

    def test_multiline_response_folds_continuation_lines(self) -> None:
        """Indented continuation lines fold into the response text."""
        content = (
            f"## Module 2: Ingest {EM_DASH} t\n\n"
            "### Questions & Responses\n\n"
            "- **Q:** Why two files?\n"
            "    - **R:** line one\n"
            "    line two\n"
        )
        pairs = parse_recap_sections(content)[0].questions_responses
        assert pairs == [("Why two files?", "line one\nline two")]


class TestExtractJournalSubsection:
    """Direct coverage of the ``### Journal`` block parser.

    Validates: Requirements 1.4, 2.7
    """

    def test_returns_none_when_absent(self) -> None:
        """A section with no ``### Journal`` heading yields None."""
        assert _extract_journal_subsection("### Information Shared\n- a\n") is None

    def test_parses_all_four_fields(self) -> None:
        """All four narrative fields are extracted verbatim (stripped)."""
        text = (
            "### Journal\n"
            "**What we did:** did\n"
            "**What was produced:** produced\n"
            "**Why it matters:** matters\n"
            "**Bootcamper's takeaway:** takeaway\n"
        )
        assert _extract_journal_subsection(text) == JournalFields(
            "did", "produced", "matters", "takeaway"
        )

    def test_missing_fields_default_to_empty_string(self) -> None:
        """A present-but-partial Journal fills absent fields with empty strings."""
        text = "### Journal\n**What we did:** only this\n"
        assert _extract_journal_subsection(text) == JournalFields(
            "only this", "", "", ""
        )

    def test_stops_at_next_heading(self) -> None:
        """Fields from a following section do not bleed into this Journal."""
        text = (
            "### Journal\n"
            "**What we did:** first\n"
            f"## Module 2: Next {EM_DASH} t\n"
            "**What we did:** second\n"
        )
        assert _extract_journal_subsection(text).what_we_did == "first"


class TestRenderRecapSection:
    """Rendering of structured sections back to canonical Markdown.

    Validates: Requirements 1.3, 1.4, 13.1
    """

    def test_omits_timestamp_suffix_when_empty(self) -> None:
        """An empty timestamp renders a bare ``## Module N: Name`` heading."""
        section = ParsedRecapSection(
            module_number=5,
            module_name="Query",
            timestamp="",
            information_shared=[],
            questions_responses=[],
            actions_taken=[],
            duration=None,
            journal=None,
        )
        rendered = render_recap_section(section)
        assert rendered.startswith("## Module 5: Query\n")
        assert EM_DASH not in rendered.splitlines()[0]

    def test_omits_duration_and_journal_when_absent(self) -> None:
        """No ``### Duration`` or ``### Journal`` is emitted when unset."""
        section = ParsedRecapSection(
            module_number=2,
            module_name="Ingest",
            timestamp="t",
            information_shared=["a"],
            questions_responses=[],
            actions_taken=["b"],
            duration=None,
            journal=None,
        )
        rendered = render_recap_section(section)
        assert "### Duration" not in rendered
        assert "### Journal" not in rendered

    def test_renders_journal_and_duration_when_present(self) -> None:
        """A section with duration and journal emits both subsections."""
        section = ParsedRecapSection(
            module_number=1,
            module_name="Intro",
            timestamp="t",
            information_shared=[],
            questions_responses=[],
            actions_taken=[],
            duration="1h",
            journal=JournalFields("did", "made", "matters", "N/A"),
        )
        rendered = render_recap_section(section)
        assert "### Duration\n1h" in rendered
        assert "### Journal" in rendered
        assert "**Bootcamper's takeaway:** N/A" in rendered

    def test_empty_questions_render_none_placeholder(self) -> None:
        """No pairs render the ``- None`` empty-section placeholder."""
        section = ParsedRecapSection(
            module_number=1,
            module_name="Intro",
            timestamp="t",
            information_shared=[],
            questions_responses=[],
            actions_taken=[],
            duration=None,
            journal=None,
        )
        rendered = render_recap_section(section)
        assert "### Questions & Responses\n\n- None" in rendered


class TestRoundTrip:
    """parse(render_all(parse(x))) == parse(x) on concrete inputs (Property 1).

    Validates: Requirements 2.7
    """

    def test_full_section_round_trips(self) -> None:
        """A fully populated section survives a parse/render/parse cycle."""
        once = parse_recap_sections(_full_section_markdown())
        twice = parse_recap_sections(_render_all(once))
        assert once == twice

    def test_render_is_idempotent(self) -> None:
        """Rendering parsed output twice yields identical Markdown."""
        once = parse_recap_sections(_full_section_markdown())
        first = _render_all(once)
        second = _render_all(parse_recap_sections(first))
        assert first == second

    def test_legacy_section_without_journal_round_trips(self) -> None:
        """A pre-consolidation section (no Journal) round-trips with journal None."""
        legacy = (
            f"## Module 2: Ingest {EM_DASH} t\n\n"
            "### Information Shared\n- Loaded data\n\n### Actions Taken\n- Ran loader\n"
        )
        once = parse_recap_sections(legacy)
        assert once[0].journal is None
        assert once == parse_recap_sections(_render_all(once))
