"""Unit tests for the legacy-journal -> Consolidated_Log migration.

Feature: journal-recap-consolidation — task 3.3.

Example-based and edge-case coverage for ``migrate_journal_to_recap`` and its
``--migrate`` CLI mode in ``senzing-bootcamp/scripts/completion_artifacts.py``:

    migrate_journal_to_recap    folds each legacy ``docs/bootcamp_journal.md``
                                entry into the matching ``## Module N:`` recap
                                section as a ``### Journal`` subsection, creating
                                a minimal section when the recap has no matching
                                module, preserving existing recap bytes, and
                                skipping sections that already carry a Journal
                                subsection (idempotent).
    main([..., "--migrate"])    the one-time migration CLI: requires --recap and
                                --journal, prints the merged/created/already
                                report, exits 0 on success and 1 when an argument
                                is missing.

The legacy journal format is ``## Module N: [Name] — Completed [timestamp]``
followed by the four bold narrative fields (``**What we did:**``,
``**What was produced:**``, ``**Why it matters:**``,
``**Bootcamper's takeaway:**``). The consolidated round-trip property is proven
in the Hypothesis suite; these tests pin concrete migration behavior.

Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 11.5
"""

from __future__ import annotations

import sys
from pathlib import Path

_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

import pytest  # noqa: E402

import completion_artifacts as planner  # noqa: E402

JournalFields = planner.JournalFields
migrate_journal_to_recap = planner.migrate_journal_to_recap
parse_recap_sections = planner.parse_recap_sections

EM_DASH = "\u2014"


# ---------------------------------------------------------------------------
# Content builders
# ---------------------------------------------------------------------------


def _recap_header() -> str:
    """Return the canonical Consolidated_Log header block."""
    return (
        "# Senzing Bootcamp Recap\n"
        "\n"
        "**Bootcamper:** Bootcamper\n"
        "\n"
        "---\n"
    )


def _recap_section(
    module: int,
    name: str,
    *,
    timestamp: str = "2025-01-10T10:12:00Z",
    info: str = "Identified duplicate customers",
    duration: str | None = "1h 12m",
) -> str:
    """Return one structured recap section without a ``### Journal`` subsection."""
    lines = [
        f"## Module {module}: {name} {EM_DASH} {timestamp}",
        "",
        "### Information Shared",
        f"- {info}",
        "",
        "### Actions Taken",
        f"- Completed module {module} work",
        "",
    ]
    if duration is not None:
        lines += ["### Duration", duration, ""]
    lines += ["---", ""]
    return "\n".join(lines)


def _journal_entry(
    module: int,
    name: str,
    fields: JournalFields,
    *,
    timestamp: str = "2025-01-10T10:12:00Z",
) -> str:
    """Return one legacy journal entry in the retired narrative format."""
    return (
        f"## Module {module}: {name} {EM_DASH} Completed {timestamp}\n"
        "\n"
        f"**What we did:** {fields.what_we_did}\n"
        f"**What was produced:** {fields.what_was_produced}\n"
        f"**Why it matters:** {fields.why_it_matters}\n"
        f"**Bootcamper's takeaway:** {fields.bootcamper_takeaway}\n"
    )


def _journal_header() -> str:
    """Return the legacy journal header block."""
    return "# Senzing Bootcamp Journal\n\n**Bootcamper:** Bootcamper\n\n---\n\n"


def _write(path: Path, text: str) -> None:
    """Write *text* to *path* (UTF-8)."""
    path.write_text(text, encoding="utf-8")


def _section_by_module(content: str, module: int) -> planner.ParsedRecapSection:
    """Return the parsed recap section for *module* (asserts exactly one)."""
    matches = [s for s in parse_recap_sections(content) if s.module_number == module]
    assert len(matches) == 1, f"expected exactly one Module {module} section"
    return matches[0]


# ---------------------------------------------------------------------------
# Merge into existing recap sections
# ---------------------------------------------------------------------------


