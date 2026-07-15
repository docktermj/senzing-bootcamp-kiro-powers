"""Property-based tests for Consolidated_Log parsing, rendering, and migration.

Feature: journal-recap-consolidation — task 3.2.

Hypothesis-driven coverage of the correctness properties from the design's
Correctness Properties section, exercised against the parse/render/migration
surface in ``senzing-bootcamp/scripts/completion_artifacts.py``:

    Property 1  Round-trip parsing preserves structure:
                parse(render_all(parse(log))) == parse(log).
    Property 2  Exactly one ``## Module N:`` section per completed module after
                any sequence of consolidation ops (backfill, migration).
    Property 3  Every consolidated section produced by the workflow carries a
                ``### Journal`` subsection with all four narrative fields.
    Property 4  Migration preserves all journal content (merge and create).
    Property 5  Migration and backfill are idempotent.
    Property 6  Existing content is preserved (append-only).

Validates: Requirements 1.2, 1.3, 1.4, 1.6, 2.1, 2.3, 2.4, 2.6, 2.7, 5.4, 5.5
"""

from __future__ import annotations

import json
import sys
import tempfile
from datetime import datetime
from pathlib import Path

from hypothesis import given
from hypothesis import strategies as st

_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

import completion_artifacts as planner  # noqa: E402

JournalFields = planner.JournalFields
ParsedRecapSection = planner.ParsedRecapSection
MigrationReport = planner.MigrationReport
parse_recap_sections = planner.parse_recap_sections
render_recap_section = planner.render_recap_section
render_backfill_section = planner.render_backfill_section
migrate_journal_to_recap = planner.migrate_journal_to_recap
backfill_recap_sections = planner.backfill_recap_sections

EM_DASH = "\u2014"

# Word alphabets deliberately exclude the structural characters the parser keys
# on so generated content never accidentally forges a heading, list marker, or
# bold field label: no ``*`` (bold ``**Label:**``), no ``#`` (headings), no
# em-dash (heading name/timestamp delimiter), no whitespace/newlines (line and
# item boundaries). Words are joined with single spaces so every value equals
# its own ``str.strip()`` and stays on one line — the canonical form the
# parse/render pair preserves.
_WORD_ALPHABET = (
    "abcdefghijklmnopqrstuvwxyz"
    "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    "0123456789"
    ".,:;!?()/_-"
)
_NAME_WORD_ALPHABET = (
    "abcdefghijklmnopqrstuvwxyz"
    "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    "0123456789"
)

_WORD = st.text(alphabet=_WORD_ALPHABET, min_size=1, max_size=10)
_NAME_WORD = st.text(alphabet=_NAME_WORD_ALPHABET, min_size=1, max_size=12)


@st.composite
def st_item_text(draw) -> str:
    """Draw a non-empty, single-line, already-stripped list/Q&R item string."""
    words = draw(st.lists(_WORD, min_size=1, max_size=5))
    return " ".join(words)


@st.composite
def st_module_name(draw) -> str:
    """Draw a simple multi-word module display name (no delimiters)."""
    words = draw(st.lists(_NAME_WORD, min_size=1, max_size=4))
    return " ".join(words)


def st_timestamp_text():
    """Strategy for a non-empty ISO 8601 timestamp string (no spaces/em-dash)."""
    return st.datetimes(
        min_value=datetime(2020, 1, 1), max_value=datetime(2030, 1, 1)
    ).map(lambda moment: moment.isoformat())


def st_duration_text():
    """Strategy for a realistic single-line Duration string."""
    return st.sampled_from(
        ["45s", "30m", "1h", "1h 12m", "2h 30m", "2d 3h 5m", "0m", "3d"]
    )


@st.composite
def st_field_value(draw) -> str:
    """Draw one narrative field value: prose, the ``N/A`` sentinel, or empty.

    Every value is single-line and already stripped, so it survives the
    legacy-journal parse, the migration render, and the recap re-parse unchanged.
    """
    kind = draw(st.sampled_from(["text", "na", "empty"]))
    if kind == "na":
        return "N/A"
    if kind == "empty":
        return ""
    words = draw(st.lists(_WORD, min_size=1, max_size=6))
    return " ".join(words)


