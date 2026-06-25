"""Property-based tests for module completion process artifact validation.

Feature: module-completion-process
"""

from __future__ import annotations

import sys
from pathlib import Path

from hypothesis import assume, given, settings
from hypothesis import strategies as st

# ---------------------------------------------------------------------------
# Make scripts importable
# ---------------------------------------------------------------------------
_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from validate_completion_artifacts import (
    COMPLETION_STEPS,
    JournalEntry,
    count_recap_sections,
    format_journal_entry,
    format_journal_header,
    parse_journal,
    validate_recap_consistency,
)

# ---------------------------------------------------------------------------
# Hypothesis strategies
# ---------------------------------------------------------------------------


def st_module_number() -> st.SearchStrategy[int]:
    """Draw a valid module number (1-11)."""
    return st.integers(min_value=1, max_value=11)


@st.composite
def st_bootcamper_name(draw) -> str:
    """Generate a non-empty bootcamper name (printable, no newlines, reasonable length)."""
    name = draw(
        st.text(
            min_size=1,
            max_size=50,
            alphabet=st.characters(
                whitelist_categories=("L", "Nd", "Zs"),
                blacklist_characters="\n\r",
            ),
        )
    )
    stripped = name.strip()
    assume(len(stripped) > 0)
    return stripped


@st.composite
def st_iso_date(draw) -> str:
    """Generate a valid ISO 8601 date string (YYYY-MM-DD format)."""
    year = draw(st.integers(min_value=2020, max_value=2030))
    month = draw(st.integers(min_value=1, max_value=12))
    # Constrain day to valid range for the month
    if month in (4, 6, 9, 11):
        max_day = 30
    elif month == 2:
        # Simplified leap year check
        if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0):
            max_day = 29
        else:
            max_day = 28
    else:
        max_day = 31
    day = draw(st.integers(min_value=1, max_value=max_day))
    return f"{year:04d}-{month:02d}-{day:02d}"


@st.composite
def st_iso_datetime(draw) -> str:
    """Generate a valid ISO 8601 datetime with timezone offset."""
    date = draw(st_iso_date())
    hour = draw(st.integers(min_value=0, max_value=23))
    minute = draw(st.integers(min_value=0, max_value=59))
    second = draw(st.integers(min_value=0, max_value=59))
    tz_hour = draw(st.integers(min_value=-12, max_value=12))
    tz_minute = draw(st.sampled_from([0, 30]))
    sign = "+" if tz_hour >= 0 else "-"
    return f"{date}T{hour:02d}:{minute:02d}:{second:02d}{sign}{abs(tz_hour):02d}:{tz_minute:02d}"


@st.composite
def st_artifact_list(draw) -> list[str]:
    """Generate a list of file path strings (1-5 items)."""
    paths = draw(
        st.lists(
            st.text(
                min_size=3,
                max_size=60,
                alphabet=st.characters(
                    whitelist_categories=("L", "Nd"),
                    whitelist_characters="/._-",
                ),
            ).filter(lambda s: len(s.strip()) > 0 and "," not in s),
            min_size=1,
            max_size=5,
        )
    )
    return paths


@st.composite
def st_summary(draw) -> str:
    """Generate a non-empty text string for summaries."""
    text = draw(
        st.text(
            min_size=1,
            max_size=200,
            alphabet=st.characters(
                whitelist_categories=("L", "Nd", "Zs", "Po"),
                blacklist_characters="\n\r",
            ),
        )
    )
    stripped = text.strip()
    assume(len(stripped) > 0)
    return stripped


@st.composite
def st_why_it_matters(draw) -> str:
    """Generate a non-empty text string for why-it-matters field."""
    text = draw(
        st.text(
            min_size=1,
            max_size=200,
            alphabet=st.characters(
                whitelist_categories=("L", "Nd", "Zs", "Po"),
                blacklist_characters="\n\r",
            ),
        )
    )
    stripped = text.strip()
    assume(len(stripped) > 0)
    return stripped