class TestMergeIntoExistingSection:
    """Journal entries fold into matching recap sections without content loss.

    Validates: Requirements 2.1, 2.3, 2.6
    """

    def test_merges_journal_into_existing_section(self, tmp_path: Path) -> None:
        """A journal entry becomes the matching section's ### Journal subsection."""
        recap = tmp_path / "bootcamp_recap.md"
        journal = tmp_path / "bootcamp_journal.md"
        fields = JournalFields(
            what_we_did="Framed the business problem",
            what_was_produced="docs/problem.md",
            why_it_matters="Sets the baseline",
            bootcamper_takeaway="Learned entity resolution basics",
        )
        _write(recap, _recap_header() + "\n" + _recap_section(1, "Business Problem"))
        _write(journal, _journal_header() + _journal_entry(1, "Business Problem", fields))

        report = migrate_journal_to_recap(str(recap), str(journal))

        assert report.modules_merged == [1]
        assert report.modules_created == []
        assert report.already_consolidated == []
        assert _section_by_module(recap.read_text(encoding="utf-8"), 1).journal == fields

    def test_preserves_existing_section_content(self, tmp_path: Path) -> None:
        """Merging leaves the section's existing subsections intact (append-around)."""
        recap = tmp_path / "bootcamp_recap.md"
        journal = tmp_path / "bootcamp_journal.md"
        _write(
            recap,
            _recap_header()
            + "\n"
            + _recap_section(1, "Business Problem", info="Chose SQLite"),
        )
        _write(
            journal,
            _journal_header()
            + _journal_entry(
                1,
                "Business Problem",
                JournalFields("did", "made", "matters", "N/A"),
            ),
        )

        migrate_journal_to_recap(str(recap), str(journal))

        section = _section_by_module(recap.read_text(encoding="utf-8"), 1)
        assert section.information_shared == ["Chose SQLite"]
        assert section.actions_taken == ["Completed module 1 work"]
        assert section.duration == "1h 12m"

    def test_every_journal_field_value_appears_after_merge(self, tmp_path: Path) -> None:
        """All four narrative field values survive the merge (Requirement 2.6)."""
        recap = tmp_path / "bootcamp_recap.md"
        journal = tmp_path / "bootcamp_journal.md"
        fields = JournalFields(
            what_we_did="unique-did-marker",
            what_was_produced="unique-produced-marker",
            why_it_matters="unique-matters-marker",
            bootcamper_takeaway="unique-takeaway-marker",
        )
        _write(recap, _recap_header() + "\n" + _recap_section(3, "Load"))
        _write(journal, _journal_header() + _journal_entry(3, "Load", fields))

        migrate_journal_to_recap(str(recap), str(journal))

        text = recap.read_text(encoding="utf-8")
        for value in (
            "unique-did-marker",
            "unique-produced-marker",
            "unique-matters-marker",
            "unique-takeaway-marker",
        ):
            assert value in text

    def test_preserves_bytes_of_other_sections(self, tmp_path: Path) -> None:
        """Sections without a journal entry are left byte-for-byte unchanged."""
        recap = tmp_path / "bootcamp_recap.md"
        journal = tmp_path / "bootcamp_journal.md"
        untouched = _recap_section(9, "Advanced", timestamp="2025-03-01T00:00:00Z")
        _write(
            recap,
            _recap_header() + "\n" + _recap_section(1, "Business Problem") + untouched,
        )
        _write(
            journal,
            _journal_header()
            + _journal_entry(1, "Business Problem", JournalFields("a", "b", "c", "d")),
        )

        migrate_journal_to_recap(str(recap), str(journal))

        assert untouched in recap.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Create new sections when the recap has no matching module
# ---------------------------------------------------------------------------