@st.composite
def st_journal_fields(draw) -> JournalFields:
    """Draw a :class:`JournalFields` with four valid narrative values."""
    return JournalFields(
        what_we_did=draw(st_field_value()),
        what_was_produced=draw(st_field_value()),
        why_it_matters=draw(st_field_value()),
        bootcamper_takeaway=draw(st_field_value()),
    )


@st.composite
def st_recap_section(draw, *, module_number: int | None = None,
                     with_journal: bool | None = None) -> ParsedRecapSection:
    """Draw a valid :class:`ParsedRecapSection`.

    Args:
        draw: The Hypothesis draw callable.
        module_number: Fix the module number (otherwise drawn from 1..12).
        with_journal: Force the ``### Journal`` subsection present/absent
            (otherwise drawn).

    Returns:
        A section whose fields all lie in the canonical form the parse/render
        pair round-trips.
    """
    if module_number is None:
        module_number = draw(st.integers(min_value=1, max_value=12))
    module_name = draw(st_module_name())
    timestamp = draw(st.one_of(st.just(""), st_timestamp_text()))
    information_shared = draw(st.lists(st_item_text(), max_size=4))
    questions_responses = draw(
        st.lists(st.tuples(st_item_text(), st_item_text()), max_size=3)
    )
    actions_taken = draw(st.lists(st_item_text(), max_size=4))
    duration = draw(st.one_of(st.none(), st_duration_text()))
    if with_journal is None:
        with_journal = draw(st.booleans())
    journal = draw(st_journal_fields()) if with_journal else None
    return ParsedRecapSection(
        module_number=module_number,
        module_name=module_name,
        timestamp=timestamp,
        information_shared=information_shared,
        questions_responses=questions_responses,
        actions_taken=actions_taken,
        duration=duration,
        journal=journal,
    )


@st.composite
def st_consolidated_log(draw, *, min_modules: int = 1, max_modules: int = 4,
                        with_journal: bool | None = None) -> str:
    """Draw a canonical Consolidated_Log string with unique per-module sections.

    Sections are rendered through :func:`render_recap_section` beneath the
    standard recap header, so the result is exactly the shape the workflow
    writes to ``docs/bootcamp_recap.md``.
    """
    numbers = draw(
        st.lists(
            st.integers(min_value=1, max_value=12),
            min_size=min_modules,
            max_size=max_modules,
            unique=True,
        )
    )
    sections = [
        draw(st_recap_section(module_number=number, with_journal=with_journal))
        for number in numbers
    ]
    return planner._RECAP_HEADER + _render_all(sections)


@st.composite
def st_legacy_journal(draw, *, modules: list[int] | None = None):
    """Draw a Legacy_Journal_File plus the per-module fields it encodes.

    Args:
        draw: The Hypothesis draw callable.
        modules: Fix the module numbers (otherwise 1..4 unique modules drawn).

    Returns:
        A ``(journal_markdown, entries)`` tuple where ``entries`` maps each
        module number to the :class:`JournalFields` written for it. The rendered
        text uses the retired journal heading form
        ``## Module N: Name — Completed [timestamp]`` followed by the four
        narrative field lines.
    """
    if modules is None:
        modules = draw(
            st.lists(st.integers(min_value=1, max_value=12),
                     min_size=1, max_size=4, unique=True)
        )
    entries: dict[int, JournalFields] = {}
    lines = ["# Senzing Bootcamp Journal", ""]
    for module in sorted(modules):
        fields = draw(st_journal_fields())
        name = draw(st_module_name())
        timestamp = draw(st_timestamp_text())
        entries[module] = fields
        lines.append(f"## Module {module}: {name} {EM_DASH} Completed {timestamp}")
        for attr, label in planner._JOURNAL_FIELDS:
            lines.append(f"**{label}:** {getattr(fields, attr)}")
        lines.append("")
    return "\n".join(lines) + "\n", entries


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _render_all(sections: list[ParsedRecapSection]) -> str:
    """Render and concatenate every section, as the workflow would."""
    return "".join(render_recap_section(section) for section in sections)