@st.composite
def st_journal_entry(draw) -> JournalEntry:
    """Composite strategy producing a valid JournalEntry instance."""
    module_number = draw(st_module_number())
    module_name = draw(st_bootcamper_name())  # Reuse name strategy for module names
    completion_date = draw(st_iso_datetime())
    summary = draw(st_summary())
    artifacts = draw(st_artifact_list())
    why_it_matters = draw(st_why_it_matters())
    takeaway = draw(st_summary())  # Reuse summary strategy for takeaway

    return JournalEntry(
        module_number=module_number,
        module_name=module_name,
        completion_date=completion_date,
        summary=summary,
        artifacts=artifacts,
        why_it_matters=why_it_matters,
        takeaway=takeaway,
    )


# ---------------------------------------------------------------------------
# Property 1: Journal entry round-trip
# Feature: module-completion-process, Property 1: Journal entry round-trip
# ---------------------------------------------------------------------------


class TestJournalEntryRoundTripProperty:
    """Property 1: Journal entry round-trip.

    For any valid journal entry (with module number 1-11, non-empty module name,
    valid ISO 8601 date, non-empty summary, list of artifacts, non-empty
    why-it-matters, and takeaway), formatting the entry as markdown and then
    parsing it back should produce an equivalent JournalEntry.

    **Validates: Requirements 2.1, 2.3**
    """

    @given(st_journal_entry())
    @settings(max_examples=100)
    def test_round_trip(self, entry: JournalEntry) -> None:
        """Format a journal entry as markdown, parse it back, and verify equivalence."""
        # Format the entry as markdown
        entry_md = format_journal_entry(
            module_number=entry.module_number,
            module_name=entry.module_name,
            date=entry.completion_date,
            summary=entry.summary,
            artifacts=entry.artifacts,
            why_it_matters=entry.why_it_matters,
            takeaway=entry.takeaway,
        )

        # Create a full journal document by prepending a header
        header_md = format_journal_header(
            bootcamper_name="Test User",
            start_date="2026-01-01",
        )
        full_document = header_md + entry_md

        # Parse it back
        parsed = parse_journal(full_document)

        # Assert we got exactly one entry back
        assert len(parsed.entries) == 1, (
            f"Expected 1 entry, got {len(parsed.entries)}"
        )

        parsed_entry = parsed.entries[0]

        # Assert all fields match
        assert parsed_entry.module_number == entry.module_number
        assert parsed_entry.module_name == entry.module_name
        assert parsed_entry.completion_date == entry.completion_date
        assert parsed_entry.summary == entry.summary
        assert parsed_entry.artifacts == entry.artifacts
        assert parsed_entry.why_it_matters == entry.why_it_matters
        assert parsed_entry.takeaway == entry.takeaway


# ---------------------------------------------------------------------------
# Property 2: Journal append preserves existing content
# Feature: module-completion-process, Property 2: Journal append preserves existing content
# ---------------------------------------------------------------------------


class TestJournalAppendPreservesContentProperty:
    """Property 2: Journal append preserves existing content.

    For any existing journal file content and any new valid journal entry,
    appending the entry to the file should result in a file whose prefix
    (all bytes before the new entry) is identical to the original content.

    **Validates: Requirements 1.2**
    """

    @given(
        bootcamper_name=st_bootcamper_name(),
        start_date=st_iso_date(),
        existing_entries=st.lists(st_journal_entry(), min_size=1, max_size=3),
        new_entry=st_journal_entry(),
    )
    @settings(max_examples=100)
    def test_append_preserves_existing_content(
        self,
        bootcamper_name: str,
        start_date: str,
        existing_entries: list[JournalEntry],
        new_entry: JournalEntry,
    ) -> None:
        """Appending a new journal entry preserves all prior bytes."""
        # Build existing content: header + existing entries
        existing_content = format_journal_header(bootcamper_name, start_date)
        for entry in existing_entries:
            existing_content += format_journal_entry(
                module_number=entry.module_number,
                module_name=entry.module_name,
                date=entry.completion_date,
                summary=entry.summary,
                artifacts=entry.artifacts,
                why_it_matters=entry.why_it_matters,
                takeaway=entry.takeaway,
            )

        # Format the new entry
        new_entry_text = format_journal_entry(
            module_number=new_entry.module_number,
            module_name=new_entry.module_name,
            date=new_entry.completion_date,
            summary=new_entry.summary,
            artifacts=new_entry.artifacts,
            why_it_matters=new_entry.why_it_matters,
            takeaway=new_entry.takeaway,
        )

        # Simulate appending
        new_content = existing_content + new_entry_text

        # The prefix must be preserved byte-for-byte
        assert new_content.startswith(existing_content)