class TestCreateNewSection:
    """A journal entry for an uncovered module creates a recap section.

    Validates: Requirements 2.2
    """

    def test_creates_section_when_recap_lacks_module(self, tmp_path: Path) -> None:
        """A journal-only module gets a new consolidated section preserving its fields."""
        recap = tmp_path / "bootcamp_recap.md"
        journal = tmp_path / "bootcamp_journal.md"
        fields = JournalFields(
            what_we_did="Tuned the engine",
            what_was_produced="perf.json",
            why_it_matters="Faster resolution",
            bootcamper_takeaway="N/A",
        )
        _write(recap, _recap_header() + "\n" + _recap_section(1, "Business Problem"))
        _write(journal, _journal_header() + _journal_entry(8, "Performance", fields))

        report = migrate_journal_to_recap(str(recap), str(journal))

        assert report.modules_created == [8]
        assert report.modules_merged == []
        created = _section_by_module(recap.read_text(encoding="utf-8"), 8)
        assert created.module_name == "Performance"
        assert created.journal == fields

    def test_created_section_does_not_disturb_existing_ones(self, tmp_path: Path) -> None:
        """Creating a new section leaves the existing section content intact."""
        recap = tmp_path / "bootcamp_recap.md"
        journal = tmp_path / "bootcamp_journal.md"
        _write(recap, _recap_header() + "\n" + _recap_section(1, "Business Problem"))
        _write(
            journal,
            _journal_header()
            + _journal_entry(8, "Performance", JournalFields("a", "b", "c", "d")),
        )

        migrate_journal_to_recap(str(recap), str(journal))

        text = recap.read_text(encoding="utf-8")
        existing = _section_by_module(text, 1)
        assert existing.information_shared == ["Identified duplicate customers"]
        assert existing.journal is None  # module 1 had no journal entry


# ---------------------------------------------------------------------------
# Idempotency
# ---------------------------------------------------------------------------


class TestIdempotency:
    """Re-running the migration produces no further changes.

    Validates: Requirements 2.4
    """

    def test_second_run_is_a_no_op(self, tmp_path: Path) -> None:
        """A second migration reports all modules already consolidated, no writes."""
        recap = tmp_path / "bootcamp_recap.md"
        journal = tmp_path / "bootcamp_journal.md"
        _write(
            recap,
            _recap_header()
            + "\n"
            + _recap_section(1, "Business Problem")
            + _recap_section(2, "Ingest", timestamp="2025-01-11T00:00:00Z"),
        )
        _write(
            journal,
            _journal_header()
            + _journal_entry(1, "Business Problem", JournalFields("a", "b", "c", "d"))
            + "\n"
            + _journal_entry(8, "Performance", JournalFields("e", "f", "g", "h")),
        )

        migrate_journal_to_recap(str(recap), str(journal))
        after_first = recap.read_text(encoding="utf-8")

        second = migrate_journal_to_recap(str(recap), str(journal))

        assert recap.read_text(encoding="utf-8") == after_first
        assert second.modules_merged == []
        assert second.modules_created == []
        assert sorted(second.already_consolidated) == [1, 8]

    def test_running_three_times_is_stable(self, tmp_path: Path) -> None:
        """The consolidated file is a fixed point after the first migration."""
        recap = tmp_path / "bootcamp_recap.md"
        journal = tmp_path / "bootcamp_journal.md"
        _write(recap, _recap_header() + "\n" + _recap_section(1, "Business Problem"))
        _write(
            journal,
            _journal_header()
            + _journal_entry(1, "Business Problem", JournalFields("a", "b", "c", "d")),
        )

        migrate_journal_to_recap(str(recap), str(journal))
        snapshot = recap.read_text(encoding="utf-8")
        migrate_journal_to_recap(str(recap), str(journal))
        migrate_journal_to_recap(str(recap), str(journal))

        assert recap.read_text(encoding="utf-8") == snapshot


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------