def _section_module_numbers(content: str) -> list[int]:
    """Return every ``## Module N`` heading's module number in document order.

    The list preserves duplicates so callers can assert uniqueness.
    """
    return [int(number) for number in planner._SECTION_RE.findall(content)]


def _write_progress(path: Path, modules_completed: list[int]) -> None:
    """Write a minimal ``bootcamp_progress.json`` at *path*."""
    path.write_text(
        json.dumps({"modules_completed": modules_completed}), encoding="utf-8"
    )


# ===========================================================================
# Property 1 — round-trip parsing preserves structure
# ===========================================================================


class TestRoundTripProperty:
    """parse(render_all(parse(log))) == parse(log) for any Consolidated_Log.

    Feature: journal-recap-consolidation, Property 1: Round-trip parsing
    preserves structure.

    Validates: Requirements 1.3, 1.6, 2.7
    """

    @given(log=st_consolidated_log(min_modules=0))
    def test_parse_render_parse_is_stable(self, log: str) -> None:
        """Re-parsing rendered sections yields structurally identical sections."""
        once = parse_recap_sections(log)
        twice = parse_recap_sections(_render_all(once))
        assert once == twice

    @given(log=st_consolidated_log(min_modules=0))
    def test_render_is_idempotent(self, log: str) -> None:
        """Rendering the parsed sections is a fixed point of parse+render."""
        once = parse_recap_sections(log)
        first = _render_all(once)
        second = _render_all(parse_recap_sections(first))
        assert first == second


# ===========================================================================
# Property 2 — exactly one section per completed module
# ===========================================================================


class TestSectionUniqueness:
    """Consolidation ops keep exactly one ``## Module N:`` section per module.

    Feature: journal-recap-consolidation, Property 2: Exactly one section per
    completed module.

    Validates: Requirements 1.2
    """

    @given(completed=st.lists(st.integers(min_value=1, max_value=12),
                              min_size=0, max_size=6, unique=True))
    def test_backfill_one_section_per_completed_module(self, completed) -> None:
        """Backfilling a fresh recap yields one section per completed module."""
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            progress = base / "bootcamp_progress.json"
            recap = base / "bootcamp_recap.md"
            _write_progress(progress, completed)

            backfill_recap_sections(str(progress), str(recap), module_names={})

            content = recap.read_text(encoding="utf-8") if recap.is_file() else ""
            numbers = _section_module_numbers(content)
            assert sorted(numbers) == sorted(completed)
            assert len(numbers) == len(set(numbers))

    @given(data=st.data(),
           completed=st.lists(st.integers(min_value=1, max_value=12),
                              min_size=2, max_size=6, unique=True))
    def test_backfill_never_duplicates_existing_sections(self, data, completed) -> None:
        """Sections already on disk are not re-emitted when backfilling the rest."""
        existing = sorted(set(data.draw(st.lists(st.sampled_from(completed), unique=True))))
        seeded = "".join(render_backfill_section(module) for module in existing)
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            progress = base / "bootcamp_progress.json"
            recap = base / "bootcamp_recap.md"
            _write_progress(progress, completed)
            recap.write_text(planner._RECAP_HEADER + seeded, encoding="utf-8")

            backfill_recap_sections(str(progress), str(recap), module_names={})

            numbers = _section_module_numbers(recap.read_text(encoding="utf-8"))
            assert sorted(set(numbers)) == sorted(completed)
            assert len(numbers) == len(set(numbers))

    @given(case=st_legacy_journal(), data=st.data())
    def test_migration_never_duplicates_sections(self, case, data) -> None:
        """After migration the recap covers A∪B with one section per module."""
        journal_text, entries = case
        journal_modules = set(entries)
        recap_modules = sorted(
            set(data.draw(st.lists(st.integers(min_value=1, max_value=12),
                                   max_size=5, unique=True)))
        )
        sections = [
            data.draw(st_recap_section(module_number=module, with_journal=False))
            for module in recap_modules
        ]
        recap_content = planner._RECAP_HEADER + _render_all(sections)
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            recap = base / "bootcamp_recap.md"
            journal = base / "bootcamp_journal.md"
            recap.write_text(recap_content, encoding="utf-8")
            journal.write_text(journal_text, encoding="utf-8")

            migrate_journal_to_recap(str(recap), str(journal))

            numbers = _section_module_numbers(recap.read_text(encoding="utf-8"))
            assert sorted(set(numbers)) == sorted(set(recap_modules) | journal_modules)
            assert len(numbers) == len(set(numbers))