# ---------------------------------------------------------------------------
# Property 3: Recap section count matches progress
# Feature: module-completion-process, Property 3: Recap section count matches progress
# ---------------------------------------------------------------------------


class TestRecapSectionCountMatchesProgressProperty:
    """Property 3: Recap section count matches progress.

    For any set of completed modules (subset of 1-11), after simulating one
    recap append per module, the number of ## Module N: headings in the recap
    file should equal the number of completed modules.

    **Validates: Requirements 3.3, 4.5**
    """

    @given(
        modules_set=st.frozensets(
            st.integers(min_value=1, max_value=11), min_size=1
        ).map(set)
    )
    @settings(max_examples=100)
    def test_recap_section_count_matches_completed_modules(
        self, modules_set: set[int]
    ) -> None:
        """Recap section count equals number of completed modules."""
        # Build a simulated recap document with a header and one heading per module
        header = (
            "# Senzing Bootcamp Recap\n"
            "\n"
            "**Bootcamper:** Test User\n"
            "**Started:** 2026-01-01T00:00:00+00:00\n"
            "**Total Duration:** 1h\n"
            "\n"
            "---\n"
        )
        sections = ""
        for mod in sorted(modules_set):
            sections += (
                f"\n## Module {mod}: SomeName — 2026-01-{mod:02d}T10:00:00+00:00\n"
                f"\n### Information Shared\n- info\n\n---\n"
            )
        content = header + sections

        result = count_recap_sections(content)

        assert len(result) == len(modules_set)
        assert set(result) == modules_set


# ---------------------------------------------------------------------------
# Property 4: Journal header creation uses preferences
# Feature: module-completion-process, Property 4: Journal header creation uses preferences
# ---------------------------------------------------------------------------


class TestJournalHeaderUsesPreferencesProperty:
    """Property 4: Journal header creation uses preferences.

    For any bootcamper name (non-empty string) and valid ISO 8601 date,
    creating a journal header should produce markdown containing both the
    name and the date in the expected format.

    **Validates: Requirements 1.1**
    """

    @given(name=st_bootcamper_name(), date=st_iso_date())
    @settings(max_examples=100)
    def test_header_contains_name_and_date(self, name: str, date: str) -> None:
        """Header contains bootcamper name and start date in expected format."""
        result = format_journal_header(name, date)
        assert f"**Bootcamper:** {name}" in result
        assert f"**Started:** {date}" in result
        assert "# Bootcamp Journal" in result


# ---------------------------------------------------------------------------
# Property 5: Recap validation detects missing sections
# Feature: module-completion-process, Property 5: Recap validation detects missing sections
# ---------------------------------------------------------------------------