class TestEdgeCases:
    """Empty journal, empty/absent recap, partial overlap, unparseable entries.

    Validates: Requirements 2.2, 2.3, 2.4, 2.5
    """

    def test_empty_journal_is_a_no_op(self, tmp_path: Path) -> None:
        """A journal with no module headings leaves the recap unchanged."""
        recap = tmp_path / "bootcamp_recap.md"
        journal = tmp_path / "bootcamp_journal.md"
        original = _recap_header() + "\n" + _recap_section(1, "Business Problem")
        _write(recap, original)
        _write(journal, "# Senzing Bootcamp Journal\n\nNo entries recorded yet.\n")

        report = migrate_journal_to_recap(str(recap), str(journal))

        assert report.modules_merged == []
        assert report.modules_created == []
        assert report.already_consolidated == []
        assert recap.read_text(encoding="utf-8") == original

    def test_absent_journal_is_a_no_op(self, tmp_path: Path) -> None:
        """No journal file (recap-only project) is treated as already consolidated."""
        recap = tmp_path / "bootcamp_recap.md"
        journal = tmp_path / "bootcamp_journal.md"  # never created
        original = _recap_header() + "\n" + _recap_section(1, "Business Problem")
        _write(recap, original)

        report = migrate_journal_to_recap(str(recap), str(journal))

        assert report.modules_merged == []
        assert report.modules_created == []
        assert recap.read_text(encoding="utf-8") == original

    def test_absent_recap_is_created_from_journal(self, tmp_path: Path) -> None:
        """When no recap exists, journal entries seed a new Consolidated_Log."""
        recap = tmp_path / "bootcamp_recap.md"  # never created
        journal = tmp_path / "bootcamp_journal.md"
        fields = JournalFields("did", "made", "matters", "takeaway")
        _write(journal, _journal_header() + _journal_entry(1, "Intro", fields))

        report = migrate_journal_to_recap(str(recap), str(journal))

        assert recap.is_file()
        assert report.modules_created == [1]
        assert _section_by_module(recap.read_text(encoding="utf-8"), 1).journal == fields

    def test_partial_overlap_merges_and_creates(self, tmp_path: Path) -> None:
        """Overlapping modules merge; journal-only modules are created."""
        recap = tmp_path / "bootcamp_recap.md"
        journal = tmp_path / "bootcamp_journal.md"
        _write(recap, _recap_header() + "\n" + _recap_section(1, "Business Problem"))
        _write(
            journal,
            _journal_header()
            + _journal_entry(1, "Business Problem", JournalFields("a", "b", "c", "d"))
            + "\n"
            + _journal_entry(8, "Performance", JournalFields("e", "f", "g", "h")),
        )

        report = migrate_journal_to_recap(str(recap), str(journal))

        assert report.modules_merged == [1]
        assert report.modules_created == [8]
        modules = {s.module_number for s in parse_recap_sections(recap.read_text(encoding="utf-8"))}
        assert modules == {1, 8}

    def test_unparseable_entries_are_skipped(self, tmp_path: Path) -> None:
        """Non-module headings are ignored while parseable entries still migrate."""
        recap = tmp_path / "bootcamp_recap.md"
        journal = tmp_path / "bootcamp_journal.md"
        _write(recap, _recap_header() + "\n" + _recap_section(2, "Ingest"))
        _write(
            journal,
            "## Some Random Heading\n\ngarbage prose\n\n"
            "## Module: missing number\n\nmore garbage\n\n"
            + _journal_entry(2, "Ingest", JournalFields("loaded", "out", "m", "N/A")),
        )

        report = migrate_journal_to_recap(str(recap), str(journal))

        assert report.modules_merged == [2]
        assert report.modules_created == []
        section = _section_by_module(recap.read_text(encoding="utf-8"), 2)
        assert section.journal == JournalFields("loaded", "out", "m", "N/A")

    def test_existing_journal_subsection_is_left_untouched(self, tmp_path: Path) -> None:
        """A section that already has ### Journal is reported already-consolidated."""
        recap = tmp_path / "bootcamp_recap.md"
        journal = tmp_path / "bootcamp_journal.md"
        preexisting = JournalFields("kept", "kept2", "kept3", "kept4")
        # First migration folds the journal into the recap.
        _write(recap, _recap_header() + "\n" + _recap_section(1, "Business Problem"))
        _write(
            journal,
            _journal_header() + _journal_entry(1, "Business Problem", preexisting),
        )
        migrate_journal_to_recap(str(recap), str(journal))

        # A journal entry with different values must NOT overwrite the existing one.
        _write(
            journal,
            _journal_header()
            + _journal_entry(
                1,
                "Business Problem",
                JournalFields("new", "new2", "new3", "new4"),
            ),
        )
        report = migrate_journal_to_recap(str(recap), str(journal))

        assert report.already_consolidated == [1]
        assert _section_by_module(recap.read_text(encoding="utf-8"), 1).journal == preexisting