# ===========================================================================
# Property 3 — journal subsection present in every consolidated section
# ===========================================================================


class TestJournalPresence:
    """Every workflow-produced section carries a full ``### Journal`` subsection.

    Feature: journal-recap-consolidation, Property 3: Journal subsection present
    in every consolidated section.

    Validates: Requirements 1.4, 5.4
    """

    @given(module=st.integers(min_value=1, max_value=12))
    def test_backfill_section_renders_journal_scaffold(self, module) -> None:
        """render_backfill_section emits ``### Journal`` with all four fields."""
        rendered = render_backfill_section(module)
        assert planner._JOURNAL_HEADING in rendered
        for _attr, label in planner._JOURNAL_FIELDS:
            assert f"**{label}:**" in rendered

    @given(completed=st.lists(st.integers(min_value=1, max_value=12),
                              min_size=1, max_size=5, unique=True))
    def test_every_backfilled_section_parses_a_journal(self, completed) -> None:
        """Each backfilled section parses to a non-empty JournalFields (N/A scaffold)."""
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            progress = base / "bootcamp_progress.json"
            recap = base / "bootcamp_recap.md"
            _write_progress(progress, completed)

            backfill_recap_sections(str(progress), str(recap), module_names={})

            sections = parse_recap_sections(recap.read_text(encoding="utf-8"))
            assert {section.module_number for section in sections} == set(completed)
            for section in sections:
                assert section.journal is not None
                assert section.journal == JournalFields("N/A", "N/A", "N/A", "N/A")


# ===========================================================================
# Property 4 — migration preserves all journal content
# ===========================================================================


class TestMigrationPreservation:
    """Every legacy journal field value survives into the recap Journal subsection.

    Feature: journal-recap-consolidation, Property 4: Migration preserves all
    journal content.

    Validates: Requirements 2.1, 2.6
    """

    @given(case=st_legacy_journal())
    def test_migration_creates_sections_with_all_fields(self, case) -> None:
        """When the recap lacks the modules, migration creates them losslessly."""
        journal_text, entries = case
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            recap = base / "bootcamp_recap.md"
            journal = base / "bootcamp_journal.md"
            journal.write_text(journal_text, encoding="utf-8")

            report = migrate_journal_to_recap(str(recap), str(journal))

            parsed = {s.module_number: s for s in parse_recap_sections(recap.read_text("utf-8"))}
            assert set(parsed) == set(entries)
            for module, fields in entries.items():
                assert parsed[module].journal == fields
            assert sorted(report.modules_created) == sorted(entries)

    @given(case=st_legacy_journal(), data=st.data())
    def test_migration_merges_fields_into_existing_sections(self, case, data) -> None:
        """When matching journal-less sections exist, migration merges losslessly."""
        journal_text, entries = case
        modules = sorted(entries)
        sections = [
            data.draw(st_recap_section(module_number=module, with_journal=False))
            for module in modules
        ]
        recap_content = planner._RECAP_HEADER + _render_all(sections)
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            recap = base / "bootcamp_recap.md"
            journal = base / "bootcamp_journal.md"
            recap.write_text(recap_content, encoding="utf-8")
            journal.write_text(journal_text, encoding="utf-8")

            report = migrate_journal_to_recap(str(recap), str(journal))

            parsed = {s.module_number: s for s in parse_recap_sections(recap.read_text("utf-8"))}
            for module in modules:
                assert parsed[module].journal == entries[module]
            assert sorted(report.modules_merged) == modules
            assert report.modules_created == []