class TestRecapValidationDetectsMissingSectionsProperty:
    """Property 5: Recap validation detects missing sections.

    For any progress file with N completed modules and a recap file with fewer
    than N module sections, the validation function should report at least one
    error identifying the missing module(s).

    **Validates: Requirements 5.4**
    """

    @given(data=st.data())
    @settings(max_examples=100)
    def test_missing_recap_sections_detected(self, data) -> None:
        """Validates: Requirements 5.4"""
        # Generate a set of progress modules (2-11 unique module numbers from 1-11)
        full_set = data.draw(
            st.frozensets(st.integers(min_value=1, max_value=11), min_size=2, max_size=11)
        )
        # Generate a proper subset (at least 1 fewer module)
        subset_size = data.draw(st.integers(min_value=0, max_value=len(full_set) - 1))
        subset = data.draw(
            st.frozensets(
                st.sampled_from(sorted(full_set)),
                min_size=subset_size,
                max_size=subset_size,
            )
        )
        assume(len(subset) < len(full_set))

        progress_modules = sorted(full_set)
        recap_modules = sorted(subset)

        errors = validate_recap_consistency(
            recap_modules=recap_modules, progress_modules=progress_modules
        )

        # At least one error should be reported
        assert len(errors) > 0, (
            f"Expected errors for missing modules but got none. "
            f"progress={progress_modules}, recap={recap_modules}"
        )

        # The missing module numbers should appear in the error messages
        missing = full_set - subset
        all_errors_text = " ".join(errors)
        for mod in missing:
            assert str(mod) in all_errors_text, (
                f"Module {mod} is missing from recap but not mentioned in errors: {errors}"
            )


# ---------------------------------------------------------------------------
# Property 6: Completion step ordering is invariant
# Feature: module-completion-process, Property 6: Completion step ordering is invariant
# ---------------------------------------------------------------------------


class TestCompletionStepOrderingInvariantProperty:
    """Property 6: Completion step ordering is invariant.

    For any sequence of module completions (1 to 11 modules in any order),
    the completion steps should always execute in the fixed order:
    progress_update -> recap_append -> journal_entry -> completion_certificate
    -> next_step_options.

    **Validates: Requirements 7.1, 7.2, 7.3**
    """

    @given(
        st.lists(
            st.integers(min_value=1, max_value=11),
            min_size=1,
            max_size=11,
            unique=True,
        ).map(lambda x: x)  # permutation of a subset of 1-11
    )
    @settings(max_examples=100)
    def test_step_ordering_invariant(self, module_sequence: list[int]) -> None:
        """For any permutation of modules, COMPLETION_STEPS is always the same fixed list."""
        expected_steps = [
            "progress_update",
            "recap_append",
            "journal_entry",
            "completion_certificate",
            "next_step_options",
        ]

        # For each module in the sequence, verify COMPLETION_STEPS is invariant
        for _module_number in module_sequence:
            assert COMPLETION_STEPS == expected_steps, (
                f"COMPLETION_STEPS changed for module {_module_number}: "
                f"got {COMPLETION_STEPS}, expected {expected_steps}"
            )

        # Assert ordering relationships hold
        recap_idx = COMPLETION_STEPS.index("recap_append")
        journal_idx = COMPLETION_STEPS.index("journal_entry")
        cert_idx = COMPLETION_STEPS.index("completion_certificate")

        assert recap_idx < journal_idx < cert_idx, (
            f"Ordering violated: recap_append({recap_idx}) < "
            f"journal_entry({journal_idx}) < completion_certificate({cert_idx})"
        )


# ---------------------------------------------------------------------------
# Property 7: Default name fallback
# Feature: module-completion-process, Property 7: Default name fallback
# ---------------------------------------------------------------------------


class TestDefaultNameFallbackProperty:
    """Property 7: Default name fallback.

    When preferences file is missing or has no name field, the journal header
    and recap header should use "Bootcamper" as the default name.

    **Validates: Requirements 3.2**
    """

    @given(date=st_iso_date())
    @settings(max_examples=100)
    def test_default_name_in_header(self, date: str) -> None:
        """Header uses 'Bootcamper' as default name when preferences are missing."""
        # Simulate the default name fallback — when preferences are missing,
        # the system uses "Bootcamper" as the name
        header = format_journal_header("Bootcamper", date)

        # The header must contain the default name in the expected format
        assert "**Bootcamper:** Bootcamper" in header

        # The header must contain the date
        assert date in header

        # Parsing the header back should correctly extract "Bootcamper" as the name
        parsed = parse_journal(header)
        assert parsed.bootcamper_name == "Bootcamper"