# ---------------------------------------------------------------------------
# --migrate CLI mode
# ---------------------------------------------------------------------------


class TestMigrateCLI:
    """The one-time ``--migrate`` CLI mode.

    Validates: Requirements 2.1, 2.2, 11.5
    """

    def test_migrate_mode_reports_and_exits_zero(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """--migrate merges, prints the report, and exits 0 on success."""
        recap = tmp_path / "bootcamp_recap.md"
        journal = tmp_path / "bootcamp_journal.md"
        _write(recap, _recap_header() + "\n" + _recap_section(1, "Business Problem"))
        _write(
            journal,
            _journal_header()
            + _journal_entry(1, "Business Problem", JournalFields("a", "b", "c", "d"))
            + "\n"
            + _journal_entry(8, "Performance", JournalFields("e", "f", "g", "h")),
        )

        with pytest.raises(SystemExit) as exc:
            planner.main(["--recap", str(recap), "--journal", str(journal), "--migrate"])

        assert exc.value.code == 0
        out = capsys.readouterr().out
        assert "Modules merged:" in out
        assert "[1]" in out
        assert "Modules created:" in out
        assert "[8]" in out
        assert "Already consolidated:" in out
        assert _section_by_module(recap.read_text(encoding="utf-8"), 1).journal is not None

    def test_migrate_mode_is_idempotent_via_cli(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """A second --migrate run reports the modules as already consolidated."""
        recap = tmp_path / "bootcamp_recap.md"
        journal = tmp_path / "bootcamp_journal.md"
        _write(recap, _recap_header() + "\n" + _recap_section(1, "Business Problem"))
        _write(
            journal,
            _journal_header()
            + _journal_entry(1, "Business Problem", JournalFields("a", "b", "c", "d")),
        )

        with pytest.raises(SystemExit):
            planner.main(["--recap", str(recap), "--journal", str(journal), "--migrate"])
        capsys.readouterr()  # discard first-run output

        with pytest.raises(SystemExit) as exc:
            planner.main(["--recap", str(recap), "--journal", str(journal), "--migrate"])

        assert exc.value.code == 0
        out = capsys.readouterr().out
        assert "Already consolidated:     [1]" in out

    def test_migrate_requires_journal_argument(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """--migrate without --journal exits 1 with a descriptive message."""
        recap = tmp_path / "bootcamp_recap.md"
        _write(recap, _recap_header() + "\n" + _recap_section(1, "Business Problem"))

        with pytest.raises(SystemExit) as exc:
            planner.main(["--recap", str(recap), "--migrate"])

        assert exc.value.code == 1
        assert "--migrate requires --journal" in capsys.readouterr().err

    def test_migrate_requires_recap_argument(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """--migrate without --recap exits 1 with a descriptive message."""
        journal = tmp_path / "bootcamp_journal.md"
        _write(
            journal,
            _journal_header()
            + _journal_entry(1, "Business Problem", JournalFields("a", "b", "c", "d")),
        )

        with pytest.raises(SystemExit) as exc:
            planner.main(["--journal", str(journal), "--migrate"])

        assert exc.value.code == 1
        assert "--migrate requires --recap" in capsys.readouterr().err