# ===========================================================================
# Property 5 — migration and backfill are idempotent
# ===========================================================================


class TestIdempotence:
    """Re-running migration or backfill on a consolidated log makes no changes.

    Feature: journal-recap-consolidation, Property 5: Migration and backfill are
    idempotent.

    Validates: Requirements 2.4, 5.5
    """

    @given(case=st_legacy_journal())
    def test_migration_is_idempotent(self, case) -> None:
        """A second migration leaves the file byte-identical and merges nothing."""
        journal_text, entries = case
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            recap = base / "bootcamp_recap.md"
            journal = base / "bootcamp_journal.md"
            journal.write_text(journal_text, encoding="utf-8")

            migrate_journal_to_recap(str(recap), str(journal))
            first = recap.read_text(encoding="utf-8")
            report = migrate_journal_to_recap(str(recap), str(journal))
            second = recap.read_text(encoding="utf-8")

            assert first == second
            assert report.modules_merged == []
            assert report.modules_created == []
            assert sorted(report.already_consolidated) == sorted(entries)

    @given(completed=st.lists(st.integers(min_value=1, max_value=12),
                              min_size=1, max_size=5, unique=True))
    def test_backfill_is_idempotent(self, completed) -> None:
        """A second backfill writes nothing and leaves the file unchanged."""
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            progress = base / "bootcamp_progress.json"
            recap = base / "bootcamp_recap.md"
            _write_progress(progress, completed)

            backfill_recap_sections(str(progress), str(recap), module_names={})
            first = recap.read_text(encoding="utf-8")
            written = backfill_recap_sections(str(progress), str(recap), module_names={})
            second = recap.read_text(encoding="utf-8")

            assert written == []
            assert first == second


# ===========================================================================
# Property 6 — existing content is preserved (append-only)
# ===========================================================================


class TestAppendOnly:
    """Migration and backfill never rewrite existing Consolidated_Log content.

    Feature: journal-recap-consolidation, Property 6: Existing content is
    preserved (append-only).

    Validates: Requirements 2.3
    """

    @given(data=st.data(),
           completed=st.lists(st.integers(min_value=1, max_value=12),
                              min_size=1, max_size=6, unique=True))
    def test_backfill_preserves_original_bytes_as_prefix(self, data, completed) -> None:
        """Backfill appends: the original recap content is a verbatim prefix."""
        existing = sorted(set(data.draw(st.lists(st.sampled_from(completed), unique=True))))
        seeded = "".join(render_backfill_section(module) for module in existing)
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            progress = base / "bootcamp_progress.json"
            recap = base / "bootcamp_recap.md"
            _write_progress(progress, completed)
            recap.write_text(planner._RECAP_HEADER + seeded, encoding="utf-8")
            original = recap.read_text(encoding="utf-8")

            backfill_recap_sections(str(progress), str(recap), module_names={})

            assert recap.read_text(encoding="utf-8").startswith(original)

    @given(case=st_legacy_journal(), data=st.data())
    def test_migration_preserves_every_existing_line(self, case, data) -> None:
        """Migration only inserts/appends, so every original line still appears."""
        journal_text, _entries = case
        recap_modules = sorted(
            set(data.draw(st.lists(st.integers(min_value=1, max_value=12),
                                   max_size=5, unique=True)))
        )
        sections = [
            data.draw(st_recap_section(module_number=module, with_journal=False))
            for module in recap_modules
        ]
        recap_content = planner._RECAP_HEADER + _render_all(sections)
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            recap = base / "bootcamp_recap.md"
            journal = base / "bootcamp_journal.md"
            recap.write_text(recap_content, encoding="utf-8")
            journal.write_text(journal_text, encoding="utf-8")
            original = recap.read_text(encoding="utf-8")

            migrate_journal_to_recap(str(recap), str(journal))

            new_lines = set(recap.read_text(encoding="utf-8").splitlines())
            for line in original.splitlines():
                if line.strip():
                    assert line in new_lines
